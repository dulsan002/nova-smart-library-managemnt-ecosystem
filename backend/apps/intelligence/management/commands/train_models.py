"""
Train recommendation and classification models.

Usage:
    python manage.py train_models
    python manage.py train_models --pipeline embedding
    python manage.py train_models --pipeline collaborative
    python manage.py train_models --pipeline overdue
    python manage.py train_models --pipeline all
"""

import time

from django.core.management.base import BaseCommand


PIPELINE_CHOICES = ['embedding', 'collaborative', 'overdue', 'all']


class Command(BaseCommand):
    help = 'Train AI/ML models in the Nova ecosystem.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pipeline',
            type=str,
            default='all',
            choices=PIPELINE_CHOICES,
            help='Which pipeline to run (default: all).',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed metrics for each pipeline.',
        )

    def handle(self, *args, **options):
        from apps.intelligence.infrastructure.training_pipeline import (
            CollaborativeFilterPipeline,
            EmbeddingPipeline,
            OverdueClassifierPipeline,
        )

        pipeline = options['pipeline']
        verbose = options['verbose']
        results = []

        if pipeline in ('embedding', 'all'):
            self.stdout.write(self.style.HTTP_INFO('Running embedding pipeline…'))
            result = EmbeddingPipeline.run_full()
            results.append(result)
            self._report(result, verbose)

        if pipeline in ('collaborative', 'all'):
            self.stdout.write(
                self.style.HTTP_INFO('Running collaborative filter pipeline…'),
            )
            result = CollaborativeFilterPipeline.run_full()
            results.append(result)
            self._report(result, verbose)

        if pipeline in ('overdue', 'all'):
            self.stdout.write(
                self.style.HTTP_INFO('Running overdue classifier pipeline…'),
            )
            result = OverdueClassifierPipeline.run_full()
            results.append(result)
            self._report(result, verbose)

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Training Summary ==='))
        for r in results:
            status_style = (
                self.style.SUCCESS if r.status == 'SUCCESS'
                else self.style.WARNING if r.status == 'PARTIAL'
                else self.style.ERROR
            )
            self.stdout.write(
                f'  {r.pipeline_name}: {status_style(r.status)} '
                f'({r.total_time_seconds}s)',
            )

    def _report(self, result, verbose):
        """Print pipeline result."""
        status_style = (
            self.style.SUCCESS if result.status == 'SUCCESS'
            else self.style.WARNING if result.status == 'PARTIAL'
            else self.style.ERROR
        )

        self.stdout.write(
            f'  Status: {status_style(result.status)} '
            f'({result.total_time_seconds}s)',
        )

        if result.stages_completed:
            self.stdout.write(
                f'  Stages completed: {", ".join(result.stages_completed)}',
            )
        if result.stages_failed:
            self.stdout.write(
                self.style.ERROR(
                    f'  Stages failed: {", ".join(result.stages_failed)}',
                ),
            )
        if result.errors:
            for err in result.errors:
                self.stdout.write(self.style.ERROR(f'    Error: {err}'))

        if verbose and result.metrics:
            self.stdout.write('  Metrics:')
            for k, v in result.metrics.items():
                self.stdout.write(f'    {k}: {v}')

        self.stdout.write('')
