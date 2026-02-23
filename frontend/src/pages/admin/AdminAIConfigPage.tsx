/**
 * AdminAIConfigPage — super-admin page to configure AI providers
 * (Ollama, Google Gemini, OpenAI). CRUD operations, health check testing,
 * activation, and a test generation playground.
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  CpuChipIcon,
  PlusIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  BeakerIcon,
  BoltIcon,
  ServerIcon,
  CloudIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { AI_PROVIDER_CONFIGS } from '@/graphql/queries/intelligence';
import {
  CREATE_AI_PROVIDER_CONFIG,
  UPDATE_AI_PROVIDER_CONFIG,
  DELETE_AI_PROVIDER_CONFIG,
  ACTIVATE_AI_PROVIDER_CONFIG,
  TEST_AI_PROVIDER_CONFIG,
  GENERATE_AI_RESPONSE,
} from '@/graphql/mutations/intelligence';
import { Card, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { extractGqlError, timeAgo } from '@/lib/utils';

// ----- Constants -----

const PROVIDERS = [
  { value: 'OLLAMA', label: 'Ollama (Local)', icon: ServerIcon, color: 'text-green-600' },
  { value: 'GEMINI', label: 'Google Gemini', icon: CloudIcon, color: 'text-blue-600' },
  { value: 'OPENAI', label: 'OpenAI', icon: CpuChipIcon, color: 'text-purple-600' },
  { value: 'LOCAL_TRANSFORMERS', label: 'Local Transformers', icon: CpuChipIcon, color: 'text-orange-600' },
];

const CAPABILITIES = [
  { value: 'CHAT', label: 'Chat / Text Generation' },
  { value: 'EMBEDDING', label: 'Embedding' },
  { value: 'SUMMARIZATION', label: 'Summarization' },
  { value: 'CLASSIFICATION', label: 'Classification' },
];

const PRESET_MODELS: Record<string, { models: string[]; defaultUrl: string; needsKey: boolean }> = {
  OLLAMA: {
    models: ['llama3.1', 'llama3.1:70b', 'mistral', 'codellama', 'nomic-embed-text', 'mxbai-embed-large'],
    defaultUrl: 'http://localhost:11434',
    needsKey: false,
  },
  GEMINI: {
    models: ['gemini-pro', 'gemini-1.5-pro', 'gemini-1.5-flash', 'embedding-001'],
    defaultUrl: '',
    needsKey: true,
  },
  OPENAI: {
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo', 'text-embedding-3-small', 'text-embedding-3-large'],
    defaultUrl: '',
    needsKey: true,
  },
  LOCAL_TRANSFORMERS: {
    models: ['all-MiniLM-L6-v2', 'all-mpnet-base-v2', 'paraphrase-multilingual-MiniLM-L12-v2'],
    defaultUrl: '',
    needsKey: false,
  },
};

// ----- Main Component -----

export default function AdminAIConfigPage() {
  useDocumentTitle('AI Provider Configuration');

  const { data, loading, refetch } = useQuery(AI_PROVIDER_CONFIGS, {
    fetchPolicy: 'cache-and-network',
  });

  const configs = data?.aiProviderConfigs ?? [];

  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; name: string } | null>(null);
  const [testPrompt, setTestPrompt] = useState('');
  const [testResult, setTestResult] = useState<{ text: string; model: string; error: string } | null>(null);

  // Mutations
  const [createConfig, { loading: creating }] = useMutation(CREATE_AI_PROVIDER_CONFIG, {
    onCompleted: () => {
      toast.success('Provider configuration created');
      setShowForm(false);
      refetch();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [updateConfig, { loading: updating }] = useMutation(UPDATE_AI_PROVIDER_CONFIG, {
    onCompleted: () => {
      toast.success('Configuration updated');
      setEditId(null);
      refetch();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [deleteConfig] = useMutation(DELETE_AI_PROVIDER_CONFIG, {
    onCompleted: () => {
      toast.success('Configuration deleted');
      setDeleteConfirm(null);
      refetch();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [activateConfig] = useMutation(ACTIVATE_AI_PROVIDER_CONFIG, {
    onCompleted: () => {
      toast.success('Provider activated');
      refetch();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [testConfig, { loading: testing }] = useMutation(TEST_AI_PROVIDER_CONFIG, {
    onCompleted: (d) => {
      const result = d.testAiProviderConfig;
      if (result.healthy) {
        toast.success(result.message);
      } else {
        toast.error(result.message);
      }
      refetch();
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [generateResponse, { loading: generating }] = useMutation(GENERATE_AI_RESPONSE, {
    onCompleted: (d) => {
      setTestResult(d.generateAiResponse);
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  // Group configs by capability
  const grouped = CAPABILITIES.map((cap) => ({
    ...cap,
    configs: configs.filter((c: any) => c.capability === cap.value),
  }));

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">
            <CpuChipIcon className="mr-2 inline h-6 w-6 text-primary-500" />
            AI Provider Configuration
          </h1>
          <p className="text-sm text-nova-text-secondary">
            Configure and manage AI providers — Ollama (local), Google Gemini, OpenAI
          </p>
        </div>
        <Button
          leftIcon={<PlusIcon className="h-4 w-4" />}
          onClick={() => { setShowForm(true); setEditId(null); }}
        >
          Add Provider
        </Button>
      </div>

      {/* New / Edit Form */}
      {showForm && (
        <ProviderForm
          onSubmit={(formData) => {
            if (editId) {
              updateConfig({ variables: { configId: editId, ...formData } });
            } else {
              createConfig({ variables: formData });
            }
          }}
          onCancel={() => { setShowForm(false); setEditId(null); }}
          loading={creating || updating}
          initial={editId ? configs.find((c: any) => c.id === editId) : undefined}
        />
      )}

      {loading ? (
        <LoadingOverlay message="Loading AI configurations…" />
      ) : configs.length === 0 && !showForm ? (
        <EmptyState
          icon={<CpuChipIcon />}
          title="No AI providers configured"
          description="Add your first AI provider to enable intelligent features like recommendations, search, and content analysis."
          action={
            <Button
              leftIcon={<PlusIcon className="h-4 w-4" />}
              onClick={() => setShowForm(true)}
            >
              Add Provider
            </Button>
          }
        />
      ) : (
        <div className="space-y-8">
          {grouped.map((group) => (
            <div key={group.value}>
              <h2 className="mb-3 text-lg font-semibold text-nova-text">{group.label}</h2>
              {group.configs.length === 0 ? (
                <p className="text-sm text-nova-text-muted italic">
                  No providers configured for {group.label.toLowerCase()}
                </p>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  {group.configs.map((config: any) => {
                    const providerMeta = PROVIDERS.find((p) => p.value === config.provider);
                    const ProviderIcon = providerMeta?.icon ?? CpuChipIcon;

                    return (
                      <Card key={config.id} className="relative">
                        {config.isActive && (
                          <div className="absolute right-3 top-3">
                            <Badge variant="success" size="xs" dot>Active</Badge>
                          </div>
                        )}

                        <div className="space-y-3">
                          <div className="flex items-center gap-3">
                            <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-gray-100 dark:bg-gray-800 ${providerMeta?.color ?? ''}`}>
                              <ProviderIcon className="h-5 w-5" />
                            </div>
                            <div className="min-w-0">
                              <p className="font-semibold text-nova-text truncate">{config.displayName}</p>
                              <p className="text-xs text-nova-text-muted">{config.modelName}</p>
                            </div>
                          </div>

                          {/* Health status */}
                          <div className="flex items-center gap-2 text-xs">
                            {config.isHealthy ? (
                              <CheckCircleIcon className="h-4 w-4 text-green-500" />
                            ) : (
                              <XCircleIcon className="h-4 w-4 text-red-400" />
                            )}
                            <span className={config.isHealthy ? 'text-green-600' : 'text-red-500'}>
                              {config.isHealthy ? 'Healthy' : 'Unhealthy'}
                            </span>
                            {config.lastHealthCheck && (
                              <span className="text-nova-text-muted">
                                · checked {timeAgo(config.lastHealthCheck)}
                              </span>
                            )}
                          </div>

                          {config.lastError && !config.isHealthy && (
                            <p className="rounded bg-red-50 p-2 text-xs text-red-600 dark:bg-red-900/10">
                              {config.lastError}
                            </p>
                          )}

                          {config.apiBaseUrl && (
                            <p className="text-xs text-nova-text-muted truncate">
                              URL: {config.apiBaseUrl}
                            </p>
                          )}

                          {/* Actions */}
                          <div className="flex flex-wrap gap-2 pt-1">
                            <Button
                              size="xs"
                              variant="outline"
                              leftIcon={<BeakerIcon className="h-3.5 w-3.5" />}
                              onClick={() => testConfig({ variables: { configId: config.id } })}
                              isLoading={testing}
                            >
                              Test
                            </Button>
                            {!config.isActive && (
                              <Button
                                size="xs"
                                variant="primary"
                                leftIcon={<BoltIcon className="h-3.5 w-3.5" />}
                                onClick={() => activateConfig({ variables: { configId: config.id } })}
                              >
                                Activate
                              </Button>
                            )}
                            <Button
                              size="xs"
                              variant="outline"
                              onClick={() => { setEditId(config.id); setShowForm(true); }}
                            >
                              Edit
                            </Button>
                            <Button
                              size="xs"
                              variant="ghost"
                              leftIcon={<TrashIcon className="h-3.5 w-3.5" />}
                              onClick={() => setDeleteConfirm({ id: config.id, name: config.displayName })}
                              className="text-red-500 hover:text-red-700"
                            >
                              Delete
                            </Button>
                          </div>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Test Generation Playground */}
      <Card>
        <CardHeader
          title="Test Generation"
          description="Send a test prompt to the active CHAT provider"
        />
        <div className="mt-4 space-y-3">
          <textarea
            value={testPrompt}
            onChange={(e) => setTestPrompt(e.target.value)}
            placeholder="Enter a test prompt… e.g. 'Recommend 3 classic novels for beginners'"
            className="w-full rounded-lg border border-nova-border bg-nova-surface p-3 text-sm text-nova-text placeholder:text-nova-text-muted focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            rows={3}
          />
          <Button
            onClick={() =>
              generateResponse({
                variables: { prompt: testPrompt, capability: 'CHAT' },
              })
            }
            isLoading={generating}
            disabled={!testPrompt.trim()}
            leftIcon={<ArrowPathIcon className="h-4 w-4" />}
          >
            Generate
          </Button>
          {testResult && (
            <div className="rounded-lg border border-nova-border bg-gray-50 p-4 dark:bg-gray-800/50">
              {testResult.error ? (
                <p className="text-sm text-red-600">{testResult.error}</p>
              ) : (
                <>
                  <p className="whitespace-pre-wrap text-sm text-nova-text">{testResult.text}</p>
                  {testResult.model && (
                    <p className="mt-2 text-xs text-nova-text-muted">Model: {testResult.model}</p>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </Card>

      {/* Delete confirm dialog */}
      <ConfirmDialog
        open={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        title="Delete Provider Configuration"
        description={deleteConfirm ? `Are you sure you want to delete "${deleteConfirm.name}"? This cannot be undone.` : ''}
        confirmLabel="Delete"
        variant="danger"
        onConfirm={() => { if (deleteConfirm) deleteConfig({ variables: { configId: deleteConfirm.id } }); }}
      />
    </div>
  );
}

// ----- Provider Form Component -----

function ProviderForm({
  onSubmit,
  onCancel,
  loading,
  initial,
}: {
  onSubmit: (data: any) => void;
  onCancel: () => void;
  loading: boolean;
  initial?: any;
}) {
  const [provider, setProvider] = useState(initial?.provider ?? 'OLLAMA');
  const [capability, setCapability] = useState(initial?.capability ?? 'CHAT');
  const [displayName, setDisplayName] = useState(initial?.displayName ?? '');
  const [modelName, setModelName] = useState(initial?.modelName ?? '');
  const [apiBaseUrl, setApiBaseUrl] = useState(initial?.apiBaseUrl ?? '');
  const [apiKey, setApiKey] = useState('');
  const [temperature, setTemperature] = useState('0.7');

  const preset = PRESET_MODELS[provider];

  // Auto-fill defaults when provider changes
  const handleProviderChange = (val: string) => {
    setProvider(val);
    const p = PRESET_MODELS[val];
    if (p) {
      setApiBaseUrl(p.defaultUrl);
      if (p.models.length > 0) setModelName(p.models[0]);
      setDisplayName(`${PROVIDERS.find((pr) => pr.value === val)?.label ?? val} — ${p.models[0] ?? ''}`);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      provider,
      capability,
      displayName,
      modelName,
      apiBaseUrl: apiBaseUrl || undefined,
      apiKey: apiKey || undefined,
      extraConfig: JSON.stringify({ temperature: parseFloat(temperature) || 0.7 }),
    });
  };

  return (
    <Card>
      <CardHeader
        title={initial ? 'Edit Provider' : 'Add AI Provider'}
        description="Configure a new AI model provider"
      />
      <form onSubmit={handleSubmit} className="mt-4 grid gap-4 sm:grid-cols-2">
        {/* Provider */}
        <div>
          <label className="mb-1 block text-sm font-medium text-nova-text">Provider</label>
          <select
            value={provider}
            onChange={(e) => handleProviderChange(e.target.value)}
            className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>

        {/* Capability */}
        <div>
          <label className="mb-1 block text-sm font-medium text-nova-text">Capability</label>
          <select
            value={capability}
            onChange={(e) => setCapability(e.target.value)}
            className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
          >
            {CAPABILITIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>

        {/* Display Name */}
        <div className="sm:col-span-2">
          <label className="mb-1 block text-sm font-medium text-nova-text">Display Name</label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="e.g. Ollama llama3.1 8B"
            className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
            required
          />
        </div>

        {/* Model Name */}
        <div>
          <label className="mb-1 block text-sm font-medium text-nova-text">Model Name</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="llama3.1"
              className="flex-1 rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
              required
              list="model-suggestions"
            />
            <datalist id="model-suggestions">
              {preset?.models.map((m) => (
                <option key={m} value={m} />
              ))}
            </datalist>
          </div>
          {preset && (
            <p className="mt-1 text-xs text-nova-text-muted">
              Suggestions: {preset.models.join(', ')}
            </p>
          )}
        </div>

        {/* API Base URL */}
        <div>
          <label className="mb-1 block text-sm font-medium text-nova-text">
            API Base URL {!preset?.needsKey && '(optional)'}
          </label>
          <input
            type="text"
            value={apiBaseUrl}
            onChange={(e) => setApiBaseUrl(e.target.value)}
            placeholder="http://localhost:11434"
            className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
          />
        </div>

        {/* API Key */}
        {preset?.needsKey && (
          <div className="sm:col-span-2">
            <label className="mb-1 block text-sm font-medium text-nova-text">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter API key…"
              className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
            />
            <p className="mt-1 text-xs text-nova-text-muted">
              The key is stored securely and never exposed via the API.
            </p>
          </div>
        )}

        {/* Temperature */}
        <div>
          <label className="mb-1 block text-sm font-medium text-nova-text">Temperature</label>
          <input
            type="number"
            value={temperature}
            onChange={(e) => setTemperature(e.target.value)}
            min="0"
            max="2"
            step="0.1"
            className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm text-nova-text"
          />
        </div>

        {/* Actions */}
        <div className="flex gap-2 sm:col-span-2">
          <Button type="submit" isLoading={loading}>
            {initial ? 'Update' : 'Create Provider'}
          </Button>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  );
}
