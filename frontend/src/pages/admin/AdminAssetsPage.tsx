/**
 * Admin Asset Management Page
 * Full CRUD for library physical assets with stats, categories, and maintenance tracking.
 */

import { useState, useCallback } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import toast from 'react-hot-toast';
import {
  WrenchScrewdriverIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  CubeIcon,
  TrashIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  PencilSquareIcon,
} from '@heroicons/react/24/outline';
import { useDocumentTitle } from '@/hooks';
import { GET_ASSETS, GET_ASSET_CATEGORIES, GET_ASSET_STATS, GET_MAINTENANCE_LOGS } from '@/graphql/queries/assets';
import { CREATE_ASSET, UPDATE_ASSET, DELETE_ASSET, LOG_MAINTENANCE, CREATE_ASSET_CATEGORY } from '@/graphql/mutations/assets';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Modal, ModalBody, ModalFooter } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { Spinner } from '@/components/ui/Spinner';
import { Tabs } from '@/components/ui/Tabs';
import { extractGqlError, formatDate } from '@/lib/utils';

const STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'IN_STORAGE', label: 'In Storage' },
  { value: 'UNDER_MAINTENANCE', label: 'Under Maintenance' },
  { value: 'DISPOSED', label: 'Disposed' },
  { value: 'ON_ORDER', label: 'On Order' },
];

const CONDITION_OPTIONS = [
  { value: 'EXCELLENT', label: 'Excellent' },
  { value: 'GOOD', label: 'Good' },
  { value: 'FAIR', label: 'Fair' },
  { value: 'POOR', label: 'Poor' },
  { value: 'CRITICAL', label: 'Critical' },
];

const MAINT_TYPES = [
  { value: 'PREVENTIVE', label: 'Preventive' },
  { value: 'CORRECTIVE', label: 'Corrective' },
  { value: 'INSPECTION', label: 'Inspection' },
  { value: 'UPGRADE', label: 'Upgrade' },
];

const statusColor = (s: string) => {
  switch (s) {
    case 'ACTIVE': return 'success';
    case 'IN_STORAGE': return 'neutral';
    case 'UNDER_MAINTENANCE': return 'warning';
    case 'DISPOSED': return 'danger';
    case 'ON_ORDER': return 'info';
    default: return 'neutral';
  }
};

const conditionColor = (c: string) => {
  switch (c) {
    case 'EXCELLENT': return 'success';
    case 'GOOD': return 'info';
    case 'FAIR': return 'warning';
    case 'POOR': return 'danger';
    case 'CRITICAL': return 'danger';
    default: return 'neutral';
  }
};

export default function AdminAssetsPage() {
  useDocumentTitle('Asset Management');
  const [activeTab, setActiveTab] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showMaintenanceModal, setShowMaintenanceModal] = useState(false);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editAssetId, setEditAssetId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    name: '', description: '', status: 'ACTIVE', condition: 'GOOD',
    floorNumber: '', room: '',
  });

  // Form state
  const [form, setForm] = useState({
    assetTag: '', name: '', categoryId: '', description: '',
    status: 'ACTIVE', condition: 'GOOD', floorNumber: '', room: '',
    purchaseDate: '', purchasePrice: '', supplier: '',
    serialNumber: '', manufacturer: '', modelNumber: '',
  });
  const [maintForm, setMaintForm] = useState({
    maintenanceType: 'PREVENTIVE', description: '', performedDate: '',
    cost: '', vendor: '', notes: '', conditionAfter: '',
  });
  const [catForm, setCatForm] = useState({ name: '', slug: '', description: '', icon: '' });

  // Queries
  const { data: statsData } = useQuery(GET_ASSET_STATS);
  const { data: assetsData, loading: assetsLoading, refetch: refetchAssets } = useQuery(GET_ASSETS, {
    variables: { status: statusFilter || undefined, search: search || undefined, limit: 100 },
  });
  const { data: categoriesData, refetch: refetchCategories } = useQuery(GET_ASSET_CATEGORIES);
  const { data: logsData, refetch: refetchLogs } = useQuery(GET_MAINTENANCE_LOGS, { variables: { limit: 30 } });

  // Mutations
  const [createAsset, { loading: creating }] = useMutation(CREATE_ASSET);
  const [updateAsset, { loading: updating }] = useMutation(UPDATE_ASSET);
  const [deleteAsset] = useMutation(DELETE_ASSET);
  const [logMaintenance, { loading: logMaintLoading }] = useMutation(LOG_MAINTENANCE);
  const [createCategory, { loading: creatingCat }] = useMutation(CREATE_ASSET_CATEGORY);

  const stats = statsData?.assetStats;
  const assets = assetsData?.assets || [];
  const categories = categoriesData?.assetCategories || [];
  const logs = logsData?.maintenanceLogs || [];

  const handleCreateAsset = useCallback(async () => {
    try {
      await createAsset({
        variables: {
          ...form,
          floorNumber: form.floorNumber ? parseInt(form.floorNumber) : undefined,
          purchasePrice: form.purchasePrice ? parseFloat(form.purchasePrice) : undefined,
        },
      });
      toast.success('Asset created successfully');
      setShowCreateModal(false);
      setForm({ assetTag: '', name: '', categoryId: '', description: '', status: 'ACTIVE', condition: 'GOOD', floorNumber: '', room: '', purchaseDate: '', purchasePrice: '', supplier: '', serialNumber: '', manufacturer: '', modelNumber: '' });
      refetchAssets();
    } catch (err) { toast.error(extractGqlError(err)); }
  }, [form, createAsset, refetchAssets]);

  const handleUpdateStatus = useCallback(async (id: string, status: string) => {
    try {
      await updateAsset({ variables: { id, status } });
      toast.success('Status updated');
      refetchAssets();
    } catch (err) { toast.error(extractGqlError(err)); }
  }, [updateAsset, refetchAssets]);

  const openEditModal = useCallback((asset: any) => {
    setEditAssetId(asset.id);
    setEditForm({
      name: asset.name || '',
      description: asset.description || '',
      status: asset.status || 'ACTIVE',
      condition: asset.condition || 'GOOD',
      floorNumber: asset.floorNumber?.toString() || '',
      room: asset.room || '',
    });
    setShowEditModal(true);
  }, []);

  const handleEditAsset = useCallback(async () => {
    if (!editAssetId) return;
    try {
      await updateAsset({
        variables: {
          id: editAssetId,
          name: editForm.name || undefined,
          status: editForm.status || undefined,
          condition: editForm.condition || undefined,
          floorNumber: editForm.floorNumber ? parseInt(editForm.floorNumber) : undefined,
          room: editForm.room || undefined,
          description: editForm.description || undefined,
        },
      });
      toast.success('Asset updated successfully');
      setShowEditModal(false);
      refetchAssets();
    } catch (err) { toast.error(extractGqlError(err)); }
  }, [editAssetId, editForm, updateAsset, refetchAssets]);

  const handleDelete = useCallback(async (id: string) => {
    if (!confirm('Are you sure you want to delete this asset?')) return;
    try {
      await deleteAsset({ variables: { id } });
      toast.success('Asset deleted');
      refetchAssets();
    } catch (err) { toast.error(extractGqlError(err)); }
  }, [deleteAsset, refetchAssets]);

  const handleLogMaintenance = useCallback(async () => {
    if (!selectedAssetId) return;
    try {
      await logMaintenance({
        variables: {
          assetId: selectedAssetId,
          ...maintForm,
          cost: maintForm.cost ? parseFloat(maintForm.cost) : undefined,
          conditionAfter: maintForm.conditionAfter || undefined,
        },
      });
      toast.success('Maintenance logged');
      setShowMaintenanceModal(false);
      setMaintForm({ maintenanceType: 'PREVENTIVE', description: '', performedDate: '', cost: '', vendor: '', notes: '', conditionAfter: '' });
      refetchAssets();
      refetchLogs();
    } catch (err) { toast.error(extractGqlError(err)); }
  }, [selectedAssetId, maintForm, logMaintenance, refetchAssets, refetchLogs]);

  const handleCreateCategory = useCallback(async () => {
    try {
      await createCategory({ variables: catForm });
      toast.success('Category created');
      setShowCategoryModal(false);
      setCatForm({ name: '', slug: '', description: '', icon: '' });
      refetchCategories();
    } catch (err) { toast.error(extractGqlError(err)); }
  }, [catForm, createCategory, refetchCategories]);

  const tabs = [
    { id: 'assets', label: 'Assets', content: null },
    { id: 'maintenance', label: 'Maintenance Logs', content: null },
    { id: 'categories', label: 'Categories', content: null },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Asset Management</h1>
          <p className="text-sm text-gray-500 mt-1">Track and manage library physical assets</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowCategoryModal(true)}>
            <PlusIcon className="h-4 w-4 mr-1" /> Category
          </Button>
          <Button onClick={() => setShowCreateModal(true)}>
            <PlusIcon className="h-4 w-4 mr-1" /> New Asset
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          <Card className="p-3 text-center">
            <CubeIcon className="h-5 w-5 mx-auto text-blue-500" />
            <p className="text-xl font-bold mt-1">{stats.totalAssets}</p>
            <p className="text-xs text-gray-500">Total</p>
          </Card>
          <Card className="p-3 text-center">
            <CheckCircleIcon className="h-5 w-5 mx-auto text-green-500" />
            <p className="text-xl font-bold mt-1">{stats.activeCount}</p>
            <p className="text-xs text-gray-500">Active</p>
          </Card>
          <Card className="p-3 text-center">
            <WrenchScrewdriverIcon className="h-5 w-5 mx-auto text-yellow-500" />
            <p className="text-xl font-bold mt-1">{stats.underMaintenanceCount}</p>
            <p className="text-xs text-gray-500">Under Maint.</p>
          </Card>
          <Card className="p-3 text-center">
            <TrashIcon className="h-5 w-5 mx-auto text-red-500" />
            <p className="text-xl font-bold mt-1">{stats.disposedCount}</p>
            <p className="text-xs text-gray-500">Disposed</p>
          </Card>
          <Card className="p-3 text-center">
            <p className="text-xl font-bold">${(stats.totalValue || 0).toLocaleString()}</p>
            <p className="text-xs text-gray-500">Total Value</p>
          </Card>
          <Card className="p-3 text-center">
            <ExclamationTriangleIcon className="h-5 w-5 mx-auto text-orange-500" />
            <p className="text-xl font-bold mt-1">{stats.maintenanceOverdueCount}</p>
            <p className="text-xs text-gray-500">Maint. Overdue</p>
          </Card>
          <Card className="p-3 text-center">
            <ShieldCheckIcon className="h-5 w-5 mx-auto text-purple-500" />
            <p className="text-xl font-bold mt-1">{stats.warrantyExpiringSoon}</p>
            <p className="text-xs text-gray-500">Warranty Soon</p>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs tabs={tabs} active={activeTab} onChange={setActiveTab} />

      {/* Assets Tab */}
      {activeTab === 0 && (
        <div className="space-y-4">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <Input placeholder="Search assets..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
            </div>
            <Select value={statusFilter} onChange={(value) => setStatusFilter(value)} options={STATUS_OPTIONS} className="w-44" />
          </div>

          {assetsLoading ? (
            <div className="flex justify-center py-12"><Spinner /></div>
          ) : assets.length === 0 ? (
            <EmptyState icon={<CubeIcon className="h-12 w-12" />} title="No Assets Found" description="No assets match your filters." />
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Asset</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Condition</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {assets.map((asset: any) => (
                    <tr key={asset.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900 dark:text-white">{asset.name}</p>
                        <p className="text-xs text-gray-500">{asset.assetTag} • {asset.serialNumber || 'No S/N'}</p>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{asset.category?.name}</td>
                      <td className="px-4 py-3">
                        <Badge variant={statusColor(asset.status)}>{asset.status.replace('_', ' ')}</Badge>
                        {asset.maintenanceOverdue && <Badge variant="danger" className="ml-1 text-xs">OVERDUE</Badge>}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={conditionColor(asset.condition)}>{asset.condition}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                        {asset.floorNumber ? `Floor ${asset.floorNumber}` : ''}{asset.room ? ` • ${asset.room}` : ''}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <p className="font-medium">${parseFloat(asset.currentValue || 0).toLocaleString()}</p>
                        {asset.isUnderWarranty && <span className="text-xs text-green-600">Under Warranty</span>}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-1">
                          <Button size="sm" variant="ghost" onClick={() => openEditModal(asset)} title="Edit Asset">
                            <PencilSquareIcon className="h-4 w-4 text-blue-500" />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => { setSelectedAssetId(asset.id); setShowMaintenanceModal(true); }}>
                            <WrenchScrewdriverIcon className="h-4 w-4" />
                          </Button>
                          {asset.status !== 'DISPOSED' && (
                            <Button size="sm" variant="ghost" onClick={() => handleUpdateStatus(asset.id, 'UNDER_MAINTENANCE')}>
                              <ArrowPathIcon className="h-4 w-4 text-yellow-500" />
                            </Button>
                          )}
                          <Button size="sm" variant="ghost" onClick={() => handleDelete(asset.id)}>
                            <TrashIcon className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Maintenance Logs Tab */}
      {activeTab === 1 && (
        <div className="space-y-4">
          {logs.length === 0 ? (
            <EmptyState icon={<WrenchScrewdriverIcon className="h-12 w-12" />} title="No Maintenance Logs" description="No maintenance has been logged yet." />
          ) : (
            <div className="space-y-3">
              {logs.map((log: any) => (
                <Card key={log.id} className="p-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{log.asset.name} <span className="text-xs text-gray-500">({log.asset.assetTag})</span></p>
                      <p className="text-sm mt-1">{log.description}</p>
                      <div className="flex gap-2 mt-2">
                        <Badge variant="info">{log.maintenanceType}</Badge>
                        {log.conditionAfter && <Badge variant="success">After: {log.conditionAfter}</Badge>}
                        {log.vendor && <span className="text-xs text-gray-500">Vendor: {log.vendor}</span>}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{log.cost > 0 ? `$${parseFloat(log.cost).toLocaleString()}` : 'No cost'}</p>
                      <p className="text-xs text-gray-500">{formatDate(log.performedDate)}</p>
                      <p className="text-xs text-gray-500">By: {log.performedBy?.firstName} {log.performedBy?.lastName}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Categories Tab */}
      {activeTab === 2 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.map((cat: any) => (
            <Card key={cat.id} className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <CubeIcon className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">{cat.name}</p>
                  <p className="text-xs text-gray-500">{cat.assetCount} assets {cat.parent ? `• Parent: ${cat.parent.name}` : ''}</p>
                </div>
              </div>
              {cat.description && <p className="text-sm text-gray-500 mt-2">{cat.description}</p>}
            </Card>
          ))}
        </div>
      )}

      {/* Create Asset Modal */}
      <Modal open={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create New Asset" size="xl">
        <ModalBody>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Asset Tag *" value={form.assetTag} onChange={(e) => setForm({ ...form, assetTag: e.target.value })} placeholder="AST-007" />
            <Input label="Name *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Asset name" />
            <Select label="Category *" value={form.categoryId} onChange={(value) => setForm({ ...form, categoryId: value })} options={[{ value: '', label: 'Select...' }, ...categories.map((c: any) => ({ value: c.id, label: c.name }))]} />
            <Select label="Condition" value={form.condition} onChange={(value) => setForm({ ...form, condition: value })} options={CONDITION_OPTIONS} />
            <Input label="Floor Number" type="number" value={form.floorNumber} onChange={(e) => setForm({ ...form, floorNumber: e.target.value })} />
            <Input label="Room" value={form.room} onChange={(e) => setForm({ ...form, room: e.target.value })} placeholder="e.g. Main Reading Hall" />
            <Input label="Purchase Date" type="date" value={form.purchaseDate} onChange={(e) => setForm({ ...form, purchaseDate: e.target.value })} />
            <Input label="Purchase Price ($)" type="number" value={form.purchasePrice} onChange={(e) => setForm({ ...form, purchasePrice: e.target.value })} />
            <Input label="Supplier" value={form.supplier} onChange={(e) => setForm({ ...form, supplier: e.target.value })} />
            <Input label="Serial Number" value={form.serialNumber} onChange={(e) => setForm({ ...form, serialNumber: e.target.value })} />
            <Input label="Manufacturer" value={form.manufacturer} onChange={(e) => setForm({ ...form, manufacturer: e.target.value })} />
            <Input label="Model Number" value={form.modelNumber} onChange={(e) => setForm({ ...form, modelNumber: e.target.value })} />
          </div>
          <Input label="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="mt-4" placeholder="Brief description" />
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
          <Button onClick={handleCreateAsset} disabled={creating || !form.assetTag || !form.name || !form.categoryId}>
            {creating ? 'Creating...' : 'Create Asset'}
          </Button>
        </ModalFooter>
      </Modal>

      {/* Log Maintenance Modal */}
      <Modal open={showMaintenanceModal} onClose={() => setShowMaintenanceModal(false)} title="Log Maintenance" size="lg">
        <ModalBody>
          <div className="grid gap-4 sm:grid-cols-2">
            <Select label="Type *" value={maintForm.maintenanceType} onChange={(value) => setMaintForm({ ...maintForm, maintenanceType: value })} options={MAINT_TYPES} />
            <Input label="Date *" type="date" value={maintForm.performedDate} onChange={(e) => setMaintForm({ ...maintForm, performedDate: e.target.value })} />
            <Input label="Cost ($)" type="number" value={maintForm.cost} onChange={(e) => setMaintForm({ ...maintForm, cost: e.target.value })} />
            <Input label="Vendor" value={maintForm.vendor} onChange={(e) => setMaintForm({ ...maintForm, vendor: e.target.value })} />
            <Select label="Condition After" value={maintForm.conditionAfter} onChange={(value) => setMaintForm({ ...maintForm, conditionAfter: value })} options={[{ value: '', label: 'N/A' }, ...CONDITION_OPTIONS]} />
          </div>
          <Input label="Description *" value={maintForm.description} onChange={(e) => setMaintForm({ ...maintForm, description: e.target.value })} className="mt-4" placeholder="What was done?" />
          <Input label="Notes" value={maintForm.notes} onChange={(e) => setMaintForm({ ...maintForm, notes: e.target.value })} className="mt-3" placeholder="Additional notes" />
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setShowMaintenanceModal(false)}>Cancel</Button>
          <Button onClick={handleLogMaintenance} disabled={logMaintLoading || !maintForm.description || !maintForm.performedDate}>
            {logMaintLoading ? 'Logging...' : 'Log Maintenance'}
          </Button>
        </ModalFooter>
      </Modal>

      {/* Create Category Modal */}
      <Modal open={showCategoryModal} onClose={() => setShowCategoryModal(false)} title="Create Asset Category" size="md">
        <ModalBody>
          <div className="space-y-4">
            <Input label="Name *" value={catForm.name} onChange={(e) => setCatForm({ ...catForm, name: e.target.value })} placeholder="e.g. Electronics" />
            <Input label="Slug *" value={catForm.slug} onChange={(e) => setCatForm({ ...catForm, slug: e.target.value })} placeholder="e.g. electronics" />
            <Input label="Icon" value={catForm.icon} onChange={(e) => setCatForm({ ...catForm, icon: e.target.value })} placeholder="e.g. computer" />
            <Input label="Description" value={catForm.description} onChange={(e) => setCatForm({ ...catForm, description: e.target.value })} placeholder="Category description" />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setShowCategoryModal(false)}>Cancel</Button>
          <Button onClick={handleCreateCategory} disabled={creatingCat || !catForm.name || !catForm.slug}>
            {creatingCat ? 'Creating...' : 'Create Category'}
          </Button>
        </ModalFooter>
      </Modal>

      {/* Edit Asset Modal */}
      <Modal open={showEditModal} onClose={() => setShowEditModal(false)} title="Edit Asset" size="lg">
        <ModalBody>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <Input label="Name *" value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
            </div>
            <Select label="Status" value={editForm.status} onChange={(value) => setEditForm({ ...editForm, status: value })} options={STATUS_OPTIONS.filter((o) => o.value)} />
            <Select label="Condition" value={editForm.condition} onChange={(value) => setEditForm({ ...editForm, condition: value })} options={CONDITION_OPTIONS} />
            <Input label="Floor Number" type="number" value={editForm.floorNumber} onChange={(e) => setEditForm({ ...editForm, floorNumber: e.target.value })} />
            <Input label="Room" value={editForm.room} onChange={(e) => setEditForm({ ...editForm, room: e.target.value })} placeholder="e.g. Main Reading Hall" />
          </div>
          <Input label="Description" value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} className="mt-4" placeholder="Brief description" />
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={() => setShowEditModal(false)}>Cancel</Button>
          <Button onClick={handleEditAsset} disabled={updating || !editForm.name}>
            {updating ? 'Saving...' : 'Save Changes'}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
