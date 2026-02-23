/**
 * AdminEmployeesPage — Premium enterprise HR management with 360° panoramic view,
 * departments, job vacancies, applications, icon‑only action buttons, and rich data cards.
 */

import { useState, useCallback, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useQuery, useLazyQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  MagnifyingGlassIcon,
  UserPlusIcon,
  EyeIcon,
  PencilSquareIcon,
  ArrowPathIcon,
  EllipsisVerticalIcon,
  BuildingOfficeIcon,
  BriefcaseIcon,
  UserGroupIcon,
  ClockIcon,
  CalendarDaysIcon,
  DocumentTextIcon,
  CurrencyDollarIcon,
  PhoneIcon,
  EnvelopeIcon,
  CheckCircleIcon,
  XCircleIcon,
  PlusCircleIcon,
  IdentificationIcon,
  MapPinIcon,
  AcademicCapIcon,
  NoSymbolIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle, useDebounce } from '@/hooks';
import {
  GET_DEPARTMENTS, GET_EMPLOYEES, GET_EMPLOYEE,
  GET_JOB_VACANCIES, GET_JOB_APPLICATIONS, GET_HR_STATS,
} from '@/graphql/queries/hr';
import { GET_USERS } from '@/graphql/queries/admin';
import {
  CREATE_DEPARTMENT, CREATE_EMPLOYEE, UPDATE_EMPLOYEE,
  CREATE_JOB_VACANCY, UPDATE_JOB_VACANCY, UPDATE_APPLICATION_STATUS,
} from '@/graphql/mutations/hr';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Select } from '@/components/ui/Select';
import { Avatar } from '@/components/ui/Avatar';
import { Modal, ModalBody, ModalFooter } from '@/components/ui/Modal';
import { Tabs } from '@/components/ui/Tabs';
import { Tooltip } from '@/components/ui/Tooltip';
import { Dropdown } from '@/components/ui/Dropdown';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { LoadingOverlay, Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { extractGqlError, formatDate, formatCurrency } from '@/lib/utils';

/* ═══════════════════════════════════════════════════
   Constants & Helpers
   ═══════════════════════════════════════════════════ */

const EMP_STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'ON_LEAVE', label: 'On Leave' },
  { value: 'TERMINATED', label: 'Terminated' },
  { value: 'PROBATION', label: 'Probation' },
];

const EMPLOYMENT_TYPE_OPTIONS = [
  { value: 'FULL_TIME', label: 'Full-Time' },
  { value: 'PART_TIME', label: 'Part-Time' },
  { value: 'CONTRACT', label: 'Contract' },
  { value: 'INTERN', label: 'Intern' },
];

const VACANCY_STATUS = [
  { value: '', label: 'All Statuses' },
  { value: 'OPEN', label: 'Open' },
  { value: 'CLOSED', label: 'Closed' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'ON_HOLD', label: 'On Hold' },
];

const APP_STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'SUBMITTED', label: 'Submitted' },
  { value: 'UNDER_REVIEW', label: 'Under Review' },
  { value: 'SHORTLISTED', label: 'Shortlisted' },
  { value: 'INTERVIEW', label: 'Interview' },
  { value: 'OFFERED', label: 'Offered' },
  { value: 'ACCEPTED', label: 'Accepted' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'WITHDRAWN', label: 'Withdrawn' },
];

const EXPERIENCE_LEVEL_OPTIONS = [
  { value: 'ENTRY', label: 'Entry Level' },
  { value: 'MID', label: 'Mid Level' },
  { value: 'SENIOR', label: 'Senior' },
  { value: 'LEAD', label: 'Lead' },
];

const empStatusColor = (s: string) => {
  switch (s) {
    case 'ACTIVE': return 'success';
    case 'ON_LEAVE': return 'warning';
    case 'PROBATION': return 'info';
    case 'TERMINATED': return 'danger';
    default: return 'neutral';
  }
};

const vacancyStatusColor = (s: string) => {
  switch (s) {
    case 'OPEN': return 'success';
    case 'CLOSED': return 'danger';
    case 'DRAFT': return 'neutral';
    case 'ON_HOLD': return 'warning';
    default: return 'neutral';
  }
};

const appStatusColor = (s: string) => {
  switch (s) {
    case 'SUBMITTED': return 'warning';
    case 'UNDER_REVIEW': return 'info';
    case 'SHORTLISTED': return 'primary';
    case 'INTERVIEW': return 'info';
    case 'OFFERED': return 'success';
    case 'ACCEPTED': return 'success';
    case 'REJECTED': return 'danger';
    case 'WITHDRAWN': return 'neutral';
    default: return 'neutral';
  }
};

/* ── Stat Mini Card ────────────────────── */
function StatMini({ icon, label, value, color = 'primary' }: { icon: React.ReactNode; label: string; value: string | number; color?: string }) {
  const bgMap: Record<string, string> = {
    primary: 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400',
    success: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    warning: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400',
    danger: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400',
    info: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
  };
  return (
    <div className="flex items-center gap-3 rounded-xl border border-nova-border bg-nova-surface p-4 transition-shadow hover:shadow-md">
      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${bgMap[color] ?? bgMap.primary}`}>{icon}</div>
      <div>
        <p className="text-2xl font-bold text-nova-text">{value}</p>
        <p className="text-xs text-nova-text-muted">{label}</p>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════════════ */

export default function AdminEmployeesPage() {
  useDocumentTitle('HR Management');

  const location = useLocation();
  const isJobsRoute = location.pathname === '/admin/jobs';

  /* ── Top‑level tab ─────────────────────── */
  const [mainTab, setMainTab] = useState(isJobsRoute ? 2 : 0);

  // Sync tab when route changes (e.g. navigating from Employees to Jobs)
  useEffect(() => {
    setMainTab(isJobsRoute ? 2 : 0);
  }, [isJobsRoute]);

  /* ── Employee list state ───────────────── */
  const [empSearch, setEmpSearch] = useState('');
  const [empStatusFilter, setEmpStatusFilter] = useState('');
  const [empDeptFilter, setEmpDeptFilter] = useState('');
  const debouncedEmpSearch = useDebounce(empSearch, 400);

  /* ── View / Edit modals ────────────────── */
  const [viewEmpId, setViewEmpId] = useState<string | null>(null);
  const [editEmpId, setEditEmpId] = useState<string | null>(null);
  const [viewTab, setViewTab] = useState(0);

  /* ── Create modals ─────────────────────── */
  const [showCreateDept, setShowCreateDept] = useState(false);
  const [showCreateEmp, setShowCreateEmp] = useState(false);
  const [showCreateVacancy, setShowCreateVacancy] = useState(false);

  /* ── Confirm ───────────────────────────── */
  const [terminateTarget, setTerminateTarget] = useState<{ id: string; name: string } | null>(null);

  /* ── Vacancy/Application filters ───────── */
  const [vacStatusFilter, setVacStatusFilter] = useState('');
  const [appVacancyFilter, setAppVacancyFilter] = useState('');
  const [appStatusFilter, setAppStatusFilter] = useState('');

  /* ── Edit form state ───────────────────── */
  const [editForm, setEditForm] = useState({
    departmentId: '', jobTitle: '', employmentType: '', status: '',
    salary: '', reportsToId: '', terminationDate: '',
  });

  /* ── Create forms ──────────────────────── */
  const [deptForm, setDeptForm] = useState({ name: '', code: '', description: '' });
  const [empForm, setEmpForm] = useState({
    userId: '', employeeId: '', departmentId: '', jobTitle: '',
    hireDate: '', employmentType: 'FULL_TIME', salary: '', reportsToId: '',
  });
  const [vacForm, setVacForm] = useState({
    title: '', departmentId: '', description: '', requirements: '',
    responsibilities: '', experienceLevel: 'MID', employmentType: 'FULL_TIME',
    positionsAvailable: '1', salaryRangeMin: '', salaryRangeMax: '',
    closingDate: '', location: '',
  });

  /* ══════════════════════════════════════════
     Queries
     ══════════════════════════════════════════ */

  const { data: statsData } = useQuery(GET_HR_STATS, { fetchPolicy: 'cache-and-network' });
  const stats = statsData?.hrStats;

  const { data: deptsData, refetch: refetchDepts } = useQuery(GET_DEPARTMENTS, { fetchPolicy: 'cache-and-network' });
  const departments = deptsData?.departments ?? [];

  const { data: empsData, loading: empsLoading, refetch: refetchEmps } = useQuery(GET_EMPLOYEES, {
    variables: {
      search: debouncedEmpSearch || undefined,
      status: empStatusFilter || undefined,
      departmentId: empDeptFilter || undefined,
      limit: 50,
    },
    fetchPolicy: 'cache-and-network',
  });
  const employees = empsData?.employees ?? [];

  const { data: vacsData, loading: vacsLoading, refetch: refetchVacs } = useQuery(GET_JOB_VACANCIES, {
    variables: { status: vacStatusFilter || undefined, limit: 50 },
    fetchPolicy: 'cache-and-network',
  });
  const vacancies = vacsData?.jobVacancies ?? [];

  const { data: appsData, loading: appsLoading, refetch: refetchApps } = useQuery(GET_JOB_APPLICATIONS, {
    variables: {
      vacancyId: appVacancyFilter || undefined,
      status: appStatusFilter || undefined,
      limit: 50,
    },
    fetchPolicy: 'cache-and-network',
  });
  const applications = appsData?.jobApplications ?? [];

  /* For user dropdown when creating employee */
  const { data: usersData } = useQuery(GET_USERS, {
    variables: { first: 100 },
    fetchPolicy: 'cache-and-network',
  });
  const userOptions = (usersData?.users?.edges ?? [])
    .filter((e: any) => e?.node)
    .map(({ node: u }: any) => ({ value: u.id, label: `${u.firstName} ${u.lastName} (${u.email})` }));

  /* ── 360° lazy queries ─────────────────── */
  const [fetchEmployee, { data: empDetailData, loading: empDetailLoading }] = useLazyQuery(GET_EMPLOYEE, {
    fetchPolicy: 'network-only',
    onError: (e) => toast.error(extractGqlError(e)),
  });
  const viewEmp = empDetailData?.employee;

  /* ══════════════════════════════════════════
     Mutations
     ══════════════════════════════════════════ */

  const [createDepartment, { loading: creatingDept }] = useMutation(CREATE_DEPARTMENT, {
    onCompleted: () => { toast.success('Department created'); setShowCreateDept(false); setDeptForm({ name: '', code: '', description: '' }); refetchDepts(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [createEmployee, { loading: creatingEmp }] = useMutation(CREATE_EMPLOYEE, {
    onCompleted: () => { toast.success('Employee created'); setShowCreateEmp(false); refetchEmps(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [updateEmployee, { loading: updatingEmp }] = useMutation(UPDATE_EMPLOYEE, {
    onCompleted: () => { toast.success('Employee updated'); setEditEmpId(null); refetchEmps(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [createJobVacancy, { loading: creatingVac }] = useMutation(CREATE_JOB_VACANCY, {
    onCompleted: () => { toast.success('Vacancy created'); setShowCreateVacancy(false); refetchVacs(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [updateJobVacancy] = useMutation(UPDATE_JOB_VACANCY, {
    onCompleted: () => { toast.success('Vacancy updated'); refetchVacs(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const [updateAppStatus] = useMutation(UPDATE_APPLICATION_STATUS, {
    onCompleted: () => { toast.success('Application updated'); refetchApps(); },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  /* ══════════════════════════════════════════
     Callbacks
     ══════════════════════════════════════════ */

  const deptOptions = [{ value: '', label: 'All Departments' }, ...departments.map((d: any) => ({ value: d.id, label: d.name }))];
  const deptCreateOptions = departments.map((d: any) => ({ value: d.id, label: d.name }));
  const empOptions = employees.map((e: any) => ({ value: e.id, label: e.fullName }));

  const openView = useCallback((empId: string) => {
    setViewEmpId(empId);
    setViewTab(0);
    fetchEmployee({ variables: { id: empId } });
  }, [fetchEmployee]);

  const [fetchEditEmp, { loading: editEmpLoading }] = useLazyQuery(GET_EMPLOYEE, {
    fetchPolicy: 'network-only',
    onCompleted: (d: any) => {
      const e = d.employee;
      if (e) {
        setEditForm({
          departmentId: e.department?.id ?? '',
          jobTitle: e.jobTitle ?? '',
          employmentType: e.employmentType ?? '',
          status: e.status ?? '',
          salary: e.salary?.toString() ?? '',
          reportsToId: e.reportsTo?.id ?? '',
          terminationDate: e.terminationDate ?? '',
        });
      }
    },
    onError: (e) => toast.error(extractGqlError(e)),
  });

  const openEdit = useCallback((empId: string) => {
    setEditEmpId(empId);
    fetchEditEmp({ variables: { id: empId } });
  }, [fetchEditEmp]);

  const handleEditSubmit = useCallback((ev: React.FormEvent) => {
    ev.preventDefault();
    if (!editEmpId) return;
    updateEmployee({
      variables: {
        id: editEmpId,
        departmentId: editForm.departmentId || undefined,
        jobTitle: editForm.jobTitle || undefined,
        employmentType: editForm.employmentType || undefined,
        status: editForm.status || undefined,
        salary: editForm.salary ? parseFloat(editForm.salary) : undefined,
        reportsToId: editForm.reportsToId || undefined,
        terminationDate: editForm.terminationDate || undefined,
      },
    });
  }, [editEmpId, editForm, updateEmployee]);

  const handleTerminate = useCallback(() => {
    if (!terminateTarget) return;
    updateEmployee({
      variables: { id: terminateTarget.id, status: 'TERMINATED', terminationDate: new Date().toISOString().split('T')[0] },
    });
    setTerminateTarget(null);
  }, [terminateTarget, updateEmployee]);

  const handleCreateDept = useCallback((ev: React.FormEvent) => {
    ev.preventDefault();
    createDepartment({ variables: { name: deptForm.name, code: deptForm.code, description: deptForm.description || undefined } });
  }, [deptForm, createDepartment]);

  const handleCreateEmp = useCallback((ev: React.FormEvent) => {
    ev.preventDefault();
    createEmployee({
      variables: {
        userId: empForm.userId,
        employeeId: empForm.employeeId,
        departmentId: empForm.departmentId,
        jobTitle: empForm.jobTitle,
        hireDate: empForm.hireDate,
        employmentType: empForm.employmentType || undefined,
        salary: empForm.salary ? parseFloat(empForm.salary) : undefined,
        reportsToId: empForm.reportsToId || undefined,
      },
    });
  }, [empForm, createEmployee]);

  const handleCreateVacancy = useCallback((ev: React.FormEvent) => {
    ev.preventDefault();
    createJobVacancy({
      variables: {
        title: vacForm.title,
        departmentId: vacForm.departmentId,
        description: vacForm.description,
        requirements: vacForm.requirements,
        responsibilities: vacForm.responsibilities || undefined,
        experienceLevel: vacForm.experienceLevel || undefined,
        employmentType: vacForm.employmentType || undefined,
        positionsAvailable: vacForm.positionsAvailable ? parseInt(vacForm.positionsAvailable) : undefined,
        salaryRangeMin: vacForm.salaryRangeMin ? parseFloat(vacForm.salaryRangeMin) : undefined,
        salaryRangeMax: vacForm.salaryRangeMax ? parseFloat(vacForm.salaryRangeMax) : undefined,
        closingDate: vacForm.closingDate || undefined,
        location: vacForm.location || undefined,
      },
    });
  }, [vacForm, createJobVacancy]);

  const refetchAll = useCallback(() => {
    refetchEmps();
    refetchDepts();
    refetchVacs();
    refetchApps();
  }, [refetchEmps, refetchDepts, refetchVacs, refetchApps]);

  /* ══════════════════════════════════════════
     360° View Tabs
     ══════════════════════════════════════════ */

  const viewTabs = [
    {
      label: 'Profile',
      icon: <IdentificationIcon className="h-4 w-4" />,
      content: empDetailLoading ? <div className="flex justify-center py-12"><Spinner /></div> : viewEmp ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatMini icon={<CalendarDaysIcon className="h-5 w-5" />} label="Years of Service" value={viewEmp.yearsOfService ?? 0} color="info" />
            <StatMini icon={<CurrencyDollarIcon className="h-5 w-5" />} label="Salary" value={viewEmp.salary ? formatCurrency(viewEmp.salary, viewEmp.salaryCurrency || 'USD') : '—'} color="success" />
            <StatMini icon={<UserGroupIcon className="h-5 w-5" />} label="Direct Reports" value={viewEmp.directReports?.length ?? 0} color="purple" />
            <StatMini icon={<BriefcaseIcon className="h-5 w-5" />} label="Type" value={viewEmp.employmentType?.replace(/_/g, ' ') ?? '—'} color="primary" />
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <Card className="p-5 space-y-4">
              <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest flex items-center gap-2">
                <IdentificationIcon className="h-4 w-4" /> Employee Details
              </h4>
              <div className="space-y-3 text-sm">
                {([
                  ['Full Name', viewEmp.fullName],
                  ['Employee ID', viewEmp.employeeId],
                  ['Email', viewEmp.user?.email ?? '—'],
                  ['Job Title', viewEmp.jobTitle ?? '—'],
                  ['Employment Type', viewEmp.employmentType?.replace(/_/g, ' ') ?? '—'],
                  ['Status', viewEmp.status ?? '—'],
                  ['Hire Date', viewEmp.hireDate ? formatDate(viewEmp.hireDate) : '—'],
                  ['Probation End', viewEmp.probationEndDate ? formatDate(viewEmp.probationEndDate) : '—'],
                  ['Termination Date', viewEmp.terminationDate ? formatDate(viewEmp.terminationDate) : '—'],
                ] as const).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50 last:border-0">
                    <span className="text-nova-text-muted">{k}</span>
                    <span className="font-medium text-nova-text">{v}</span>
                  </div>
                ))}
              </div>
            </Card>
            <Card className="p-5 space-y-4">
              <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest flex items-center gap-2">
                <CurrencyDollarIcon className="h-4 w-4" /> Compensation & Emergency
              </h4>
              <div className="space-y-3 text-sm">
                {([
                  ['Salary', viewEmp.salary ? `${formatCurrency(viewEmp.salary, viewEmp.salaryCurrency || 'USD')}/yr` : '—'],
                  ['Currency', viewEmp.salaryCurrency || '—'],
                  ['Emergency Contact', viewEmp.emergencyContactName || '—'],
                  ['Emergency Phone', viewEmp.emergencyContactPhone || '—'],
                ] as const).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50 last:border-0">
                    <span className="text-nova-text-muted">{k}</span>
                    <span className="font-medium text-nova-text">{v}</span>
                  </div>
                ))}
              </div>
              {viewEmp.notes && (
                <div className="pt-2">
                  <p className="text-xs font-bold text-nova-text-muted uppercase tracking-widest mb-2">Notes</p>
                  <p className="text-sm text-nova-text bg-nova-surface-hover rounded-lg p-3 whitespace-pre-line">{viewEmp.notes}</p>
                </div>
              )}
            </Card>
          </div>
        </div>
      ) : null,
    },
    {
      label: 'Organization',
      icon: <BuildingOfficeIcon className="h-4 w-4" />,
      content: empDetailLoading ? <div className="flex justify-center py-12"><Spinner /></div> : viewEmp ? (
        <div className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card className="p-5 space-y-4">
              <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest flex items-center gap-2">
                <BuildingOfficeIcon className="h-4 w-4" /> Department
              </h4>
              {viewEmp.department ? (
                <div className="space-y-3 text-sm">
                  <div className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50">
                    <span className="text-nova-text-muted">Department</span>
                    <span className="font-medium text-nova-text">{viewEmp.department.name}</span>
                  </div>
                  <div className="flex items-center justify-between py-1.5 border-b border-dashed border-nova-border/50">
                    <span className="text-nova-text-muted">Code</span>
                    <Badge variant="neutral" size="sm">{viewEmp.department.code}</Badge>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-nova-text-muted">No department assigned.</p>
              )}
              {viewEmp.reportsTo && (
                <div className="pt-3 border-t border-nova-border">
                  <p className="text-xs font-bold text-nova-text-muted uppercase tracking-widest mb-2">Reports To</p>
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-nova-surface-hover">
                    <Avatar name={viewEmp.reportsTo.fullName ?? '?'} size="sm" />
                    <div>
                      <p className="font-medium text-nova-text text-sm">{viewEmp.reportsTo.fullName}</p>
                      <p className="text-xs text-nova-text-muted">{viewEmp.reportsTo.jobTitle}</p>
                    </div>
                  </div>
                </div>
              )}
            </Card>
            <Card className="p-5 space-y-4">
              <h4 className="text-xs font-bold text-nova-text-muted uppercase tracking-widest flex items-center gap-2">
                <UserGroupIcon className="h-4 w-4" /> Direct Reports ({viewEmp.directReports?.length ?? 0})
              </h4>
              {viewEmp.directReports?.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {viewEmp.directReports.map((dr: any) => (
                    <div key={dr.id} className="flex items-center gap-3 p-3 rounded-lg bg-nova-surface-hover hover:ring-1 hover:ring-primary-500/30 transition-all cursor-pointer" onClick={() => openView(dr.id)}>
                      <Avatar name={dr.fullName ?? '?'} size="sm" />
                      <div>
                        <p className="font-medium text-nova-text text-sm">{dr.fullName}</p>
                        <p className="text-xs text-nova-text-muted">{dr.jobTitle}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-nova-text-muted">No direct reports.</p>
              )}
            </Card>
          </div>
        </div>
      ) : null,
    },
  ];

  /* ══════════════════════════════════════════
     Main Tabs Content
     ══════════════════════════════════════════ */

  const mainTabs = [
    {
      label: 'Employees',
      icon: <UserGroupIcon className="h-4 w-4" />,
      badge: stats?.totalEmployees ?? undefined,
      content: (
        <div className="space-y-5">
          {/* Filters */}
          <div className="flex flex-wrap gap-3">
            <div className="w-64">
              <Input placeholder="Search employees…" value={empSearch} onChange={(e) => setEmpSearch(e.target.value)} leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />} />
            </div>
            <div className="w-40"><Select value={empStatusFilter} onChange={setEmpStatusFilter} options={EMP_STATUS_OPTIONS} /></div>
            <div className="w-48"><Select value={empDeptFilter} onChange={setEmpDeptFilter} options={deptOptions} /></div>
            <div className="ml-auto">
              <Button leftIcon={<UserPlusIcon className="h-4 w-4" />} onClick={() => {
                setEmpForm({ userId: '', employeeId: '', departmentId: '', jobTitle: '', hireDate: '', employmentType: 'FULL_TIME', salary: '', reportsToId: '' });
                setShowCreateEmp(true);
              }}>Add Employee</Button>
            </div>
          </div>

          {/* Table */}
          {empsLoading && employees.length === 0 ? <LoadingOverlay /> : employees.length === 0 ? (
            <EmptyState icon={<UserGroupIcon />} title="No employees found" description="Adjust your filters or add a new employee." />
          ) : (
            <Card padding="none">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-nova-border bg-nova-surface text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                      <th className="px-4 py-3">Employee</th>
                      <th className="px-4 py-3">Department</th>
                      <th className="px-4 py-3">Job Title</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Type</th>
                      <th className="px-4 py-3">Service</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-nova-border">
                    {employees.map((emp: any) => (
                      <tr key={emp.id} className="hover:bg-nova-surface-hover transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <Avatar name={emp.fullName ?? emp.user?.email ?? '?'} size="sm" src={emp.user?.avatarUrl} />
                            <div>
                              <p className="font-medium text-nova-text">{emp.fullName}</p>
                              <p className="text-xs text-nova-text-muted">{emp.employeeId}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="neutral" size="sm">{emp.department?.name ?? '—'}</Badge>
                        </td>
                        <td className="px-4 py-3 text-nova-text">{emp.jobTitle ?? '—'}</td>
                        <td className="px-4 py-3">
                          <Badge variant={empStatusColor(emp.status)} size="sm" dot>{emp.status}</Badge>
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">{emp.employmentType?.replace(/_/g, ' ') ?? '—'}</td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">{emp.yearsOfService != null ? `${emp.yearsOfService} yr${emp.yearsOfService !== 1 ? 's' : ''}` : '—'}</td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Tooltip content="360° View">
                              <Button variant="ghost" size="sm" onClick={() => openView(emp.id)} className="!px-2">
                                <EyeIcon className="h-4 w-4" />
                              </Button>
                            </Tooltip>
                            <Tooltip content="Edit Employee">
                              <Button variant="ghost" size="sm" onClick={() => openEdit(emp.id)} className="!px-2">
                                <PencilSquareIcon className="h-4 w-4" />
                              </Button>
                            </Tooltip>
                            <Dropdown
                              trigger={<Button variant="ghost" size="sm" className="!px-2"><EllipsisVerticalIcon className="h-4 w-4" /></Button>}
                              items={[
                                ...(emp.status !== 'TERMINATED' ? [{
                                  label: 'Terminate',
                                  icon: <NoSymbolIcon className="h-4 w-4" />,
                                  danger: true,
                                  onClick: () => setTerminateTarget({ id: emp.id, name: emp.fullName }),
                                }] : []),
                              ]}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      ),
    },
    {
      label: 'Departments',
      icon: <BuildingOfficeIcon className="h-4 w-4" />,
      badge: stats?.departmentsCount ?? undefined,
      content: (
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-nova-text-muted">{departments.length} department{departments.length !== 1 ? 's' : ''}</p>
            <Button leftIcon={<PlusCircleIcon className="h-4 w-4" />} onClick={() => { setDeptForm({ name: '', code: '', description: '' }); setShowCreateDept(true); }}>
              Add Department
            </Button>
          </div>
          {departments.length === 0 ? (
            <EmptyState icon={<BuildingOfficeIcon />} title="No departments" description="Create your first department." />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {departments.map((dept: any) => (
                <Card key={dept.id} className="p-5 space-y-3 hover:shadow-lg transition-shadow" hoverable>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/30 dark:to-primary-800/30 shadow-sm">
                        <BuildingOfficeIcon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                      </div>
                      <div>
                        <p className="font-bold text-nova-text">{dept.name}</p>
                        <Badge variant="neutral" size="xs">{dept.code}</Badge>
                      </div>
                    </div>
                    <Badge variant={dept.isActive ? 'success' : 'danger'} size="xs" dot>{dept.isActive ? 'Active' : 'Inactive'}</Badge>
                  </div>
                  {dept.description && <p className="text-xs text-nova-text-muted line-clamp-2">{dept.description}</p>}
                  <div className="flex items-center justify-between pt-2 border-t border-nova-border">
                    <span className="text-xs text-nova-text-muted flex items-center gap-1">
                      <UserGroupIcon className="h-3.5 w-3.5" /> {dept.employeeCount ?? 0} employees
                    </span>
                    {dept.head && (
                      <span className="text-xs text-nova-text-muted flex items-center gap-1">
                        <IdentificationIcon className="h-3.5 w-3.5" /> {dept.head.fullName}
                      </span>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      ),
    },
    {
      label: 'Vacancies',
      icon: <BriefcaseIcon className="h-4 w-4" />,
      badge: stats?.openVacancies ?? undefined,
      content: (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-3 items-center">
            <div className="w-40"><Select value={vacStatusFilter} onChange={setVacStatusFilter} options={VACANCY_STATUS} /></div>
            <div className="ml-auto">
              <Button leftIcon={<PlusCircleIcon className="h-4 w-4" />} onClick={() => {
                setVacForm({ title: '', departmentId: '', description: '', requirements: '', responsibilities: '', experienceLevel: 'MID', employmentType: 'FULL_TIME', positionsAvailable: '1', salaryRangeMin: '', salaryRangeMax: '', closingDate: '', location: '' });
                setShowCreateVacancy(true);
              }}>Post Vacancy</Button>
            </div>
          </div>
          {vacsLoading && vacancies.length === 0 ? <LoadingOverlay /> : vacancies.length === 0 ? (
            <EmptyState icon={<BriefcaseIcon />} title="No vacancies" description="Post a job to start recruiting." />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {vacancies.map((vac: any) => (
                <Card key={vac.id} className="p-5 space-y-3 hover:shadow-lg transition-shadow" hoverable>
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-bold text-nova-text">{vac.title}</p>
                      <p className="text-xs text-nova-text-muted">{vac.department?.name}</p>
                    </div>
                    <Badge variant={vacancyStatusColor(vac.status)} size="sm">{vac.status}</Badge>
                  </div>
                  <p className="text-xs text-nova-text-muted line-clamp-2">{vac.description}</p>
                  <div className="flex flex-wrap gap-2 text-xs text-nova-text-muted">
                    {vac.experienceLevel && <span className="flex items-center gap-1"><AcademicCapIcon className="h-3.5 w-3.5" />{vac.experienceLevel}</span>}
                    {vac.employmentType && <span className="flex items-center gap-1"><ClockIcon className="h-3.5 w-3.5" />{vac.employmentType?.replace(/_/g, ' ')}</span>}
                    {vac.location && <span className="flex items-center gap-1"><MapPinIcon className="h-3.5 w-3.5" />{vac.location}</span>}
                    <span className="flex items-center gap-1"><UserGroupIcon className="h-3.5 w-3.5" />{vac.positionsAvailable} position{vac.positionsAvailable !== 1 ? 's' : ''}</span>
                  </div>
                  {(vac.salaryRangeMin || vac.salaryRangeMax) && (
                    <p className="text-xs font-medium text-nova-text">
                      {vac.salaryRangeMin ? formatCurrency(vac.salaryRangeMin) : '?'} – {vac.salaryRangeMax ? formatCurrency(vac.salaryRangeMax) : '?'}
                      <span className="text-nova-text-muted ml-1">/ yr</span>
                    </p>
                  )}
                  <div className="flex items-center justify-between pt-2 border-t border-nova-border text-xs text-nova-text-muted">
                    <span>{vac.applicationCount ?? 0} application{(vac.applicationCount ?? 0) !== 1 ? 's' : ''}</span>
                    <div className="flex gap-1">
                      {vac.closingDate && <span>Closes {formatDate(vac.closingDate)}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 pt-1">
                    {vac.status === 'OPEN' && (
                      <Button size="sm" variant="outline" onClick={() => updateJobVacancy({ variables: { id: vac.id, status: 'CLOSED' } })}>Close</Button>
                    )}
                    {vac.status === 'DRAFT' && (
                      <Button size="sm" onClick={() => updateJobVacancy({ variables: { id: vac.id, status: 'OPEN' } })}>Publish</Button>
                    )}
                    {vac.status === 'CLOSED' && (
                      <Button size="sm" variant="outline" onClick={() => updateJobVacancy({ variables: { id: vac.id, status: 'OPEN' } })}>Reopen</Button>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      ),
    },
    {
      label: 'Applications',
      icon: <DocumentTextIcon className="h-4 w-4" />,
      badge: stats?.pendingApplications ?? undefined,
      content: (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-3">
            <div className="w-52">
              <Select value={appVacancyFilter} onChange={setAppVacancyFilter} options={[
                { value: '', label: 'All Vacancies' },
                ...vacancies.map((v: any) => ({ value: v.id, label: v.title })),
              ]} />
            </div>
            <div className="w-40"><Select value={appStatusFilter} onChange={setAppStatusFilter} options={APP_STATUS_OPTIONS} /></div>
          </div>
          {appsLoading && applications.length === 0 ? <LoadingOverlay /> : applications.length === 0 ? (
            <EmptyState icon={<DocumentTextIcon />} title="No applications" description="No applications match your filters." />
          ) : (
            <Card padding="none">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-nova-border bg-nova-surface text-left text-xs font-medium uppercase tracking-wider text-nova-text-muted">
                      <th className="px-4 py-3">Applicant</th>
                      <th className="px-4 py-3">Vacancy</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Applied</th>
                      <th className="px-4 py-3">Interview</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-nova-border">
                    {applications.map((app: any) => (
                      <tr key={app.id} className="hover:bg-nova-surface-hover transition-colors">
                        <td className="px-4 py-3">
                          <div>
                            <p className="font-medium text-nova-text">{app.applicantName}</p>
                            <p className="text-xs text-nova-text-muted flex items-center gap-1"><EnvelopeIcon className="h-3 w-3" />{app.applicantEmail}</p>
                            {app.applicantPhone && <p className="text-xs text-nova-text-muted flex items-center gap-1"><PhoneIcon className="h-3 w-3" />{app.applicantPhone}</p>}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-nova-text">{app.vacancy?.title ?? '—'}</td>
                        <td className="px-4 py-3">
                          <Badge variant={appStatusColor(app.status)} size="sm">{app.status}</Badge>
                        </td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">{formatDate(app.createdAt)}</td>
                        <td className="px-4 py-3 text-xs text-nova-text-muted">{app.interviewDate ? formatDate(app.interviewDate) : '—'}</td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Dropdown
                              trigger={<Button variant="ghost" size="sm" className="!px-2"><EllipsisVerticalIcon className="h-4 w-4" /></Button>}
                              items={[
                                { label: 'Shortlist', icon: <CheckCircleIcon className="h-4 w-4" />, onClick: () => updateAppStatus({ variables: { id: app.id, status: 'SHORTLISTED' } }), disabled: app.status === 'SHORTLISTED' },
                                { label: 'Schedule Interview', icon: <CalendarDaysIcon className="h-4 w-4" />, onClick: () => updateAppStatus({ variables: { id: app.id, status: 'INTERVIEW' } }), disabled: app.status === 'INTERVIEW' },
                                { label: 'Offer', icon: <CheckCircleIcon className="h-4 w-4" />, onClick: () => updateAppStatus({ variables: { id: app.id, status: 'OFFERED' } }), disabled: app.status === 'OFFERED' },
                                { label: 'Hire', icon: <UserPlusIcon className="h-4 w-4" />, onClick: () => updateAppStatus({ variables: { id: app.id, status: 'HIRED' } }), disabled: app.status === 'HIRED' },
                                { label: 'Reject', icon: <XCircleIcon className="h-4 w-4" />, danger: true, onClick: () => updateAppStatus({ variables: { id: app.id, status: 'REJECTED' } }), disabled: app.status === 'REJECTED' },
                              ]}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      ),
    },
  ];

  /* ══════════════════════════════════════════
     Render
     ══════════════════════════════════════════ */

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-nova-text">HR Management</h1>
          <p className="text-sm text-nova-text-secondary">Employees, departments, vacancies & applications</p>
        </div>
        <Button variant="outline" size="sm" leftIcon={<ArrowPathIcon className="h-4 w-4" />} onClick={refetchAll}>Refresh</Button>
      </div>

      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <StatMini icon={<UserGroupIcon className="h-5 w-5" />} label="Total Employees" value={stats.totalEmployees ?? 0} color="primary" />
          <StatMini icon={<CheckCircleIcon className="h-5 w-5" />} label="Active" value={stats.activeEmployees ?? 0} color="success" />
          <StatMini icon={<ClockIcon className="h-5 w-5" />} label="On Leave" value={stats.onLeaveCount ?? 0} color="warning" />
          <StatMini icon={<BuildingOfficeIcon className="h-5 w-5" />} label="Departments" value={stats.departmentsCount ?? 0} color="info" />
          <StatMini icon={<BriefcaseIcon className="h-5 w-5" />} label="Open Vacancies" value={stats.openVacancies ?? 0} color="purple" />
          <StatMini icon={<DocumentTextIcon className="h-5 w-5" />} label="Pending Apps" value={stats.pendingApplications ?? 0} color="danger" />
        </div>
      )}

      {/* Main Tabs */}
      <Tabs tabs={mainTabs} active={mainTab} onChange={setMainTab} />

      {/* ══════════════════════════════════════
         360° VIEW MODAL
         ══════════════════════════════════════ */}
      <Modal open={!!viewEmpId} onClose={() => setViewEmpId(null)} title="" size="full">
        <ModalBody className="!p-0 !space-y-0">
          {/* Gradient Banner */}
          {viewEmp && (
            <div className="relative overflow-hidden bg-gradient-to-r from-violet-600 via-purple-500 to-fuchsia-500 px-8 py-6 text-white">
              <div className="absolute inset-0 opacity-10">
                <svg width="100%" height="100%"><defs><pattern id="emp-dots" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="currentColor" /></pattern></defs><rect width="100%" height="100%" fill="url(#emp-dots)" /></svg>
              </div>
              <div className="relative flex items-center gap-5">
                <div className="ring-4 ring-white/20 rounded-full">
                  <Avatar name={viewEmp.fullName ?? '?'} size="xl" src={viewEmp.user?.avatarUrl} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-2xl font-bold">{viewEmp.fullName}</h3>
                  <p className="text-white/80 text-sm">{viewEmp.jobTitle} — {viewEmp.department?.name}</p>
                  {viewEmp.user?.email && <p className="text-white/60 text-xs mt-0.5 flex items-center gap-1"><EnvelopeIcon className="h-3 w-3" />{viewEmp.user.email}</p>}
                </div>
                <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
                  <span className="rounded-full bg-white/20 backdrop-blur-sm px-3 py-1 text-xs font-bold">{viewEmp.employeeId}</span>
                  <span className={`rounded-full px-3 py-1 text-xs font-bold ${viewEmp.status === 'ACTIVE' ? 'bg-green-500/30 text-green-100' : viewEmp.status === 'ON_LEAVE' ? 'bg-amber-500/30 text-amber-100' : 'bg-red-500/30 text-red-100'}`}>
                    {viewEmp.status === 'ACTIVE' ? '● Active' : viewEmp.status === 'ON_LEAVE' ? '● On Leave' : `● ${viewEmp.status}`}
                  </span>
                  <span className="rounded-full bg-white/20 backdrop-blur-sm px-3 py-1 text-xs font-bold">{viewEmp.employmentType?.replace(/_/g, ' ')}</span>
                </div>
              </div>
            </div>
          )}
          <div className="px-6 py-4">
            <Tabs tabs={viewTabs} active={viewTab} onChange={setViewTab} />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => { const id = viewEmpId; setViewEmpId(null); if (id) openEdit(id); }} leftIcon={<PencilSquareIcon className="h-4 w-4" />}>Edit Employee</Button>
          <Button onClick={() => setViewEmpId(null)}>Close</Button>
        </ModalFooter>
      </Modal>

      {/* ══════════════════════════════════════
         EDIT EMPLOYEE MODAL
         ══════════════════════════════════════ */}
      <Modal open={!!editEmpId} onClose={() => setEditEmpId(null)} title="Edit Employee" size="lg">
        <form onSubmit={handleEditSubmit}>
          <ModalBody>
            {editEmpLoading ? <div className="flex justify-center py-8"><Spinner /></div> : (
              <div className="grid gap-4 sm:grid-cols-2">
                <Select label="Department" value={editForm.departmentId} onChange={(v) => setEditForm({ ...editForm, departmentId: v })} options={deptCreateOptions} />
                <Input label="Job Title" value={editForm.jobTitle} onChange={(e) => setEditForm({ ...editForm, jobTitle: e.target.value })} />
                <Select label="Employment Type" value={editForm.employmentType} onChange={(v) => setEditForm({ ...editForm, employmentType: v })} options={EMPLOYMENT_TYPE_OPTIONS} />
                <Select label="Status" value={editForm.status} onChange={(v) => setEditForm({ ...editForm, status: v })} options={EMP_STATUS_OPTIONS.filter(o => o.value !== '')} />
                <Input label="Salary" type="number" value={editForm.salary} onChange={(e) => setEditForm({ ...editForm, salary: e.target.value })} leftIcon={<CurrencyDollarIcon className="h-4 w-4" />} />
                <Select label="Reports To" value={editForm.reportsToId} onChange={(v) => setEditForm({ ...editForm, reportsToId: v })} options={[{ value: '', label: 'None' }, ...empOptions]} />
                <Input label="Termination Date" type="date" value={editForm.terminationDate} onChange={(e) => setEditForm({ ...editForm, terminationDate: e.target.value })} />
              </div>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => setEditEmpId(null)}>Cancel</Button>
            <Button type="submit" isLoading={updatingEmp}>Save Changes</Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* ══════════════════════════════════════
         CREATE DEPARTMENT MODAL
         ══════════════════════════════════════ */}
      <Modal open={showCreateDept} onClose={() => setShowCreateDept(false)} title="New Department">
        <form onSubmit={handleCreateDept}>
          <ModalBody>
            <div className="space-y-4">
              <Input label="Name *" value={deptForm.name} onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })} placeholder="e.g. Digital Services" />
              <Input label="Code *" value={deptForm.code} onChange={(e) => setDeptForm({ ...deptForm, code: e.target.value })} placeholder="e.g. DIG" />
              <Textarea label="Description" value={deptForm.description} onChange={(e) => setDeptForm({ ...deptForm, description: e.target.value })} rows={3} />
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => setShowCreateDept(false)}>Cancel</Button>
            <Button type="submit" isLoading={creatingDept}>Create</Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* ══════════════════════════════════════
         CREATE EMPLOYEE MODAL
         ══════════════════════════════════════ */}
      <Modal open={showCreateEmp} onClose={() => setShowCreateEmp(false)} title="Add Employee" size="lg">
        <form onSubmit={handleCreateEmp}>
          <ModalBody>
            <div className="grid gap-4 sm:grid-cols-2">
              <Select label="User Account *" value={empForm.userId} onChange={(v) => setEmpForm({ ...empForm, userId: v })} options={[{ value: '', label: 'Select user…' }, ...userOptions]} />
              <Input label="Employee ID *" value={empForm.employeeId} onChange={(e) => setEmpForm({ ...empForm, employeeId: e.target.value })} placeholder="e.g. EMP-004" />
              <Select label="Department *" value={empForm.departmentId} onChange={(v) => setEmpForm({ ...empForm, departmentId: v })} options={[{ value: '', label: 'Select department…' }, ...deptCreateOptions]} />
              <Input label="Job Title *" value={empForm.jobTitle} onChange={(e) => setEmpForm({ ...empForm, jobTitle: e.target.value })} placeholder="e.g. Reference Librarian" />
              <Input label="Hire Date *" type="date" value={empForm.hireDate} onChange={(e) => setEmpForm({ ...empForm, hireDate: e.target.value })} />
              <Select label="Employment Type" value={empForm.employmentType} onChange={(v) => setEmpForm({ ...empForm, employmentType: v })} options={EMPLOYMENT_TYPE_OPTIONS} />
              <Input label="Salary" type="number" value={empForm.salary} onChange={(e) => setEmpForm({ ...empForm, salary: e.target.value })} leftIcon={<CurrencyDollarIcon className="h-4 w-4" />} />
              <Select label="Reports To" value={empForm.reportsToId} onChange={(v) => setEmpForm({ ...empForm, reportsToId: v })} options={[{ value: '', label: 'None' }, ...empOptions]} />
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => setShowCreateEmp(false)}>Cancel</Button>
            <Button type="submit" isLoading={creatingEmp}>Create Employee</Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* ══════════════════════════════════════
         CREATE VACANCY MODAL
         ══════════════════════════════════════ */}
      <Modal open={showCreateVacancy} onClose={() => setShowCreateVacancy(false)} title="Post Job Vacancy" size="lg">
        <form onSubmit={handleCreateVacancy}>
          <ModalBody>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Title *" value={vacForm.title} onChange={(e) => setVacForm({ ...vacForm, title: e.target.value })} placeholder="e.g. Digital Services Librarian" />
              <Select label="Department *" value={vacForm.departmentId} onChange={(v) => setVacForm({ ...vacForm, departmentId: v })} options={[{ value: '', label: 'Select department…' }, ...deptCreateOptions]} />
              <Select label="Experience Level" value={vacForm.experienceLevel} onChange={(v) => setVacForm({ ...vacForm, experienceLevel: v })} options={EXPERIENCE_LEVEL_OPTIONS} />
              <Select label="Employment Type" value={vacForm.employmentType} onChange={(v) => setVacForm({ ...vacForm, employmentType: v })} options={EMPLOYMENT_TYPE_OPTIONS} />
              <Input label="Positions Available" type="number" value={vacForm.positionsAvailable} onChange={(e) => setVacForm({ ...vacForm, positionsAvailable: e.target.value })} />
              <Input label="Location" value={vacForm.location} onChange={(e) => setVacForm({ ...vacForm, location: e.target.value })} placeholder="Nova Library - Main Campus" leftIcon={<MapPinIcon className="h-4 w-4" />} />
              <Input label="Salary Min" type="number" value={vacForm.salaryRangeMin} onChange={(e) => setVacForm({ ...vacForm, salaryRangeMin: e.target.value })} leftIcon={<CurrencyDollarIcon className="h-4 w-4" />} />
              <Input label="Salary Max" type="number" value={vacForm.salaryRangeMax} onChange={(e) => setVacForm({ ...vacForm, salaryRangeMax: e.target.value })} leftIcon={<CurrencyDollarIcon className="h-4 w-4" />} />
              <Input label="Closing Date" type="date" value={vacForm.closingDate} onChange={(e) => setVacForm({ ...vacForm, closingDate: e.target.value })} />
            </div>
            <div className="mt-4 space-y-4">
              <Textarea label="Description *" value={vacForm.description} onChange={(e) => setVacForm({ ...vacForm, description: e.target.value })} rows={3} />
              <Textarea label="Requirements *" value={vacForm.requirements} onChange={(e) => setVacForm({ ...vacForm, requirements: e.target.value })} rows={3} placeholder="One requirement per line" />
              <Textarea label="Responsibilities" value={vacForm.responsibilities} onChange={(e) => setVacForm({ ...vacForm, responsibilities: e.target.value })} rows={3} />
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={() => setShowCreateVacancy(false)}>Cancel</Button>
            <Button type="submit" isLoading={creatingVac}>Post Vacancy</Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* ══════════════════════════════════════
         TERMINATE CONFIRM
         ══════════════════════════════════════ */}
      {terminateTarget && (
        <ConfirmDialog
          open
          onClose={() => setTerminateTarget(null)}
          onConfirm={handleTerminate}
          title="Terminate Employee"
          description={`Are you sure you want to terminate ${terminateTarget.name}? This action will set their status to TERMINATED and record today as the termination date.`}
          variant="danger"
          confirmLabel="Terminate"
        />
      )}
    </div>
  );
}
