"""
Refresh trending books analysis.

Usage:
    python manage.py refresh_trending
    python manage.py refresh_trending --days 7 --top 20
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Recompute trending books based on recent activity.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Lookback window in days (default: 7).',
        )
        parser.add_argument(
            '--top',
            type=int,
            default=20,
            help='Number of top trending books to keep (default: 20).',
        )

    def handle(self, *args, **options):
        from datetime import timedelta

        from django.db.models import Count, Q
        from django.utils import timezone

        from apps.catalog.domain.models import Book
        from apps.circulation.domain.models import BorrowRecord
        from apps.intelligence.domain.models import TrendingBook

        days = options['days']
        top = options['top']
        cutoff = timezone.now() - timedelta(days=days)

        self.stdout.write(f'Computing trending books (last {days} days, top {top})…')

        # Score = recent borrows + 2 × recent reservations + 0.5 × recent reviews
        book_scores = {}

        # Recent borrows
        borrows = (
            BorrowRecord.objects
            .filter(created_at__gte=cutoff)
            .values('book_copy__book_id')
            .annotate(cnt=Count('id'))
        )
        for entry in borrows:
            bid = entry['book_copy__book_id']
            book_scores[bid] = book_scores.get(bid, 0) + entry['cnt']

        # Recent reservations
        from apps.circulation.domain.models import Reservation
        reservations = (
            Reservation.objects
            .filter(created_at__gte=cutoff)
            .values('book_id')
            .annotate(cnt=Count('id'))
        )
        for entry in reservations:
            bid = entry['book_id']
            book_scores[bid] = book_scores.get(bid, 0) + entry['cnt'] * 2

        # Recent reviews
        from apps.catalog.domain.models import BookReview
        reviews = (
            BookReview.objects
            .filter(created_at__gte=cutoff)
            .values('book_id')
            .annotate(cnt=Count('id'))
        )
        for entry in reviews:
            bid = entry['book_id']
            book_scores[bid] = book_scores.get(bid, 0) + entry['cnt'] * 0.5

        # Sort and take top-N
        sorted_books = sorted(
            book_scores.items(), key=lambda x: x[1], reverse=True,
        )[:top]

        # Clear old trending entries and create new
        TrendingBook.objects.all().delete()

        for rank, (book_id, score) in enumerate(sorted_books, 1):
            try:
                book = Book.objects.get(id=book_id)
                TrendingBook.objects.create(
                    book=book,
                    score=score,
                    rank=rank,
                    period_days=days,
                )
            except Book.DoesNotExist:
                continue

        self.stdout.write(self.style.SUCCESS(
            f'Trending refresh complete.\n'
            f'  Books scored: {len(book_scores)}\n'
            f'  Top trending: {len(sorted_books)}\n'
            f'  Period: {days} days',
        ))
