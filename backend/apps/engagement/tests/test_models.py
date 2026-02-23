"""
Tests for the Engagement bounded context
==========================================
Covers: UserEngagement KP system, streak logic, level-up, Achievements.
"""

import pytest
from datetime import date, timedelta

from django.utils import timezone

from apps.engagement.domain.models import (
    UserEngagement,
    Achievement,
    UserAchievement,
    DailyActivity,
)


# ─── UserEngagement ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserEngagement:

    def test_create_engagement(self, make_engagement):
        eng = make_engagement()
        assert eng.total_kp == 0
        assert eng.level == 1

    def test_award_kp(self, make_engagement):
        eng = make_engagement()
        awarded = eng.award_kp(50, dimension="SCHOLAR")
        eng.refresh_from_db()
        assert awarded == 50
        assert eng.total_kp == 50
        assert eng.scholar_kp == 50

    def test_award_kp_daily_cap(self, make_engagement):
        eng = make_engagement()
        # Award a large amount — should be capped
        awarded = eng.award_kp(500, dimension="EXPLORER")
        eng.refresh_from_db()
        # Daily cap is 200 by default
        assert awarded <= 200

    def test_deduct_kp(self, make_engagement):
        eng = make_engagement(total_kp=100, scholar_kp=100)
        deducted = eng.deduct_kp(30, dimension="SCHOLAR")
        eng.refresh_from_db()
        assert deducted == 30
        assert eng.total_kp == 70
        assert eng.scholar_kp == 70

    def test_deduct_kp_floor_zero(self, make_engagement):
        eng = make_engagement(total_kp=10)
        deducted = eng.deduct_kp(50)
        eng.refresh_from_db()
        assert eng.total_kp == 0
        assert deducted == 10

    def test_level_up(self, make_engagement):
        eng = make_engagement()
        # Level 2 at 100 KP
        eng.award_kp(150)
        eng.refresh_from_db()
        assert eng.level >= 2

    def test_update_streak_consecutive(self, make_engagement):
        eng = make_engagement()
        eng.last_activity_date = date.today() - timedelta(days=1)
        eng.current_streak = 5
        eng.save()
        eng.update_streak()
        eng.refresh_from_db()
        assert eng.current_streak == 6

    def test_update_streak_gap_resets(self, make_engagement):
        eng = make_engagement()
        eng.last_activity_date = date.today() - timedelta(days=3)
        eng.current_streak = 10
        eng.save()
        eng.update_streak()
        eng.refresh_from_db()
        assert eng.current_streak == 1

    def test_update_streak_same_day_noop(self, make_engagement):
        eng = make_engagement()
        eng.last_activity_date = date.today()
        eng.current_streak = 5
        eng.save()
        eng.update_streak()
        eng.refresh_from_db()
        assert eng.current_streak == 5  # unchanged

    def test_streak_multiplier(self, make_engagement):
        eng = make_engagement()
        eng.current_streak = 0
        assert eng.get_streak_multiplier() == 1.0

        eng.current_streak = 7
        mult = eng.get_streak_multiplier()
        assert mult >= 1.2

        eng.current_streak = 30
        mult = eng.get_streak_multiplier()
        assert mult >= 1.5

    def test_longest_streak_tracked(self, make_engagement):
        eng = make_engagement()
        eng.last_activity_date = date.today() - timedelta(days=1)
        eng.current_streak = 20
        eng.longest_streak = 15
        eng.save()
        eng.update_streak()
        eng.refresh_from_db()
        assert eng.longest_streak == 21


# ─── Achievement ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAchievement:

    def test_create_achievement(self):
        ach = Achievement.objects.create(
            code="TEST_ACH",
            name="Test Achievement",
            description="For testing.",
            category="MILESTONE",
            rarity="COMMON",
            kp_reward=10,
            criteria={},
        )
        assert str(ach) == "Test Achievement" or ach.name == "Test Achievement"

    def test_unique_code(self):
        Achievement.objects.create(
            code="UNIQUE_ACH", name="A", description="D",
            category="MILESTONE", rarity="COMMON", kp_reward=5, criteria={},
        )
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Achievement.objects.create(
                code="UNIQUE_ACH", name="B", description="D2",
                category="MILESTONE", rarity="RARE", kp_reward=10, criteria={},
            )


# ─── UserAchievement ────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserAchievement:

    def test_award_achievement(self, user):
        ach = Achievement.objects.create(
            code="FIRST_BORROW_TEST", name="First Borrow", description="Test",
            category="BORROWING", rarity="COMMON", kp_reward=10, criteria={},
        )
        ua = UserAchievement.objects.create(
            user=user, achievement=ach, kp_awarded=10,
        )
        assert ua.kp_awarded == 10
        assert ua.notified is False

    def test_unique_user_achievement(self, user):
        ach = Achievement.objects.create(
            code="DUP_TEST", name="Dup", description="T",
            category="MILESTONE", rarity="COMMON", kp_reward=5, criteria={},
        )
        UserAchievement.objects.create(user=user, achievement=ach, kp_awarded=5)
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            UserAchievement.objects.create(user=user, achievement=ach, kp_awarded=5)


# ─── DailyActivity ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestDailyActivity:

    def test_create_daily_activity(self, user):
        da = DailyActivity.objects.create(
            user=user,
            date=date.today(),
            kp_earned=25,
            books_borrowed=1,
            reading_minutes=45,
            pages_read=30,
        )
        assert da.kp_earned == 25
        assert da.books_borrowed == 1
