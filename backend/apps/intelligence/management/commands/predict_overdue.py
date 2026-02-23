"""
Run overdue risk predictions for active borrows.

Usage:
    python manage.py predict_overdue
    python manage.py predict_overdue --threshold 0.7
    python manage.py predict_overdue --notify
"""

import time

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Predict overdue probability for all active borrows.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.6,
            help='Risk threshold for flagging borrows (default: 0.6).',
        )
        parser.add_argument(
            '--notify',
            action='store_true',
            help='Send notifications for high-risk borrows.',
        )

    def handle(self, *args, **options):
        from apps.circulation.domain.models import BorrowRecord
        from apps.intelligence.infrastructure.predictive_analytics import (
            OverduePredictor,
        )

        threshold = options['threshold']
        notify = options['notify']

        active_borrows = BorrowRecord.objects.filter(
            status='ACTIVE',
        ).select_related('user', 'book_copy__book')

        total = active_borrows.count()
        self.stdout.write(
            f'Analysing {total} active borrows (threshold: {threshold})…',
        )

        start = time.monotonic()
        high_risk = []
        stats = {'LOW': 0, 'MODERATE': 0, 'HIGH': 0, 'CRITICAL': 0}

        for record in active_borrows.iterator(chunk_size=100):
            try:
                prediction = OverduePredictor.predict(record)
                stats[prediction.risk_level] = stats.get(prediction.risk_level, 0) + 1

                if prediction.probability >= threshold:
                    high_risk.append({
                        'borrow_id': str(record.id),
                        'user': record.user.email,
                        'book': record.book_copy.book.title[:50],
                        'probability': prediction.probability,
                        'risk': prediction.risk_level,
                        'factors': prediction.contributing_factors,
                    })

            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f'  Error for {record.id}: {exc}'),
                )

        elapsed = time.monotonic() - start

        # Report
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Risk Distribution:'))
        for level, count in stats.items():
            style = (
                self.style.ERROR if level in ('HIGH', 'CRITICAL')
                else self.style.WARNING if level == 'MODERATE'
                else self.style.SUCCESS
            )
            self.stdout.write(f'  {style(level)}: {count}')

        if high_risk:
            self.stdout.write(
                self.style.WARNING(
                    f'\n{len(high_risk)} borrows above {threshold} threshold:',
                ),
            )
            for item in high_risk[:20]:
                self.stdout.write(
                    f'  {item["user"][:30]} — {item["book"]} '
                    f'(p={item["probability"]:.2f}, {item["risk"]})',
                )
                for factor in item['factors']:
                    self.stdout.write(f'    ↳ {factor}')

        if notify and high_risk:
            self._send_notifications(high_risk)

        self.stdout.write(self.style.SUCCESS(
            f'\nOverdue prediction complete ({elapsed:.1f}s).',
        ))

    def _send_notifications(self, high_risk):
        """Send overdue warning notifications."""
        from apps.identity.domain.models import User
        from apps.intelligence.infrastructure.notification_engine import (
            NotificationEngine,
        )

        sent = 0
        for item in high_risk:
            try:
                user = User.objects.get(email=item['user'])
                NotificationEngine.create(
                    user=user,
                    notification_type='OVERDUE_WARNING',
                    data={
                        'book_title': item['book'],
                        'probability': item['probability'],
                        'risk_level': item['risk'],
                    },
                )
                sent += 1
            except Exception:
                pass

        self.stdout.write(self.style.SUCCESS(
            f'  Sent {sent} overdue warning notifications.',
        ))
