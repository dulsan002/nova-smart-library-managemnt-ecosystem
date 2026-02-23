"""
Nova — Predictive Analytics Engine
=======================================
ML models for library operations intelligence:

1. **Overdue Predictor**: Classifies borrow records likely to become overdue
   using logistic regression on historical features.
2. **Demand Forecaster**: Predicts weekly borrow demand per book using
   exponential smoothing + linear trend.
3. **Churn Predictor**: Identifies users at risk of disengaging based on
   declining activity patterns.
4. **Collection Gap Analyzer**: Identifies subject areas where demand
   exceeds supply, recommending acquisition targets.
"""

import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from django.conf import settings
from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone

logger = logging.getLogger('nova.intelligence.analytics')


# ====================================================================
# 1. Overdue Predictor
# ====================================================================

@dataclass
class OverduePrediction:
    borrow_id: str
    user_id: str
    book_id: str
    probability: float        # 0.0–1.0
    risk_level: str           # 'LOW', 'MEDIUM', 'HIGH'
    contributing_factors: List[str] = field(default_factory=list)


class OverduePredictor:
    """
    Logistic-regression-style overdue prediction using hand-crafted
    features derived from the user's borrowing history.

    Features:
      - User's historical overdue rate
      - Current number of active borrows
      - Days remaining until due date
      - Book popularity (borrow count)
      - User's average borrow duration
      - Day-of-week borrowing pattern
      - KP level (engagement proxy)
    """

    # Feature weights learned from heuristic tuning
    # (In production these would be trained via scikit-learn)
    WEIGHTS = {
        'overdue_rate': 3.5,
        'active_borrows_ratio': 1.2,
        'days_remaining_norm': -2.8,
        'book_popularity_norm': -0.3,
        'avg_duration_norm': 0.8,
        'low_engagement': 1.5,
        'weekend_borrow': 0.2,
        'bias': -1.5,
    }

    @classmethod
    def predict_batch(cls, active_borrow_ids=None) -> List[OverduePrediction]:
        """
        Predict overdue probability for all active borrows
        (or a specified subset).
        """
        from apps.circulation.domain.models import BorrowRecord

        qs = BorrowRecord.objects.filter(status='ACTIVE')
        if active_borrow_ids:
            qs = qs.filter(id__in=active_borrow_ids)

        qs = qs.select_related('user', 'book_copy__book')

        predictions = []
        for record in qs:
            pred = cls._predict_single(record)
            predictions.append(pred)

        predictions.sort(key=lambda p: p.probability, reverse=True)
        return predictions

    @classmethod
    def _predict_single(cls, record) -> OverduePrediction:
        from apps.circulation.domain.models import BorrowRecord
        from apps.engagement.domain.models import UserEngagement

        user = record.user
        factors = []

        # Feature 1: Historical overdue rate
        total_past = BorrowRecord.objects.filter(user=user).exclude(
            id=record.id,
        ).count()
        overdue_past = BorrowRecord.objects.filter(
            user=user, status__in=['OVERDUE', 'LOST'],
        ).exclude(id=record.id).count()

        overdue_rate = overdue_past / max(total_past, 1)
        if overdue_rate > 0.3:
            factors.append(f'High historical overdue rate ({overdue_rate:.0%})')

        # Feature 2: Active borrows vs limit
        active_count = BorrowRecord.objects.filter(
            user=user, status='ACTIVE',
        ).count()
        borrow_limit = settings.CIRCULATION_CONFIG.get(
            'MAX_CONCURRENT_BORROWS', 5,
        )
        active_ratio = active_count / borrow_limit
        if active_ratio > 0.8:
            factors.append(f'Near borrow limit ({active_count}/{borrow_limit})')

        # Feature 3: Days remaining
        today = timezone.now().date()
        days_remaining = (record.due_date - today).days
        days_remaining_norm = max(min(days_remaining / 14.0, 1.0), -1.0)
        if days_remaining <= 2:
            factors.append(f'Only {days_remaining} day(s) until due')

        # Feature 4: Book popularity (inverse — popular books return faster)
        book_popularity = record.book_copy.book.total_borrows
        pop_norm = min(book_popularity / 100.0, 1.0)

        # Feature 5: Average borrow duration
        avg_duration = (
            BorrowRecord.objects
            .filter(user=user, status='RETURNED', returned_at__isnull=False)
            .annotate(
                duration=F('returned_at') - F('created_at'),
            )
            .aggregate(avg=Avg('duration'))
        )
        avg_days = 14.0  # default
        if avg_duration['avg']:
            avg_days = avg_duration['avg'].total_seconds() / 86400
        avg_norm = min(avg_days / 28.0, 1.0)
        if avg_days > 18:
            factors.append(f'Tends to keep books longer (avg {avg_days:.0f} days)')

        # Feature 6: Engagement level
        low_engagement = 0.0
        try:
            eng = UserEngagement.objects.get(user=user)
            if eng.level <= 2:
                low_engagement = 1.0
                factors.append('Low engagement level')
        except UserEngagement.DoesNotExist:
            low_engagement = 1.0

        # Feature 7: Weekend borrow
        weekend = 1.0 if record.created_at.weekday() >= 5 else 0.0

        # Logistic regression
        z = (
            cls.WEIGHTS['overdue_rate'] * overdue_rate
            + cls.WEIGHTS['active_borrows_ratio'] * active_ratio
            + cls.WEIGHTS['days_remaining_norm'] * days_remaining_norm
            + cls.WEIGHTS['book_popularity_norm'] * pop_norm
            + cls.WEIGHTS['avg_duration_norm'] * avg_norm
            + cls.WEIGHTS['low_engagement'] * low_engagement
            + cls.WEIGHTS['weekend_borrow'] * weekend
            + cls.WEIGHTS['bias']
        )
        probability = 1.0 / (1.0 + math.exp(-z))

        # Risk level
        if probability >= 0.7:
            risk = 'HIGH'
        elif probability >= 0.4:
            risk = 'MEDIUM'
        else:
            risk = 'LOW'

        return OverduePrediction(
            borrow_id=str(record.id),
            user_id=str(record.user_id),
            book_id=str(record.book_copy.book_id),
            probability=round(probability, 4),
            risk_level=risk,
            contributing_factors=factors,
        )


# ====================================================================
# 2. Demand Forecaster
# ====================================================================

@dataclass
class DemandForecast:
    book_id: str
    title: str
    current_weekly_demand: float
    forecasted_demand: float
    trend: str                   # 'RISING', 'STABLE', 'DECLINING'
    confidence: float
    recommended_copies: int


class DemandForecaster:
    """
    Predicts future borrowing demand per book using exponential
    smoothing with trend decomposition.
    """

    ALPHA = 0.3   # Level smoothing factor
    BETA = 0.1    # Trend smoothing factor
    WEEKS_HISTORY = 12

    @classmethod
    def forecast_all(cls, top_n: int = 100) -> List[DemandForecast]:
        """Forecast demand for the most-borrowed books."""
        from apps.catalog.domain.models import Book

        books = Book.objects.order_by('-total_borrows')[:top_n]
        forecasts = []

        for book in books:
            forecast = cls._forecast_book(book)
            if forecast:
                forecasts.append(forecast)

        forecasts.sort(key=lambda f: f.forecasted_demand, reverse=True)
        return forecasts

    @classmethod
    def _forecast_book(cls, book) -> Optional[DemandForecast]:
        from apps.circulation.domain.models import BorrowRecord

        now = timezone.now()
        weekly_counts = []

        for week_offset in range(cls.WEEKS_HISTORY, 0, -1):
            start = now - timedelta(weeks=week_offset)
            end = now - timedelta(weeks=week_offset - 1)
            count = BorrowRecord.objects.filter(
                book_copy__book=book,
                created_at__gte=start,
                created_at__lt=end,
            ).count()
            weekly_counts.append(count)

        if not weekly_counts or sum(weekly_counts) == 0:
            return None

        # Holt's double exponential smoothing
        level = weekly_counts[0]
        trend = 0.0

        for obs in weekly_counts[1:]:
            new_level = cls.ALPHA * obs + (1 - cls.ALPHA) * (level + trend)
            new_trend = cls.BETA * (new_level - level) + (1 - cls.BETA) * trend
            level = new_level
            trend = new_trend

        forecasted = max(level + trend, 0)
        current = weekly_counts[-1] if weekly_counts else 0

        # Trend classification
        if trend > 0.5:
            trend_label = 'RISING'
        elif trend < -0.5:
            trend_label = 'DECLINING'
        else:
            trend_label = 'STABLE'

        # Recommended copies: forecasted demand * 1.5 ÷ avg turnover rate
        avg_borrow_days = settings.CIRCULATION_CONFIG.get(
            'DEFAULT_BORROW_DAYS', 14,
        )
        turns_per_week = 7.0 / avg_borrow_days
        recommended = max(
            int(math.ceil(forecasted / max(turns_per_week, 0.5) * 1.5)),
            1,
        )

        # Confidence based on data variance
        if len(weekly_counts) > 2:
            std = np.std(weekly_counts)
            mean = np.mean(weekly_counts)
            cv = std / max(mean, 0.01)  # coefficient of variation
            confidence = max(0.0, min(1.0, 1.0 - cv))
        else:
            confidence = 0.3

        return DemandForecast(
            book_id=str(book.id),
            title=book.title,
            current_weekly_demand=current,
            forecasted_demand=round(forecasted, 2),
            trend=trend_label,
            confidence=round(confidence, 3),
            recommended_copies=recommended,
        )


# ====================================================================
# 3. Churn Predictor
# ====================================================================

@dataclass
class ChurnPrediction:
    user_id: str
    email: str
    churn_probability: float
    risk_level: str
    days_since_last_activity: int
    activity_trend: str          # 'DECLINING', 'STAGNANT', 'ACTIVE'
    recommendations: List[str] = field(default_factory=list)


class ChurnPredictor:
    """
    Identifies users likely to disengage based on declining
    activity patterns over rolling windows.
    """

    @classmethod
    def predict_all(cls, min_days_registered: int = 30) -> List[ChurnPrediction]:
        """
        Analyse all users registered for at least `min_days_registered`
        days and predict churn risk.
        """
        from apps.identity.domain.models import User
        from apps.engagement.domain.models import UserEngagement, DailyActivity

        cutoff_date = timezone.now() - timedelta(days=min_days_registered)
        users = User.objects.filter(
            is_active=True,
            date_joined__lte=cutoff_date,
        ).select_related('engagement')

        predictions = []
        for user in users:
            pred = cls._predict_user(user)
            if pred:
                predictions.append(pred)

        predictions.sort(key=lambda p: p.churn_probability, reverse=True)
        return predictions

    @classmethod
    def _predict_user(cls, user) -> Optional[ChurnPrediction]:
        from apps.engagement.domain.models import DailyActivity

        now = timezone.now()
        today = now.date()

        # Get activity over last 8 weeks in 2-week windows
        windows = []
        for w in range(4):
            start = today - timedelta(weeks=(w + 1) * 2)
            end = today - timedelta(weeks=w * 2)
            activity = DailyActivity.objects.filter(
                user=user, date__gte=start, date__lt=end,
            ).aggregate(
                total_kp=Sum('kp_earned'),
                active_days=Count('id'),
            )
            windows.append({
                'kp': activity['total_kp'] or 0,
                'days': activity['active_days'] or 0,
            })

        # Recent window is index 0, oldest is index 3
        recent_kp = windows[0]['kp']
        recent_days = windows[0]['days']
        older_kp = sum(w['kp'] for w in windows[1:]) / 3 if len(windows) > 1 else 0

        # Days since last activity
        try:
            eng = user.engagement
            last_activity = eng.last_activity_date
            if last_activity:
                days_inactive = (today - last_activity).days
            else:
                days_inactive = (today - user.date_joined.date()).days
        except Exception:
            days_inactive = 30

        # Churn score components
        inactivity_score = min(days_inactive / 30.0, 1.0)

        activity_decline = 0.0
        if older_kp > 0:
            activity_decline = max(0.0, 1.0 - (recent_kp / older_kp))
        elif recent_kp == 0:
            activity_decline = 1.0

        frequency_score = max(0.0, 1.0 - (recent_days / 14.0))

        # Weighted combination
        churn_prob = (
            0.40 * inactivity_score
            + 0.35 * activity_decline
            + 0.25 * frequency_score
        )
        churn_prob = min(max(churn_prob, 0.0), 1.0)

        # Risk level
        if churn_prob >= 0.7:
            risk = 'HIGH'
        elif churn_prob >= 0.4:
            risk = 'MEDIUM'
        else:
            risk = 'LOW'

        # Activity trend
        if activity_decline > 0.5:
            trend = 'DECLINING'
        elif recent_kp == 0 and older_kp == 0:
            trend = 'STAGNANT'
        else:
            trend = 'ACTIVE'

        # Recommendations
        recs = []
        if days_inactive > 7:
            recs.append('Send re-engagement email with personalised picks')
        if activity_decline > 0.5:
            recs.append('Offer bonus KP for returning')
        if recent_days < 3:
            recs.append('Push notification with new arrivals in favourite genres')
        if risk == 'HIGH':
            recs.append('Personal outreach from librarian')

        return ChurnPrediction(
            user_id=str(user.id),
            email=user.email,
            churn_probability=round(churn_prob, 4),
            risk_level=risk,
            days_since_last_activity=days_inactive,
            activity_trend=trend,
            recommendations=recs,
        )


# ====================================================================
# 4. Collection Gap Analyzer
# ====================================================================

@dataclass
class CollectionGap:
    category_id: str
    category_name: str
    demand_score: float          # borrow_count / available_copies
    search_demand: int           # how often searched
    borrow_count: int
    available_copies: int
    waitlist_count: int
    gap_severity: str            # 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'
    suggested_acquisitions: int


class CollectionGapAnalyzer:
    """
    Identifies subject areas where borrowing demand and search
    interest exceed the library's collection capacity.
    """

    @classmethod
    def analyse(cls) -> List[CollectionGap]:
        from apps.catalog.domain.models import Category, Book
        from apps.circulation.domain.models import BorrowRecord, Reservation
        from apps.intelligence.domain.models import SearchLog

        now = timezone.now()
        period = now - timedelta(days=90)

        categories = Category.objects.all()
        gaps = []

        for cat in categories:
            books_in_cat = Book.objects.filter(
                categories=cat, deleted_at__isnull=True,
            )
            book_ids = list(books_in_cat.values_list('id', flat=True))

            if not book_ids:
                continue

            # Borrows in period
            borrow_count = BorrowRecord.objects.filter(
                book_copy__book_id__in=book_ids,
                created_at__gte=period,
            ).count()

            # Available copies
            available = books_in_cat.aggregate(
                total=Sum('available_copies'),
            )['total'] or 0

            # Active reservations (waitlist)
            waitlist = Reservation.objects.filter(
                book_id__in=book_ids,
                status__in=['PENDING', 'READY'],
            ).count()

            # Search demand (queries containing category name)
            search_demand = SearchLog.objects.filter(
                query_text__icontains=cat.name,
                timestamp__gte=period,
            ).count()

            # Demand score
            demand_score = borrow_count / max(available, 1)

            # Gap severity
            if demand_score > 5 or (waitlist > 10 and available < 3):
                severity = 'CRITICAL'
            elif demand_score > 3 or waitlist > 5:
                severity = 'HIGH'
            elif demand_score > 1.5:
                severity = 'MODERATE'
            else:
                severity = 'LOW'

            # Suggested acquisitions
            if severity == 'CRITICAL':
                suggested = max(int(demand_score * 2), waitlist)
            elif severity == 'HIGH':
                suggested = max(int(demand_score), waitlist // 2)
            elif severity == 'MODERATE':
                suggested = max(int(demand_score * 0.5), 1)
            else:
                suggested = 0

            gaps.append(CollectionGap(
                category_id=str(cat.id),
                category_name=cat.name,
                demand_score=round(demand_score, 2),
                search_demand=search_demand,
                borrow_count=borrow_count,
                available_copies=available,
                waitlist_count=waitlist,
                gap_severity=severity,
                suggested_acquisitions=suggested,
            ))

        gaps.sort(key=lambda g: g.demand_score, reverse=True)
        return gaps
