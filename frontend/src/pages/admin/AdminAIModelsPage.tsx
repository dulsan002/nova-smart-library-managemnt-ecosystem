/**
 * AdminAIModelsPage — manage AI/ML models, view recommendation metrics,
 * trigger training pipelines, activate model versions.
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  CpuChipIcon,
  PlayIcon,
  CheckCircleIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { AI_MODELS, RECOMMENDATION_METRICS } from '@/graphql/queries/intelligence';
import {
  TRIGGER_MODEL_TRAINING,
  TRIGGER_EMBEDDING_COMPUTATION,
  ACTIVATE_AI_MODEL,
} from '@/graphql/mutations/intelligence';
import { Card, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { extractGqlError, timeAgo } from '@/lib/utils';

export default function AdminAIModelsPage() {
  useDocumentTitle('AI Models');

  const [confirmActivate, setConfirmActivate] = useState<{ id: string; name: string } | null>(
    null,
  );

  const { data: modelsData, loading: mL, refetch } = useQuery(AI_MODELS);
  const { data: metricsData, loading: metL } = useQuery(RECOMMENDATION_METRICS, {
    variables: { k: 10 },
  });

  const models = modelsData?.aiModels ?? [];
  const metrics = metricsData?.recommendationMetrics;

  const [triggerTraining, { loading: training }] = useMutation(TRIGGER_MODEL_TRAINING, {
    onCompleted: (d) => {
      toast.success(`Training started — task ${d.triggerModelTraining.taskId}`);
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [triggerEmbeddings, { loading: embedding }] = useMutation(TRIGGER_EMBEDDING_COMPUTATION, {
    onCompleted: (d) => {
      toast.success(`Embedding computation started — task ${d.triggerEmbeddingComputation.taskId}`);
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [activateModel] = useMutation(ACTIVATE_AI_MODEL, {
    onCompleted: () => {
      toast.success('Model activated');
      refetch();
      setConfirmActivate(null);
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const loading = mL || metL;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">AI Models</h1>
          <p className="text-sm text-nova-text-secondary">
            Manage recommendation engine models, trigger training, and monitor metrics.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            leftIcon={<PlayIcon className="h-4 w-4" />}
            onClick={() => triggerTraining({ variables: { pipeline: 'all' } })}
            isLoading={training}
          >
            Run Training
          </Button>
          <Button
            variant="outline"
            size="sm"
            leftIcon={<SparklesIcon className="h-4 w-4" />}
            onClick={() => triggerEmbeddings({ variables: { batchSize: 100 } })}
            isLoading={embedding}
          >
            Compute Embeddings
          </Button>
        </div>
      </div>

      {loading ? (
        <LoadingOverlay />
      ) : (
        <>
          {/* Recommendation metrics */}
          {metrics && (
            <Card>
              <CardHeader>
                <h3 className="font-semibold text-nova-text">Recommendation Engine Metrics (k=10)</h3>
              </CardHeader>
              <div className="grid gap-4 p-4 pt-0 sm:grid-cols-2 lg:grid-cols-4">
                <MetricCard label="Precision@K" value={(metrics.precisionAtK * 100).toFixed(1) + '%'} />
                <MetricCard label="Recall@K" value={(metrics.recallAtK * 100).toFixed(1) + '%'} />
                <MetricCard label="NDCG@K" value={(metrics.ndcgAtK * 100).toFixed(1) + '%'} />
                <MetricCard label="MRR" value={metrics.mrr.toFixed(3)} />
                <MetricCard label="Hit Rate" value={(metrics.hitRate * 100).toFixed(1) + '%'} />
                <MetricCard
                  label="Catalog Coverage"
                  value={(metrics.catalogCoverage * 100).toFixed(1) + '%'}
                />
                <MetricCard label="Diversity" value={metrics.diversity.toFixed(3)} />
                <MetricCard label="Novelty" value={metrics.novelty.toFixed(3)} />
              </div>
            </Card>
          )}

          {/* Models list */}
          {models.length === 0 ? (
            <EmptyState
              icon={<CpuChipIcon />}
              title="No AI models"
              description="Train your first model to get started."
              action={
                <Button
                  size="sm"
                  onClick={() => triggerTraining({ variables: { pipeline: 'all' } })}
                  isLoading={training}
                >
                  Run Training
                </Button>
              }
            />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {models.map((model: any) => (
                <Card key={model.id} className="flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CpuChipIcon className="h-5 w-5 text-nova-text-muted" />
                        <h4 className="font-semibold text-nova-text">{model.name}</h4>
                      </div>
                      {model.isActive ? (
                        <Badge variant="success" size="sm" dot>
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="neutral" size="sm">
                          Inactive
                        </Badge>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-nova-text-muted">{model.description}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge variant="info" size="sm">
                        {model.modelType}
                      </Badge>
                      <Badge variant="neutral" size="sm">
                        v{model.version}
                      </Badge>
                    </div>

                    {model.metrics && typeof model.metrics === 'object' && (
                      <div className="mt-3 space-y-1">
                        {Object.entries(model.metrics as Record<string, number>)
                          .slice(0, 3)
                          .map(([key, val]) => (
                            <div
                              key={key}
                              className="flex items-center justify-between text-xs text-nova-text-muted"
                            >
                              <span>{key}</span>
                              <span className="font-medium text-nova-text">
                                {typeof val === 'number' ? val.toFixed(3) : val}
                              </span>
                            </div>
                          ))}
                      </div>
                    )}

                    <p className="mt-2 text-[11px] text-nova-text-muted">
                      Created {timeAgo(model.createdAt)}
                    </p>
                  </div>

                  {!model.isActive && (
                    <div className="mt-4">
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        leftIcon={<CheckCircleIcon className="h-4 w-4" />}
                        onClick={() =>
                          setConfirmActivate({ id: model.id, name: model.name })
                        }
                      >
                        Activate
                      </Button>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {/* Confirm activate dialog */}
      {confirmActivate && (
        <ConfirmDialog
          open
          onClose={() => setConfirmActivate(null)}
          onConfirm={() =>
            activateModel({ variables: { modelId: confirmActivate.id } })
          }
          title="Activate Model"
          description={`Replace the current active model with "${confirmActivate.name}"? This will take effect immediately.`}
          variant="warning"
          confirmLabel="Activate"
        />
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-nova-border bg-nova-surface p-3 text-center">
      <p className="text-[11px] font-medium uppercase tracking-wider text-nova-text-muted">
        {label}
      </p>
      <p className="mt-1 text-lg font-bold text-nova-text">{value}</p>
    </div>
  );
}
