"""
Nova — Intelligence GraphQL Schema
=======================================
Recommendations, preferences, search analytics, trending, AI models,
hybrid search, predictive analytics, notifications, reading behaviour.
"""

import graphene
from graphene_django import DjangoObjectType

from apps.common.decorators import require_authentication, require_roles
from apps.common.permissions import Role

from apps.intelligence.application import (
    RecommendationService,
    SearchAnalyticsService,
    TrendingService,
    UserPreferenceService,
)
from apps.intelligence.domain.models import (
    AIModelVersion,
    AIProviderConfig,
    BookView,
    Recommendation,
    SearchLog,
    TrendingBook,
    UserPreference,
)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class RecommendationType(DjangoObjectType):
    class Meta:
        model = Recommendation
        fields = (
            'id', 'user', 'book', 'strategy', 'score',
            'explanation', 'seed_book', 'is_dismissed',
            'is_clicked', 'clicked_at', 'created_at',
        )


class UserPreferenceType(DjangoObjectType):
    class Meta:
        model = UserPreference
        fields = (
            'id', 'user', 'preferred_categories',
            'preferred_authors', 'preferred_languages',
            'disliked_categories', 'reading_speed',
            'last_computed_at', 'created_at', 'updated_at',
        )


class SearchLogType(DjangoObjectType):
    class Meta:
        model = SearchLog
        fields = (
            'id', 'user', 'query_text', 'filters_applied',
            'results_count', 'clicked_result_id', 'timestamp',
        )


class TrendingBookType(DjangoObjectType):
    class Meta:
        model = TrendingBook
        fields = (
            'id', 'book', 'period', 'rank',
            'borrow_count', 'view_count', 'review_count', 'score',
        )


class AIModelVersionType(DjangoObjectType):
    class Meta:
        model = AIModelVersion
        fields = (
            'id', 'model_type', 'version', 'name',
            'description', 'config', 'metrics',
            'is_active', 'created_at',
        )


class TrendingSearchType(graphene.ObjectType):
    query_text = graphene.String()
    count = graphene.Int()


# -- Hybrid search result types ---

class SearchResultType(graphene.ObjectType):
    book_id = graphene.UUID()
    title = graphene.String()
    subtitle = graphene.String()
    author_names = graphene.List(graphene.String)
    isbn = graphene.String()
    score = graphene.Float()
    snippet = graphene.String()


class SearchFacetValueType(graphene.ObjectType):
    value = graphene.String()
    count = graphene.Int()


class SearchFacetType(graphene.ObjectType):
    name = graphene.String()
    values = graphene.List(SearchFacetValueType)


class SearchResponseType(graphene.ObjectType):
    results = graphene.List(SearchResultType)
    total = graphene.Int()
    page = graphene.Int()
    facets = graphene.List(SearchFacetType)
    query_time_ms = graphene.Float()
    corrected_query = graphene.String()


class AutoSuggestType(graphene.ObjectType):
    text = graphene.String()
    source = graphene.String()


# -- Predictive analytics types ---

class OverduePredictionType(graphene.ObjectType):
    borrow_id = graphene.UUID()
    user_email = graphene.String()
    book_title = graphene.String()
    probability = graphene.Float()
    risk_level = graphene.String()
    contributing_factors = graphene.List(graphene.String)


class DemandForecastType(graphene.ObjectType):
    book_id = graphene.UUID()
    book_title = graphene.String()
    trend = graphene.String()
    predicted_borrows = graphene.Float()
    recommended_copies = graphene.Int()


class ChurnPredictionType(graphene.ObjectType):
    user_id = graphene.UUID()
    user_email = graphene.String()
    churn_probability = graphene.Float()
    risk_level = graphene.String()
    weeks_inactive = graphene.Int()
    recommendations = graphene.List(graphene.String)


class CollectionGapType(graphene.ObjectType):
    category_name = graphene.String()
    gap_severity = graphene.String()
    current_copies = graphene.Int()
    borrow_demand = graphene.Int()
    search_demand = graphene.Int()
    waitlist_count = graphene.Int()
    suggested_acquisitions = graphene.Int()


# -- Notification types ---

class NotificationType(graphene.ObjectType):
    id = graphene.UUID()
    notification_type = graphene.String()
    channel = graphene.String()
    priority = graphene.Int()
    title = graphene.String()
    body = graphene.String()
    data = graphene.JSONString()
    is_read = graphene.Boolean()
    read_at = graphene.DateTime()
    created_at = graphene.DateTime()


class NotificationCountType(graphene.ObjectType):
    total_unread = graphene.Int()
    by_type = graphene.JSONString()


# -- Reading behaviour types ---

class ReadingSpeedType(graphene.ObjectType):
    words_per_minute = graphene.Float()
    category = graphene.String()
    sessions_analyzed = graphene.Int()


class SessionPatternType(graphene.ObjectType):
    peak_hour = graphene.Int()
    peak_day = graphene.String()
    avg_session_minutes = graphene.Float()
    preferred_time = graphene.String()
    sessions_per_week = graphene.Float()
    total_sessions = graphene.Int()


class EngagementHeatmapType(graphene.ObjectType):
    heatmap = graphene.List(graphene.List(graphene.Float))
    days = graphene.List(graphene.String)
    hours = graphene.List(graphene.Int)


class CompletionPredictionType(graphene.ObjectType):
    asset_id = graphene.UUID()
    title = graphene.String()
    completion_probability = graphene.Float()
    estimated_days = graphene.Int()
    current_progress = graphene.Float()


# -- Content analysis types ---

class ReadingLevelType(graphene.ObjectType):
    level = graphene.String()
    grade_level = graphene.Float()
    flesch_kincaid = graphene.Float()
    gunning_fog = graphene.Float()
    coleman_liau = graphene.Float()


# -- Evaluation types ---

class RecommendationMetricsType(graphene.ObjectType):
    precision_at_k = graphene.Float()
    recall_at_k = graphene.Float()
    ndcg_at_k = graphene.Float()
    mrr = graphene.Float()
    hit_rate = graphene.Float()
    catalog_coverage = graphene.Float()
    diversity = graphene.Float()
    novelty = graphene.Float()


class PipelineResultType(graphene.ObjectType):
    pipeline_name = graphene.String()
    status = graphene.String()
    stages_completed = graphene.List(graphene.String)
    stages_failed = graphene.List(graphene.String)
    metrics = graphene.JSONString()
    total_time_seconds = graphene.Float()
    errors = graphene.List(graphene.String)


# ---------------------------------------------------------------------------
# AI Provider Configuration Type (must be before Query)
# ---------------------------------------------------------------------------

class AIProviderConfigType(DjangoObjectType):
    class Meta:
        model = AIProviderConfig
        fields = (
            'id', 'provider', 'capability', 'display_name', 'model_name',
            'api_base_url', 'extra_config', 'is_active', 'is_healthy',
            'last_health_check', 'last_error', 'created_at', 'updated_at',
        )
        # Deliberately exclude api_key from GraphQL output


class BookViewType(DjangoObjectType):
    class Meta:
        model = BookView
        fields = (
            'id', 'user', 'book', 'viewed_at',
            'duration_seconds', 'source',
        )


# -- LLM Analytics type ---

class LLMAnalyticsType(graphene.ObjectType):
    summary = graphene.String()
    overdue_insights = graphene.String()
    demand_insights = graphene.String()
    user_insights = graphene.String()
    collection_insights = graphene.String()
    recommendations = graphene.List(graphene.String)
    model_used = graphene.String()
    error = graphene.String()


# -- AI Search types ---

class AISearchSourceType(graphene.ObjectType):
    book_id = graphene.String()
    title = graphene.String()
    subtitle = graphene.String()
    authors = graphene.List(graphene.String)
    categories = graphene.List(graphene.String)
    isbn = graphene.String()
    rating = graphene.Float()
    available_copies = graphene.Int()
    total_copies = graphene.Int()
    total_borrows = graphene.Int()


class AISearchResponseType(graphene.ObjectType):
    answer = graphene.String()
    sources = graphene.List(AISearchSourceType)
    model_used = graphene.String()
    error = graphene.String()


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

class IntelligenceQuery(graphene.ObjectType):
    # --- Existing queries ---
    my_recommendations = graphene.List(
        RecommendationType,
        limit=graphene.Int(default_value=20),
        strategy=graphene.String(),
    )
    my_preferences = graphene.Field(UserPreferenceType)

    trending_books = graphene.List(
        TrendingBookType,
        period=graphene.String(default_value='WEEKLY'),
        limit=graphene.Int(default_value=20),
    )
    trending_searches = graphene.List(
        TrendingSearchType,
        limit=graphene.Int(default_value=10),
        days=graphene.Int(default_value=7),
    )

    # Admin
    ai_models = graphene.List(
        AIModelVersionType,
        model_type=graphene.String(),
    )
    search_analytics = graphene.List(
        SearchLogType,
        limit=graphene.Int(default_value=50),
    )

    # --- Hybrid search ---
    search_books = graphene.Field(
        SearchResponseType,
        query=graphene.String(required=True),
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        category=graphene.String(),
        author=graphene.String(),
        language=graphene.String(),
        min_rating=graphene.Float(),
        year_from=graphene.Int(),
        year_to=graphene.Int(),
        digital_only=graphene.Boolean(),
        available_only=graphene.Boolean(),
    )
    auto_suggest = graphene.List(
        AutoSuggestType,
        prefix=graphene.String(required=True),
        limit=graphene.Int(default_value=8),
    )

    # --- Predictive analytics (admin) ---
    overdue_predictions = graphene.List(
        OverduePredictionType,
        limit=graphene.Int(default_value=50),
    )
    demand_forecasts = graphene.List(
        DemandForecastType,
        limit=graphene.Int(default_value=20),
    )
    churn_predictions = graphene.List(
        ChurnPredictionType,
        limit=graphene.Int(default_value=50),
    )
    collection_gaps = graphene.List(
        CollectionGapType,
        min_severity=graphene.String(default_value='LOW'),
    )

    # --- Notifications ---
    my_notifications = graphene.List(
        NotificationType,
        limit=graphene.Int(default_value=20),
        unread_only=graphene.Boolean(default_value=False),
    )
    notification_count = graphene.Field(NotificationCountType)

    # --- Reading behaviour ---
    my_reading_speed = graphene.Field(ReadingSpeedType)
    my_session_patterns = graphene.Field(SessionPatternType)
    my_engagement_heatmap = graphene.Field(
        EngagementHeatmapType,
        days=graphene.Int(default_value=30),
    )
    my_completion_predictions = graphene.List(CompletionPredictionType)

    # --- Model evaluation (admin) ---
    recommendation_metrics = graphene.Field(
        RecommendationMetricsType,
        k=graphene.Int(default_value=10),
    )

    # --- AI Provider Configuration (super-admin) ---
    ai_provider_configs = graphene.List(
        AIProviderConfigType,
        capability=graphene.String(),
        active_only=graphene.Boolean(default_value=False),
    )
    ai_provider_config = graphene.Field(
        AIProviderConfigType,
        id=graphene.UUID(required=True),
    )

    # --- LLM-powered analytics (admin) ---
    llm_analytics = graphene.Field(LLMAnalyticsType)

    # --- AI-powered search ---
    ai_search = graphene.Field(
        AISearchResponseType,
        query=graphene.String(required=True),
    )

    # --- Browse history ---
    my_browse_history = graphene.List(
        BookViewType,
        limit=graphene.Int(default_value=20),
    )

    # --- Existing resolvers ---

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def resolve_ai_provider_configs(self, info, capability=None, active_only=False):
        qs = AIProviderConfig.objects.all()
        if capability:
            qs = qs.filter(capability=capability)
        if active_only:
            qs = qs.filter(is_active=True)
        return qs

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def resolve_ai_provider_config(self, info, id):
        return AIProviderConfig.objects.get(id=id)

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_llm_analytics(self, info):
        from apps.intelligence.infrastructure.llm_analytics import (
            generate_llm_analytics,
        )

        result = generate_llm_analytics()
        return LLMAnalyticsType(
            summary=result.summary,
            overdue_insights=result.overdue_insights,
            demand_insights=result.demand_insights,
            user_insights=result.user_insights,
            collection_insights=result.collection_insights,
            recommendations=result.recommendations,
            model_used=result.model_used,
            error=result.error,
        )

    def resolve_ai_search(self, info, query):
        from apps.intelligence.infrastructure.llm_search import ai_search

        user = getattr(info.context, 'user', None)
        user_id = str(user.id) if user and user.is_authenticated else None

        result = ai_search(query=query, user_id=user_id)

        sources = [
            AISearchSourceType(
                book_id=s['bookId'],
                title=s['title'],
                subtitle=s.get('subtitle', ''),
                authors=s.get('authors', []),
                categories=s.get('categories', []),
                isbn=s.get('isbn', ''),
                rating=s.get('rating', 0),
                available_copies=s.get('availableCopies', 0),
                total_copies=s.get('totalCopies', 0),
                total_borrows=s.get('totalBorrows', 0),
            )
            for s in result.sources
        ]

        return AISearchResponseType(
            answer=result.answer,
            sources=sources,
            model_used=result.model_used,
            error=result.error,
        )

    @require_authentication
    def resolve_my_browse_history(self, info, limit=20):
        return BookView.objects.filter(
            user=info.context.user,
        ).select_related('book')[:limit]

    @require_authentication
    def resolve_my_recommendations(self, info, limit=20, strategy=None):
        return RecommendationService.get_for_user(
            info.context.user.id, limit=limit, strategy=strategy,
        )

    @require_authentication
    def resolve_my_preferences(self, info):
        return UserPreferenceService.get_or_create(info.context.user.id)

    def resolve_trending_books(self, info, period='WEEKLY', limit=20):
        return TrendingService.get_trending(period=period, limit=limit)

    def resolve_trending_searches(self, info, limit=10, days=7):
        results = SearchAnalyticsService.trending_searches(
            limit=limit, days=days,
        )
        return [
            TrendingSearchType(
                query_text=r['query_text'], count=r['count'],
            )
            for r in results
        ]

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def resolve_ai_models(self, info, model_type=None):
        qs = AIModelVersion.objects.all()
        if model_type:
            qs = qs.filter(model_type=model_type)
        return qs

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_search_analytics(self, info, limit=50):
        return SearchLog.objects.all()[:limit]

    # --- Search resolvers ---

    def resolve_search_books(
        self, info,
        query, page=1, page_size=20,
        category=None, author=None, language=None,
        min_rating=None, year_from=None, year_to=None,
        digital_only=None, available_only=None,
    ):
        import time
        from apps.intelligence.infrastructure.search_engine import (
            SearchEngine, SearchRequest,
        )

        user = getattr(info.context, 'user', None)
        user_id = str(user.id) if user and user.is_authenticated else None

        filters = {}
        if category:
            filters['category'] = category
        if author:
            filters['author'] = author
        if language:
            filters['language'] = language
        if min_rating is not None:
            filters['min_rating'] = min_rating
        if year_from is not None:
            filters['year_from'] = year_from
        if year_to is not None:
            filters['year_to'] = year_to
        if digital_only:
            filters['digital_only'] = True
        if available_only:
            filters['available_only'] = True

        request = SearchRequest(
            query=query,
            user_id=user_id,
            page=page,
            page_size=page_size,
            filters=filters,
        )

        try:
            start = time.monotonic()
            response = SearchEngine.search(request)
            query_time = (time.monotonic() - start) * 1000
        except Exception as exc:
            import logging
            logging.getLogger('nova.intelligence.search').error(
                'Search engine error: %s', exc, exc_info=True,
            )
            return SearchResponseType(
                results=[], total=0, page=page, facets=[],
                query_time_ms=0, corrected_query=None,
            )

        # Fetch full book details for enrichment
        from apps.catalog.domain.models import Book
        import uuid as _uuid
        book_ids = []
        for r in response.results:
            try:
                _uuid.UUID(str(r.book_id))
                book_ids.append(r.book_id)
            except (ValueError, AttributeError):
                continue

        books_qs = (
            Book.all_objects
            .filter(id__in=book_ids, deleted_at__isnull=True)
            .select_related()
            .prefetch_related('authors')
        )
        book_map = {str(b.id): b for b in books_qs}

        results = []
        for r in response.results:
            book = book_map.get(r.book_id)
            results.append(SearchResultType(
                book_id=r.book_id,
                title=r.title,
                subtitle=getattr(book, 'subtitle', '') if book else '',
                author_names=[a.full_name for a in book.authors.all()] if book else [],
                isbn=getattr(book, 'isbn_13', '') if book else '',
                score=r.score,
                snippet=(book.description[:200] + '…') if book and book.description else '',
            ))

        facets = []
        for name, values in response.facets.items():
            if isinstance(values, dict):
                facets.append(SearchFacetType(
                    name=name,
                    values=[
                        SearchFacetValueType(value=str(v), count=c)
                        for v, c in values.items()
                    ],
                ))
            elif isinstance(values, list):
                facets.append(SearchFacetType(
                    name=name,
                    values=[
                        SearchFacetValueType(
                            value=item.get('name') or item.get('code') or str(item),
                            count=item.get('count', 0),
                        )
                        for item in values
                    ],
                ))

        # Log the search
        if user_id:
            try:
                SearchLog.objects.create(
                    user_id=user_id,
                    query_text=query,
                    filters_applied=filters,
                    results_count=response.total_count,
                )
            except Exception:
                pass  # Don't let logging failures break search

        return SearchResponseType(
            results=results,
            total=response.total_count,
            page=page,
            facets=facets,
            query_time_ms=round(query_time, 1),
            corrected_query=getattr(response, 'corrected_query', None),
        )

    def resolve_auto_suggest(self, info, prefix, limit=8):
        from apps.intelligence.infrastructure.search_engine import (
            AutoSuggestEngine,
        )

        user = getattr(info.context, 'user', None)
        user_id = str(user.id) if user and user.is_authenticated else None

        suggestions = AutoSuggestEngine.suggest(
            prefix=prefix, user_id=user_id, limit=limit,
        )
        return [
            AutoSuggestType(text=s['text'], source=s['source'])
            for s in suggestions
        ]

    # --- Predictive analytics resolvers ---

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_overdue_predictions(self, info, limit=50):
        from apps.intelligence.infrastructure.predictive_analytics import (
            OverduePredictor,
        )

        all_preds = OverduePredictor.predict_batch()[:limit]

        return [
            OverduePredictionType(
                borrow_id=p.borrow_id,
                user_email=p.user_id,  # will be resolved below
                book_title=p.book_id,  # will be resolved below
                probability=p.probability,
                risk_level=p.risk_level,
                contributing_factors=p.contributing_factors,
            )
            for p in all_preds
        ]

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_demand_forecasts(self, info, limit=20):
        from apps.intelligence.infrastructure.predictive_analytics import (
            DemandForecaster,
        )

        forecasts = DemandForecaster.forecast_all(top_n=limit)

        return [
            DemandForecastType(
                book_id=f.book_id,
                book_title=f.title,
                trend=f.trend,
                predicted_borrows=f.forecasted_demand,
                recommended_copies=f.recommended_copies,
            )
            for f in forecasts
        ]

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_churn_predictions(self, info, limit=50):
        from apps.intelligence.infrastructure.predictive_analytics import (
            ChurnPredictor,
        )

        all_preds = ChurnPredictor.predict_all(min_days_registered=30)
        # Filter to meaningful risk and limit
        filtered = [p for p in all_preds if p.churn_probability >= 0.3][:limit]

        return [
            ChurnPredictionType(
                user_id=p.user_id,
                user_email=p.email,
                churn_probability=p.churn_probability,
                risk_level=p.risk_level,
                weeks_inactive=p.days_since_last_activity // 7,
                recommendations=p.recommendations,
            )
            for p in filtered
        ]

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_collection_gaps(self, info, min_severity='LOW'):
        from apps.intelligence.infrastructure.predictive_analytics import (
            CollectionGapAnalyzer,
        )

        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2, 'LOW': 3}
        min_order = severity_order.get(min_severity, 3)

        gaps = CollectionGapAnalyzer.analyse()
        return [
            CollectionGapType(
                category_name=g.category_name,
                gap_severity=g.gap_severity,
                current_copies=g.current_copies,
                borrow_demand=g.borrow_demand,
                search_demand=g.search_demand,
                waitlist_count=g.waitlist_count,
                suggested_acquisitions=g.suggested_acquisitions,
            )
            for g in gaps
            if severity_order.get(g.gap_severity, 3) <= min_order
        ]

    # --- Notification resolvers ---

    @require_authentication
    def resolve_my_notifications(self, info, limit=20, unread_only=False):
        from apps.intelligence.infrastructure.notification_engine import (
            NotificationEngine,
        )

        if unread_only:
            notifs = NotificationEngine.get_unread(info.context.user)[:limit]
        else:
            from apps.intelligence.infrastructure.notification_engine import (
                UserNotification,
            )
            notifs = UserNotification.objects.filter(
                user=info.context.user,
            ).order_by('-created_at')[:limit]

        return [
            NotificationType(
                id=n.id,
                notification_type=n.notification_type,
                channel=n.channel,
                priority=n.priority,
                title=n.title,
                body=n.body,
                data=n.data,
                is_read=n.is_read,
                read_at=n.read_at,
                created_at=n.created_at,
            )
            for n in notifs
        ]

    @require_authentication
    def resolve_notification_count(self, info):
        from django.db.models import Count
        from apps.intelligence.infrastructure.notification_engine import (
            UserNotification,
        )

        qs = UserNotification.objects.filter(
            user=info.context.user, is_read=False,
        )
        total = qs.count()
        by_type = dict(
            qs.values_list('notification_type')
            .annotate(cnt=Count('id'))
            .values_list('notification_type', 'cnt')
        )

        return NotificationCountType(
            total_unread=total,
            by_type=by_type,
        )

    # --- Reading behaviour resolvers ---

    @require_authentication
    def resolve_my_reading_speed(self, info):
        from apps.intelligence.infrastructure.reading_behavior import (
            ReadingSpeedAnalyzer,
        )

        result = ReadingSpeedAnalyzer.analyze(info.context.user)
        return ReadingSpeedType(
            words_per_minute=result.words_per_minute,
            category=result.category,
            sessions_analyzed=result.sessions_analyzed,
        )

    @require_authentication
    def resolve_my_session_patterns(self, info):
        from apps.intelligence.infrastructure.reading_behavior import (
            SessionPatternAnalyzer,
        )

        result = SessionPatternAnalyzer.analyze(info.context.user)
        return SessionPatternType(
            peak_hour=result.peak_hour,
            peak_day=result.peak_day,
            avg_session_minutes=result.avg_session_minutes,
            preferred_time=result.preferred_time,
            sessions_per_week=result.sessions_per_week,
            total_sessions=result.total_sessions,
        )

    @require_authentication
    def resolve_my_engagement_heatmap(self, info, days=30):
        from apps.intelligence.infrastructure.reading_behavior import (
            EngagementHeatmapGenerator,
        )

        result = EngagementHeatmapGenerator.generate(
            info.context.user, days=days,
        )
        return EngagementHeatmapType(
            heatmap=result.heatmap,
            days=result.days,
            hours=result.hours,
        )

    @require_authentication
    def resolve_my_completion_predictions(self, info):
        from apps.digital_content.domain.models import ReadingSession
        from apps.intelligence.infrastructure.reading_behavior import (
            CompletionPredictor,
        )

        # Get active digital reading sessions
        active_assets = (
            ReadingSession.objects
            .filter(user=info.context.user)
            .values_list('digital_asset_id', flat=True)
            .distinct()
        )

        results = []
        for asset_id in active_assets[:10]:
            try:
                from apps.digital_content.domain.models import DigitalAsset
                asset = DigitalAsset.objects.get(id=asset_id)
                pred = CompletionPredictor.predict(info.context.user, asset.id)
                results.append(CompletionPredictionType(
                    asset_id=asset.id,
                    title=asset.book.title if asset.book else 'Unknown',
                    completion_probability=pred.completion_probability,
                    estimated_days=pred.estimated_days,
                    current_progress=pred.current_progress,
                ))
            except Exception:
                continue

        return results

    # --- Model evaluation resolver ---

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def resolve_recommendation_metrics(self, info, k=10):
        from apps.intelligence.infrastructure.evaluation import (
            RecommendationEvaluator,
        )

        metrics = RecommendationEvaluator.evaluate(k=k)
        return RecommendationMetricsType(
            precision_at_k=metrics.precision_at_k,
            recall_at_k=metrics.recall_at_k,
            ndcg_at_k=metrics.ndcg_at_k,
            mrr=metrics.mrr,
            hit_rate=metrics.hit_rate,
            catalog_coverage=metrics.catalog_coverage,
            diversity=metrics.diversity,
            novelty=metrics.novelty,
        )


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

class GenerateRecommendations(graphene.Mutation):
    """Trigger async recommendation generation for current user."""
    task_id = graphene.String()
    success = graphene.Boolean()

    @require_authentication
    def mutate(self, info):
        try:
            task_id = RecommendationService.generate_for_user(
                info.context.user.id,
            )
            return GenerateRecommendations(task_id=task_id, success=True)
        except Exception as exc:
            logger.error('GenerateRecommendations mutation failed: %s', exc)
            return GenerateRecommendations(task_id=None, success=False)


class ClickRecommendation(graphene.Mutation):
    class Arguments:
        recommendation_id = graphene.UUID(required=True)

    success = graphene.Boolean()

    @require_authentication
    def mutate(self, info, recommendation_id):
        ok = RecommendationService.record_click(
            recommendation_id, info.context.user.id,
        )
        return ClickRecommendation(success=ok)


class DismissRecommendation(graphene.Mutation):
    class Arguments:
        recommendation_id = graphene.UUID(required=True)

    success = graphene.Boolean()

    @require_authentication
    def mutate(self, info, recommendation_id):
        ok = RecommendationService.dismiss(
            recommendation_id, info.context.user.id,
        )
        return DismissRecommendation(success=ok)


class UpdatePreferences(graphene.Mutation):
    class Arguments:
        preferred_categories = graphene.List(graphene.String)
        preferred_authors = graphene.List(graphene.String)
        preferred_languages = graphene.List(graphene.String)
        disliked_categories = graphene.List(graphene.String)

    preferences = graphene.Field(UserPreferenceType)

    @require_authentication
    def mutate(
        self, info,
        preferred_categories=None,
        preferred_authors=None,
        preferred_languages=None,
        disliked_categories=None,
    ):
        from apps.intelligence.application import UserPreferenceDTO

        dto = UserPreferenceDTO(
            preferred_categories=preferred_categories or [],
            preferred_authors=preferred_authors or [],
            preferred_languages=preferred_languages or [],
            disliked_categories=disliked_categories or [],
        )
        pref = UserPreferenceService.update_explicit(
            info.context.user.id, dto,
        )
        return UpdatePreferences(preferences=pref)


class RecomputePreferenceVector(graphene.Mutation):
    """Trigger async recomputation of the user's preference embedding."""
    task_id = graphene.String()

    @require_authentication
    def mutate(self, info):
        task_id = UserPreferenceService.recompute_preference_vector(
            info.context.user.id,
        )
        return RecomputePreferenceVector(task_id=task_id)


class ActivateAIModel(graphene.Mutation):
    """Admin: activate a specific AI model version."""
    class Arguments:
        model_id = graphene.UUID(required=True)

    success = graphene.Boolean()
    model = graphene.Field(AIModelVersionType)

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def mutate(self, info, model_id):
        try:
            version = AIModelVersion.objects.get(id=model_id)
            version.activate()
            return ActivateAIModel(success=True, model=version)
        except AIModelVersion.DoesNotExist:
            return ActivateAIModel(success=False, model=None)


class MarkNotificationRead(graphene.Mutation):
    """Mark a single notification as read."""
    class Arguments:
        notification_id = graphene.UUID(required=True)

    success = graphene.Boolean()

    @require_authentication
    def mutate(self, info, notification_id):
        from django.utils import timezone
        from apps.intelligence.infrastructure.notification_engine import (
            UserNotification,
        )

        try:
            notif = UserNotification.objects.get(
                id=notification_id, user=info.context.user,
            )
            notif.is_read = True
            notif.read_at = timezone.now()
            notif.save(update_fields=['is_read', 'read_at'])
            return MarkNotificationRead(success=True)
        except UserNotification.DoesNotExist:
            return MarkNotificationRead(success=False)


class MarkAllNotificationsRead(graphene.Mutation):
    """Mark all notifications as read for the current user."""
    count = graphene.Int()

    @require_authentication
    def mutate(self, info):
        from apps.intelligence.infrastructure.notification_engine import (
            NotificationEngine,
        )

        count = NotificationEngine.mark_all_read(info.context.user)
        return MarkAllNotificationsRead(count=count)


class LogSearchClick(graphene.Mutation):
    """Record that a user clicked a search result."""
    class Arguments:
        search_log_id = graphene.UUID(required=True)
        clicked_book_id = graphene.UUID(required=True)

    success = graphene.Boolean()

    @require_authentication
    def mutate(self, info, search_log_id, clicked_book_id):
        try:
            log = SearchLog.objects.get(
                id=search_log_id, user=info.context.user,
            )
            log.clicked_result_id = clicked_book_id
            log.save(update_fields=['clicked_result_id'])
            return LogSearchClick(success=True)
        except SearchLog.DoesNotExist:
            return LogSearchClick(success=False)


class LogBookView(graphene.Mutation):
    """Record that a user viewed a book detail page."""
    class Arguments:
        book_id = graphene.UUID(required=True)
        source = graphene.String(default_value='catalog')
        duration_seconds = graphene.Int(default_value=0)

    success = graphene.Boolean()
    view_id = graphene.UUID()

    @require_authentication
    def mutate(self, info, book_id, source='catalog', duration_seconds=0):
        from apps.catalog.domain.models import Book
        from django.utils import timezone
        from datetime import timedelta

        user = info.context.user

        # Deduplicate: if user viewed same book within last 5 minutes, update duration
        recent_cutoff = timezone.now() - timedelta(minutes=5)
        existing = BookView.objects.filter(
            user=user, book_id=book_id, viewed_at__gte=recent_cutoff,
        ).first()

        if existing:
            if duration_seconds > 0:
                existing.duration_seconds = duration_seconds
                existing.save(update_fields=['duration_seconds'])
            return LogBookView(success=True, view_id=existing.id)

        try:
            Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return LogBookView(success=False, view_id=None)

        view = BookView.objects.create(
            user=user,
            book_id=book_id,
            source=source,
            duration_seconds=duration_seconds,
        )
        return LogBookView(success=True, view_id=view.id)


class TriggerModelTraining(graphene.Mutation):
    """Admin: trigger an ML training pipeline asynchronously."""
    class Arguments:
        pipeline = graphene.String(default_value='all')

    task_id = graphene.String()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def mutate(self, info, pipeline='all'):
        from apps.intelligence.infrastructure.tasks import run_model_training

        result = run_model_training.apply_async(
            kwargs={'pipeline': pipeline},
        )
        return TriggerModelTraining(task_id=str(result.id))


class TriggerEmbeddingComputation(graphene.Mutation):
    """Admin: trigger batch embedding computation."""
    class Arguments:
        batch_size = graphene.Int(default_value=200)

    task_id = graphene.String()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def mutate(self, info, batch_size=200):
        from apps.intelligence.infrastructure.tasks import (
            compute_book_embeddings_batch,
        )

        result = compute_book_embeddings_batch.apply_async(
            args=[batch_size],
        )
        return TriggerEmbeddingComputation(task_id=str(result.id))


# ---------------------------------------------------------------------------
# AI Provider Configuration (Super-Admin)
# ---------------------------------------------------------------------------

class CreateAIProviderConfig(graphene.Mutation):
    """Super-Admin: register a new AI provider configuration."""
    class Arguments:
        provider = graphene.String(required=True)
        capability = graphene.String(required=True)
        display_name = graphene.String(required=True)
        model_name = graphene.String(required=True)
        api_base_url = graphene.String(default_value='')
        api_key = graphene.String(default_value='')
        extra_config = graphene.JSONString(default_value='{}')

    config = graphene.Field(AIProviderConfigType)

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def mutate(self, info, provider, capability, display_name, model_name,
               api_base_url='', api_key='', extra_config=None):
        import json
        if isinstance(extra_config, str):
            extra_config = json.loads(extra_config) if extra_config else {}

        config = AIProviderConfig.objects.create(
            provider=provider,
            capability=capability,
            display_name=display_name,
            model_name=model_name,
            api_base_url=api_base_url,
            api_key=api_key,
            extra_config=extra_config or {},
        )
        return CreateAIProviderConfig(config=config)


class UpdateAIProviderConfig(graphene.Mutation):
    """Super-Admin: update an existing AI provider configuration."""
    class Arguments:
        config_id = graphene.UUID(required=True)
        display_name = graphene.String()
        model_name = graphene.String()
        api_base_url = graphene.String()
        api_key = graphene.String()
        extra_config = graphene.JSONString()

    config = graphene.Field(AIProviderConfigType)

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def mutate(self, info, config_id, **kwargs):
        import json
        config = AIProviderConfig.objects.get(id=config_id)

        for field in ('display_name', 'model_name', 'api_base_url', 'api_key'):
            if kwargs.get(field) is not None:
                setattr(config, field, kwargs[field])

        if kwargs.get('extra_config') is not None:
            ec = kwargs['extra_config']
            config.extra_config = json.loads(ec) if isinstance(ec, str) else ec

        config.save()
        return UpdateAIProviderConfig(config=config)


class DeleteAIProviderConfig(graphene.Mutation):
    """Super-Admin: remove an AI provider configuration."""
    class Arguments:
        config_id = graphene.UUID(required=True)

    success = graphene.Boolean()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def mutate(self, info, config_id):
        AIProviderConfig.objects.filter(id=config_id).delete()
        return DeleteAIProviderConfig(success=True)


class ActivateAIProviderConfig(graphene.Mutation):
    """Super-Admin: activate a provider config (deactivates others for same capability)."""
    class Arguments:
        config_id = graphene.UUID(required=True)

    config = graphene.Field(AIProviderConfigType)

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def mutate(self, info, config_id):
        config = AIProviderConfig.objects.get(id=config_id)
        config.activate()
        return ActivateAIProviderConfig(config=config)


class TestAIProviderConfig(graphene.Mutation):
    """Super-Admin: run a health check on a provider configuration."""
    class Arguments:
        config_id = graphene.UUID(required=True)

    healthy = graphene.Boolean()
    message = graphene.String()
    config = graphene.Field(AIProviderConfigType)

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def mutate(self, info, config_id):
        from apps.intelligence.infrastructure.ai_providers.factory import (
            test_provider_config,
        )
        healthy, message = test_provider_config(str(config_id))
        config = AIProviderConfig.objects.get(id=config_id)
        return TestAIProviderConfig(healthy=healthy, message=message, config=config)


class GenerateAIResponse(graphene.Mutation):
    """Super-Admin: test text generation with the active chat provider."""
    class Arguments:
        prompt = graphene.String(required=True)
        system_prompt = graphene.String(default_value='')
        capability = graphene.String(default_value='CHAT')

    text = graphene.String()
    model = graphene.String()
    error = graphene.String()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    def mutate(self, info, prompt, system_prompt='', capability='CHAT'):
        from apps.intelligence.infrastructure.ai_providers.factory import get_provider
        provider = get_provider(capability)
        if not provider:
            return GenerateAIResponse(
                text='', model='',
                error=f'No active provider for capability "{capability}".',
            )
        try:
            resp = provider.generate(prompt, system_prompt=system_prompt)
            return GenerateAIResponse(text=resp.text, model=resp.model, error='')
        except Exception as e:
            return GenerateAIResponse(text='', model='', error=str(e))


class IntelligenceMutation(graphene.ObjectType):
    generate_recommendations = GenerateRecommendations.Field()
    click_recommendation = ClickRecommendation.Field()
    dismiss_recommendation = DismissRecommendation.Field()
    update_preferences = UpdatePreferences.Field()
    recompute_preference_vector = RecomputePreferenceVector.Field()
    activate_ai_model = ActivateAIModel.Field()
    # Role 5 additions
    mark_notification_read = MarkNotificationRead.Field()
    mark_all_notifications_read = MarkAllNotificationsRead.Field()
    log_search_click = LogSearchClick.Field()
    log_book_view = LogBookView.Field()
    trigger_model_training = TriggerModelTraining.Field()
    trigger_embedding_computation = TriggerEmbeddingComputation.Field()
    # AI Provider Configuration (super-admin)
    create_ai_provider_config = CreateAIProviderConfig.Field()
    update_ai_provider_config = UpdateAIProviderConfig.Field()
    delete_ai_provider_config = DeleteAIProviderConfig.Field()
    activate_ai_provider_config = ActivateAIProviderConfig.Field()
    test_ai_provider_config = TestAIProviderConfig.Field()
    generate_ai_response = GenerateAIResponse.Field()
