import { useState, useEffect, useRef } from 'react';
import {
    Users, HardDrive, Zap,
    Plus,
    CheckCircle2, AlertCircle, Brain, RefreshCw, Building2,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import StatCard from '../components/admin/StatCard';
import UserModal from '../components/admin/UserModal';
import UsersTable, { PAGE_SIZE } from '../components/admin/UsersTable';
import LogsTable, { LOG_PAGE_SIZE, LogDetailModal } from '../components/admin/LogsTable';
import ConfirmDeleteModal from '../components/shared/ConfirmDeleteModal';
import Breadcrumb from '../components/shared/Breadcrumb';
import Departments from './Departments';

// ── Main ───────────────────────────────────────────────────────────────────────
export default function Admin() {
    const { authFetch, user: currentUser } = useAuth();

    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [roleFilter, setRoleFilter] = useState('Tất cả');
    
    // -- Logs State --
    const [activeTab, setActiveTab] = useState('users'); // 'users' | 'logs' | 'departments'
    const [logs, setLogs] = useState([]);
    const [logTotal, setLogTotal] = useState(0);
    const [logPage, setLogPage] = useState(1);
    const [logSearch, setLogSearch] = useState('');
    const [selectedLog, setSelectedLog] = useState(null);

    const [openMenu, setOpenMenu] = useState(null);
    const [addModal, setAddModal] = useState(false);
    const [editUser, setEditUser] = useState(null);
    const [deleteUser, setDeleteUser] = useState(null);
    const [toast, setToast] = useState(null);
    const searchDebounce = useRef(null);
    const [buildingCommunities, setBuildingCommunities] = useState(false);

    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const logTotalPages = Math.max(1, Math.ceil(logTotal / LOG_PAGE_SIZE));

    useEffect(() => { fetchStats(); }, []);
    
    // Users effect
    useEffect(() => {
        clearTimeout(searchDebounce.current);
        searchDebounce.current = setTimeout(() => { setPage(1); fetchUsers(1); }, 350);
        return () => clearTimeout(searchDebounce.current);
    }, [search, roleFilter]);
    useEffect(() => { if (activeTab === 'users') fetchUsers(page); }, [page, activeTab]);

    // Logs effect
    useEffect(() => {
        clearTimeout(searchDebounce.current);
        searchDebounce.current = setTimeout(() => { setLogPage(1); fetchLogs(1); }, 350);
        return () => clearTimeout(searchDebounce.current);
    }, [logSearch]);
    useEffect(() => { if (activeTab === 'logs') fetchLogs(logPage); }, [logPage, activeTab]);

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const fetchStats = async () => {
        try {
            const res = await authFetch('/api/admin/stats');
            if (res.ok) setStats(await res.json());
        } catch { /* silent */ }
    };

    const fetchUsers = async (p = page) => {
        try {
            const params = new URLSearchParams({ page: p, page_size: PAGE_SIZE });
            if (search) params.append('search', search);
            if (roleFilter !== 'Tất cả') params.append('role', roleFilter);
            const res = await authFetch(`/api/admin/users?${params}`);
            if (res.ok) {
                const data = await res.json();
                setUsers(data.users);
                setTotal(data.total);
            }
        } catch { /* silent */ }
    };

    const fetchLogs = async (p = logPage) => {
        try {
            const params = new URLSearchParams({ page: p, page_size: LOG_PAGE_SIZE });
            if (logSearch) params.append('search', logSearch);
            const res = await authFetch(`/api/admin/chat-logs?${params}`);
            if (res.ok) {
                const data = await res.json();
                setLogs(data.logs);
                setLogTotal(data.total);
            }
        } catch { /* silent */ }
    };

    const handleSave = async (form) => {
        try {
            const isEdit = !!editUser;
            const url = isEdit ? `/api/admin/users/${editUser.id}` : '/api/admin/users';
            const method = isEdit ? 'PUT' : 'POST';
            const payload = { ...form };
            if (isEdit && !payload.password) delete payload.password;

            const res = await authFetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (res.ok) {
                setAddModal(false);
                setEditUser(null);
                await fetchUsers();
                await fetchStats();
                showToast(isEdit ? `Cập nhật ${form.name} thành công` : `Thêm ${form.name} thành công`);
            } else {
                const err = await res.json();
                showToast(err.detail || 'Thao tác thất bại', 'error');
            }
        } catch { showToast('Có lỗi xảy ra', 'error'); }
    };

    const handleDelete = async (id) => {
        try {
            const res = await authFetch(`/api/admin/users/${id}`, { method: 'DELETE' });
            if (res.ok || res.status === 204) {
                setDeleteUser(null);
                await fetchUsers();
                await fetchStats();
                showToast('Xóa người dùng thành công');
            } else {
                const err = await res.json();
                showToast(err.detail || 'Xóa thất bại', 'error');
            }
        } catch { showToast('Xóa thất bại', 'error'); }
    };

    const handleExport = () => {
        if (activeTab === 'users') {
            const rows = [['Tên', 'Email', 'Vai trò', 'Ngày tạo'], ...users.map(u => [u.name, u.email, u.role, u.created_at])];
            const csv = rows.map(r => r.map(v => `"${v}"`).join(',')).join('\n');
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = 'users.csv'; a.click();
            URL.revokeObjectURL(url);
        } else {
            const rows = [['ID', 'Thời gian', 'IP', 'Phương thức', 'Độ trễ', 'Câu hỏi', 'Trả lời'], ...logs.map(l => [l.id, l.timestamp, l.ip_address, l.method, l.response_time, l.question, l.answer])];
            const csv = rows.map(r => r.map(v => `"${v}"`).join(',')).join('\n');
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = 'system_logs.csv'; a.click();
            URL.revokeObjectURL(url);
        }
    };

    const handleBuildCommunities = async () => {
        setBuildingCommunities(true);
        try {
            const res = await authFetch('/api/admin/communities/build', { method: 'POST' });
            if (res.ok) {
                const data = await res.json();
                showToast(`Build communities xong: ${data.communities_created || 0} communities tạo mới`);
            } else {
                const err = await res.json().catch(() => ({}));
                showToast(err.detail || 'Build communities thất bại', 'error');
            }
        } catch { showToast('Có lỗi xảy ra', 'error'); }
        finally { setBuildingCommunities(false); }
    };

    // Close menu on outside click
    useEffect(() => {
        const h = () => setOpenMenu(null);
        document.addEventListener('click', h);
        return () => document.removeEventListener('click', h);
    }, []);

    // Derived user status (based on recency of creation as approximation)
    const isActive = (u) => {
        if (!u.created_at) return false;
        return (Date.now() - new Date(u.created_at)) < 30 * 24 * 3600 * 1000;
    };

    const statCards = stats ? [
        { icon: Users, label: 'Tổng người dùng', value: stats.totalUsers?.toLocaleString(), change: stats.totalUsersChange, positive: true },
        { icon: HardDrive, label: 'Dung lượng dùng', value: stats.storageUsed, change: stats.storageChange, positive: true },
        { icon: Zap, label: 'Phiên hoạt động', value: stats.activeSessions, change: stats.activeSessionsChange, positive: false },
    ] : [];

    return (
        <div className="space-y-6 px-2 md:px-4">

            {/* ── Breadcrumb ─────────────────────────────────────────────── */}
            <div className="px-2 pt-4">
                <Breadcrumb items={[
                    { label: 'Tổng quan', href: '/dashboard' },
                    { label: 'Quản trị' },
                ]} />
            </div>

            {/* ── Toast ──────────────────────────────────────────────────── */}
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

            {/* ── Header ─────────────────────────────────────────────────── */}
            <div className="flex items-center justify-between px-2">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Tổng quan hệ thống</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">Quản lý người dùng, vai trò và hoạt động hệ thống</p>
                </div>
                <button
                    onClick={() => { setEditUser(null); setAddModal(true); }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
                >
                    <Plus className="w-4 h-4" />
                    Thêm người dùng mới
                </button>
            </div>

            {/* ── Stat Cards ─────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 px-2">
                {statCards.map(s => (
                    <StatCard key={s.label} {...s} />
                ))}
            </div>

            {/* ── Tabs ─────────────────────────────────────────────────── */}
            <div className="flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-800/50 rounded-xl w-fit">
                <button
                    onClick={() => setActiveTab('users')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${activeTab === 'users'
                        ? 'bg-white dark:bg-slate-900 text-primary-600 shadow-sm'
                        : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Users className="w-4 h-4" />
                        Người dùng
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('logs')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${activeTab === 'logs'
                        ? 'bg-white dark:bg-slate-900 text-primary-600 shadow-sm'
                        : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4" />
                        Lịch sử hệ thống
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('departments')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${activeTab === 'departments'
                        ? 'bg-white dark:bg-slate-900 text-primary-600 shadow-sm'
                        : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4" />
                        Phòng ban
                    </div>
                </button>
            </div>

            {/* ── Table Content ───────────────────────────────────────────── */}
            <div className="px-2">
            {activeTab === 'users' ? (
                <UsersTable
                    users={users}
                    total={total}
                    page={page}
                    totalPages={totalPages}
                    search={search}
                    roleFilter={roleFilter}
                    openMenu={openMenu}
                    currentUserId={currentUser?.id}
                    onSearchChange={setSearch}
                    onRoleFilterChange={setRoleFilter}
                    onExport={handleExport}
                    onPageChange={setPage}
                    onOpenMenu={setOpenMenu}
                    onEdit={(u) => { setEditUser(u); setAddModal(true); }}
                    onDelete={setDeleteUser}
                    isActive={isActive}
                />
            ) : activeTab === 'logs' ? (
                <LogsTable
                    logs={logs}
                    total={logTotal}
                    page={logPage}
                    totalPages={logTotalPages}
                    search={logSearch}
                    onSearchChange={setLogSearch}
                    onPageChange={setLogPage}
                    onExport={handleExport}
                    onViewDetail={setSelectedLog}
                />
            ) : activeTab === 'departments' ? (
                <Departments embedded={true} />
            ) : null}
            </div>

            {/* ── AI Tools ────────────────────────────────────────────── */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm mx-2">
                <div className="flex items-center gap-2 mb-4">
                    <Brain className="w-5 h-5 text-violet-500" />
                    <h3 className="text-base font-semibold text-slate-900 dark:text-white">AI Tools</h3>
                    <span className="text-xs text-slate-400">GraphRAG Utilities</span>
                </div>
                <div className="flex flex-wrap gap-3">
                    <div className="flex flex-col gap-1">
                        <button
                            onClick={handleBuildCommunities}
                            disabled={buildingCommunities}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium transition-colors disabled:opacity-60"
                        >
                            {buildingCommunities
                                ? <RefreshCw className="w-4 h-4 animate-spin" />
                                : <Zap className="w-4 h-4" />
                            }
                            {buildingCommunities ? 'Đang xây dựng...' : 'Build Communities'}
                        </button>
                        <p className="text-xs text-slate-400 max-w-xs">
                            Phân tích cộng đồng trong knowledge graph (Leiden algorithm + LLM summary)
                        </p>
                    </div>
                </div>
            </div>

            {/* ── Modals ─────────────────────────────────────────────────── */}
            <UserModal
                open={addModal || !!editUser}
                onClose={() => { setAddModal(false); setEditUser(null); }}
                onSave={handleSave}
                editUser={editUser}
            />
            {deleteUser && (
                <ConfirmDeleteModal
                    title="Xóa người dùng"
                    description={
                        <>
                            Bạn có chắc chắn muốn xóa{' '}
                            <span className="font-semibold text-slate-700 dark:text-slate-200">"{deleteUser.name}"</span>?
                            {' '}Hành động này không thể hoàn tác.
                        </>
                    }
                    onClose={() => setDeleteUser(null)}
                    onConfirm={() => handleDelete(deleteUser.id)}
                />
            )}
            <LogDetailModal 
                log={selectedLog} 
                onClose={() => setSelectedLog(null)} 
            />
        </div>
    );
}
