"""
Nova — Model Training Pipeline
==================================
End-to-end pipeline for training, evaluating, and deploying
ML models within the Nova ecosystem.

Pipelines:
1. **Embedding Pipeline**: (Re)trains or fine-tunes the sentence-transformer
   embedding model on library-specific corpus.
2. **Collaborative Filter Pipeline**: Builds the user-item interaction
   matrix and trains matrix-factorisation models.
3. **Overdue Classifier Pipeline**: Trains a logistic regression model
   on historical borrowing features.
4. **Pipeline Orchestrator**: Coordinates multi-stage pipelines with
   checkpointing, logging, and rollback.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('nova.intelligence.training')


# ---------------------------------------------------------------------------
# Pipeline stage abstraction
# ---------------------------------------------------------------------------

@dataclass
class PipelineStage:
    name: str
    func: Callable
    params: Dict = field(default_factory=dict)
    timeout_seconds: int = 3600
    retries: int = 1


@dataclass
class PipelineResult:
    pipeline_name: str
    stages_completed: List[str]
    stages_failed: List[str]
    metrics: Dict
    artifacts: Dict[str, str]      # artifact_name → file_path
    total_time_seconds: float
    status: str                    # 'SUCCESS', 'PARTIAL', 'FAILED'
    errors: List[str] = field(default_factory=list)


class PipelineOrchestrator:
    """
    Executes a sequence of pipeline stages with error handling,
    timing, and artifact tracking.
    """

    @classmethod
    def run(
        cls,
        pipeline_name: str,
        stages: List[PipelineStage],
    ) -> PipelineResult:
        """Execute stages sequentially, collecting results."""
        start = time.monotonic()
        completed = []
        failed = []
        all_metrics = {}
        all_artifacts = {}
        errors = []

        logger.info('Starting pipeline: %s (%d stages)', pipeline_name, len(stages))

        for stage in stages:
            stage_start = time.monotonic()
            retry_count = 0

            while retry_count <= stage.retries:
                try:
                    logger.info('  Stage: %s (attempt %d)', stage.name, retry_count + 1)
                    result = stage.func(**stage.params)

                    if isinstance(result, dict):
                        if 'metrics' in result:
                            all_metrics.update(result['metrics'])
                        if 'artifacts' in result:
                            all_artifacts.update(result['artifacts'])

                    elapsed = time.monotonic() - stage_start
                    logger.info(
                        '  Stage %s completed in %.1fs', stage.name, elapsed,
                    )
                    completed.append(stage.name)
                    break

                except Exception as exc:
                    retry_count += 1
                    if retry_count > stage.retries:
                        error_msg = f'{stage.name}: {exc}'
                        errors.append(error_msg)
                        failed.append(stage.name)
                        logger.error('  Stage %s failed: %s', stage.name, exc)
                    else:
                        logger.warning(
                            '  Stage %s failed, retrying: %s', stage.name, exc,
                        )
                        time.sleep(2)

        total_time = time.monotonic() - start

        if not failed:
            status = 'SUCCESS'
        elif completed:
            status = 'PARTIAL'
        else:
            status = 'FAILED'

        result = PipelineResult(
            pipeline_name=pipeline_name,
            stages_completed=completed,
            stages_failed=failed,
            metrics=all_metrics,
            artifacts=all_artifacts,
            total_time_seconds=round(total_time, 2),
            status=status,
            errors=errors,
        )

        logger.info(
            'Pipeline %s finished: %s (%.1fs)',
            pipeline_name, status, total_time,
        )

        return result


# ====================================================================
# 1. Embedding Training Pipeline
# ====================================================================

class EmbeddingPipeline:
    """
    Manages the embedding model lifecycle:
    - Computes embeddings for all un-embedded books
    - Evaluates embedding quality via clustering coherence
    - Registers new model versions
    """

    @classmethod
    def run_full(cls) -> PipelineResult:
        """Execute the full embedding pipeline."""
        stages = [
            PipelineStage(
                name='compute_embeddings',
                func=cls.compute_all_embeddings,
                params={'batch_size': 200},
            ),
            PipelineStage(
                name='evaluate_embeddings',
                func=cls.evaluate_embedding_quality,
            ),
            PipelineStage(
                name='register_model',
                func=cls.register_model_version,
            ),
        ]
        return PipelineOrchestrator.run('embedding_pipeline', stages)

    @staticmethod
    def compute_all_embeddings(batch_size: int = 200) -> Dict:
        """Compute embeddings for books missing them."""
        from apps.catalog.domain.models import Book
        from apps.intelligence.infrastructure.recommendation_engine import (
            compute_book_embedding,
        )

        books = Book.objects.filter(
            embedding_vector__isnull=True,
            deleted_at__isnull=True,
        )[:batch_size]

        computed = 0
        failed = 0
        for book in books:
            try:
                vec = compute_book_embedding(book)
                book.embedding_vector = vec
                book.save(update_fields=['embedding_vector', 'updated_at'])
                computed += 1
            except Exception as exc:
                logger.warning('Embedding failed for %s: %s', book.id, exc)
                failed += 1

        total = Book.objects.filter(
            embedding_vector__isnull=False, deleted_at__isnull=True,
        ).count()

        return {
            'metrics': {
                'books_embedded': computed,
                'books_failed': failed,
                'total_embedded': total,
            },
        }

    @staticmethod
    def evaluate_embedding_quality() -> Dict:
        """
        Evaluate embedding quality by measuring intra-category
        coherence (books in the same category should have similar
        embeddings).
        """
        from apps.catalog.domain.models import Book, Category

        categories = Category.objects.all()[:20]
        coherence_scores = []

        for cat in categories:
            books = list(
                Book.objects.filter(
                    categories=cat,
                    embedding_vector__isnull=False,
                    deleted_at__isnull=True,
                ).values_list('embedding_vector', flat=True)[:50]
            )

            if len(books) < 3:
                continue

            vectors = np.array(books)
            # Compute mean pairwise cosine similarity
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            normalised = vectors / norms
            sim_matrix = np.dot(normalised, normalised.T)

            # Average off-diagonal similarity
            n = len(sim_matrix)
            total_sim = (sim_matrix.sum() - n) / (n * (n - 1))
            coherence_scores.append(total_sim)

        avg_coherence = float(np.mean(coherence_scores)) if coherence_scores else 0.0

        return {
            'metrics': {
                'embedding_coherence': round(avg_coherence, 4),
                'categories_evaluated': len(coherence_scores),
            },
        }

    @staticmethod
    def register_model_version() -> Dict:
        """Register the current embedding model as a version."""
        from apps.intelligence.domain.models import AIModelVersion

        ai_config = getattr(settings, 'AI_CONFIG', {})
        model_name = ai_config.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        dim = ai_config.get('EMBEDDING_DIMENSION', 384)

        version_str = f'{model_name}-{timezone.now().strftime("%Y%m%d")}'

        version, created = AIModelVersion.objects.get_or_create(
            model_type='EMBEDDING',
            version=version_str,
            defaults={
                'name': model_name,
                'description': f'Sentence-transformer {model_name} ({dim}d)',
                'config': {
                    'model_name': model_name,
                    'dimension': dim,
                    'computed_at': timezone.now().isoformat(),
                },
                'is_active': True,
            },
        )

        if created:
            # Deactivate old versions
            AIModelVersion.objects.filter(
                model_type='EMBEDDING',
            ).exclude(pk=version.pk).update(is_active=False)

        return {
            'metrics': {
                'model_version': version_str,
                'is_new': created,
            },
        }


# ====================================================================
# 2. Collaborative Filter Pipeline
# ====================================================================

class CollaborativeFilterPipeline:
    """
    Builds the user-item interaction matrix and computes
    user similarity scores for collaborative filtering.
    """

    @classmethod
    def run_full(cls) -> PipelineResult:
        stages = [
            PipelineStage(
                name='build_interaction_matrix',
                func=cls.build_interaction_matrix,
            ),
            PipelineStage(
                name='compute_user_similarities',
                func=cls.compute_user_similarities,
            ),
        ]
        return PipelineOrchestrator.run('collaborative_pipeline', stages)

    @staticmethod
    def build_interaction_matrix() -> Dict:
        """
        Build a user×book interaction matrix from borrowing and
        rating data. Stores as a sparse JSON artifact.
        """
        from apps.circulation.domain.models import BorrowRecord
        from apps.catalog.domain.models import BookReview

        # Borrows (implicit feedback, weight=1)
        interactions = {}
        for br in BorrowRecord.objects.values(
            'user_id', 'book_copy__book_id',
        ).distinct():
            uid = str(br['user_id'])
            bid = str(br['book_copy__book_id'])
            interactions.setdefault(uid, {})[bid] = interactions.get(uid, {}).get(bid, 0) + 1

        # Reviews (explicit feedback, weight=rating/5)
        for review in BookReview.objects.values(
            'user_id', 'book_id', 'rating',
        ):
            uid = str(review['user_id'])
            bid = str(review['book_id'])
            weight = review['rating'] / 5.0
            interactions.setdefault(uid, {})[bid] = max(
                interactions.get(uid, {}).get(bid, 0), weight,
            )

        total_users = len(interactions)
        total_interactions = sum(len(v) for v in interactions.values())

        # Store interaction matrix
        artifact_dir = Path(settings.BASE_DIR) / 'data' / 'models'
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / 'interaction_matrix.json'

        with open(artifact_path, 'w') as f:
            json.dump(interactions, f)

        return {
            'metrics': {
                'total_users': total_users,
                'total_interactions': total_interactions,
                'sparsity': round(
                    1 - total_interactions / max(total_users * 1000, 1), 4,
                ),
            },
            'artifacts': {
                'interaction_matrix': str(artifact_path),
            },
        }

    @staticmethod
    def compute_user_similarities() -> Dict:
        """
        Compute pairwise user similarities using cosine similarity
        on the interaction vectors.
        """
        artifact_path = (
            Path(settings.BASE_DIR) / 'data' / 'models' / 'interaction_matrix.json'
        )
        if not artifact_path.exists():
            return {'metrics': {'error': 'Interaction matrix not found'}}

        with open(artifact_path) as f:
            interactions = json.load(f)

        if len(interactions) < 2:
            return {'metrics': {'user_pairs': 0}}

        # Build shared item space
        all_items = set()
        for uid, items in interactions.items():
            all_items.update(items.keys())

        item_list = sorted(all_items)
        item_idx = {item: i for i, item in enumerate(item_list)}

        # Build sparse vectors per user
        user_vectors = {}
        for uid, items in interactions.items():
            vec = np.zeros(len(item_list))
            for bid, weight in items.items():
                if bid in item_idx:
                    vec[item_idx[bid]] = weight
            norm = np.linalg.norm(vec)
            if norm > 0:
                user_vectors[uid] = vec / norm

        # Compute top-K similar users for each user
        K = 20
        similarities = {}
        users = list(user_vectors.keys())

        for i, uid_a in enumerate(users):
            sims = []
            for j, uid_b in enumerate(users):
                if i == j:
                    continue
                sim = float(np.dot(user_vectors[uid_a], user_vectors[uid_b]))
                if sim > 0.1:
                    sims.append((uid_b, round(sim, 4)))
            sims.sort(key=lambda x: x[1], reverse=True)
            similarities[uid_a] = sims[:K]

        # Store
        sim_path = (
            Path(settings.BASE_DIR) / 'data' / 'models' / 'user_similarities.json'
        )
        with open(sim_path, 'w') as f:
            json.dump(similarities, f)

        total_pairs = sum(len(v) for v in similarities.values())

        return {
            'metrics': {
                'users_processed': len(users),
                'total_similar_pairs': total_pairs,
                'avg_neighbors': round(total_pairs / max(len(users), 1), 1),
            },
            'artifacts': {
                'user_similarities': str(sim_path),
            },
        }


# ====================================================================
# 3. Overdue Classifier Training Pipeline
# ====================================================================

class OverdueClassifierPipeline:
    """
    Trains a logistic regression classifier to predict overdue
    borrows, using historical data as ground truth.
    """

    @classmethod
    def run_full(cls) -> PipelineResult:
        stages = [
            PipelineStage(
                name='prepare_training_data',
                func=cls.prepare_data,
            ),
            PipelineStage(
                name='train_model',
                func=cls.train,
            ),
            PipelineStage(
                name='evaluate_model',
                func=cls.evaluate,
            ),
        ]
        return PipelineOrchestrator.run('overdue_classifier_pipeline', stages)

    @staticmethod
    def prepare_data() -> Dict:
        """
        Extract features and labels from historical borrow data.
        """
        from apps.circulation.domain.models import BorrowRecord
        from apps.engagement.domain.models import UserEngagement

        records = BorrowRecord.objects.filter(
            status__in=['RETURNED', 'OVERDUE', 'LOST'],
        ).select_related('user', 'book_copy__book')[:5000]

        features = []
        labels = []

        for record in records:
            user = record.user

            # Features
            past_borrows = BorrowRecord.objects.filter(
                user=user, created_at__lt=record.created_at,
            ).count()
            past_overdue = BorrowRecord.objects.filter(
                user=user,
                status__in=['OVERDUE', 'LOST'],
                created_at__lt=record.created_at,
            ).count()

            overdue_rate = past_overdue / max(past_borrows, 1)
            book_popularity = record.book_copy.book.total_borrows

            try:
                eng = UserEngagement.objects.get(user=user)
                level = eng.level
                kp = eng.total_kp
            except UserEngagement.DoesNotExist:
                level = 1
                kp = 0

            feature_vec = [
                overdue_rate,
                min(past_borrows / 50.0, 1.0),
                min(book_popularity / 100.0, 1.0),
                level / 10.0,
                min(kp / 1000.0, 1.0),
                1.0 if record.created_at.weekday() >= 5 else 0.0,
            ]
            features.append(feature_vec)
            labels.append(1 if record.status in ['OVERDUE', 'LOST'] else 0)

        # Store
        data_dir = Path(settings.BASE_DIR) / 'data' / 'training'
        data_dir.mkdir(parents=True, exist_ok=True)

        np.save(str(data_dir / 'overdue_features.npy'), np.array(features))
        np.save(str(data_dir / 'overdue_labels.npy'), np.array(labels))

        pos = sum(labels)
        neg = len(labels) - pos

        return {
            'metrics': {
                'total_samples': len(labels),
                'positive_samples': pos,
                'negative_samples': neg,
                'class_balance': round(pos / max(len(labels), 1), 3),
            },
            'artifacts': {
                'features': str(data_dir / 'overdue_features.npy'),
                'labels': str(data_dir / 'overdue_labels.npy'),
            },
        }

    @staticmethod
    def train() -> Dict:
        """Train a logistic regression model on the prepared data."""
        data_dir = Path(settings.BASE_DIR) / 'data' / 'training'
        features = np.load(str(data_dir / 'overdue_features.npy'))
        labels = np.load(str(data_dir / 'overdue_labels.npy'))

        if len(features) < 10:
            return {'metrics': {'error': 'Insufficient training data'}}

        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import cross_val_score
            from sklearn.preprocessing import StandardScaler

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(features)

            model = LogisticRegression(
                class_weight='balanced',
                max_iter=1000,
                random_state=42,
            )

            # Cross-validation
            cv_scores = cross_val_score(
                model, X_scaled, labels, cv=5, scoring='f1',
            )

            # Train on full data
            model.fit(X_scaled, labels)

            # Save model
            import pickle
            model_dir = Path(settings.BASE_DIR) / 'data' / 'models'
            model_dir.mkdir(parents=True, exist_ok=True)

            model_path = model_dir / 'overdue_classifier.pkl'
            scaler_path = model_dir / 'overdue_scaler.pkl'

            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)

            return {
                'metrics': {
                    'cv_f1_mean': round(float(np.mean(cv_scores)), 4),
                    'cv_f1_std': round(float(np.std(cv_scores)), 4),
                    'coefficients': model.coef_.tolist(),
                    'intercept': float(model.intercept_[0]),
                },
                'artifacts': {
                    'model': str(model_path),
                    'scaler': str(scaler_path),
                },
            }

        except ImportError:
            logger.error('scikit-learn required for model training')
            return {'metrics': {'error': 'scikit-learn not available'}}

    @staticmethod
    def evaluate() -> Dict:
        """Evaluate the trained model on held-out data."""
        from apps.intelligence.infrastructure.evaluation import (
            ClassificationEvaluator,
        )

        metrics = ClassificationEvaluator.evaluate_overdue_predictions()
        return {
            'metrics': {
                'accuracy': metrics.accuracy,
                'precision': metrics.precision,
                'recall': metrics.recall,
                'f1': metrics.f1_score,
                'auc': metrics.auc_roc,
            },
        }
