import { useState, useEffect } from 'react';
import {
    Building2, Plus, Pencil, Trash2, Users,
    CheckCircle2, AlertCircle, X, Search,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Breadcrumb from '../components/shared/Breadcrumb';
import ConfirmDeleteModal from '../components/shared/ConfirmDeleteModal';

export default function Departments() {
    const { authFetch } = useAuth();
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [modalOpen, setModalOpen] = useState(false);
    const [editDept, setEditDept] = useState(null);
    const [deleteDept, setDeleteDept] = useState(null);
    const [toast, setToast] = useState(null);

    useEffect(() => { fetchDepartments(); }, []);

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const fetchDepartments = async () => {
        try {
            const res = await authFetch('/api/admin/departments');
            if (res.ok) setDepartments(await res.json());
        } catch { /* silent */ }
        finally { setLoading(false); }
    };

    const handleSave = async (form) => {
        try {
            const isEdit = !!editDept;
            const url = isEdit ? `/api/admin/departments/${editDept.id}` : '/api/admin/departments';
            const method = isEdit ? 'PUT' : 'POST';
            const res = await authFetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form),
            });
            if (res.ok) {
                setModalOpen(false);
                setEditDept(null);
                await fetchDepartments();
                showToast(isEdit ? `Cập nhật "${form.name}" thành công` : `Thêm "${form.name}" thành công`);
            } else {
                const err = await res.json();
                showToast(err.detail || 'Thao tác thất bại', 'error');
            }
        } catch { showToast('Có lỗi xảy ra', 'error'); }
    };

    const handleDelete = async (id) => {
        try {
            const res = await authFetch(`/api/admin/departments/${id}`, { method: 'DELETE' });
            if (res.ok || res.status === 204) {
                setDeleteDept(null);
                await fetchDepartments();
                showToast('Xóa phòng ban thành công');
            } else {
                const err = await res.json();
                showToast(err.detail || 'Xóa thất bại', 'error');
            }
        } catch { showToast('Xóa thất bại', 'error'); }
    };

    const filtered = departments.filter(d =>
        d.name.toLowerCase().includes(search.toLowerCase()) ||
        (d.description || '').toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="space-y-8">
            <Breadcrumb items={[
                { label: 'Tổng quan', href: '/dashboard' },
                { label: 'Phòng ban' },
            ]} />

            {/* Toast */}
            {toast && (
                <div className={`fixed top-6 right-6 z-[60] flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-xl border text-sm font-medium transition-all
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
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Quản lý phòng ban</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">Tạo và quản lý các phòng ban trong hệ thống</p>
                </div>
                <button
                    onClick={() => { setEditDept(null); setModalOpen(true); }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
                >
                    <Plus className="w-4 h-4" />
                    Thêm phòng ban
                </button>
            </div>

            {/* Search */}
            <div className="flex items-center gap-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3.5 py-2.5 max-w-sm shadow-sm">
                <Search className="w-4 h-4 text-slate-400" />
                <input
                    type="text"
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    placeholder="Tìm kiếm phòng ban..."
                    className="bg-transparent outline-none text-sm text-slate-700 dark:text-slate-300 w-full placeholder-slate-400"
                />
            </div>

            {/* Department Cards */}
            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {[0, 1, 2].map(i => (
                        <div key={i} className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm animate-pulse">
                            <div className="h-5 w-32 bg-slate-100 dark:bg-slate-800 rounded mb-3" />
                            <div className="h-3 w-48 bg-slate-100 dark:bg-slate-800 rounded mb-4" />
                            <div className="h-3 w-20 bg-slate-100 dark:bg-slate-800 rounded" />
                        </div>
                    ))}
                </div>
            ) : filtered.length === 0 ? (
                <div className="text-center py-16">
                    <Building2 className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
                    <p className="text-slate-500 dark:text-slate-400 text-sm">
                        {search ? 'Không tìm thấy phòng ban nào' : 'Chưa có phòng ban nào'}
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {filtered.map(dept => (
                        <div key={dept.id} className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-shadow p-6 group">
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-primary-600/10 dark:bg-primary-500/10 flex items-center justify-center">
                                        <Building2 className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-slate-900 dark:text-white text-sm">{dept.name}</h3>
                                        <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">{dept.description || 'Không có mô tả'}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={() => { setEditDept(dept); setModalOpen(true); }}
                                        className="p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
                                    >
                                        <Pencil className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                        onClick={() => setDeleteDept(dept)}
                                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            </div>
                            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                                <Users className="w-3.5 h-3.5" />
                                <span>{dept.user_count} thành viên</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Department Modal */}
            {modalOpen && (
                <DepartmentModal
                    editDept={editDept}
                    onClose={() => { setModalOpen(false); setEditDept(null); }}
                    onSave={handleSave}
                />
            )}

            {/* Delete Confirmation */}
            {deleteDept && (
                <ConfirmDeleteModal
                    title="Xóa phòng ban"
                    description={
                        <>
                            Bạn có chắc chắn muốn xóa phòng ban{' '}
                            <span className="font-semibold text-slate-700 dark:text-slate-200">"{deleteDept.name}"</span>?
                            {deleteDept.user_count > 0 && (
                                <span className="block mt-1 text-amber-600 dark:text-amber-400">
                                    Phòng ban này có {deleteDept.user_count} thành viên. Họ sẽ không còn thuộc phòng ban nào.
                                </span>
                            )}
                        </>
                    }
                    onClose={() => setDeleteDept(null)}
                    onConfirm={() => handleDelete(deleteDept.id)}
                />
            )}
        </div>
    );
}


function DepartmentModal({ editDept, onClose, onSave }) {
    const [form, setForm] = useState({ name: '', description: '' });
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (editDept) {
            setForm({ name: editDept.name, description: editDept.description || '' });
        } else {
            setForm({ name: '', description: '' });
        }
    }, [editDept]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        await onSave(form);
        setSaving(false);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
            <div className="relative bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-md mx-4 shadow-2xl border border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-primary-600/10 flex items-center justify-center">
                            <Building2 className="w-4 h-4 text-primary-700 dark:text-primary-400" />
                        </div>
                        <h3 className="text-base font-bold text-slate-900 dark:text-white">
                            {editDept ? 'Chỉnh sửa phòng ban' : 'Thêm phòng ban mới'}
                        </h3>
                    </div>
                    <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                        <X className="w-4 h-4" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Tên phòng ban</label>
                        <input
                            required
                            value={form.name}
                            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                            placeholder="VD: Kỹ thuật, Nhân sự..."
                            className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 outline-none focus:ring-2 focus:ring-primary-600/30 focus:border-primary-600 transition-all"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Mô tả</label>
                        <textarea
                            rows={3}
                            value={form.description}
                            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                            placeholder="Mô tả ngắn về phòng ban..."
                            className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 outline-none focus:ring-2 focus:ring-primary-600/30 focus:border-primary-600 transition-all resize-none"
                        />
                    </div>

                    <div className="flex gap-3 pt-2">
                        <button type="button" onClick={onClose} className="flex-1 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                            Hủy
                        </button>
                        <button type="submit" disabled={saving} className="flex-1 py-2.5 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                            {saving && <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                            {editDept ? 'Lưu thay đổi' : 'Thêm phòng ban'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
