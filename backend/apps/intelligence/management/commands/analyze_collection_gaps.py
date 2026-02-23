"""
Analyse collection gaps and recommend acquisitions.

Usage:
    python manage.py analyze_collection_gaps
    python manage.py analyze_collection_gaps --min-severity HIGH
"""

from django.core.management.base import BaseCommand


SEVERITY_ORDER = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2, 'LOW': 3}


class Command(BaseCommand):
    help = 'Identify gaps in the library collection and recommend acquisitions.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-severity',
            type=str,
            default='LOW',
            choices=['CRITICAL', 'HIGH', 'MODERATE', 'LOW'],
            help='Minimum severity to display (default: LOW).',
        )
        parser.add_argument(
            '--output-json',
            type=str,
            default=None,
            help='Optional path to save results as JSON.',
        )

    def handle(self, *args, **options):
        import json

        from apps.intelligence.infrastructure.predictive_analytics import (
            CollectionGapAnalyzer,
        )

        min_severity = options['min_severity']
        min_order = SEVERITY_ORDER[min_severity]

        self.stdout.write('Analysing collection gaps…')
        gaps = CollectionGapAnalyzer.analyze()

        # Filter by severity
        filtered = [
            g for g in gaps
            if SEVERITY_ORDER.get(g.gap_severity, 3) <= min_order
        ]

        if not filtered:
            self.stdout.write(self.style.SUCCESS(
                f'No gaps found at {min_severity} severity or above.',
            ))
            return

        self.stdout.write(
            self.style.WARNING(f'\n{len(filtered)} collection gaps identified:'),
        )

        for gap in filtered:
            severity_style = (
                self.style.ERROR if gap.gap_severity in ('CRITICAL', 'HIGH')
                else self.style.WARNING
            )
            self.stdout.write(
                f'\n  {severity_style(gap.gap_severity)} — {gap.category_name}',
            )
            self.stdout.write(f'    Current copies: {gap.current_copies}')
            self.stdout.write(f'    Borrow demand: {gap.borrow_demand}')
            self.stdout.write(f'    Search demand: {gap.search_demand}')
            self.stdout.write(f'    Wait-listed: {gap.waitlist_count}')
            self.stdout.write(
                f'    Recommended acquisitions: {gap.suggested_acquisitions}',
            )

        if options['output_json']:
            data = [
                {
                    'category': g.category_name,
                    'severity': g.gap_severity,
                    'current_copies': g.current_copies,
                    'borrow_demand': g.borrow_demand,
                    'search_demand': g.search_demand,
                    'waitlist_count': g.waitlist_count,
                    'suggested_acquisitions': g.suggested_acquisitions,
                }
                for g in filtered
            ]
            with open(options['output_json'], 'w') as f:
                json.dump(data, f, indent=2)
            self.stdout.write(self.style.SUCCESS(
                f'\nResults saved to {options["output_json"]}',
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\nCollection gap analysis complete. {len(filtered)} gaps found.',
        ))
