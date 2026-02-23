"""
Detect duplicate books in the catalog.

Usage:
    python manage.py detect_duplicates
    python manage.py detect_duplicates --auto-flag
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Find potential duplicate books in the catalog.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto-flag',
            action='store_true',
            help='Automatically flag duplicates for review.',
        )

    def handle(self, *args, **options):
        from apps.intelligence.infrastructure.content_analysis import (
            DuplicateDetector,
        )

        auto_flag = options['auto_flag']

        self.stdout.write('Scanning for duplicate books…')
        groups = DuplicateDetector.find_duplicates()

        if not groups:
            self.stdout.write(self.style.SUCCESS('No duplicates found.'))
            return

        self.stdout.write(
            self.style.WARNING(f'Found {len(groups)} duplicate groups:'),
        )

        for i, group in enumerate(groups, 1):
            self.stdout.write(f'\n  Group {i} (score: {group.similarity_score:.3f}):')
            for book in group.books:
                isbn = getattr(book, 'isbn', 'no ISBN')
                self.stdout.write(f'    - {book.title} (ISBN: {isbn}, ID: {book.id})')

        if auto_flag:
            flagged = 0
            for group in groups:
                for book in group.books[1:]:
                    book.metadata = book.metadata or {}
                    book.metadata['duplicate_review'] = True
                    book.metadata['duplicate_group_lead'] = str(group.books[0].id)
                    book.save(update_fields=['metadata', 'updated_at'])
                    flagged += 1

            self.stdout.write(self.style.SUCCESS(
                f'\nFlagged {flagged} books for duplicate review.',
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\nDuplicate scan complete. {len(groups)} groups found.',
        ))
