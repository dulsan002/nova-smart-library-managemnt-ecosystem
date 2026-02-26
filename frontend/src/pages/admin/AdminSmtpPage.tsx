/**
 * Admin SMTP Configuration Page
 * User-friendly email setup with provider presets, step-by-step guide, and test email.
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  EnvelopeIcon,
  ServerStackIcon,
  KeyIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PaperAirplaneIcon,
  InformationCircleIcon,
  LightBulbIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { GET_SYSTEM_SETTINGS } from '@/graphql/queries/settings';
import { UPDATE_SYSTEM_SETTING, SYNC_DEFAULT_SETTINGS, SEND_TEST_EMAIL } from '@/graphql/mutations/settings';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { extractGqlError } from '@/lib/utils';

/* ── Provider presets ── */
interface ProviderPreset {
  name: string;
  logo: string;
  host: string;
  port: number;
  tls: boolean;
  instructions: string[];
}

const PRESETS: ProviderPreset[] = [
  {
    name: 'Gmail',
    logo: '📧',
    host: 'smtp.gmail.com',
    port: 587,
    tls: true,
    instructions: [
      'Go to myaccount.google.com and sign in.',
      'Navigate to Security → 2-Step Verification (enable if not already).',
      'Scroll down to "App passwords" and click it.',
      'Select "Mail" and your device, then click Generate.',
      'Copy the 16-character app password — use it as your SMTP password below.',
      'Your SMTP username is your full Gmail address (e.g. library@gmail.com).',
    ],
  },
  {
    name: 'Outlook / Microsoft 365',
    logo: '📨',
    host: 'smtp.office365.com',
    port: 587,
    tls: true,
    instructions: [
      'Sign in to your Microsoft account at account.microsoft.com.',
      'Go to Security → Advanced security options.',
      'If 2FA is enabled, create an App password under "App passwords".',
      'Your SMTP username is your full Outlook/Microsoft email address.',
      'Use your account password (or the app password if 2FA is on).',
    ],
  },
  {
    name: 'Zoho Mail',
    logo: '✉️',
    host: 'smtp.zoho.com',
    port: 587,
    tls: true,
    instructions: [
      'Log in to Zoho Mail at mail.zoho.com.',
      'Go to Settings → Mail Accounts → SMTP.',
      'Enable SMTP access for your account.',
      'Your SMTP username is your full Zoho email address.',
      'Use your Zoho account password (or generate an App-specific password).',
    ],
  },
  {
    name: 'Custom SMTP',
    logo: '⚙️',
    host: '',
    port: 587,
    tls: true,
    instructions: [
      'Enter the SMTP server host and port provided by your email service.',
      'Enter the username and password for SMTP authentication.',
      'Most servers use port 587 with TLS enabled.',
      'Contact your email provider if you need help with settings.',
    ],
  },
];

/* ── Types ── */
interface SmtpFormState {
  host: string;
  port: string;
  username: string;
  password: string;
  from_email: string;
  from_name: string;
  use_tls: boolean;
}

const INITIAL_STATE: SmtpFormState = {
  host: '',
  port: '587',
  username: '',
  password: '',
  from_email: '',
  from_name: 'Nova Smart Library',
  use_tls: true,
};

const FIELD_KEY_MAP: Record<string, keyof SmtpFormState> = {
  'smtp.host': 'host',
  'smtp.port': 'port',
  'smtp.username': 'username',
  'smtp.password': 'password',
  'smtp.from_email': 'from_email',
  'smtp.from_name': 'from_name',
  'smtp.use_tls': 'use_tls',
};

export default function AdminSmtpPage() {
  useDocumentTitle('Email / SMTP Configuration');

  const [form, setForm] = useState<SmtpFormState>(INITIAL_STATE);
  const [selectedPreset, setSelectedPreset] = useState<ProviderPreset | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const [configStatus, setConfigStatus] = useState<'unconfigured' | 'configured' | 'unknown'>('unknown');

  const { data, loading, refetch } = useQuery(GET_SYSTEM_SETTINGS, {
    variables: { category: 'EMAIL' },
  });

  const [updateSetting, { loading: saving }] = useMutation(UPDATE_SYSTEM_SETTING);
  const [syncDefaults] = useMutation(SYNC_DEFAULT_SETTINGS);
  const [sendTestEmailMut, { loading: sending }] = useMutation(SEND_TEST_EMAIL);

  // Load current settings into form
  useEffect(() => {
    if (!data?.systemSettings) return;
    const next = { ...INITIAL_STATE };
    let hasHost = false;
    for (const s of data.systemSettings) {
      const field = FIELD_KEY_MAP[s.key];
      if (!field) continue;
      const val = s.isSensitive ? '' : s.value; // Don't populate masked values
      if (field === 'use_tls') {
        (next as any)[field] = ['true', '1', 'yes'].includes(val.toLowerCase());
      } else {
        (next as any)[field] = val;
      }
      if (field === 'host' && val) hasHost = true;
    }
    setForm(next);
    setConfigStatus(hasHost ? 'configured' : 'unconfigured');
    setHasChanges(false);
  }, [data]);

  const updateField = useCallback((field: keyof SmtpFormState, value: string | boolean) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
  }, []);

  const applyPreset = useCallback((preset: ProviderPreset) => {
    setSelectedPreset(preset);
    setForm(prev => ({
      ...prev,
      host: preset.host,
      port: String(preset.port),
      use_tls: preset.tls,
    }));
    setHasChanges(true);
  }, []);

  /* Save all SMTP settings */
  const handleSave = async () => {
    try {
      // First ensure defaults exist
      await syncDefaults();

      const updates = [
        { key: 'smtp.host', value: form.host },
        { key: 'smtp.port', value: form.port },
        { key: 'smtp.username', value: form.username },
        { key: 'smtp.from_email', value: form.from_email },
        { key: 'smtp.from_name', value: form.from_name },
        { key: 'smtp.use_tls', value: form.use_tls ? 'true' : 'false' },
      ];

      // Only update password if the user actually typed something
      if (form.password) {
        updates.push({ key: 'smtp.password', value: form.password });
      }

      for (const { key, value } of updates) {
        await updateSetting({ variables: { key, value } });
      }

      toast.success('SMTP settings saved successfully!');
      setHasChanges(false);
      setConfigStatus('configured');
      refetch();
    } catch (err) {
      toast.error(extractGqlError(err));
    }
  };

  /* Send test email */
  const handleTestEmail = async () => {
    if (!testEmail) {
      toast.error('Please enter an email address to send the test to.');
      return;
    }
    try {
      const { data: result } = await sendTestEmailMut({ variables: { toEmail: testEmail } });
      if (result?.sendTestEmail?.success) {
        toast.success(result.sendTestEmail.message, { duration: 5000 });
      } else {
        const detail = result?.sendTestEmail?.message || 'Test failed — unknown error.';
        toast.error(detail, { duration: 8000 });
      }
    } catch (err) {
      toast.error(extractGqlError(err), { duration: 8000 });
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg">
              <EnvelopeIcon className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-nova-text">Email Configuration</h1>
              <p className="text-sm text-nova-text-secondary">
                Configure SMTP settings so Nova can send emails (password resets, notifications, etc.)
              </p>
            </div>
          </div>
        </div>
        <Badge variant={configStatus === 'configured' ? 'success' : 'warning'}>
          {configStatus === 'configured' ? 'Configured' : 'Not configured'}
        </Badge>
      </div>

      {/* ── Step 1: Choose provider ── */}
      <Card>
        <div className="p-6">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
              1
            </div>
            <h2 className="text-lg font-semibold text-nova-text">Choose your email provider</h2>
          </div>
          <p className="mb-4 text-sm text-nova-text-secondary">
            Select your email provider to auto-fill server settings, or choose Custom for manual configuration.
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {PRESETS.map(preset => (
              <button
                key={preset.name}
                onClick={() => applyPreset(preset)}
                className={`group relative flex flex-col items-center gap-2 rounded-xl border-2 p-4 text-center transition-all duration-200 hover:shadow-md ${
                  selectedPreset?.name === preset.name
                    ? 'border-blue-500 bg-blue-50 shadow-sm dark:border-blue-400 dark:bg-blue-900/20'
                    : 'border-nova-border bg-nova-surface hover:border-blue-300 dark:hover:border-blue-600'
                }`}
              >
                <span className="text-2xl">{preset.logo}</span>
                <span className="text-sm font-medium text-nova-text">{preset.name}</span>
                {selectedPreset?.name === preset.name && (
                  <CheckCircleIcon className="absolute right-2 top-2 h-5 w-5 text-blue-500" />
                )}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* ── Step 2: Instructions ── */}
      {selectedPreset && (
        <Card>
          <div className="border-b border-nova-border bg-amber-50/50 p-4 dark:bg-amber-900/10">
            <div className="flex items-start gap-3">
              <LightBulbIcon className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600" />
              <div>
                <h3 className="font-semibold text-amber-800 dark:text-amber-300">
                  Setup Guide — {selectedPreset.name}
                </h3>
                <p className="mt-1 text-xs text-amber-700 dark:text-amber-400">
                  Follow these steps to get your SMTP credentials:
                </p>
              </div>
            </div>
          </div>
          <div className="p-6">
            <ol className="space-y-3">
              {selectedPreset.instructions.map((step, i) => (
                <li key={i} className="flex gap-3 text-sm text-nova-text-secondary">
                  <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                    {i + 1}
                  </span>
                  <span className="pt-0.5">{step}</span>
                </li>
              ))}
            </ol>
          </div>
        </Card>
      )}

      {/* ── Step 3: SMTP Settings form ── */}
      <Card>
        <div className="p-6">
          <div className="mb-6 flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
              {selectedPreset ? '3' : '2'}
            </div>
            <h2 className="text-lg font-semibold text-nova-text">SMTP Server Settings</h2>
          </div>

          <div className="space-y-6">
            {/* Server row */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-nova-text">
                  SMTP Host <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <ServerStackIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-nova-text-secondary" />
                  <input
                    type="text"
                    value={form.host}
                    onChange={e => updateField('host', e.target.value)}
                    placeholder="smtp.gmail.com"
                    className="w-full rounded-lg border border-nova-border bg-nova-surface py-2.5 pl-10 pr-3 text-sm text-nova-text placeholder:text-nova-text-secondary/50 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-nova-text">
                  Port <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={form.port}
                  onChange={e => updateField('port', e.target.value)}
                  placeholder="587"
                  className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2.5 text-sm text-nova-text placeholder:text-nova-text-secondary/50 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
                <p className="mt-1 text-xs text-nova-text-secondary">587 (TLS) or 465 (SSL)</p>
              </div>
            </div>

            {/* Auth row */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-nova-text">
                  Username <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <EnvelopeIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-nova-text-secondary" />
                  <input
                    type="text"
                    value={form.username}
                    onChange={e => updateField('username', e.target.value)}
                    placeholder="library@gmail.com"
                    className="w-full rounded-lg border border-nova-border bg-nova-surface py-2.5 pl-10 pr-3 text-sm text-nova-text placeholder:text-nova-text-secondary/50 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <p className="mt-1 text-xs text-nova-text-secondary">Usually your full email address</p>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-nova-text">
                  Password / App Password <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <KeyIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-nova-text-secondary" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={form.password}
                    onChange={e => updateField('password', e.target.value)}
                    placeholder="Enter app password"
                    className="w-full rounded-lg border border-nova-border bg-nova-surface py-2.5 pl-10 pr-10 text-sm text-nova-text placeholder:text-nova-text-secondary/50 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-blue-600 hover:text-blue-500"
                  >
                    {showPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
                <p className="mt-1 text-xs text-nova-text-secondary">
                  Use an App Password if 2FA is enabled (leave blank to keep existing)
                </p>
              </div>
            </div>

            {/* Sender row */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-nova-text">
                  Sender Email <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <PaperAirplaneIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-nova-text-secondary" />
                  <input
                    type="email"
                    value={form.from_email}
                    onChange={e => updateField('from_email', e.target.value)}
                    placeholder="noreply@yourlibrary.org"
                    className="w-full rounded-lg border border-nova-border bg-nova-surface py-2.5 pl-10 pr-3 text-sm text-nova-text placeholder:text-nova-text-secondary/50 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <p className="mt-1 text-xs text-nova-text-secondary">
                  The &quot;From&quot; address recipients will see
                </p>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-nova-text">
                  Sender Display Name
                </label>
                <input
                  type="text"
                  value={form.from_name}
                  onChange={e => updateField('from_name', e.target.value)}
                  placeholder="Nova Smart Library"
                  className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2.5 text-sm text-nova-text placeholder:text-nova-text-secondary/50 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
                <p className="mt-1 text-xs text-nova-text-secondary">
                  Shown as the sender name in email clients
                </p>
              </div>
            </div>

            {/* TLS toggle */}
            <div className="flex items-center justify-between rounded-lg border border-nova-border bg-nova-surface/50 p-4">
              <div className="flex items-center gap-3">
                <ShieldCheckIcon className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm font-medium text-nova-text">TLS Encryption</p>
                  <p className="text-xs text-nova-text-secondary">Recommended for secure email delivery (port 587)</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => updateField('use_tls', !form.use_tls)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  form.use_tls ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform ${
                    form.use_tls ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Save button */}
            <div className="flex items-center gap-3 border-t border-nova-border pt-4">
              <Button
                onClick={handleSave}
                isLoading={saving}
                disabled={!hasChanges || saving}
                size="lg"
                className="shadow-lg shadow-blue-500/20"
              >
                <CheckCircleIcon className="mr-2 h-5 w-5" />
                Save SMTP Settings
              </Button>
              {hasChanges && (
                <span className="text-xs text-amber-600 dark:text-amber-400">
                  You have unsaved changes
                </span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* ── Step 4: Test email ── */}
      <Card>
        <div className="p-6">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-green-100 text-sm font-bold text-green-700 dark:bg-green-900/40 dark:text-green-300">
              {selectedPreset ? '4' : '3'}
            </div>
            <h2 className="text-lg font-semibold text-nova-text">Test your configuration</h2>
          </div>
          <p className="mb-4 text-sm text-nova-text-secondary">
            Send a test email to verify everything works. Make sure you&apos;ve saved your settings first.
          </p>

          <div className="flex gap-3">
            <div className="relative flex-1">
              <EnvelopeIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-nova-text-secondary" />
              <input
                type="email"
                value={testEmail}
                onChange={e => setTestEmail(e.target.value)}
                placeholder="your@email.com"
                className="w-full rounded-lg border border-nova-border bg-nova-surface py-2.5 pl-10 pr-3 text-sm text-nova-text placeholder:text-nova-text-secondary/50 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
            <Button
              onClick={handleTestEmail}
              isLoading={sending}
              disabled={sending || !testEmail || configStatus !== 'configured'}
              variant="outline"
            >
              <PaperAirplaneIcon className="mr-2 h-4 w-4" />
              Send Test
            </Button>
          </div>

          {configStatus !== 'configured' && (
            <p className="mt-2 flex items-center gap-1 text-xs text-amber-600">
              <ExclamationTriangleIcon className="h-3.5 w-3.5" />
              Save your SMTP settings before testing.
            </p>
          )}
        </div>
      </Card>

      {/* ── Help section ── */}
      <Card>
        <div className="p-6">
          <div className="mb-4 flex items-center gap-2">
            <QuestionMarkCircleIcon className="h-5 w-5 text-nova-text-secondary" />
            <h2 className="text-lg font-semibold text-nova-text">Troubleshooting</h2>
          </div>
          <div className="space-y-4 text-sm text-nova-text-secondary">
            <div className="rounded-lg border border-nova-border bg-nova-surface/50 p-4">
              <p className="mb-2 font-medium text-nova-text">Common issues:</p>
              <ul className="list-inside list-disc space-y-2">
                <li>
                  <strong>Authentication failed</strong> — Make sure you&apos;re using an{' '}
                  <em>App Password</em>, not your regular account password (especially for Gmail with 2FA).
                </li>
                <li>
                  <strong>Connection timeout</strong> — Verify the host and port are correct. Port 587 with TLS is the most common setup.
                </li>
                <li>
                  <strong>Email not received</strong> — Check your spam/junk folder. Some providers may delay first-time emails.
                </li>
                <li>
                  <strong>&quot;Less secure apps&quot; (Gmail)</strong> — Google removed this option.
                  You <em>must</em> use App Passwords with 2-Step Verification enabled.
                </li>
              </ul>
            </div>
            <div className="flex items-start gap-2 rounded-lg bg-blue-50 p-3 dark:bg-blue-900/20">
              <InformationCircleIcon className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600" />
              <p className="text-xs text-blue-700 dark:text-blue-300">
                <strong>Tip:</strong> Your SMTP password is stored securely and never displayed after saving.
                Leave the password field blank when editing other settings to keep your existing password.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
