"""
Nova — AI Content Analysis Service
=======================================
Automated book metadata enrichment using NLP:

1. **Auto-tagger**: Extracts topic tags from book descriptions using
   TF-IDF keyword extraction.
2. **Reading Level Estimator**: Estimates text complexity (Flesch-Kincaid,
   Gunning-Fog, Coleman-Liau) and maps to reader-level labels.
3. **Topic Extractor**: Clusters books into latent topics using
   embedding KMeans and labels each cluster.
4. **Duplicate Detector**: Finds near-duplicate book entries using
   embedding similarity + ISBN matching.
5. **Summary Generator**: Produces concise summaries from long
   descriptions via extractive summarisation.
"""

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from django.conf import settings

logger = logging.getLogger('nova.intelligence.content')


# ====================================================================
# 1. Auto-Tagger (TF-IDF keyword extraction)
# ====================================================================

@dataclass
class TagResult:
    tags: List[str]
    confidence_scores: Dict[str, float]


class AutoTagger:
    """
    Extracts meaningful topic tags from book descriptions using
    a simplified TF-IDF approach without external dependencies.
    """

    # Domain-specific stop words (in addition to general ones)
    DOMAIN_STOP = frozenset({
        'book', 'books', 'chapter', 'chapters', 'edition', 'volume',
        'page', 'pages', 'author', 'reader', 'readers', 'reading',
        'written', 'write', 'published', 'publication', 'publisher',
        'introduction', 'guide', 'comprehensive', 'complete',
        'new', 'first', 'second', 'third', 'one', 'two', 'also',
        'many', 'much', 'well', 'like', 'including', 'includes',
        'provides', 'presents', 'covers', 'explores', 'offers',
        'based', 'using', 'used', 'use', 'work', 'works',
    })

    @classmethod
    def extract_tags(
        cls,
        text: str,
        max_tags: int = 10,
        min_word_length: int = 3,
    ) -> TagResult:
        """
        Extract the top-N tags from the given text using term
        frequency with inverse document frequency approximation.
        """
        if not text or len(text.strip()) < 20:
            return TagResult(tags=[], confidence_scores={})

        # Tokenise and clean
        words = re.findall(r'\b[a-z][a-z\-]+\b', text.lower())
        words = [
            w for w in words
            if len(w) >= min_word_length
            and w not in cls.DOMAIN_STOP
            and not w.isdigit()
        ]

        if not words:
            return TagResult(tags=[], confidence_scores={})

        # Term frequency
        tf = Counter(words)
        total_words = len(words)
        unique_words = len(tf)

        # Approximate IDF using Zipf's law heuristic
        # Rarer terms get higher scores
        max_freq = tf.most_common(1)[0][1]
        scores = {}

        for word, count in tf.items():
            # Augmented TF to prevent bias towards long documents
            augmented_tf = 0.5 + 0.5 * (count / max_freq)
            # IDF approximation: penalise very common words
            rarity = math.log(1 + unique_words / (1 + count))
            # Length bonus: longer words are often more specific
            length_bonus = min(len(word) / 10.0, 0.3)

            scores[word] = augmented_tf * rarity + length_bonus

        # Bigram extraction for compound terms
        bigrams = cls._extract_bigrams(words)
        for bigram, count in bigrams.most_common(20):
            if count >= 2:
                scores[bigram] = scores.get(bigram, 0) + count * 0.5

        # Sort by score and take top-N
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top = ranked[:max_tags]

        # Normalise confidence to 0–1
        max_score = top[0][1] if top else 1.0
        confidence = {
            word: round(score / max_score, 3)
            for word, score in top
        }

        return TagResult(
            tags=[word for word, _ in top],
            confidence_scores=confidence,
        )

    @staticmethod
    def _extract_bigrams(words: List[str]) -> Counter:
        """Extract meaningful bigram phrases."""
        bigrams = []
        for i in range(len(words) - 1):
            bigram = f'{words[i]} {words[i + 1]}'
            bigrams.append(bigram)
        return Counter(bigrams)

    @classmethod
    def auto_tag_book(cls, book) -> List[str]:
        """
        Auto-tag a book model instance from its description,
        title, and subtitle. Persists tags to book.tags.
        """
        text_parts = [book.title]
        if book.subtitle:
            text_parts.append(book.subtitle)
        if book.description:
            text_parts.append(book.description)

        combined = ' '.join(text_parts)
        result = cls.extract_tags(combined, max_tags=8)

        if result.tags:
            existing = set(book.tags or [])
            new_tags = list(existing | set(result.tags))
            book.tags = new_tags
            book.save(update_fields=['tags', 'updated_at'])
            logger.info(
                'Auto-tagged book %s with %d tags', book.id, len(result.tags),
            )

        return result.tags


# ====================================================================
# 2. Reading Level Estimator
# ====================================================================

@dataclass
class ReadingLevelResult:
    flesch_kincaid_grade: float
    gunning_fog_index: float
    coleman_liau_index: float
    average_grade: float
    level_label: str          # 'ELEMENTARY', 'INTERMEDIATE', 'ADVANCED', 'ACADEMIC'
    word_count: int
    sentence_count: int
    avg_words_per_sentence: float
    avg_syllables_per_word: float


class ReadingLevelEstimator:
    """
    Estimates the readability / reading level of text using
    multiple established formulas.
    """

    LEVEL_THRESHOLDS = {
        'ELEMENTARY': (0, 6),
        'INTERMEDIATE': (6, 10),
        'ADVANCED': (10, 14),
        'ACADEMIC': (14, float('inf')),
    }

    @classmethod
    def estimate(cls, text: str) -> ReadingLevelResult:
        """Analyse text and return reading level metrics."""
        if not text or len(text) < 50:
            return ReadingLevelResult(
                flesch_kincaid_grade=0, gunning_fog_index=0,
                coleman_liau_index=0, average_grade=0,
                level_label='UNKNOWN', word_count=0, sentence_count=0,
                avg_words_per_sentence=0, avg_syllables_per_word=0,
            )

        sentences = cls._count_sentences(text)
        words = cls._get_words(text)
        word_count = len(words)
        sentence_count = max(sentences, 1)

        syllable_counts = [cls._count_syllables(w) for w in words]
        total_syllables = sum(syllable_counts)
        complex_words = sum(1 for s in syllable_counts if s >= 3)

        avg_wps = word_count / sentence_count
        avg_spw = total_syllables / max(word_count, 1)

        # Flesch-Kincaid Grade Level
        fk_grade = (
            0.39 * avg_wps
            + 11.8 * avg_spw
            - 15.59
        )

        # Gunning Fog Index
        fog = 0.4 * (
            avg_wps + 100 * (complex_words / max(word_count, 1))
        )

        # Coleman-Liau Index
        letters = sum(len(w) for w in words)
        L = (letters / max(word_count, 1)) * 100  # letters per 100 words
        S = (sentence_count / max(word_count, 1)) * 100  # sentences per 100 words
        cli = 0.0588 * L - 0.296 * S - 15.8

        avg_grade = (fk_grade + fog + cli) / 3

        # Map to label
        level_label = 'ACADEMIC'
        for label, (low, high) in cls.LEVEL_THRESHOLDS.items():
            if low <= avg_grade < high:
                level_label = label
                break

        return ReadingLevelResult(
            flesch_kincaid_grade=round(fk_grade, 1),
            gunning_fog_index=round(fog, 1),
            coleman_liau_index=round(cli, 1),
            average_grade=round(avg_grade, 1),
            level_label=level_label,
            word_count=word_count,
            sentence_count=sentence_count,
            avg_words_per_sentence=round(avg_wps, 1),
            avg_syllables_per_word=round(avg_spw, 2),
        )

    @staticmethod
    def _count_sentences(text: str) -> int:
        return len(re.findall(r'[.!?]+', text))

    @staticmethod
    def _get_words(text: str) -> List[str]:
        return re.findall(r'\b[a-zA-Z]+\b', text)

    @staticmethod
    def _count_syllables(word: str) -> int:
        """Estimate syllable count using vowel-group heuristic."""
        word = word.lower()
        if len(word) <= 3:
            return 1
        # Remove trailing silent 'e'
        if word.endswith('e') and not word.endswith('le'):
            word = word[:-1]
        vowel_groups = re.findall(r'[aeiouy]+', word)
        return max(len(vowel_groups), 1)

    @classmethod
    def estimate_book(cls, book) -> Optional[ReadingLevelResult]:
        """Estimate reading level for a book from its description."""
        text = book.description or ''
        if len(text) < 100:
            return None
        return cls.estimate(text)


# ====================================================================
# 3. Topic Extractor (Embedding Clustering)
# ====================================================================

@dataclass
class TopicCluster:
    cluster_id: int
    label: str
    representative_books: List[str]
    book_count: int
    centroid_keywords: List[str]


class TopicExtractor:
    """
    Groups books into latent topics using KMeans clustering on
    their embedding vectors.
    """

    @classmethod
    def extract_topics(
        cls,
        n_clusters: int = 15,
        min_books: int = 50,
    ) -> List[TopicCluster]:
        """
        Cluster all books with embeddings and return labelled topics.
        """
        from apps.catalog.domain.models import Book

        books = list(
            Book.all_objects.filter(
                deleted_at__isnull=True,
                embedding_vector__isnull=False,
            ).values('id', 'title', 'embedding_vector', 'tags')[:5000]
        )

        if len(books) < min_books:
            logger.warning(
                'Only %d books with embeddings, need %d for clustering',
                len(books), min_books,
            )
            return []

        # Build matrix
        ids = [str(b['id']) for b in books]
        titles = {str(b['id']): b['title'] for b in books}
        tags_map = {str(b['id']): b['tags'] or [] for b in books}
        matrix = np.array([b['embedding_vector'] for b in books])

        # KMeans clustering
        try:
            from sklearn.cluster import KMeans
            n_clusters = min(n_clusters, len(books) // 3)
            km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = km.fit_predict(matrix)
        except ImportError:
            logger.error('scikit-learn is required for topic extraction')
            return []

        # Group books by cluster
        clusters_dict: Dict[int, List[str]] = {}
        for idx, label in enumerate(labels):
            clusters_dict.setdefault(label, []).append(ids[idx])

        topics = []
        for cluster_id, book_ids in sorted(clusters_dict.items()):
            # Label the cluster from the most common tags
            all_tags = []
            for bid in book_ids:
                all_tags.extend(tags_map.get(bid, []))
            tag_counts = Counter(all_tags)
            top_tags = [t for t, _ in tag_counts.most_common(5)]

            label = ', '.join(top_tags[:3]) if top_tags else f'Topic {cluster_id}'

            # Representative books: closest to centroid
            cluster_indices = [i for i, l in enumerate(labels) if l == cluster_id]
            centroid = km.cluster_centers_[cluster_id]
            distances = [
                (ids[i], np.linalg.norm(matrix[i] - centroid))
                for i in cluster_indices
            ]
            distances.sort(key=lambda x: x[1])
            reps = [titles.get(d[0], '') for d in distances[:5]]

            topics.append(TopicCluster(
                cluster_id=cluster_id,
                label=label,
                representative_books=reps,
                book_count=len(book_ids),
                centroid_keywords=top_tags,
            ))

        topics.sort(key=lambda t: t.book_count, reverse=True)
        return topics


# ====================================================================
# 4. Duplicate Detector
# ====================================================================

@dataclass
class DuplicateGroup:
    primary_book_id: str
    primary_title: str
    duplicates: List[Dict]
    similarity_score: float
    match_reason: str


class DuplicateDetector:
    """
    Detects near-duplicate book entries in the catalog by comparing
    ISBN, title similarity, and embedding distance.
    """

    TITLE_SIMILARITY_THRESHOLD = 0.85
    EMBEDDING_SIMILARITY_THRESHOLD = 0.92

    @classmethod
    def detect(cls, batch_size: int = 500) -> List[DuplicateGroup]:
        """Scan the catalog for potential duplicates."""
        from apps.catalog.domain.models import Book
        from apps.intelligence.infrastructure.recommendation_engine import (
            cosine_similarity,
        )

        books = list(
            Book.all_objects.filter(deleted_at__isnull=True)
            .values('id', 'title', 'isbn_13', 'isbn_10', 'embedding_vector')
            [:batch_size]
        )

        groups = []
        checked = set()

        for i, book_a in enumerate(books):
            if str(book_a['id']) in checked:
                continue

            dupes = []
            for j, book_b in enumerate(books):
                if i == j or str(book_b['id']) in checked:
                    continue

                reason = cls._check_duplicate(book_a, book_b)
                if reason:
                    dupes.append({
                        'book_id': str(book_b['id']),
                        'title': book_b['title'],
                        'reason': reason,
                    })
                    checked.add(str(book_b['id']))

            if dupes:
                groups.append(DuplicateGroup(
                    primary_book_id=str(book_a['id']),
                    primary_title=book_a['title'],
                    duplicates=dupes,
                    similarity_score=0.95,
                    match_reason='Multiple signals',
                ))
                checked.add(str(book_a['id']))

        return groups

    @classmethod
    def _check_duplicate(cls, a: Dict, b: Dict) -> Optional[str]:
        """Check if two books are potential duplicates."""
        # ISBN match (strongest signal)
        if a.get('isbn_13') and a['isbn_13'] == b.get('isbn_13'):
            return 'Identical ISBN-13'
        if a.get('isbn_10') and a['isbn_10'] == b.get('isbn_10'):
            return 'Identical ISBN-10'

        # Title similarity (normalised)
        title_sim = cls._title_similarity(a['title'], b['title'])
        if title_sim >= cls.TITLE_SIMILARITY_THRESHOLD:
            return f'Title similarity {title_sim:.0%}'

        # Embedding similarity
        if a.get('embedding_vector') and b.get('embedding_vector'):
            from apps.intelligence.infrastructure.recommendation_engine import (
                cosine_similarity as cos_sim,
            )
            emb_sim = cos_sim(
                np.array(a['embedding_vector']),
                np.array(b['embedding_vector']),
            )
            if emb_sim >= cls.EMBEDDING_SIMILARITY_THRESHOLD:
                return f'Embedding similarity {emb_sim:.0%}'

        return None

    @staticmethod
    def _title_similarity(a: str, b: str) -> float:
        """Normalised Jaccard similarity on word bigrams."""
        def bigrams(s):
            words = s.lower().split()
            return set(
                f'{words[i]} {words[i+1]}'
                for i in range(len(words) - 1)
            ) if len(words) > 1 else {s.lower()}

        set_a = bigrams(a)
        set_b = bigrams(b)
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)


# ====================================================================
# 5. Extractive Text Summariser
# ====================================================================

class TextSummariser:
    """
    Extractive summarisation: selects the most important sentences
    from a text using TF-IDF sentence scoring.
    """

    @classmethod
    def summarise(
        cls, text: str, max_sentences: int = 3,
    ) -> str:
        """Return the top-N most important sentences."""
        if not text or len(text) < 100:
            return text

        sentences = cls._split_sentences(text)
        if len(sentences) <= max_sentences:
            return text

        # Score each sentence by average TF-IDF of its words
        word_counts = Counter()
        for sent in sentences:
            words = re.findall(r'\b[a-z]+\b', sent.lower())
            word_counts.update(words)

        total_sents = len(sentences)
        # Inverse sentence frequency: how many sentences contain each word
        isf = Counter()
        for sent in sentences:
            unique_words = set(re.findall(r'\b[a-z]+\b', sent.lower()))
            for w in unique_words:
                isf[w] += 1

        scored_sentences = []
        for idx, sent in enumerate(sentences):
            words = re.findall(r'\b[a-z]+\b', sent.lower())
            if not words:
                continue
            score = 0.0
            for w in words:
                tf = word_counts[w] / max(len(words), 1)
                idf = math.log(total_sents / max(isf[w], 1))
                score += tf * idf
            score /= len(words)

            # Position bonus: first and last sentences are often important
            if idx == 0:
                score *= 1.3
            elif idx == len(sentences) - 1:
                score *= 1.1

            scored_sentences.append((idx, sent, score))

        scored_sentences.sort(key=lambda x: x[2], reverse=True)
        top = scored_sentences[:max_sentences]

        # Re-order by original position for coherence
        top.sort(key=lambda x: x[0])
        return ' '.join(s[1] for s in top)

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences using regex."""
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]
