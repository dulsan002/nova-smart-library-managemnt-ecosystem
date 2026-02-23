"""
Auto-tag books using TF-IDF keyword extraction.

Usage:
    python manage.py auto_tag_books
    python manage.py auto_tag_books --max-tags 8
    python manage.py auto_tag_books --retag-all
"""

import time

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Auto-tag books using NLP-based keyword extraction.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-tags',
            type=int,
            default=5,
            help='Maximum tags per book (default: 5).',
        )
        parser.add_argument(
            '--retag-all',
            action='store_true',
            help='Re-tag all books, including those already tagged.',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of books per batch (default: 100).',
        )

    def handle(self, *args, **options):
        from apps.catalog.domain.models import Book
        from apps.intelligence.infrastructure.content_analysis import AutoTagger

        max_tags = options['max_tags']
        retag = options['retag_all']
        batch_size = options['batch_size']

        qs = Book.objects.filter(deleted_at__isnull=True)
        if not retag:
            qs = qs.filter(tags=[])

        total = qs.count()
        self.stdout.write(f'Books to tag: {total} (max_tags={max_tags})')

        start = time.monotonic()
        processed = 0
        failed = 0

        for book in qs.iterator(chunk_size=batch_size):
            try:
                tags = AutoTagger.auto_tag_book(book, top_n=max_tags)
                processed += 1
                if processed % 50 == 0:
                    self.stdout.write(f'  Processed: {processed}/{total}')
            except Exception as exc:
                failed += 1
                self.stderr.write(
                    self.style.ERROR(f'  Failed to tag {book.id}: {exc}'),
                )

        elapsed = time.monotonic() - start
        self.stdout.write(self.style.SUCCESS(
            f'Auto-tagging complete.\n'
            f'  Processed: {processed}\n'
            f'  Failed: {failed}\n'
            f'  Time: {elapsed:.1f}s',
        ))
