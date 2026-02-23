"""
Nova — AI Recommendation Engine
====================================
Produces personalised book recommendations using:
  1. Content-based filtering (sentence-transformer embeddings + cosine similarity)
  2. Collaborative filtering (user-item matrix)
  3. Hybrid blending of (1) and (2)
  4. Trending / popular fallback for cold-start users
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
from django.conf import settings
from django.db.models import Avg, Count, Q
from django.utils import timezone

logger = logging.getLogger('nova.intelligence.engine')

# Lazy-loaded model — avoids import-time GPU/memory cost
_embedding_model = None


def _get_embedding_model():
    """
    Return the sentence-transformer model, loading on first call.
    The model name comes from settings.AI_CONFIG['EMBEDDING_MODEL'].
    """
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = getattr(settings, 'AI_CONFIG', {}).get(
                'EMBEDDING_MODEL', 'all-MiniLM-L6-v2',
            )
            _embedding_model = SentenceTransformer(model_name)
            logger.info('Loaded embedding model: %s', model_name)
        except Exception as exc:
            logger.error('Failed to load embedding model: %s', exc)
            raise
    return _embedding_model


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def compute_book_embedding(book) -> List[float]:
    """
    Compute a dense embedding vector for a book by concatenating
    its title, subtitle, description, and category names.
    """
    parts = [book.title]
    if book.subtitle:
        parts.append(book.subtitle)
    if book.description:
        parts.append(book.description)
    categories = book.categories.values_list('name', flat=True)
    parts.extend(categories)
    authors = book.authors.values_list('name', flat=True)
    parts.extend(authors)

    text = ' '.join(parts)
    model = _get_embedding_model()
    vector = model.encode(text, show_progress_bar=False)
    return vector.tolist()


def compute_user_preference_vector(user_id) -> List[float]:
    """
    Build a user preference vector by averaging the embeddings of
    books the user has borrowed, reviewed highly, or favourited.
    """
    from apps.catalog.domain.models import Book
    from apps.circulation.domain.models import BorrowRecord
    from apps.digital_content.domain.models import UserLibrary

    # Collect book IDs from borrows
    borrowed_ids = list(
        BorrowRecord.objects.filter(user_id=user_id)
        .values_list('book_copy__book_id', flat=True)
        .distinct()[:100]
    )

    # Highly-rated reviews (>= 4 stars)
    from apps.catalog.domain.models import BookReview
    reviewed_ids = list(
        BookReview.objects.filter(user_id=user_id, rating__gte=4)
        .values_list('book_id', flat=True)
        .distinct()[:50]
    )

    # Favourited digital assets
    fav_ids = list(
        UserLibrary.objects.filter(user_id=user_id, is_favorite=True)
        .values_list('digital_asset__book_id', flat=True)
        .distinct()[:50]
    )

    # Browsed books (weighted by interest — recent, multi-view)
    from apps.intelligence.domain.models import BookView
    from datetime import timedelta
    browse_cutoff = timezone.now() - timedelta(days=30)
    viewed_ids = list(
        BookView.objects.filter(user_id=user_id, viewed_at__gte=browse_cutoff)
        .values('book_id')
        .annotate(view_count=Count('id'))
        .filter(view_count__gte=2)  # Only include books viewed 2+ times
        .values_list('book_id', flat=True)[:30]
    )

    all_book_ids = list(set(borrowed_ids + reviewed_ids + fav_ids + list(viewed_ids)))
    if not all_book_ids:
        return []

    books = Book.objects.filter(id__in=all_book_ids)
    vectors = []
    for book in books:
        if book.embedding_vector:
            vectors.append(np.array(book.embedding_vector))
        else:
            try:
                vec = compute_book_embedding(book)
                book.embedding_vector = vec
                book.save(update_fields=['embedding_vector', 'updated_at'])
                vectors.append(np.array(vec))
            except Exception:
                continue

    if not vectors:
        return []

    mean_vector = np.mean(vectors, axis=0)
    return mean_vector.tolist()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ---------------------------------------------------------------------------
# Recommendation Generators
# ---------------------------------------------------------------------------

def content_based_recommendations(
    user_id, limit: int = 30,
) -> List[Tuple[str, float, str, Optional[str]]]:
    """
    Content-based: find books whose embedding is most similar to the
    user's preference vector.

    Returns list of (book_id, score, explanation, seed_book_id).
    """
    from apps.intelligence.domain.models import UserPreference
    from apps.catalog.domain.models import Book

    try:
        pref = UserPreference.objects.get(user_id=user_id)
    except UserPreference.DoesNotExist:
        return []

    if not pref.preference_vector:
        return []

    user_vec = np.array(pref.preference_vector)

    # Exclude books user already borrowed
    from apps.circulation.domain.models import BorrowRecord
    borrowed_ids = set(
        BorrowRecord.objects.filter(user_id=user_id)
        .values_list('book_copy__book_id', flat=True)
    )

    # Filter by disliked categories
    disliked = pref.disliked_categories or []

    books = Book.all_objects.filter(
        deleted_at__isnull=True,
    ).exclude(id__in=borrowed_ids)

    if disliked:
        books = books.exclude(categories__id__in=disliked)

    # Only books with embeddings
    scored: List[Tuple[str, float, str, Optional[str]]] = []
    for book in books.iterator():
        if not book.embedding_vector:
            continue
        sim = cosine_similarity(user_vec, np.array(book.embedding_vector))
        if sim > 0.3:
            explanation = (
                f'Matches your reading profile with {sim:.0%} similarity.'
            )
            scored.append((str(book.id), sim, explanation, None))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


def collaborative_recommendations(
    user_id, limit: int = 30,
) -> List[Tuple[str, float, str, Optional[str]]]:
    """
    Simple collaborative filtering: find users who borrowed the same
    books, then recommend books those similar users liked but current
    user hasn't seen.
    """
    from apps.circulation.domain.models import BorrowRecord
    from apps.catalog.domain.models import BookReview

    my_books = set(
        BorrowRecord.objects.filter(user_id=user_id)
        .values_list('book_copy__book_id', flat=True)
    )
    if not my_books:
        return []

    # Find similar users (borrowed >= 2 same books)
    from django.db.models import Count as _Count
    similar_users = (
        BorrowRecord.objects
        .filter(book_copy__book_id__in=my_books)
        .exclude(user_id=user_id)
        .values('user_id')
        .annotate(overlap=_Count('id'))
        .filter(overlap__gte=2)
        .order_by('-overlap')[:50]
    )
    similar_user_ids = [s['user_id'] for s in similar_users]
    if not similar_user_ids:
        return []

    # Books those users borrowed that I haven't
    candidate_books = (
        BorrowRecord.objects
        .filter(user_id__in=similar_user_ids)
        .exclude(book_copy__book_id__in=my_books)
        .values('book_copy__book_id')
        .annotate(
            borrow_count=_Count('id'),
            avg_rating=Avg('book_copy__book__average_rating'),
        )
        .order_by('-borrow_count')[:limit]
    )

    scored = []
    for cb in candidate_books:
        book_id = str(cb['book_copy__book_id'])
        # Normalise borrow_count to a 0–1 score
        score = min(cb['borrow_count'] / 10.0, 1.0)
        explanation = (
            f'Readers with similar taste borrowed this book '
            f'({cb["borrow_count"]} times).'
        )
        scored.append((book_id, score, explanation, None))

    return scored


def trending_recommendations(
    limit: int = 20,
) -> List[Tuple[str, float, str, Optional[str]]]:
    """Fallback: return currently trending books."""
    from apps.intelligence.domain.models import TrendingBook

    trending = TrendingBook.objects.filter(
        period='WEEKLY',
    ).select_related('book').order_by('rank')[:limit]

    return [
        (str(t.book_id), t.score, f'Trending #{t.rank} this week.', None)
        for t in trending
    ]


def because_you_read_recommendations(
    user_id, limit: int = 20,
) -> List[Tuple[str, float, str, Optional[str]]]:
    """
    For each recently-read book, find similar books by embedding
    distance and return with the seed reference.
    """
    from apps.circulation.domain.models import BorrowRecord
    from apps.catalog.domain.models import Book

    recent_borrows = (
        BorrowRecord.objects.filter(user_id=user_id)
        .order_by('-created_at')[:5]
        .values_list('book_copy__book_id', flat=True)
    )

    already_read = set(
        BorrowRecord.objects.filter(user_id=user_id)
        .values_list('book_copy__book_id', flat=True)
    )

    scored = []
    for seed_id in recent_borrows:
        try:
            seed_book = Book.objects.get(id=seed_id)
        except Book.DoesNotExist:
            continue
        if not seed_book.embedding_vector:
            continue

        seed_vec = np.array(seed_book.embedding_vector)
        candidates = (
            Book.all_objects
            .filter(deleted_at__isnull=True)
            .exclude(id__in=already_read)
            .exclude(id=seed_id)
        )

        for book in candidates.iterator():
            if not book.embedding_vector:
                continue
            sim = cosine_similarity(seed_vec, np.array(book.embedding_vector))
            if sim > 0.5:
                explanation = (
                    f'Similar to "{seed_book.title}" '
                    f'({sim:.0%} match).'
                )
                scored.append((str(book.id), sim, explanation, str(seed_id)))

    scored.sort(key=lambda x: x[1], reverse=True)
    # Deduplicate by book_id, keep highest score
    seen = set()
    deduped = []
    for item in scored:
        if item[0] not in seen:
            seen.add(item[0])
            deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


# ---------------------------------------------------------------------------
# Browse-Based Recommendations (from viewing history)
# ---------------------------------------------------------------------------

def browse_based_recommendations(
    user_id, limit: int = 20,
) -> List[Tuple[str, float, str, Optional[str]]]:
    """
    Recommend books similar to ones the user has viewed/browsed
    but hasn't borrowed yet. Weighted by view recency and duration.
    """
    from apps.intelligence.domain.models import BookView
    from apps.circulation.domain.models import BorrowRecord
    from apps.catalog.domain.models import Book

    # Get recent views (last 30 days, top 15 by most viewed)
    from django.db.models import Sum
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(days=30)

    viewed_books = (
        BookView.objects.filter(user_id=user_id, viewed_at__gte=cutoff)
        .values('book_id')
        .annotate(
            view_count=Count('id'),
            total_duration=Sum('duration_seconds'),
        )
        .order_by('-view_count', '-total_duration')[:15]
    )

    if not viewed_books:
        return []

    already_read = set(
        BorrowRecord.objects.filter(user_id=user_id)
        .values_list('book_copy__book_id', flat=True)
    )

    scored = []
    for entry in viewed_books:
        seed_id = entry['book_id']
        if str(seed_id) in already_read:
            continue

        try:
            seed_book = Book.objects.get(id=seed_id)
        except Book.DoesNotExist:
            continue

        # Interest signal strength: views + time spent
        interest_weight = min(1.0, (entry['view_count'] * 0.3 + (entry['total_duration'] or 0) / 120) / 3)

        # The book the user viewed itself is a strong candidate
        base_score = 0.6 + interest_weight * 0.3  # 0.6 - 0.9
        explanation = (
            f'You showed interest in "{seed_book.title}" '
            f'(viewed {entry["view_count"]}x).'
        )
        if str(seed_id) not in {s[0] for s in scored}:
            scored.append((str(seed_id), base_score, explanation, None))

        # Also find similar books by embedding
        if seed_book.embedding_vector:
            seed_vec = np.array(seed_book.embedding_vector)
            candidates = (
                Book.all_objects
                .filter(deleted_at__isnull=True)
                .exclude(id__in=already_read)
                .exclude(id=seed_id)
            )
            for book in candidates.iterator():
                if not book.embedding_vector:
                    continue
                sim = cosine_similarity(seed_vec, np.array(book.embedding_vector))
                if sim > 0.4:  # Lower threshold since browse is weaker signal
                    sim_adjusted = sim * interest_weight
                    explanation = (
                        f'Similar to "{seed_book.title}" which you browsed '
                        f'({sim:.0%} match).'
                    )
                    scored.append((str(book.id), sim_adjusted, explanation, str(seed_id)))

    scored.sort(key=lambda x: x[1], reverse=True)
    seen = set()
    deduped = []
    for item in scored:
        if item[0] not in seen:
            seen.add(item[0])
            deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


# ---------------------------------------------------------------------------
# Hybrid Blender
# ---------------------------------------------------------------------------

def generate_hybrid_recommendations(
    user_id, limit: int = 50,
) -> List[Tuple[str, float, str, str, Optional[str]]]:
    """
    Blend all strategies into a single ranked list.
    Returns list of (book_id, score, explanation, strategy, seed_book_id).
    """
    results: Dict[str, Tuple[float, str, str, Optional[str]]] = {}

    # Weights
    w_content = 0.35
    w_collab = 0.25
    w_because = 0.15
    w_browse = 0.15
    w_trending = 0.10

    def _merge(items, strategy, weight):
        for book_id, score, explanation, seed_id in items:
            weighted = score * weight
            if book_id in results:
                existing = results[book_id]
                if weighted > existing[0]:
                    results[book_id] = (weighted, explanation, strategy, seed_id)
                else:
                    # Boost score and keep existing explanation
                    results[book_id] = (
                        existing[0] + weighted * 0.5,
                        existing[1], existing[2], existing[3],
                    )
            else:
                results[book_id] = (weighted, explanation, strategy, seed_id)

    try:
        content = content_based_recommendations(user_id, limit=40)
        _merge(content, 'CONTENT_BASED', w_content)
    except Exception as exc:
        logger.warning('Content-based recs failed: %s', exc)

    try:
        collab = collaborative_recommendations(user_id, limit=40)
        _merge(collab, 'COLLABORATIVE', w_collab)
    except Exception as exc:
        logger.warning('Collaborative recs failed: %s', exc)

    try:
        because = because_you_read_recommendations(user_id, limit=30)
        _merge(because, 'BECAUSE_YOU_READ', w_because)
    except Exception as exc:
        logger.warning('Because-you-read recs failed: %s', exc)

    try:
        browse = browse_based_recommendations(user_id, limit=30)
        _merge(browse, 'BROWSE_BASED', w_browse)
    except Exception as exc:
        logger.warning('Browse-based recs failed: %s', exc)

    try:
        trend = trending_recommendations(limit=20)
        _merge(trend, 'TRENDING', w_trending)
    except Exception as exc:
        logger.warning('Trending recs failed: %s', exc)

    # Sort by final score descending
    ranked = sorted(
        [
            (bid, score, expl, strat, seed)
            for bid, (score, expl, strat, seed) in results.items()
        ],
        key=lambda x: x[1],
        reverse=True,
    )
    return ranked[:limit]
