"""
Run churn risk analysis for library members.

Usage:
    python manage.py analyze_churn
    python manage.py analyze_churn --weeks 8
    python manage.py analyze_churn --notify
"""

import time

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Analyse user churn risk and identify at-risk members.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--weeks',
            type=int,
            default=8,
            help='Analysis window in weeks (default: 8).',
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.6,
            help='Churn risk threshold for flagging (default: 0.6).',
        )
        parser.add_argument(
            '--notify',
            action='store_true',
            help='Send re-engagement notifications to at-risk users.',
        )

    def handle(self, *args, **options):
        from apps.identity.domain.models import User
        from apps.intelligence.infrastructure.predictive_analytics import (
            ChurnPredictor,
        )

        weeks = options['weeks']
        threshold = options['threshold']
        notify = options['notify']

        users = User.objects.filter(is_active=True, role__in=['MEMBER', 'STUDENT'])
        total = users.count()

        self.stdout.write(
            f'Analysing churn risk for {total} users '
            f'({weeks}-week window, threshold: {threshold})…',
        )

        start = time.monotonic()
        at_risk = []
        stats = {'LOW': 0, 'MODERATE': 0, 'HIGH': 0, 'CRITICAL': 0}

        for user in users.iterator(chunk_size=100):
            try:
                prediction = ChurnPredictor.predict(user, weeks=weeks)
                stats[prediction.risk_level] = stats.get(prediction.risk_level, 0) + 1

                if prediction.churn_probability >= threshold:
                    at_risk.append({
                        'user_id': str(user.id),
                        'email': user.email,
                        'probability': prediction.churn_probability,
                        'risk': prediction.risk_level,
                        'inactivity_weeks': prediction.weeks_since_last_activity,
                        'recs': prediction.recommendations[:2],
                    })
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f'  Error for {user.id}: {exc}'),
                )

        elapsed = time.monotonic() - start

        # Report
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Churn Risk Distribution:'))
        for level, count in stats.items():
            style = (
                self.style.ERROR if level in ('HIGH', 'CRITICAL')
                else self.style.WARNING if level == 'MODERATE'
                else self.style.SUCCESS
            )
            self.stdout.write(f'  {style(level)}: {count}')

        if at_risk:
            self.stdout.write(
                self.style.WARNING(f'\n{len(at_risk)} at-risk users:'),
            )
            for item in at_risk[:20]:
                self.stdout.write(
                    f'  {item["email"][:35]} '
                    f'(p={item["probability"]:.2f}, {item["risk"]}, '
                    f'inactive {item["inactivity_weeks"]}w)',
                )
                for rec in item['recs']:
                    self.stdout.write(f'    ↳ {rec}')

        if notify and at_risk:
            self._send_re_engagement(at_risk)

        self.stdout.write(self.style.SUCCESS(
            f'\nChurn analysis complete ({elapsed:.1f}s). '
            f'{len(at_risk)} users at risk.',
        ))

    def _send_re_engagement(self, at_risk):
        """Send re-engagement notifications."""
        from apps.identity.domain.models import User
        from apps.intelligence.infrastructure.notification_engine import (
            NotificationEngine,
        )

        sent = 0
        for item in at_risk:
            try:
                user = User.objects.get(id=item['user_id'])
                NotificationEngine.create(
                    user=user,
                    notification_type='RE_ENGAGEMENT',
                    data={
                        'weeks_inactive': item['inactivity_weeks'],
                        'recommendations': item['recs'],
                    },
                )
                sent += 1
            except Exception:
                pass

        self.stdout.write(self.style.SUCCESS(
            f'  Sent {sent} re-engagement notifications.',
        ))
