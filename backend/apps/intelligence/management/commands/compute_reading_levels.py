"""
Compute reading levels for books in the catalog.

Usage:
    python manage.py compute_reading_levels
    python manage.py compute_reading_levels --recompute-all
"""

import time

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Estimate reading difficulty levels for books.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recompute-all',
            action='store_true',
            help='Recompute for all books, not just those without a level.',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Books per batch (default: 100).',
        )

    def handle(self, *args, **options):
        from apps.catalog.domain.models import Book
        from apps.intelligence.infrastructure.content_analysis import (
            ReadingLevelEstimator,
        )

        recompute = options['recompute_all']
        batch_size = options['batch_size']

        qs = Book.objects.filter(deleted_at__isnull=True)
        if not recompute:
            qs = qs.filter(reading_level='')

        total = qs.count()
        self.stdout.write(f'Books to process: {total}')

        start = time.monotonic()
        levels = {'ELEMENTARY': 0, 'INTERMEDIATE': 0, 'ADVANCED': 0, 'ACADEMIC': 0}
        processed = 0
        failed = 0

        for book in qs.iterator(chunk_size=batch_size):
            try:
                text = f'{book.title} {book.subtitle or ""} {book.description or ""}'
                result = ReadingLevelEstimator.estimate(text)
                book.reading_level = result.level
                book.save(update_fields=['reading_level', 'updated_at'])
                levels[result.level] = levels.get(result.level, 0) + 1
                processed += 1
            except Exception as exc:
                failed += 1
                self.stderr.write(
                    self.style.ERROR(f'  Failed for {book.id}: {exc}'),
                )

        elapsed = time.monotonic() - start
        self.stdout.write(self.style.SUCCESS(
            f'Reading level estimation complete.\n'
            f'  Processed: {processed}, Failed: {failed}\n'
            f'  Distribution: {levels}\n'
            f'  Time: {elapsed:.1f}s',
        ))
