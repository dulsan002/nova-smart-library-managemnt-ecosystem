/**
 * Admin Settings Page
 * User-friendly configuration management grouped by category.
 */

import { useState, useCallback } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  Cog6ToothIcon,
  ShieldCheckIcon,
  BookOpenIcon,
  BellAlertIcon,
  SparklesIcon,
  WrenchScrewdriverIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { GET_SYSTEM_SETTINGS } from '@/graphql/queries/settings';
import { UPDATE_SYSTEM_SETTING, SYNC_DEFAULT_SETTINGS } from '@/graphql/mutations/settings';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Spinner } from '@/components/ui/Spinner';
import { extractGqlError } from '@/lib/utils';

const CATEGORY_META: Record<string, { label: string; icon: any; description: string; color: string }> = {
  CIRCULATION: {
    label: 'Circulation Policy',
    icon: BookOpenIcon,
    description: 'Book borrowing limits, loan durations, and fine amounts',
    color: 'text-blue-500 bg-blue-50 dark:bg-blue-900/30',
  },
  ENGAGEMENT: {
    label: 'Engagement',
    icon: SparklesIcon,
    description: 'Gamification, points, and reward system configuration',
    color: 'text-purple-500 bg-purple-50 dark:bg-purple-900/30',
  },
  SECURITY: {
    label: 'Security',
    icon: ShieldCheckIcon,
    description: 'Authentication, session limits, and access control',
    color: 'text-red-500 bg-red-50 dark:bg-red-900/30',
  },
  GENERAL: {
    label: 'General Settings',
    icon: Cog6ToothIcon,
    description: 'Library name, operating hours, and general configuration',
    color: 'text-gray-500 bg-gray-50 dark:bg-gray-900/30',
  },
  NOTIFICATIONS: {
    label: 'Notifications',
    icon: BellAlertIcon,
    description: 'Email notifications, due date reminders, and alerts',
    color: 'text-orange-500 bg-orange-50 dark:bg-orange-900/30',
  },
};

interface SettingItem {
  id: string;
  key: string;
  value: string;
  valueType: string;
  category: string;
  label: string;
  description: string;
  isSensitive: boolean;
}

export default function AdminSettingsPage() {
  useDocumentTitle('System Settings');
  const [activeCategory, setActiveCategory] = useState('GENERAL');
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const { data, loading, refetch } = useQuery(GET_SYSTEM_SETTINGS, {
    variables: { category: activeCategory },
  });
  const [updateSetting, { loading: saving }] = useMutation(UPDATE_SYSTEM_SETTING);
  const [syncDefaults, { loading: syncing }] = useMutation(SYNC_DEFAULT_SETTINGS);

  const settings: SettingItem[] = data?.systemSettings || [];

  // Group settings by category
  const categories = Object.keys(CATEGORY_META);

  const handleStartEdit = (setting: SettingItem) => {
    setEditingKey(setting.key);
    setEditValue(setting.value);
  };

  const handleCancelEdit = () => {
    setEditingKey(null);
    setEditValue('');
  };

  const handleSave = useCallback(async (key: string) => {
    try {
      await updateSetting({ variables: { key, value: editValue } });
      toast.success('Setting updated successfully');
      setEditingKey(null);
      setEditValue('');
      refetch();
    } catch (err) {
      toast.error(extractGqlError(err));
    }
  }, [editValue, updateSetting, refetch]);

  const handleSync = useCallback(async () => {
    try {
      const result = await syncDefaults();
      toast.success(`${result.data?.syncDefaultSettings?.createdCount || 0} defaults synced`);
      refetch();
    } catch (err) {
      toast.error(extractGqlError(err));
    }
  }, [syncDefaults, refetch]);

  const renderSettingInput = (setting: SettingItem) => {
    const isEditing = editingKey === setting.key;
    const displayValue = setting.isSensitive ? '••••••••' : setting.value;

    if (!isEditing) {
      return (
        <div className="flex items-center gap-3">
          {setting.valueType === 'BOOLEAN' ? (
            <button
              onClick={async () => {
                const newVal = setting.value === 'true' ? 'false' : 'true';
                try {
                  await updateSetting({ variables: { key: setting.key, value: newVal } });
                  toast.success('Updated');
                  refetch();
                } catch (err) { toast.error(extractGqlError(err)); }
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                setting.value === 'true'
                  ? 'bg-emerald-500'
                  : 'bg-gray-300 dark:bg-gray-600'
              }`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                setting.value === 'true' ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          ) : (
            <span className="text-sm font-mono text-gray-900 dark:text-gray-100 bg-gray-100 dark:bg-gray-800 px-3 py-1.5 rounded-md min-w-[100px]">
              {displayValue}
            </span>
          )}
          {setting.valueType !== 'BOOLEAN' && (
            <Button size="sm" variant="ghost" onClick={() => handleStartEdit(setting)}>
              Edit
            </Button>
          )}
        </div>
      );
    }

    // Editing mode
    switch (setting.valueType) {
      case 'JSON':
        return (
          <div className="space-y-2 w-full max-w-md">
            <Textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              rows={4}
              className="font-mono text-sm"
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={() => handleSave(setting.key)} disabled={saving}>
                {saving ? 'Saving...' : 'Save'}
              </Button>
              <Button size="sm" variant="ghost" onClick={handleCancelEdit}>Cancel</Button>
            </div>
          </div>
        );
      case 'INTEGER':
      case 'FLOAT':
        return (
          <div className="flex items-center gap-2">
            <Input
              type="number"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="w-32"
              step={setting.valueType === 'FLOAT' ? '0.01' : '1'}
              autoFocus
            />
            <Button size="sm" onClick={() => handleSave(setting.key)} disabled={saving}>
              <CheckCircleIcon className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="ghost" onClick={handleCancelEdit}>Cancel</Button>
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-2">
            <Input
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="w-64"
              autoFocus
            />
            <Button size="sm" onClick={() => handleSave(setting.key)} disabled={saving}>
              <CheckCircleIcon className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="ghost" onClick={handleCancelEdit}>Cancel</Button>
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">System Settings</h1>
          <p className="text-sm text-gray-500 mt-1">Configure library system parameters — changes take effect immediately</p>
        </div>
        <Button variant="outline" onClick={handleSync} disabled={syncing}>
          <ArrowPathIcon className={`h-4 w-4 mr-1 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing...' : 'Sync Defaults'}
        </Button>
      </div>

      {/* Category Navigation */}
      <div className="flex gap-2 flex-wrap">
        {categories.map((cat) => {
          const meta = CATEGORY_META[cat];
          if (!meta) return null;
          const Icon = meta.icon;
          const isActive = activeCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-medium transition-all ${
                isActive
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 shadow-sm'
                  : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
            >
              <Icon className="h-4 w-4" />
              {meta?.label}
            </button>
          );
        })}
      </div>

      {/* Category Description */}
      {CATEGORY_META[activeCategory] && (
        <div className={`flex items-start gap-3 p-4 rounded-lg ${CATEGORY_META[activeCategory]!.color}`}>
          <InformationCircleIcon className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium">{CATEGORY_META[activeCategory]!.label}</p>
            <p className="text-sm opacity-75">{CATEGORY_META[activeCategory]!.description}</p>
          </div>
        </div>
      )}

      {/* Settings List */}
      {loading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : settings.length === 0 ? (
        <Card className="p-8 text-center">
          <WrenchScrewdriverIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">No settings found for this category.</p>
          <Button variant="outline" className="mt-4" onClick={handleSync}>Sync Defaults</Button>
        </Card>
      ) : (
        <Card className="divide-y divide-gray-100 dark:divide-gray-800">
          {settings.map((setting) => (
            <div key={setting.id} className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
              <div className="flex-1 mr-8">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-gray-900 dark:text-white">{setting.label}</p>
                  {setting.isSensitive && <Badge variant="warning">Sensitive</Badge>}
                  <Badge variant="neutral" className="text-[10px]">{setting.valueType}</Badge>
                </div>
                <p className="text-sm text-gray-500 mt-0.5">{setting.description}</p>
                <p className="text-xs text-gray-400 font-mono mt-0.5">{setting.key}</p>
              </div>
              <div className="flex-shrink-0">
                {renderSettingInput(setting)}
              </div>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
