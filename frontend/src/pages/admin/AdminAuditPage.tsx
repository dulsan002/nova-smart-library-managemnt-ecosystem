/**
 * AdminAuditPage — audit logs and security events viewer.
 */

import { useState } from 'react';
import { useQuery } from '@apollo/client';
import {
  ShieldCheckIcon,
  DocumentMagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { AUDIT_LOGS, SECURITY_EVENTS } from '@/graphql/queries/governance';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Select } from '@/components/ui/Select';
import { Tabs } from '@/components/ui/Tabs';
import { Pagination } from '@/components/ui/Pagination';
import { LoadingOverlay } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatDate } from '@/lib/utils';
import { ITEMS_PER_PAGE } from '@/lib/constants';

const severityOptions = [
  { value: '', label: 'All severities' },
  { value: 'CRITICAL', label: 'Critical' },
  { value: 'HIGH', label: 'High' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'LOW', label: 'Low' },
  { value: 'INFO', label: 'Info' },
];

const resolvedOptions = [
  { value: '', label: 'All' },
  { value: 'false', label: 'Unresolved' },
  { value: 'true', label: 'Resolved' },
];

const sevBadge = (sev: string) => {
  const map: Record<string, 'danger' | 'warning' | 'info' | 'neutral'> = {
    CRITICAL: 'danger',
    HIGH: 'danger',
    MEDIUM: 'warning',
    LOW: 'info',
    INFO: 'neutral',
  };
  return map[sev] ?? ('neutral' as any);
};

export default function AdminAuditPage() {
  useDocumentTitle('Audit & Security');

  const [activeTab, setActiveTab] = useState(0);

  // Audit log state
  const [logAfter, setLogAfter] = useState<string | null>(null);
  const [logCursorStack, setLogCursorStack] = useState<string[]>([]);
  const [logActionFilter, setLogActionFilter] = useState('');

  // Security event state
  const [sevFilter, setSevFilter] = useState('');
  const [resolvedFilter, setResolvedFilter] = useState('');

  // Queries
  const {
    data: logData,
    loading: logLoading,
  } = useQuery(AUDIT_LOGS, {
    variables: {
      first: ITEMS_PER_PAGE,
      after: logAfter,
      action: logActionFilter || undefined,
    },
    fetchPolicy: 'cache-and-network',
    skip: activeTab !== 0,
  });

  const {
    data: secData,
    loading: secLoading,
  } = useQuery(SECURITY_EVENTS, {
    variables: {
      severity: sevFilter || undefined,
      resolved: resolvedFilter ? resolvedFilter === 'true' : undefined,
      limit: 50,
    },
    fetchPolicy: 'cache-and-network',
    skip: activeTab !== 1,
  });

  const logEdges = (logData?.auditLogs?.edges ?? []).map((e: any) => e.node);
  const logPageInfo = logData?.auditLogs?.pageInfo;
  const secEvents = secData?.securityEvents ?? [];

  const tabs = [
    { label: 'Audit Logs', content: null },
    {
      label: 'Security Events',
      badge: secEvents.filter((e: any) => !e.resolved).length
        ? String(secEvents.filter((e: any) => !e.resolved).length)
        : undefined,
      content: null,
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold text-nova-text">Audit &amp; Security</h1>

      <Tabs tabs={tabs} active={activeTab} onChange={setActiveTab} />

      {/* ─── Audit Logs ─────── */}
      {activeTab === 0 && (
        <>
          <div className="flex gap-3">
            <div className="w-44">
              <Select
                value={logActionFilter}
                onChange={(v) => {
                  setLogActionFilter(v);
                  setLogAfter(null);
                  setLogCursorStack([]);
                }}
                options={[
                  { value: '', label: 'All actions' },
                  { value: 'CREATE', label: 'Create' },
                  { value: 'UPDATE', label: 'Update' },
                  { value: 'DELETE', label: 'Delete' },
                  { value: 'LOGIN', label: 'Login' },
                  { value: 'LOGOUT', label: 'Logout' },
                ]}
              />
            </div>
          </div>

          {logLoading && !logData ? (
            <LoadingOverlay />
          ) : logEdges.length === 0 ? (
            <EmptyState
              icon={<DocumentMagnifyingGlassIcon />}
              title="No audit logs"
              description="No matching audit log entries found."
            />
          ) : (
            <Card padding="none">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-nova-border text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                      <th className="px-4 py-3">Timestamp</th>
                      <th className="px-4 py-3">Action</th>
                      <th className="px-4 py-3">Resource</th>
                      <th className="px-4 py-3">Actor</th>
                      <th className="px-4 py-3">IP</th>
                      <th className="px-4 py-3">Changes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-nova-border">
                    {logEdges.map((log: any) => (
                      <tr key={log.id} className="hover:bg-nova-surface-hover transition-colors">
                        <td className="px-4 py-3 whitespace-nowrap text-xs text-nova-text-muted">
                          {formatDate(log.createdAt)}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="info" size="sm">
                            {log.action}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-nova-text">
                          <span className="block text-xs font-medium">{log.resourceType}</span>
                          <span className="font-mono text-[10px] text-nova-text-muted">
                            {log.resourceId?.slice(0, 8)}…
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-secondary">
                          {log.actorEmail ?? log.actorId?.slice(0, 8)}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-nova-text-muted">
                          {log.ipAddress ?? '—'}
                        </td>
                        <td className="px-4 py-3 max-w-[200px]">
                          {log.description ? (
                            <pre className="truncate text-[10px] text-nova-text-muted">
                              {log.description.slice(0, 80)}
                            </pre>
                          ) : (
                            <span className="text-xs text-nova-text-muted">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {logPageInfo && (
            <Pagination
              pageInfo={{ ...logPageInfo, hasPreviousPage: logCursorStack.length > 0 }}
              onNext={() => {
                setLogCursorStack((prev) => [...prev, logAfter ?? '']);
                setLogAfter(logPageInfo.endCursor);
              }}
              onPrev={() => {
                const stack = [...logCursorStack];
                const prev = stack.pop() ?? '';
                setLogCursorStack(stack);
                setLogAfter(prev === '' ? null : prev);
              }}
            />
          )}
        </>
      )}

      {/* ─── Security Events ─────── */}
      {activeTab === 1 && (
        <>
          <div className="flex flex-wrap gap-3">
            <div className="w-44">
              <Select
                value={sevFilter}
                onChange={setSevFilter}
                options={severityOptions}
              />
            </div>
            <div className="w-36">
              <Select
                value={resolvedFilter}
                onChange={setResolvedFilter}
                options={resolvedOptions}
              />
            </div>
          </div>

          {secLoading && !secData ? (
            <LoadingOverlay />
          ) : secEvents.length === 0 ? (
            <EmptyState
              icon={<ShieldCheckIcon />}
              title="No security events"
              description="No matching security events found."
            />
          ) : (
            <Card padding="none">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-nova-border text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                      <th className="px-4 py-3">Timestamp</th>
                      <th className="px-4 py-3">Event Type</th>
                      <th className="px-4 py-3">Severity</th>
                      <th className="px-4 py-3">Description</th>
                      <th className="px-4 py-3">IP</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-nova-border">
                    {secEvents.map((ev: any) => (
                      <tr key={ev.id} className="hover:bg-nova-surface-hover transition-colors">
                        <td className="px-4 py-3 whitespace-nowrap text-xs text-nova-text-muted">
                          {formatDate(ev.createdAt)}
                        </td>
                        <td className="px-4 py-3 text-xs font-medium text-nova-text">
                          {ev.eventType.replace(/_/g, ' ')}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={sevBadge(ev.severity)} size="sm">
                            {ev.severity}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 max-w-[300px] truncate text-xs text-nova-text-secondary">
                          {ev.description}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-nova-text-muted">
                          {ev.ipAddress ?? '—'}
                        </td>
                        <td className="px-4 py-3">
                          {ev.resolved ? (
                            <Badge variant="success" size="sm">
                              Resolved
                            </Badge>
                          ) : (
                            <Badge variant="danger" size="sm" dot>
                              Open
                            </Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
