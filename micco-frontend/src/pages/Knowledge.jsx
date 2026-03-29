// Knowledge.jsx - Knowledge Base Management page
// New "Tri thức" tab for managing knowledge entries
import { useState, useEffect, useRef } from 'react';
import {
    Search, Plus, Filter, Grid, List, BookOpen,
    CheckCircle2, AlertCircle, Loader2, X
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import KnowledgeCard from '../components/knowledge/KnowledgeCard';
import KnowledgeForm from '../components/knowledge/KnowledgeForm';
import Breadcrumb from '../components/shared/Breadcrumb';
import ConfirmDeleteModal from '../components/shared/ConfirmDeleteModal';

export default function Knowledge() {
    const { authFetch } = useAuth();

    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [categoryFilter, setCategoryFilter] = useState('Tất cả');
    const [statusFilter, setStatusFilter] = useState('Tất cả');
    const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'

    const [formOpen, setFormOpen] = useState(false);
    const [editEntry, setEditEntry] = useState(null);
    const [deleteEntry, setDeleteEntry] = useState(null);
    const [saving, setSaving] = useState(false);
    const [toast, setToast] = useState(null);

    const searchDebounce = useRef(null);

    const CATEGORIES = [
        'Tất cả', 'Chung', 'Quy trình', 'Hướng dẫn', 'Tiêu chuẩn',
        'Quy định', 'Kinh nghiệm', 'Vật tư', 'Nhà cung cấp', 'An toàn', 'Kỹ thuật'
    ];

    const STATUSES = ['Tất cả', 'Hoạt động', 'Chờ duyệt', 'Bị từ chối', 'Bản nháp', 'Lưu trữ'];

    // Fetch entries
    const fetchEntries = async () => {
        try {
            setLoading(true);
            const res = await authFetch('/api/knowledge');
            if (res.ok) {
                const data = await res.json();
                setEntries(data.items || []);
            }
        } catch (err) {
            showToast('Không thể tải danh sách tri thức', 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchEntries();
    }, []);

    // Debounced search
    useEffect(() => {
        clearTimeout(searchDebounce.current);
        searchDebounce.current = setTimeout(() => {
            // Search is client-side for now
        }, 300);
        return () => clearTimeout(searchDebounce.current);
    }, [search]);

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    // Filter entries
    const filteredEntries = entries.filter(entry => {
        const matchSearch = !search ||
            entry.title?.toLowerCase().includes(search.toLowerCase()) ||
            entry.content_text?.toLowerCase().includes(search.toLowerCase());

        const matchCategory = categoryFilter === 'Tất cả' ||
            entry.category === categoryFilter;

        const matchStatus = statusFilter === 'Tất cả' ||
            (statusFilter === 'Hoạt động' && (entry.status === 'Active' && entry.approval_status === 'approved')) ||
            (statusFilter === 'Chờ duyệt' && entry.approval_status === 'pending_approval') ||
            (statusFilter === 'Bị từ chối' && entry.approval_status === 'rejected') ||
            (statusFilter === 'Bản nháp' && entry.status === 'Draft' && entry.approval_status !== 'pending_approval') ||
            (statusFilter === 'Lưu trữ' && entry.status === 'Archived');

        return matchSearch && matchCategory && matchStatus;
    });


    // Create/Update entry
    const handleSave = async (formData) => {
        try {
            setSaving(true);
            const isEdit = !!editEntry;
            const url = isEdit ? `/api/knowledge/${editEntry.id}` : '/api/knowledge';
            const method = isEdit ? 'PUT' : 'POST';

            const res = await authFetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            if (res.ok) {
                setFormOpen(false);
                setEditEntry(null);
                await fetchEntries();
                showToast(isEdit ? 'Cập nhật thành công' : 'Thêm tri thức thành công');
            } else {
                const err = await res.json();
                showToast(err.detail || 'Thao tác thất bại', 'error');
            }
        } catch (err) {
            showToast('Có lỗi xảy ra', 'error');
        } finally {
            setSaving(false);
        }
    };

    // Delete entry
    const handleDelete = async () => {
        if (!deleteEntry) return;
        try {
            const res = await authFetch(`/api/knowledge/${deleteEntry.id}`, {
                method: 'DELETE',
            });

            if (res.ok || res.status === 204) {
                setDeleteEntry(null);
                await fetchEntries();
                showToast('Xóa tri thức thành công');
            } else {
                const err = await res.json();
                showToast(err.detail || 'Xóa thất bại', 'error');
            }
        } catch {
            showToast('Xóa thất bại', 'error');
        }
    };

    return (
        <div className="space-y-6 px-2 md:px-4">
            {/* Breadcrumb */}
            <div className="px-2 pt-4">
                <Breadcrumb items={[
                    { label: 'Tổng quan', href: '/dashboard' },
                    { label: 'Tri thức' },
                ]} />
            </div>

            {/* Toast */}
            {toast && (
                <div className={`fixed top-6 right-6 z-[70] flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-xl border text-sm font-medium transition-all
                    ${toast.type === 'error'
                        ? 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700 text-red-700 dark:text-red-300'
                        : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200'
                    }`}>
                    {toast.type === 'error'
                        ? <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
                        : <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    }
                    {toast.msg}
                </div>
            )}

            {/* Header */}
            <div className="flex items-center justify-between px-2">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Quản lý Tri thức</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                        {entries.length} bài viết tri thức
                    </p>
                </div>
                <button
                    onClick={() => { setEditEntry(null); setFormOpen(true); }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
                >
                    <Plus className="w-4 h-4" />
                    Thêm tri thức mới
                </button>
            </div>

            {/* Filters & Search */}
            <div className="flex flex-wrap items-center gap-3 px-2">
                {/* Search */}
                <div className="relative flex-1 min-w-[200px] max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        placeholder="Tìm kiếm tri thức..."
                        className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 placeholder-slate-400 outline-none focus:ring-2 focus:ring-primary-600/30 focus:border-primary-600 transition-all"
                    />
                </div>

                {/* Category Filter */}
                <select
                    value={categoryFilter}
                    onChange={e => setCategoryFilter(e.target.value)}
                    className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 outline-none focus:ring-2 focus:ring-primary-600/30"
                >
                    {CATEGORIES.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                    ))}
                </select>

                {/* Status Filter */}
                <select
                    value={statusFilter}
                    onChange={e => setStatusFilter(e.target.value)}
                    className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 outline-none focus:ring-2 focus:ring-primary-600/30"
                >
                    {STATUSES.map(s => (
                        <option key={s} value={s}>{s}</option>
                    ))}
                </select>

                {/* View Mode Toggle */}
                <div className="flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg">
                    <button
                        onClick={() => setViewMode('grid')}
                        className={`p-2 rounded-md transition-colors ${viewMode === 'grid' ? 'bg-white dark:bg-slate-700 shadow-sm text-primary-600' : 'text-slate-400 hover:text-slate-600'}`}
                    >
                        <Grid className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setViewMode('list')}
                        className={`p-2 rounded-md transition-colors ${viewMode === 'list' ? 'bg-white dark:bg-slate-700 shadow-sm text-primary-600' : 'text-slate-400 hover:text-slate-600'}`}
                    >
                        <List className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="px-2">
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
                </div>
            ) : filteredEntries.length === 0 ? (
                <div className="text-center py-16">
                    <BookOpen className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
                    <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">
                        {search || categoryFilter !== 'Tất cả' || statusFilter !== 'Tất cả'
                            ? 'Không tìm thấy tri thức phù hợp'
                            : 'Chưa có tri thức nào'}
                    </p>
                    {!search && categoryFilter === 'Tất cả' && statusFilter === 'Tất cả' && (
                        <button
                            onClick={() => { setEditEntry(null); setFormOpen(true); }}
                            className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-lg transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                            Thêm tri thức đầu tiên
                        </button>
                    )}
                </div>
            ) : viewMode === 'grid' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {filteredEntries.map(entry => (
                        <KnowledgeCard
                            key={entry.id}
                            entry={entry}
                            onEdit={(e) => { setEditEntry(e); setFormOpen(true); }}
                            onDelete={setDeleteEntry}
                        />
                    ))}
                </div>
            ) : (
                <div className="space-y-3">
                    {filteredEntries.map(entry => (
                        <KnowledgeCard
                            key={entry.id}
                            entry={entry}
                            onEdit={(e) => { setEditEntry(e); setFormOpen(true); }}
                            onDelete={setDeleteEntry}
                        />
                    ))}
                </div>
            )}

            {/* Knowledge Form Modal */}
            {formOpen && (
                <KnowledgeForm
                    entry={editEntry}
                    onSave={handleSave}
                    onClose={() => { setFormOpen(false); setEditEntry(null); }}
                    saving={saving}
                />
            )}

            {/* Delete Confirmation */}
            {deleteEntry && (
                <ConfirmDeleteModal
                    title="Xóa tri thức"
                    description={
                        <>
                            Bạn có chắc chắn muốn xóa{' '}
                            <span className="font-semibold text-slate-700 dark:text-slate-200">"{deleteEntry.title}"</span>?
                            {' '}Hành động này không thể hoàn tác.
                        </>
                    }
                    onClose={() => setDeleteEntry(null)}
                    onConfirm={handleDelete}
                />
            )}
            </div>
        </div>
    );
}
