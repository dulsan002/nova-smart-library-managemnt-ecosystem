"""
Evaluate AI model performance.

Usage:
    python manage.py evaluate_models
    python manage.py evaluate_models --type recommendations
    python manage.py evaluate_models --type overdue
    python manage.py evaluate_models --type all
"""

import json

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Evaluate AI/ML model quality with standard metrics.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='all',
            choices=['recommendations', 'overdue', 'all'],
            help='Which model to evaluate (default: all).',
        )
        parser.add_argument(
            '--top-k',
            type=int,
            default=10,
            help='K value for Precision@K / Recall@K (default: 10).',
        )
        parser.add_argument(
            '--output-json',
            type=str,
            default=None,
            help='Optional path to save metrics as JSON.',
        )

    def handle(self, *args, **options):
        from apps.intelligence.infrastructure.evaluation import (
            ClassificationEvaluator,
            RecommendationEvaluator,
        )

        eval_type = options['type']
        top_k = options['top_k']
        all_metrics = {}

        if eval_type in ('recommendations', 'all'):
            self.stdout.write(self.style.HTTP_INFO(
                f'Evaluating recommendation model (K={top_k})…',
            ))
            metrics = RecommendationEvaluator.evaluate(k=top_k)
            self._print_metrics('Recommendation Metrics', {
                'Precision@K': metrics.precision_at_k,
                'Recall@K': metrics.recall_at_k,
                'NDCG@K': metrics.ndcg_at_k,
                'MRR': metrics.mrr,
                'Hit Rate': metrics.hit_rate,
                'Catalog Coverage': metrics.catalog_coverage,
                'Diversity': metrics.diversity,
                'Novelty': metrics.novelty,
            })
            all_metrics['recommendations'] = {
                'precision_at_k': metrics.precision_at_k,
                'recall_at_k': metrics.recall_at_k,
                'ndcg_at_k': metrics.ndcg_at_k,
                'mrr': metrics.mrr,
                'hit_rate': metrics.hit_rate,
                'catalog_coverage': metrics.catalog_coverage,
                'diversity': metrics.diversity,
                'novelty': metrics.novelty,
            }

        if eval_type in ('overdue', 'all'):
            self.stdout.write(self.style.HTTP_INFO(
                'Evaluating overdue prediction classifier…',
            ))
            metrics = ClassificationEvaluator.evaluate_overdue_predictions()
            self._print_metrics('Overdue Classifier Metrics', {
                'Accuracy': metrics.accuracy,
                'Precision': metrics.precision,
                'Recall': metrics.recall,
                'F1 Score': metrics.f1_score,
                'AUC-ROC': metrics.auc_roc,
            })
            all_metrics['overdue'] = {
                'accuracy': metrics.accuracy,
                'precision': metrics.precision,
                'recall': metrics.recall,
                'f1_score': metrics.f1_score,
                'auc_roc': metrics.auc_roc,
            }

        if options['output_json']:
            with open(options['output_json'], 'w') as f:
                json.dump(all_metrics, f, indent=2)
            self.stdout.write(self.style.SUCCESS(
                f'Metrics saved to {options["output_json"]}',
            ))

    def _print_metrics(self, title, metrics):
        """Pretty-print a metrics dictionary."""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'  === {title} ==='))
        for name, value in metrics.items():
            if isinstance(value, float):
                self.stdout.write(f'    {name}: {value:.4f}')
            else:
                self.stdout.write(f'    {name}: {value}')
        self.stdout.write('')
