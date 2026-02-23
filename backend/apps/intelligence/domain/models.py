"""
Nova — Intelligence Domain Models
=======================================
Recommendation engine entities, user preferences, search logs,
and AI model tracking.
"""

import uuid

from django.conf import settings
from django.db import models

from apps.common.base_models import TimeStampedModel, UUIDModel


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------

class RecommendationStrategy(models.TextChoices):
    COLLABORATIVE = 'COLLABORATIVE', 'Collaborative Filtering'
    CONTENT_BASED = 'CONTENT_BASED', 'Content-Based'
    HYBRID = 'HYBRID', 'Hybrid'
    TRENDING = 'TRENDING', 'Trending / Popular'
    SIMILAR_USERS = 'SIMILAR_USERS', 'Similar Users'
    BECAUSE_YOU_READ = 'BECAUSE_YOU_READ', 'Because You Read'
    BROWSE_BASED = 'BROWSE_BASED', 'Based on Browsing History'


class Recommendation(UUIDModel, TimeStampedModel):
    """
    A generated recommendation linking a user to a book with
    an explanation of why it was recommended.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations',
    )
    book = models.ForeignKey(
        'catalog.Book',
        on_delete=models.CASCADE,
        related_name='recommendations',
    )
    strategy = models.CharField(
        max_length=30,
        choices=RecommendationStrategy.choices,
        default=RecommendationStrategy.HYBRID,
    )
    score = models.FloatField(
        help_text='Relevance score 0.0–1.0',
    )
    explanation = models.TextField(
        blank=True, default='',
        help_text='Human-readable reason for the recommendation.',
    )
    seed_book = models.ForeignKey(
        'catalog.Book',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        help_text='Book that triggered "because you read" recs.',
    )
    is_dismissed = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'intelligence_recommendation'
        ordering = ['-score']
        indexes = [
            models.Index(fields=['user', '-score']),
            models.Index(fields=['user', 'strategy']),
            models.Index(fields=['book']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.strategy} → {self.user} : {self.book} ({self.score:.2f})'

    def mark_clicked(self):
        from django.utils import timezone
        self.is_clicked = True
        self.clicked_at = timezone.now()
        self.save(update_fields=['is_clicked', 'clicked_at', 'updated_at'])

    def dismiss(self):
        self.is_dismissed = True
        self.save(update_fields=['is_dismissed', 'updated_at'])


# ---------------------------------------------------------------------------
# User Preference
# ---------------------------------------------------------------------------

class UserPreference(UUIDModel, TimeStampedModel):
    """
    Stores explicit and inferred reading preferences per user.
    Used by the recommendation engine to tune results.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reading_preferences',
    )
    preferred_categories = models.JSONField(
        default=list, blank=True,
        help_text='List of category IDs the user explicitly prefers.',
    )
    preferred_authors = models.JSONField(
        default=list, blank=True,
        help_text='List of author IDs the user explicitly prefers.',
    )
    preferred_languages = models.JSONField(
        default=list, blank=True,
    )
    disliked_categories = models.JSONField(
        default=list, blank=True,
    )
    reading_speed = models.CharField(
        max_length=20, blank=True, default='',
        help_text='slow / average / fast — inferred from sessions.',
    )
    preference_vector = models.JSONField(
        null=True, blank=True,
        help_text='Embedding vector derived from reading history.',
    )
    last_computed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'intelligence_user_preference'

    def __str__(self):
        return f'Preferences: {self.user}'


# ---------------------------------------------------------------------------
# Search Log (for analytics & query auto-suggest)
# ---------------------------------------------------------------------------

class SearchLog(UUIDModel):
    """
    Logs every search query to power trending searches,
    auto-suggestions, and search analytics.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='search_logs',
    )
    query_text = models.CharField(max_length=500)
    filters_applied = models.JSONField(
        default=dict, blank=True,
        help_text='Filters active during the search.',
    )
    results_count = models.PositiveIntegerField(default=0)
    clicked_result_id = models.UUIDField(null=True, blank=True)
    session_id = models.UUIDField(
        default=uuid.uuid4,
        help_text='Groups searches within the same user session.',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intelligence_search_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['query_text']),
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]

    def __str__(self):
        return f'Search "{self.query_text}" by {self.user or "anon"}'


# ---------------------------------------------------------------------------
# AI Model Registry
# ---------------------------------------------------------------------------

class AIModelVersion(UUIDModel, TimeStampedModel):
    """
    Tracks versions of AI/ML models deployed in the system.
    Enables A/B testing and rollback.
    """

    class ModelType(models.TextChoices):
        EMBEDDING = 'EMBEDDING', 'Embedding Model'
        RECOMMENDATION = 'RECOMMENDATION', 'Recommendation Model'
        OCR = 'OCR', 'OCR Pipeline'
        FACE = 'FACE', 'Face Recognition'

    model_type = models.CharField(
        max_length=20, choices=ModelType.choices,
    )
    version = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    config = models.JSONField(
        default=dict,
        help_text='Model hyper-parameters and config.',
    )
    metrics = models.JSONField(
        default=dict,
        help_text='Evaluation metrics (accuracy, precision, etc.).',
    )
    is_active = models.BooleanField(
        default=False,
        help_text='Only one version per model_type should be active.',
    )
    artifact_path = models.CharField(
        max_length=500, blank=True, default='',
        help_text='Path to the serialised model artifact.',
    )

    class Meta:
        db_table = 'intelligence_ai_model_version'
        unique_together = ('model_type', 'version')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.model_type} v{self.version} ({"active" if self.is_active else "inactive"})'

    def activate(self):
        """Activate this version and deactivate others of the same type."""
        AIModelVersion.objects.filter(
            model_type=self.model_type, is_active=True,
        ).exclude(pk=self.pk).update(is_active=False)
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


# ---------------------------------------------------------------------------
# AI Provider Configuration
# ---------------------------------------------------------------------------

class AIProviderConfig(UUIDModel, TimeStampedModel):
    """
    Stores configuration for AI providers (Ollama, Google Gemini, OpenAI, etc.).
    Super-admins can configure and switch providers via the admin UI.
    Only one provider per capability should be active at a time.
    """

    class Provider(models.TextChoices):
        OLLAMA = 'OLLAMA', 'Ollama (Local)'
        GEMINI = 'GEMINI', 'Google Gemini'
        OPENAI = 'OPENAI', 'OpenAI'
        LOCAL_TRANSFORMERS = 'LOCAL_TRANSFORMERS', 'Local Transformers'

    class Capability(models.TextChoices):
        CHAT = 'CHAT', 'Chat / Text Generation'
        EMBEDDING = 'EMBEDDING', 'Embedding'
        SUMMARIZATION = 'SUMMARIZATION', 'Summarization'
        CLASSIFICATION = 'CLASSIFICATION', 'Classification'

    provider = models.CharField(
        max_length=30, choices=Provider.choices,
    )
    capability = models.CharField(
        max_length=30, choices=Capability.choices,
    )
    display_name = models.CharField(
        max_length=200,
        help_text='Human-friendly label, e.g. "Ollama llama3.1 8B"',
    )
    model_name = models.CharField(
        max_length=200,
        help_text='Model identifier: llama3.1, gemini-pro, gpt-4o-mini, etc.',
    )
    api_base_url = models.URLField(
        max_length=500, blank=True, default='',
        help_text='Base URL for the API (e.g. http://localhost:11434 for Ollama).',
    )
    api_key = models.CharField(
        max_length=500, blank=True, default='',
        help_text='API key (encrypted at rest). Leave blank for local providers.',
    )
    extra_config = models.JSONField(
        default=dict, blank=True,
        help_text='Additional provider-specific settings (temperature, top_p, etc.).',
    )
    is_active = models.BooleanField(
        default=False,
        help_text='Only one config per capability should be active.',
    )
    is_healthy = models.BooleanField(
        default=False,
        help_text='Last health-check result.',
    )
    last_health_check = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'intelligence_ai_provider_config'
        ordering = ['capability', '-is_active', '-created_at']
        indexes = [
            models.Index(fields=['capability', 'is_active']),
            models.Index(fields=['provider']),
        ]

    def __str__(self):
        active = '✓' if self.is_active else '✗'
        return f'[{active}] {self.display_name} ({self.provider}/{self.capability})'

    def activate(self):
        """Activate this config and deactivate others with the same capability."""
        AIProviderConfig.objects.filter(
            capability=self.capability, is_active=True,
        ).exclude(pk=self.pk).update(is_active=False)
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])

    def mark_healthy(self):
        from django.utils import timezone
        self.is_healthy = True
        self.last_health_check = timezone.now()
        self.last_error = ''
        self.save(update_fields=['is_healthy', 'last_health_check', 'last_error', 'updated_at'])

    def mark_unhealthy(self, error: str):
        from django.utils import timezone
        self.is_healthy = False
        self.last_health_check = timezone.now()
        self.last_error = error[:2000]
        self.save(update_fields=['is_healthy', 'last_health_check', 'last_error', 'updated_at'])


# ---------------------------------------------------------------------------
# Trending Book (materialised view kept up-to-date by Celery beat)
# ---------------------------------------------------------------------------

class TrendingBook(UUIDModel, TimeStampedModel):
    """
    Pre-computed trending/popular books refreshed periodically.
    """

    class Period(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        MONTHLY = 'MONTHLY', 'Monthly'
        ALL_TIME = 'ALL_TIME', 'All Time'

    book = models.ForeignKey(
        'catalog.Book',
        on_delete=models.CASCADE,
        related_name='trending_entries',
    )
    period = models.CharField(
        max_length=10, choices=Period.choices,
    )
    rank = models.PositiveIntegerField()
    borrow_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    review_count = models.PositiveIntegerField(default=0)
    score = models.FloatField(default=0.0)

    class Meta:
        db_table = 'intelligence_trending_book'
        unique_together = ('book', 'period')
        ordering = ['period', 'rank']
        indexes = [
            models.Index(fields=['period', 'rank']),
        ]

    def __str__(self):
        return f'{self.period} #{self.rank}: {self.book}'


# ---------------------------------------------------------------------------
# Book View / Browse History
# ---------------------------------------------------------------------------

class BookView(UUIDModel):
    """
    Tracks when a user views a book detail page.
    Used by the recommendation engine to infer interest
    signals from browsing behaviour.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='book_views',
    )
    book = models.ForeignKey(
        'catalog.Book',
        on_delete=models.CASCADE,
        related_name='views',
    )
    viewed_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.PositiveIntegerField(
        default=0,
        help_text='Approximate time on the detail page (updated on leave).',
    )
    source = models.CharField(
        max_length=30, blank=True, default='catalog',
        help_text='Where the view originated: catalog, search, recommendation, trending.',
    )

    class Meta:
        db_table = 'intelligence_book_view'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['user', '-viewed_at']),
            models.Index(fields=['book', '-viewed_at']),
            models.Index(fields=['-viewed_at']),
        ]

    def __str__(self):
        return f'{self.user} viewed {self.book} at {self.viewed_at}'
