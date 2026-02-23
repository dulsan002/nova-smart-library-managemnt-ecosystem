"""
Batch-compute book embeddings.

Usage:
    python manage.py compute_embeddings
    python manage.py compute_embeddings --batch-size 500
    python manage.py compute_embeddings --recompute-all
"""

import time

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Compute or recompute book embeddings using the configured model.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=200,
            help='Number of books to process per batch (default: 200).',
        )
        parser.add_argument(
            '--recompute-all',
            action='store_true',
            help='Recompute embeddings for all books, not just missing ones.',
        )

    def handle(self, *args, **options):
        from apps.catalog.domain.models import Book
        from apps.intelligence.infrastructure.training_pipeline import (
            EmbeddingPipeline,
        )

        batch_size = options['batch_size']
        recompute = options['recompute_all']

        if recompute:
            self.stdout.write('Clearing existing embeddings…')
            Book.objects.filter(
                deleted_at__isnull=True,
            ).update(embedding_vector=None)
            self.stdout.write(self.style.WARNING('All embeddings cleared.'))

        total_missing = Book.objects.filter(
            embedding_vector__isnull=True,
            deleted_at__isnull=True,
        ).count()

        self.stdout.write(
            f'Books needing embeddings: {total_missing} (batch size: {batch_size})',
        )

        start = time.monotonic()
        processed = 0

        while True:
            result = EmbeddingPipeline.compute_all_embeddings(
                batch_size=batch_size,
            )
            metrics = result.get('metrics', {})
            computed = metrics.get('books_embedded', 0)
            failed = metrics.get('books_failed', 0)

            if computed == 0:
                break

            processed += computed
            self.stdout.write(
                f'  Computed: {computed}, Failed: {failed}, '
                f'Running total: {processed}',
            )

        elapsed = time.monotonic() - start
        total = Book.objects.filter(
            embedding_vector__isnull=False, deleted_at__isnull=True,
        ).count()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Embedding computation complete.\n'
            f'  Books processed: {processed}\n'
            f'  Total with embeddings: {total}\n'
            f'  Time: {elapsed:.1f}s',
        ))
