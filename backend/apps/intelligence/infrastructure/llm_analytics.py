"""
Nova — LLM-Powered Library Analytics
=======================================
Gathers real library data from the database and sends it to the
configured LLM provider for intelligent analysis and predictions.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import timedelta
from dataclasses import dataclass, field
from typing import Any

from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone

logger = logging.getLogger('nova.intelligence.llm_analytics')


@dataclass
class LLMAnalyticsResult:
    """Result from an LLM analytics run."""
    summary: str = ''
    overdue_insights: str = ''
    demand_insights: str = ''
    user_insights: str = ''
    collection_insights: str = ''
    recommendations: list[str] = field(default_factory=list)
    model_used: str = ''
    error: str = ''


class LibraryDataCollector:
    """Gathers real library data for LLM analysis."""

    @staticmethod
    def collect() -> dict[str, Any]:
        """
        Collect comprehensive library statistics from the database.
        Returns a dict suitable for inclusion in an LLM prompt.
        """
        now = timezone.now()
        data: dict[str, Any] = {}

        try:
            data['collection'] = LibraryDataCollector._collection_stats()
        except Exception as e:
            logger.warning('Failed to collect collection stats: %s', e)
            data['collection'] = {'error': str(e)}

        try:
            data['circulation'] = LibraryDataCollector._circulation_stats(now)
        except Exception as e:
            logger.warning('Failed to collect circulation stats: %s', e)
            data['circulation'] = {'error': str(e)}

        try:
            data['users'] = LibraryDataCollector._user_stats(now)
        except Exception as e:
            logger.warning('Failed to collect user stats: %s', e)
            data['users'] = {'error': str(e)}

        try:
            data['fines'] = LibraryDataCollector._fine_stats()
        except Exception as e:
            logger.warning('Failed to collect fine stats: %s', e)
            data['fines'] = {'error': str(e)}

        try:
            data['reservations'] = LibraryDataCollector._reservation_stats()
        except Exception as e:
            logger.warning('Failed to collect reservation stats: %s', e)
            data['reservations'] = {'error': str(e)}

        try:
            data['trends'] = LibraryDataCollector._trend_stats(now)
        except Exception as e:
            logger.warning('Failed to collect trend stats: %s', e)
            data['trends'] = {'error': str(e)}

        try:
            data['categories'] = LibraryDataCollector._category_stats()
        except Exception as e:
            logger.warning('Failed to collect category stats: %s', e)
            data['categories'] = {'error': str(e)}

        return data

    @staticmethod
    def _collection_stats() -> dict:
        from apps.catalog.domain.models import Book, BookCopy

        total_books = Book.objects.count()
        total_copies = BookCopy.objects.count()
        available_copies = BookCopy.objects.filter(status='AVAILABLE').count()
        damaged_copies = BookCopy.objects.filter(
            status__in=['DAMAGED', 'LOST']
        ).count()

        return {
            'total_titles': total_books,
            'total_copies': total_copies,
            'available_copies': available_copies,
            'checked_out_copies': total_copies - available_copies - damaged_copies,
            'damaged_or_lost': damaged_copies,
            'availability_rate': round(
                available_copies / max(total_copies, 1) * 100, 1
            ),
        }

    @staticmethod
    def _circulation_stats(now) -> dict:
        from apps.circulation.domain.models import BorrowRecord

        active = BorrowRecord.objects.filter(status='ACTIVE')
        overdue = BorrowRecord.objects.filter(status='OVERDUE')
        returned_last_30 = BorrowRecord.objects.filter(
            status='RETURNED',
            returned_at__gte=now - timedelta(days=30),
        )

        active_count = active.count()
        overdue_count = overdue.count()
        returned_30d = returned_last_30.count()

        # Top 10 most borrowed books (by borrow count)
        top_books = (
            BorrowRecord.objects
            .values(title=F('book_copy__book__title'))
            .annotate(borrow_count=Count('id'))
            .order_by('-borrow_count')[:10]
        )

        # Overdue details
        overdue_details = list(
            overdue.values(
                title=F('book_copy__book__title'),
                borrower=F('user__email'),
            ).annotate(
                days_overdue=Count('id'),  # placeholder
            )[:10]
        )

        # Compute actual days overdue
        for record in overdue[:10]:
            for d in overdue_details:
                if d['borrower'] == record.user.email:
                    d['days_overdue'] = (now - record.due_date).days
                    break

        return {
            'active_borrows': active_count,
            'overdue_borrows': overdue_count,
            'returned_last_30_days': returned_30d,
            'overdue_rate': round(
                overdue_count / max(active_count + overdue_count, 1) * 100, 1
            ),
            'top_borrowed_books': [
                {'title': b['title'], 'borrows': b['borrow_count']}
                for b in top_books
            ],
            'overdue_books': [
                {
                    'title': d['title'],
                    'borrower': d['borrower'],
                    'days_overdue': d.get('days_overdue', 0),
                }
                for d in overdue_details
            ],
        }

    @staticmethod
    def _user_stats(now) -> dict:
        from apps.identity.domain.models import User

        total_users = User.objects.filter(is_active=True).count()
        new_users_30d = User.objects.filter(
            created_at__gte=now - timedelta(days=30),
        ).count()

        # Users with borrows in last 30 days
        from apps.circulation.domain.models import BorrowRecord
        active_borrowers = (
            BorrowRecord.objects
            .filter(borrowed_at__gte=now - timedelta(days=30))
            .values('user')
            .distinct()
            .count()
        )

        # Users with no borrows in last 90 days but who have borrowed before
        inactive_users = (
            User.objects.filter(
                is_active=True,
                borrow_records__isnull=False,
            )
            .exclude(
                borrow_records__borrowed_at__gte=now - timedelta(days=90)
            )
            .distinct()
            .count()
        )

        return {
            'total_active_users': total_users,
            'new_users_last_30_days': new_users_30d,
            'active_borrowers_last_30_days': active_borrowers,
            'inactive_users_90_days': inactive_users,
            'engagement_rate': round(
                active_borrowers / max(total_users, 1) * 100, 1
            ),
        }

    @staticmethod
    def _fine_stats() -> dict:
        from apps.circulation.domain.models import Fine

        pending = Fine.objects.filter(status='PENDING')
        paid = Fine.objects.filter(status='PAID')
        waived = Fine.objects.filter(status='WAIVED')

        pending_amount = pending.aggregate(
            total=Sum('amount')
        )['total'] or 0
        paid_amount = paid.aggregate(
            total=Sum('amount')
        )['total'] or 0

        return {
            'pending_fines': pending.count(),
            'pending_amount': float(pending_amount),
            'paid_fines': paid.count(),
            'paid_amount': float(paid_amount),
            'waived_fines': waived.count(),
        }

    @staticmethod
    def _reservation_stats() -> dict:
        from apps.circulation.domain.models import Reservation

        pending = Reservation.objects.filter(status='PENDING').count()
        ready = Reservation.objects.filter(status='READY').count()
        fulfilled = Reservation.objects.filter(status='FULFILLED').count()
        cancelled = Reservation.objects.filter(status='CANCELLED').count()
        expired = Reservation.objects.filter(status='EXPIRED').count()

        # Most reserved books
        top_reserved = (
            Reservation.objects
            .values(title=F('book__title'))
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        return {
            'pending': pending,
            'ready_for_pickup': ready,
            'fulfilled': fulfilled,
            'cancelled': cancelled,
            'expired': expired,
            'top_reserved_books': [
                {'title': r['title'], 'reservations': r['count']}
                for r in top_reserved
            ],
        }

    @staticmethod
    def _trend_stats(now) -> dict:
        from apps.circulation.domain.models import BorrowRecord

        # Weekly borrow counts for last 8 weeks
        weekly_borrows = []
        for i in range(8):
            week_start = now - timedelta(weeks=i + 1)
            week_end = now - timedelta(weeks=i)
            count = BorrowRecord.objects.filter(
                borrowed_at__gte=week_start,
                borrowed_at__lt=week_end,
            ).count()
            weekly_borrows.append({
                'week': f'{i + 1} weeks ago',
                'borrows': count,
            })

        weekly_borrows.reverse()  # oldest first

        return {
            'weekly_borrows_last_8_weeks': weekly_borrows,
        }

    @staticmethod
    def _category_stats() -> dict:
        from apps.catalog.domain.models import Book

        # Books per category
        cat_counts = (
            Book.objects
            .values(category=F('categories__name'))
            .annotate(count=Count('id'))
            .order_by('-count')[:15]
        )

        return {
            'books_per_category': [
                {'category': c['category'] or 'Uncategorized', 'count': c['count']}
                for c in cat_counts
            ],
        }


SYSTEM_PROMPT = """You are an expert library analytics AI assistant for the Nova Smart Library Management System. 
You analyze real library operational data and provide actionable insights.

IMPORTANT: You must respond with ONLY valid JSON (no markdown, no code fences, no extra text). 
The JSON must follow this exact structure:
{
  "summary": "A 2-3 sentence executive summary of the library's current state",
  "overdue_insights": "Analysis of overdue patterns, risk factors, and predictions for upcoming overdues",
  "demand_insights": "Analysis of borrowing demand trends, popular books, and demand forecasting",
  "user_insights": "Analysis of user engagement, churn risk, and user behavior patterns",
  "collection_insights": "Analysis of collection gaps, category coverage, and acquisition recommendations",
  "recommendations": ["Actionable recommendation 1", "Actionable recommendation 2", "...(provide 5-8 specific recommendations)"]
}

Rules:
- Base all analysis strictly on the provided data
- Be specific — reference actual numbers, book titles, and percentages
- Provide forward-looking predictions where the data supports it
- Keep each insight section to 2-4 sentences
- Recommendations should be concrete and actionable
- If data is insufficient for a section, say so honestly"""


def generate_llm_analytics() -> LLMAnalyticsResult:
    """
    Collect library data and send to the configured LLM for analysis.
    Returns a structured LLMAnalyticsResult.
    """
    from apps.intelligence.infrastructure.ai_providers.factory import (
        get_chat_provider,
    )

    # 1. Get the active CHAT provider
    provider = get_chat_provider()
    if not provider:
        return LLMAnalyticsResult(
            error='No active CHAT AI provider configured. '
                  'Please configure one in AI Config settings.'
        )

    # 2. Collect library data
    try:
        data = LibraryDataCollector.collect()
    except Exception as e:
        logger.exception('Failed to collect library data')
        return LLMAnalyticsResult(error=f'Failed to collect library data: {e}')

    # 3. Build prompt
    prompt = (
        "Analyze the following real-time library operational data and provide "
        "comprehensive analytics insights.\n\n"
        f"LIBRARY DATA:\n{json.dumps(data, indent=2, default=str)}"
    )

    # 4. Send to LLM
    try:
        response = provider.generate(
            prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3,  # Low temperature for factual analysis
            max_tokens=2000,
        )
    except Exception as e:
        logger.exception('LLM generation failed')
        return LLMAnalyticsResult(
            error=f'LLM generation failed: {e}',
            model_used=getattr(provider, 'model_name', ''),
        )

    # 5. Parse the response
    raw_text = response.text.strip()
    model_used = response.model or getattr(provider, 'model_name', '')

    try:
        # Try to extract JSON from the response
        # Handle cases where LLM wraps response in markdown code fences
        if raw_text.startswith('```'):
            # Remove code fences
            lines = raw_text.split('\n')
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith('```') and not in_block:
                    in_block = True
                    continue
                elif line.strip().startswith('```') and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            raw_text = '\n'.join(json_lines)

        parsed = json.loads(raw_text)

        return LLMAnalyticsResult(
            summary=parsed.get('summary', ''),
            overdue_insights=parsed.get('overdue_insights', ''),
            demand_insights=parsed.get('demand_insights', ''),
            user_insights=parsed.get('user_insights', ''),
            collection_insights=parsed.get('collection_insights', ''),
            recommendations=parsed.get('recommendations', []),
            model_used=model_used,
        )
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(
            'LLM response was not valid JSON, returning raw text: %s', e,
        )
        # Fall back: use the raw text as the summary
        return LLMAnalyticsResult(
            summary=raw_text,
            model_used=model_used,
        )
