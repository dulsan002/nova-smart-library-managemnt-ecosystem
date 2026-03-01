"""
Nova — Reading Behaviour Analyzer
=====================================
Analyses reading session data to derive:
  1. Reading speed (WPM) and speed category inference
  2. Session pattern analysis (time-of-day, day-of-week, duration)
  3. Engagement heatmap (daily / hourly activity grids)
  4. Completion probability prediction
  5. Optimal session length recommendations
"""

import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from django.conf import settings
from django.db.models import Avg, Count, F, Sum
from django.utils import timezone

logger = logging.getLogger('nova.intelligence.behaviour')


# ====================================================================
# 1. Reading Speed Analyzer
# ====================================================================

@dataclass
class ReadingSpeedProfile:
    user_id: str
    avg_wpm: float
    median_wpm: float
    speed_category: str       # 'SLOW', 'AVERAGE', 'FAST', 'SPEED_READER'
    total_sessions_analysed: int
    confidence: float         # 0.0–1.0 based on sample size
    estimated_finish_times: Dict[str, float] = field(default_factory=dict)

    # Aliases expected by the GraphQL schema resolver
    @property
    def words_per_minute(self) -> float:
        return self.avg_wpm

    @property
    def category(self) -> str:
        return self.speed_category

    @property
    def sessions_analyzed(self) -> int:
        return self.total_sessions_analysed


class ReadingSpeedAnalyzer:
    """
    Infers reading speed from reading session data by correlating
    pages read with session duration.
    """

    SPEED_CATEGORIES = {
        'SLOW': (0, 150),
        'AVERAGE': (150, 250),
        'FAST': (250, 400),
        'SPEED_READER': (400, float('inf')),
    }

    # Average words per page for estimation
    AVG_WORDS_PER_PAGE = 250

    @classmethod
    def analyse(cls, user_id) -> ReadingSpeedProfile:
        """
        Calculate reading speed from completed reading sessions.
        """
        from apps.digital_content.domain.models import ReadingSession

        sessions = ReadingSession.objects.filter(
            user_id=user_id if not hasattr(user_id, 'id') else user_id.id,
            session_type='READING',
            status__in=['COMPLETED', 'PAUSED'],
            duration_seconds__gt=120,  # At least 2 minutes
        ).values(
            'duration_seconds', 'progress_percent',
        )

        wpm_samples = []
        for sess in sessions:
            dur = sess.get('duration_seconds') or 0
            progress = float(sess.get('progress_percent') or 0)

            # Estimate pages from progress percentage (assume 300-page book)
            pages = progress / 100.0 * 300 if progress > 0 else 0

            if pages > 0 and dur >= 120:
                words = pages * cls.AVG_WORDS_PER_PAGE
                minutes = dur / 60.0
                wpm = words / minutes
                if 50 < wpm < 1000:  # Sanity bounds
                    wpm_samples.append(wpm)

        if not wpm_samples:
            return ReadingSpeedProfile(
                user_id=str(user_id),
                avg_wpm=0,
                median_wpm=0,
                speed_category='UNKNOWN',
                total_sessions_analysed=0,
                confidence=0.0,
            )

        avg_wpm = np.mean(wpm_samples)
        median_wpm = np.median(wpm_samples)

        # Categorise
        category = 'AVERAGE'
        for cat, (low, high) in cls.SPEED_CATEGORIES.items():
            if low <= avg_wpm < high:
                category = cat
                break

        # Confidence based on sample size (asymptotic)
        confidence = min(len(wpm_samples) / 20.0, 1.0)

        # Estimated finish times for standard book lengths
        finish_estimates = {}
        for label, pages in [('short', 150), ('medium', 300), ('long', 500)]:
            words = pages * cls.AVG_WORDS_PER_PAGE
            minutes = words / max(avg_wpm, 1)
            finish_estimates[label] = round(minutes / 60.0, 1)  # hours

        # Persist speed category to user preferences
        cls._persist_speed(user_id, category)

        return ReadingSpeedProfile(
            user_id=str(user_id),
            avg_wpm=round(avg_wpm, 1),
            median_wpm=round(median_wpm, 1),
            speed_category=category,
            total_sessions_analysed=len(wpm_samples),
            confidence=round(confidence, 3),
            estimated_finish_times=finish_estimates,
        )

    @classmethod
    def analyze(cls, user_id) -> ReadingSpeedProfile:
        """Alias for analyse() — used by GraphQL resolver."""
        return cls.analyse(user_id)

    @staticmethod
    def _persist_speed(user_id, category: str):
        from apps.intelligence.domain.models import UserPreference
        try:
            pref, _ = UserPreference.objects.get_or_create(user_id=user_id)
            pref.reading_speed = category.lower()
            pref.save(update_fields=['reading_speed', 'updated_at'])
        except Exception as exc:
            logger.warning('Failed to persist reading speed: %s', exc)


# ====================================================================
# 2. Session Pattern Analyzer
# ====================================================================

@dataclass
class SessionPattern:
    user_id: str
    peak_hour: int               # 0–23
    peak_day: int                # 0=Monday, 6=Sunday
    avg_session_minutes: float
    median_session_minutes: float
    preferred_time_label: str    # 'MORNING', 'AFTERNOON', 'EVENING', 'NIGHT'
    sessions_per_week: float
    total_sessions: int
    hourly_distribution: Dict[int, int]    # hour → session count
    daily_distribution: Dict[int, int]     # weekday → session count

    # Alias expected by the GraphQL schema resolver
    @property
    def preferred_time(self) -> str:
        return self.preferred_time_label


class SessionPatternAnalyzer:
    """
    Analyses when and how long a user reads to understand their
    reading habits.
    """

    TIME_LABELS = {
        (5, 12): 'MORNING',
        (12, 17): 'AFTERNOON',
        (17, 21): 'EVENING',
        (21, 5): 'NIGHT',
    }

    @classmethod
    def analyse(cls, user_id) -> SessionPattern:
        from apps.digital_content.domain.models import ReadingSession

        uid = user_id if not hasattr(user_id, 'id') else user_id.id
        sessions = list(
            ReadingSession.objects.filter(
                user_id=uid,
                duration_seconds__gt=60,
            ).values('started_at', 'duration_seconds')
        )

        if not sessions:
            return SessionPattern(
                user_id=str(user_id),
                peak_hour=0, peak_day=0,
                avg_session_minutes=0,
                median_session_minutes=0,
                preferred_time_label='UNKNOWN',
                sessions_per_week=0,
                total_sessions=0,
                hourly_distribution={},
                daily_distribution={},
            )

        hours = Counter()
        days = Counter()
        durations = []

        for s in sessions:
            started = s['started_at']
            hours[started.hour] += 1
            days[started.weekday()] += 1
            durations.append(s['duration_seconds'] / 60.0)

        peak_hour = hours.most_common(1)[0][0]
        peak_day = days.most_common(1)[0][0]

        avg_mins = np.mean(durations)
        median_mins = np.median(durations)

        # Time label
        time_label = 'EVENING'  # default
        for (start_h, end_h), label in cls.TIME_LABELS.items():
            if start_h <= peak_hour < end_h:
                time_label = label
                break

        # Sessions per week
        if sessions:
            first_session = min(s['started_at'] for s in sessions)
            weeks_active = max(
                (timezone.now() - first_session).days / 7.0, 1.0,
            )
            sessions_per_week = len(sessions) / weeks_active
        else:
            sessions_per_week = 0

        return SessionPattern(
            user_id=str(user_id),
            peak_hour=peak_hour,
            peak_day=peak_day,
            avg_session_minutes=round(avg_mins, 1),
            median_session_minutes=round(median_mins, 1),
            preferred_time_label=time_label,
            sessions_per_week=round(sessions_per_week, 2),
            total_sessions=len(sessions),
            hourly_distribution=dict(hours),
            daily_distribution=dict(days),
        )

    @classmethod
    def analyze(cls, user_id) -> SessionPattern:
        """Alias for analyse() — used by GraphQL resolver."""
        return cls.analyse(user_id)


# ====================================================================
# 3. Engagement Heatmap Generator
# ====================================================================

@dataclass
class EngagementHeatmap:
    user_id: str
    grid: List[List[int]]  # 7 rows (days) × 24 cols (hours)
    total_minutes: float
    most_active_slot: Tuple[int, int]  # (day, hour)

    DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # Aliases expected by the GraphQL schema resolver
    @property
    def heatmap(self) -> List[List[int]]:
        return self.grid

    @property
    def days(self) -> List[str]:
        return self.DAY_NAMES

    @property
    def hours(self) -> List[int]:
        # Aggregate session counts per hour (sum across all days)
        return [sum(self.grid[d][h] for d in range(7)) for h in range(24)]


class EngagementHeatmapGenerator:
    """
    Generates a 7×24 heatmap grid showing reading minutes by
    day-of-week and hour-of-day.
    """

    @classmethod
    def generate(cls, user_id, days: int = 90) -> EngagementHeatmap:
        from apps.digital_content.domain.models import ReadingSession

        uid = user_id if not hasattr(user_id, 'id') else user_id.id
        cutoff = timezone.now() - timedelta(days=days)
        sessions = ReadingSession.objects.filter(
            user_id=uid,
            started_at__gte=cutoff,
        ).values('started_at', 'duration_seconds')

        grid = [[0] * 24 for _ in range(7)]
        total_minutes = 0.0

        for s in sessions:
            started = s['started_at']
            duration_mins = (s['duration_seconds'] or 0) / 60.0
            day = started.weekday()
            hour = started.hour
            grid[day][hour] += int(duration_mins)
            total_minutes += duration_mins

        # Find peak
        max_val = 0
        max_slot = (0, 0)
        for d in range(7):
            for h in range(24):
                if grid[d][h] > max_val:
                    max_val = grid[d][h]
                    max_slot = (d, h)

        return EngagementHeatmap(
            user_id=str(user_id),
            grid=grid,
            total_minutes=round(total_minutes, 1),
            most_active_slot=max_slot,
        )


# ====================================================================
# 4. Completion Probability Predictor
# ====================================================================

@dataclass
class CompletionPrediction:
    user_id: str
    asset_id: str
    current_progress: float
    predicted_completion_probability: float
    estimated_days_to_finish: Optional[float]
    factors: List[str] = field(default_factory=list)

    # Aliases expected by the GraphQL schema resolver
    @property
    def completion_probability(self) -> float:
        return self.predicted_completion_probability

    @property
    def estimated_days(self) -> Optional[float]:
        return self.estimated_days_to_finish


class CompletionPredictor:
    """
    Predicts the probability that a user will finish a specific
    digital asset based on their reading patterns and historical
    completion rate.
    """

    @classmethod
    def predict(cls, user_id, asset_id) -> CompletionPrediction:
        from apps.digital_content.domain.models import UserLibrary, ReadingSession

        uid = user_id if not hasattr(user_id, 'id') else user_id.id

        try:
            lib = UserLibrary.objects.get(
                user_id=uid, digital_asset_id=asset_id,
            )
        except UserLibrary.DoesNotExist:
            return CompletionPrediction(
                user_id=str(uid),
                asset_id=str(asset_id),
                current_progress=0,
                predicted_completion_probability=0,
                estimated_days_to_finish=None,
            )

        progress = lib.overall_progress or 0
        factors = []

        # Factor 1: Current progress (strongest predictor)
        progress_factor = progress / 100.0
        if progress > 70:
            factors.append(f'Already {progress:.0f}% complete')

        # Factor 2: Historical completion rate
        total_assets = UserLibrary.objects.filter(user_id=uid).count()
        completed_assets = UserLibrary.objects.filter(
            user_id=uid, is_finished=True,
        ).count()
        completion_rate = completed_assets / max(total_assets, 1)
        if completion_rate > 0.6:
            factors.append(f'High completion rate ({completion_rate:.0%})')
        elif completion_rate < 0.3:
            factors.append(f'Low completion rate ({completion_rate:.0%})')

        # Factor 3: Reading consistency
        recent_sessions = ReadingSession.objects.filter(
            user_id=uid,
            digital_asset_id=asset_id,
            started_at__gte=timezone.now() - timedelta(days=14),
        ).count()
        consistency = min(recent_sessions / 5.0, 1.0)
        if recent_sessions > 3:
            factors.append('Active reading in last 2 weeks')
        elif recent_sessions == 0:
            factors.append('No reading activity in 2 weeks')

        # Factor 4: Time since last session
        last_session = (
            ReadingSession.objects
            .filter(user_id=uid, digital_asset_id=asset_id)
            .order_by('-started_at')
            .first()
        )
        recency = 1.0
        if last_session:
            days_since = (timezone.now() - last_session.started_at).days
            recency = max(0.0, 1.0 - (days_since / 30.0))
            if days_since > 14:
                factors.append(f'{days_since} days since last session')

        # Weighted probability
        probability = (
            0.40 * progress_factor
            + 0.25 * completion_rate
            + 0.20 * consistency
            + 0.15 * recency
        )
        probability = min(max(probability, 0.0), 1.0)

        # Estimated days to finish
        est_days = None
        if progress > 0 and last_session:
            # Calculate reading velocity (progress per day)
            first_session = (
                ReadingSession.objects
                .filter(user_id=uid, digital_asset_id=asset_id)
                .order_by('started_at')
                .first()
            )
            if first_session:
                total_days = max(
                    (timezone.now() - first_session.started_at).days, 1,
                )
                velocity = progress / total_days  # % per day
                remaining = 100 - progress
                if velocity > 0:
                    est_days = round(remaining / velocity, 1)

        return CompletionPrediction(
            user_id=str(uid),
            asset_id=str(asset_id),
            current_progress=progress,
            predicted_completion_probability=round(probability, 4),
            estimated_days_to_finish=est_days,
            factors=factors,
        )


# ====================================================================
# 5. Optimal Session Recommender
# ====================================================================

class SessionRecommender:
    """
    Recommends optimal reading session length and time based on
    the user's productivity patterns.
    """

    @classmethod
    def recommend(cls, user_id) -> Dict:
        from apps.digital_content.domain.models import ReadingSession
        from apps.engagement.domain.models import DailyActivity

        sessions = list(
            ReadingSession.objects.filter(
                user_id=user_id,
                status='COMPLETED',
                duration_seconds__gt=300,  # At least 5 minutes
            ).values('started_at', 'duration_seconds', 'progress_percent')
        )

        if len(sessions) < 5:
            return {
                'optimal_duration_minutes': 30,
                'optimal_time': 'evening',
                'recommended_frequency': 'daily',
                'reasoning': 'Not enough data yet. Start with 30-minute sessions.',
            }

        # Find sessions with highest productivity (progress per minute)
        productivity = []
        for s in sessions:
            progress = float(s.get('progress_percent') or 0)
            mins = s['duration_seconds'] / 60.0
            hour = s['started_at'].hour
            if progress > 0 and mins > 5:
                productivity.append({
                    'ppm': progress / mins,
                    'duration': mins,
                    'hour': hour,
                })

        if not productivity:
            return {
                'optimal_duration_minutes': 30,
                'optimal_time': 'evening',
                'recommended_frequency': 'daily',
                'reasoning': 'Track reading progress for better recommendations.',
            }

        # Sort by productivity and find sweet spots
        productivity.sort(key=lambda x: x['ppm'], reverse=True)
        top_sessions = productivity[:len(productivity) // 3 + 1]

        optimal_duration = round(np.median([s['duration'] for s in top_sessions]))
        optimal_hour = round(np.median([s['hour'] for s in top_sessions]))

        # Time label
        if 5 <= optimal_hour < 12:
            time_label = 'morning'
        elif 12 <= optimal_hour < 17:
            time_label = 'afternoon'
        elif 17 <= optimal_hour < 21:
            time_label = 'evening'
        else:
            time_label = 'night'

        # Frequency based on current pattern
        pattern_analyzer = SessionPatternAnalyzer()
        pattern = pattern_analyzer.analyse(user_id)
        if pattern.sessions_per_week >= 5:
            frequency = 'daily'
        elif pattern.sessions_per_week >= 3:
            frequency = '4-5 times per week'
        else:
            frequency = '3 times per week'

        return {
            'optimal_duration_minutes': optimal_duration,
            'optimal_time': time_label,
            'optimal_hour': optimal_hour,
            'recommended_frequency': frequency,
            'reasoning': (
                f'Your most productive sessions are ~{optimal_duration} minutes '
                f'during the {time_label}. Aim for {frequency} to maintain your streak.'
            ),
        }
