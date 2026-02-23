"""
Nova — NLP Semantic Search Engine
=====================================
Hybrid search combining:
  1. PostgreSQL full-text search (BM25-like ranking via ts_rank_cd)
  2. Semantic embedding similarity (sentence-transformer + cosine)
  3. Trigram fuzzy matching for typo tolerance
  4. Query expansion via synonym mapping and embedding neighbours
  5. Faceted filtering (category, author, language, date, rating)
  6. Search result re-ranking with learning-to-rank signals

The search pipeline:
  query → preprocess → expand → [full-text ∪ semantic ∪ fuzzy] → merge → rerank → return
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from django.conf import settings
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.db.models import Case, F, FloatField, Q, Value, When
from django.db.models.functions import Greatest
from django.utils import timezone

logger = logging.getLogger('nova.intelligence.search')


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SearchRequest:
    query: str
    user_id: Optional[str] = None
    filters: Dict = field(default_factory=dict)
    page: int = 1
    page_size: int = 20
    enable_semantic: bool = True
    enable_fuzzy: bool = True
    enable_expansion: bool = True
    min_score: float = 0.05


@dataclass
class SearchResult:
    book_id: str
    title: str
    score: float
    match_type: str            # 'fulltext', 'semantic', 'fuzzy', 'blended'
    highlights: Dict = field(default_factory=dict)
    explanation: str = ''


@dataclass
class SearchResponse:
    results: List[SearchResult]
    total_count: int
    query: str
    expanded_query: str
    facets: Dict = field(default_factory=dict)
    search_time_ms: float = 0.0
    suggestions: List[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Stop words & synonyms
# ---------------------------------------------------------------------------

STOP_WORDS = frozenset({
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'shall', 'should', 'may', 'might', 'must', 'can',
    'could', 'of', 'in', 'to', 'for', 'with', 'on', 'at', 'from',
    'by', 'about', 'as', 'into', 'through', 'during', 'before',
    'after', 'above', 'below', 'between', 'and', 'but', 'or',
    'not', 'no', 'nor', 'so', 'yet', 'both', 'each', 'every',
    'all', 'any', 'few', 'more', 'most', 'other', 'some', 'such',
    'this', 'that', 'these', 'those', 'i', 'me', 'my', 'we', 'our',
    'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its',
    'they', 'them', 'their', 'what', 'which', 'who', 'whom',
    'book', 'books', 'read', 'reading',
})

SYNONYM_MAP = {
    'ai': ['artificial intelligence', 'machine learning', 'deep learning'],
    'ml': ['machine learning', 'statistical learning'],
    'js': ['javascript'],
    'py': ['python'],
    'db': ['database', 'databases'],
    'sci-fi': ['science fiction'],
    'scifi': ['science fiction'],
    'web dev': ['web development'],
    'devops': ['dev ops', 'development operations', 'ci cd'],
    'oop': ['object oriented programming'],
    'fp': ['functional programming'],
    'ds': ['data science', 'data structures'],
    'algo': ['algorithms', 'algorithm'],
    'bio': ['biology', 'biography', 'biographies'],
    'math': ['mathematics', 'mathematical'],
    'stats': ['statistics', 'statistical'],
    'econ': ['economics', 'economy'],
    'psych': ['psychology', 'psychological'],
    'phil': ['philosophy', 'philosophical'],
    'comp sci': ['computer science'],
    'infosec': ['information security', 'cybersecurity'],
}


# ---------------------------------------------------------------------------
# Query preprocessor
# ---------------------------------------------------------------------------

class QueryPreprocessor:
    """Clean, normalise and tokenise the raw query string."""

    @staticmethod
    def preprocess(raw_query: str) -> str:
        """
        Lowercase, strip punctuation (keep hyphens & apostrophes),
        collapse whitespace.
        """
        q = raw_query.lower().strip()
        # Keep alphanumeric, spaces, hyphens, apostrophes
        q = re.sub(r"[^\w\s\-']", ' ', q)
        q = re.sub(r'\s+', ' ', q).strip()
        return q

    @staticmethod
    def tokenise(query: str) -> List[str]:
        """Split into tokens, removing stop words."""
        tokens = query.split()
        return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]

    @staticmethod
    def expand(query: str) -> str:
        """
        Expand the query with synonyms. Appends alternative terms
        so that PostgreSQL full-text and embedding search both benefit.
        """
        tokens = query.split()
        expansions = set()

        for token in tokens:
            if token in SYNONYM_MAP:
                expansions.update(SYNONYM_MAP[token])

        # Also check bigrams
        for i in range(len(tokens) - 1):
            bigram = f'{tokens[i]} {tokens[i + 1]}'
            if bigram in SYNONYM_MAP:
                expansions.update(SYNONYM_MAP[bigram])

        if expansions:
            expanded = f'{query} {" ".join(expansions)}'
            return expanded
        return query


# ---------------------------------------------------------------------------
# Full-text search (PostgreSQL ts_vector + ts_rank_cd)
# ---------------------------------------------------------------------------

class FullTextSearcher:
    """PostgreSQL full-text search with weighted ranking."""

    WEIGHT_MAP = {
        'title': 'A',       # Highest weight
        'subtitle': 'B',
        'description': 'C',
        'tags': 'D',
    }

    @staticmethod
    def search(query_text: str, filters: Dict, limit: int = 100):
        """
        Execute a PostgreSQL full-text search across the Book model.
        Returns a queryset annotated with `search_rank`.
        """
        from apps.catalog.domain.models import Book

        if not query_text.strip():
            return Book.objects.none()

        # Build weighted search vector
        vector = (
            SearchVector('title', weight='A')
            + SearchVector('subtitle', weight='B')
            + SearchVector('description', weight='C')
        )

        search_query = SearchQuery(query_text, search_type='websearch')

        qs = (
            Book.all_objects
            .filter(deleted_at__isnull=True)
            .annotate(
                search_vector=vector,
                search_rank=SearchRank(
                    vector, search_query,
                    normalization=32,  # Divide by itself + 1
                    cover_density=True,
                ),
            )
            .filter(search_rank__gt=0.0)
        )

        # Apply facet filters
        qs = FullTextSearcher._apply_filters(qs, filters)

        return qs.order_by('-search_rank')[:limit]

    @staticmethod
    def _apply_filters(qs, filters: Dict):
        if not filters:
            return qs

        if 'category_ids' in filters:
            qs = qs.filter(categories__id__in=filters['category_ids'])

        if 'author_ids' in filters:
            qs = qs.filter(authors__id__in=filters['author_ids'])

        if 'language' in filters:
            qs = qs.filter(language=filters['language'])

        if 'min_rating' in filters:
            qs = qs.filter(average_rating__gte=filters['min_rating'])

        if 'year_from' in filters:
            qs = qs.filter(publication_date__year__gte=filters['year_from'])

        if 'year_to' in filters:
            qs = qs.filter(publication_date__year__lte=filters['year_to'])

        if 'has_digital' in filters and filters['has_digital']:
            qs = qs.filter(digital_assets__isnull=False)

        if 'available_only' in filters and filters['available_only']:
            qs = qs.filter(available_copies__gt=0)

        return qs.distinct()


# ---------------------------------------------------------------------------
# Semantic search (embedding cosine similarity)
# ---------------------------------------------------------------------------

class SemanticSearcher:
    """Embedding-based semantic search using sentence transformers."""

    @staticmethod
    def search(
        query_text: str, filters: Dict, limit: int = 50,
    ) -> List[Tuple[str, float]]:
        """
        Encode the query, compare against all book embeddings, return
        (book_id, similarity_score) pairs.
        """
        from apps.intelligence.infrastructure.recommendation_engine import (
            _get_embedding_model,
            cosine_similarity,
        )
        from apps.catalog.domain.models import Book

        try:
            model = _get_embedding_model()
            query_vec = model.encode(query_text, show_progress_bar=False)
        except Exception as exc:
            logger.warning('Semantic search model failed: %s', exc)
            return []

        # Retrieve books with embeddings
        qs = Book.all_objects.filter(
            deleted_at__isnull=True,
            embedding_vector__isnull=False,
        )
        qs = FullTextSearcher._apply_filters(qs, filters)

        scored = []
        for book in qs.iterator():
            try:
                book_vec = np.array(book.embedding_vector)
                sim = cosine_similarity(query_vec, book_vec)
                if sim > 0.25:
                    scored.append((str(book.id), float(sim)))
            except Exception:
                continue

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]


# ---------------------------------------------------------------------------
# Fuzzy search (trigram similarity for typo tolerance)
# ---------------------------------------------------------------------------

class FuzzySearcher:
    """
    PostgreSQL pg_trgm trigram similarity for typo-tolerant matching
    on title and author names.
    """

    @staticmethod
    def search(query_text: str, filters: Dict, limit: int = 50):
        """
        Returns a queryset annotated with `trgm_similarity`.
        """
        from apps.catalog.domain.models import Book

        if not query_text.strip():
            return Book.objects.none()

        qs = (
            Book.all_objects
            .filter(deleted_at__isnull=True)
            .annotate(
                title_sim=TrigramSimilarity('title', query_text),
                subtitle_sim=TrigramSimilarity('subtitle', query_text),
                trgm_similarity=Greatest('title_sim', 'subtitle_sim'),
            )
            .filter(trgm_similarity__gt=0.15)
        )

        qs = FullTextSearcher._apply_filters(qs, filters)
        return qs.order_by('-trgm_similarity')[:limit]


# ---------------------------------------------------------------------------
# Search result merger & re-ranker
# ---------------------------------------------------------------------------

class SearchMerger:
    """
    Merge results from full-text, semantic, and fuzzy search into
    a single ranked list with configurable weights.
    """

    # Blend weights
    W_FULLTEXT = 0.45
    W_SEMANTIC = 0.35
    W_FUZZY = 0.20

    @classmethod
    def merge(
        cls,
        fulltext_results,
        semantic_results: List[Tuple[str, float]],
        fuzzy_results,
        personalisation_boosts: Dict[str, float] = None,
    ) -> List[SearchResult]:
        """
        Merge three result streams into a unified ranked list.
        """
        scores: Dict[str, Dict] = {}

        # Full-text
        for book in fulltext_results:
            bid = str(book.id)
            scores.setdefault(bid, {
                'title': book.title,
                'fulltext': 0.0, 'semantic': 0.0, 'fuzzy': 0.0,
            })
            scores[bid]['fulltext'] = float(getattr(book, 'search_rank', 0))

        # Semantic
        for bid, sim in semantic_results:
            scores.setdefault(bid, {
                'title': '', 'fulltext': 0.0, 'semantic': 0.0, 'fuzzy': 0.0,
            })
            scores[bid]['semantic'] = sim

        # Fuzzy
        for book in fuzzy_results:
            bid = str(book.id)
            scores.setdefault(bid, {
                'title': book.title,
                'fulltext': 0.0, 'semantic': 0.0, 'fuzzy': 0.0,
            })
            scores[bid]['fuzzy'] = float(
                getattr(book, 'trgm_similarity', 0),
            )
            if not scores[bid]['title']:
                scores[bid]['title'] = book.title

        # Compute blended score
        results = []
        for bid, s in scores.items():
            blended = (
                s['fulltext'] * cls.W_FULLTEXT
                + s['semantic'] * cls.W_SEMANTIC
                + s['fuzzy'] * cls.W_FUZZY
            )

            # Personalisation boost
            if personalisation_boosts and bid in personalisation_boosts:
                blended *= (1.0 + personalisation_boosts[bid])

            # Determine primary match type
            match_type = 'blended'
            if s['fulltext'] > 0 and s['semantic'] == 0 and s['fuzzy'] == 0:
                match_type = 'fulltext'
            elif s['semantic'] > 0 and s['fulltext'] == 0 and s['fuzzy'] == 0:
                match_type = 'semantic'
            elif s['fuzzy'] > 0 and s['fulltext'] == 0 and s['semantic'] == 0:
                match_type = 'fuzzy'

            results.append(SearchResult(
                book_id=bid,
                title=s['title'],
                score=round(blended, 4),
                match_type=match_type,
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results


# ---------------------------------------------------------------------------
# Auto-suggestion engine
# ---------------------------------------------------------------------------

class AutoSuggestEngine:
    """
    Generates query auto-suggestions from:
    1. Recent popular search queries
    2. Book titles matching the typed prefix
    3. Author names matching the typed prefix
    """

    @staticmethod
    def suggest(
        prefix: str, limit: int = 8, user_id: str = None,
    ) -> List[dict]:
        """Return up to `limit` suggestions for the given prefix.

        Each suggestion is a dict with 'text' and 'source' keys.
        """
        from apps.intelligence.domain.models import SearchLog
        from apps.catalog.domain.models import Book, Author
        from django.db.models import Count

        prefix = prefix.strip().lower()
        if len(prefix) < 2:
            return []

        suggestions: list[dict] = []

        # 1. Popular past searches matching prefix
        past_queries = (
            SearchLog.objects
            .filter(query_text__istartswith=prefix)
            .values('query_text')
            .annotate(count=Count('id'))
            .order_by('-count')[:limit]
        )
        suggestions.extend(
            {'text': q['query_text'], 'source': 'history'}
            for q in past_queries
        )

        # 2. Book titles
        if len(suggestions) < limit:
            titles = (
                Book.all_objects
                .filter(deleted_at__isnull=True, title__icontains=prefix)
                .values_list('title', flat=True)[:limit - len(suggestions)]
            )
            suggestions.extend(
                {'text': t, 'source': 'book'} for t in titles
            )

        # 3. Author names
        if len(suggestions) < limit:
            authors = (
                Author.objects
                .filter(
                    Q(first_name__icontains=prefix)
                    | Q(last_name__icontains=prefix)
                )
                .values_list('first_name', 'last_name')[:limit - len(suggestions)]
            )
            suggestions.extend(
                {'text': f'{fn} {ln}'.strip(), 'source': 'author'}
                for fn, ln in authors
            )

        # Deduplicate preserving order
        seen = set()
        unique = []
        for s in suggestions:
            key = s['text'].lower()
            if key not in seen:
                seen.add(key)
                unique.append(s)

        return unique[:limit]


# ---------------------------------------------------------------------------
# Main search orchestrator
# ---------------------------------------------------------------------------

class SearchEngine:
    """
    Top-level search orchestrator that coordinates all search strategies
    and produces a unified SearchResponse.
    """

    @staticmethod
    def search(request: SearchRequest) -> SearchResponse:
        """Execute a full hybrid search."""
        import time
        start = time.monotonic()

        preprocessor = QueryPreprocessor()
        clean_query = preprocessor.preprocess(request.query)
        tokens = preprocessor.tokenise(clean_query)

        if not tokens:
            return SearchResponse(
                results=[],
                total_count=0,
                query=request.query,
                expanded_query=clean_query,
            )

        # Query expansion
        if request.enable_expansion:
            expanded = preprocessor.expand(clean_query)
        else:
            expanded = clean_query

        # Full-text search (always runs)
        fulltext_results = FullTextSearcher.search(
            expanded, request.filters, limit=100,
        )

        # Semantic search
        semantic_results = []
        if request.enable_semantic:
            semantic_results = SemanticSearcher.search(
                clean_query, request.filters, limit=50,
            )

        # Fuzzy search
        fuzzy_results = []
        if request.enable_fuzzy:
            fuzzy_results = FuzzySearcher.search(
                clean_query, request.filters, limit=50,
            )

        # Personalisation boosts for authenticated users
        personalisation = None
        if request.user_id:
            personalisation = SearchEngine._get_personalisation_boosts(
                request.user_id,
            )

        # Merge
        merged = SearchMerger.merge(
            fulltext_results,
            semantic_results,
            fuzzy_results,
            personalisation,
        )

        # Filter by minimum score
        merged = [r for r in merged if r.score >= request.min_score]

        total = len(merged)

        # Paginate
        offset = (request.page - 1) * request.page_size
        page_results = merged[offset:offset + request.page_size]

        # Generate suggestions if no results
        suggestions = []
        if not page_results:
            suggestions = AutoSuggestEngine.suggest(clean_query, limit=5)

        elapsed_ms = (time.monotonic() - start) * 1000

        # Facets
        facets = SearchEngine._compute_facets(merged)

        return SearchResponse(
            results=page_results,
            total_count=total,
            query=request.query,
            expanded_query=expanded,
            facets=facets,
            search_time_ms=round(elapsed_ms, 2),
            suggestions=suggestions,
        )

    @staticmethod
    def _get_personalisation_boosts(user_id: str) -> Dict[str, float]:
        """
        Compute per-book personalisation boosts based on user preferences.
        Books matching preferred categories/authors get a 10–20% boost.
        """
        from apps.intelligence.domain.models import UserPreference

        try:
            pref = UserPreference.objects.get(user_id=user_id)
        except UserPreference.DoesNotExist:
            return {}

        boosts = {}
        from apps.catalog.domain.models import Book

        preferred_cats = pref.preferred_categories or []
        preferred_auths = pref.preferred_authors or []

        if preferred_cats:
            for book in Book.objects.filter(
                categories__id__in=preferred_cats,
            ).values_list('id', flat=True).distinct()[:200]:
                boosts[str(book)] = 0.15

        if preferred_auths:
            for book in Book.objects.filter(
                authors__id__in=preferred_auths,
            ).values_list('id', flat=True).distinct()[:200]:
                bid = str(book)
                boosts[bid] = boosts.get(bid, 0.0) + 0.10

        return boosts

    @staticmethod
    def _compute_facets(results: List[SearchResult]) -> Dict:
        """
        Compute facet counts for search results.
        """
        if not results:
            return {}

        from apps.catalog.domain.models import Book
        book_ids = [r.book_id for r in results[:200]]

        # Category facets
        from django.db.models import Count
        category_facets = (
            Book.objects
            .filter(id__in=book_ids)
            .values('categories__id', 'categories__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:20]
        )

        # Language facets
        language_facets = (
            Book.objects
            .filter(id__in=book_ids)
            .values('language')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return {
            'categories': [
                {
                    'id': str(f['categories__id']),
                    'name': f['categories__name'],
                    'count': f['count'],
                }
                for f in category_facets if f['categories__id']
            ],
            'languages': [
                {
                    'code': f['language'],
                    'count': f['count'],
                }
                for f in language_facets
            ],
            'match_types': {
                'fulltext': sum(1 for r in results if r.match_type == 'fulltext'),
                'semantic': sum(1 for r in results if r.match_type == 'semantic'),
                'fuzzy': sum(1 for r in results if r.match_type == 'fuzzy'),
                'blended': sum(1 for r in results if r.match_type == 'blended'),
            },
        }
