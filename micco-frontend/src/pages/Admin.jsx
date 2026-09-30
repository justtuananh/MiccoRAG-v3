import { useState, useEffect, useRef, useCallback } from 'react';
import {
    Users, HardDrive, Zap,
    Plus,
    CheckCircle2, AlertCircle, Brain, Building2,
} from 'lucide-react';
import { useAuth } from '../context/authContextCore';
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
    const [appliedUserFilters, setAppliedUserFilters] = useState({ search: '', role: 'Tất cả' });
    // R5-2 pattern: distinguish "no users match" from "failed to load".
    const [usersError, setUsersError] = useState(null);

    // -- Logs State --
    const [activeTab, setActiveTab] = useState('users'); // 'users' | 'logs' | 'departments'
    const [logs, setLogs] = useState([]);
    const [logTotal, setLogTotal] = useState(0);
    const [logPage, setLogPage] = useState(1);
    const [logSearch, setLogSearch] = useState('');
    const [appliedLogSearch, setAppliedLogSearch] = useState('');
    const [logAccessReason, setLogAccessReason] = useState('');
    const [selectedLog, setSelectedLog] = useState(null);
    // R5-2 pattern: distinguish "no logs match" from "failed to load".
    const [logsError, setLogsError] = useState(null);

    const [openMenu, setOpenMenu] = useState(null);
    const [addModal, setAddModal] = useState(false);
    const [editUser, setEditUser] = useState(null);
    const [deleteUser, setDeleteUser] = useState(null);
    const [toast, setToast] = useState(null);
    const userSearchDebounce = useRef(null);
    const logSearchDebounce = useRef(null);

    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const logTotalPages = Math.max(1, Math.ceil(logTotal / LOG_PAGE_SIZE));

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type, id: Date.now() });
        setTimeout(() => setToast(null), 3500);
    };

    const fetchStats = useCallback(async () => {
        try {
            const res = await authFetch('/api/admin/stats');
            if (res.ok) setStats(await res.json());
        } catch { /* silent */ }
    }, [authFetch]);

    const fetchUsers = useCallback(async (p, filters = appliedUserFilters) => {
        try {
            const params = new URLSearchParams({ page: p, page_size: PAGE_SIZE });
            if (filters.search) params.append('search', filters.search);
            if (filters.role !== 'Tất cả') params.append('role', filters.role);
            const res = await authFetch(`/api/admin/users?${params}`);
            if (res.ok) {
                const data = await res.json();
                setUsers(data.users);
                setTotal(data.total);
                setUsersError(null);
            } else if (res.status !== 401) {
                // 401 → authFetch already triggered logout()/redirect.
                setUsersError('Không thể tải danh sách người dùng. Vui lòng thử lại.');
            }
        } catch {
            setUsersError('Mất kết nối mạng. Vui lòng kiểm tra kết nối và thử lại.');
        }
    }, [authFetch, appliedUserFilters]);

    const fetchLogs = useCallback(async (p, reveal = false, reason = '', searchFilter = appliedLogSearch) => {
        try {
            const params = new URLSearchParams({ page: p, page_size: LOG_PAGE_SIZE });
            if (searchFilter) params.append('search', searchFilter);
            if (reveal && reason.trim()) {
                params.append('include_content', 'true');
                params.append('reason', reason.trim());
            }
            const res = await authFetch(`/api/admin/chat-logs?${params}`);
            if (res.ok) {
                const data = await res.json();
                setLogs(data.logs);
                setLogTotal(data.total);
                setLogsError(null);
            } else if (res.status !== 401) {
                setLogsError('Không thể tải nhật ký. Vui lòng thử lại.');
            }
        } catch {
            setLogsError('Mất kết nối mạng. Vui lòng kiểm tra kết nối và thử lại.');
        }
    }, [authFetch, appliedLogSearch]);

    useEffect(() => {
        const frame = requestAnimationFrame(() => fetchStats());
        return () => cancelAnimationFrame(frame);
    }, [fetchStats]);

    // Users effect
    useEffect(() => {
        clearTimeout(userSearchDebounce.current);
        userSearchDebounce.current = setTimeout(() => {
            setPage(1);
            setAppliedUserFilters(previous =>
                previous.search === search && previous.role === roleFilter
                    ? previous : { search, role: roleFilter }
            );
            fetchUsers(1, { search, role: roleFilter });
        }, 350);
        return () => clearTimeout(userSearchDebounce.current);
    }, [search, roleFilter, fetchUsers]);
    useEffect(() => {
        if (activeTab !== 'users') return;
        const frame = requestAnimationFrame(() => fetchUsers(page));
        return () => cancelAnimationFrame(frame);
    }, [page, activeTab, fetchUsers]);

    // Logs effect
    useEffect(() => {
        clearTimeout(logSearchDebounce.current);
        logSearchDebounce.current = setTimeout(() => {
            setLogPage(1);
            setAppliedLogSearch(logSearch);
            fetchLogs(1, false, '', logSearch);
        }, 350);
        return () => clearTimeout(logSearchDebounce.current);
    }, [logSearch, fetchLogs]);
    useEffect(() => {
        if (activeTab !== 'logs') return;
        const frame = requestAnimationFrame(() => fetchLogs(logPage));
        return () => cancelAnimationFrame(frame);
    }, [logPage, activeTab, fetchLogs]);

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
                await fetchUsers(page);
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
                await fetchUsers(page);
                await fetchStats();
                showToast('Đã vô hiệu hóa tài khoản');
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

    // Backend chưa có endpoint POST /api/admin/communities/build (trả 404).
    // Nút bị vô hiệu hoá; nếu vẫn kích hoạt được thì báo lỗi rõ ràng thay vì im lặng.
    const handleBuildCommunities = () => {
        showToast('Tính năng "Build Communities" chưa được backend hỗ trợ (endpoint chưa tồn tại)', 'error');
    };

    // Close menu on outside click
    useEffect(() => {
        const h = () => setOpenMenu(null);
        document.addEventListener('click', h);
        return () => document.removeEventListener('click', h);
    }, []);

    const isActive = (u) => u.is_active !== false;

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

            {/* ── Toast Notification ─────────────────────────────────────── */}
            {toast && (
                <div
                    key={toast.id}
                    className={`fixed top-20 right-6 z-[100] flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-2xl border text-sm font-semibold
                        animate-slide-in-right
                        ${toast.type === 'error'
                            ? 'bg-gradient-to-r from-red-50 to-rose-50 dark:from-red-900/40 dark:to-rose-900/40 border-red-200 dark:border-red-700 text-red-700 dark:text-red-200'
                            : 'bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-900/40 dark:to-green-900/40 border-emerald-200 dark:border-emerald-700 text-emerald-700 dark:text-emerald-200'
                        }`}
                >
                    {toast.type === 'error' ? (
                        <AlertCircle className="w-5 h-5 text-red-500 dark:text-red-400 shrink-0" />
                    ) : (
                        <CheckCircle2 className="w-5 h-5 text-emerald-500 dark:text-emerald-400 shrink-0" />
                    )}
                    <span>{toast.msg}</span>
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
                    loadError={usersError}
                    onRetry={() => fetchUsers(page)}
                />
            ) : activeTab === 'logs' ? (
                <>
                <form className="mb-4 flex flex-wrap gap-2" onSubmit={(event) => { event.preventDefault(); fetchLogs(logPage, true, logAccessReason); }}>
                    <label className="flex-1">Lý do hỗ trợ cần xem nội dung hội thoại
                        <input required value={logAccessReason} onChange={(event) => setLogAccessReason(event.target.value)} className="w-full border rounded-lg px-3 py-2" maxLength={500} />
                    </label>
                    <button type="submit" disabled={!logAccessReason.trim()} className="px-4 py-2 rounded-lg bg-primary-600 text-white disabled:opacity-50">Xem nội dung và ghi nhật ký truy cập</button>
                </form>
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
                    loadError={logsError}
                    onRetry={() => fetchLogs(logPage)}
                />
                </>
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
                            disabled
                            title="Backend chưa hỗ trợ tính năng này"
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                        >
                            <Zap className="w-4 h-4" />
                            Build Communities
                        </button>
                        <p className="text-xs text-slate-400 max-w-xs">
                            Phân tích cộng đồng trong knowledge graph (Leiden algorithm + LLM summary) —
                            <span className="text-amber-500"> chưa khả dụng, backend chưa có endpoint</span>
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
                    title="Vô hiệu hóa tài khoản"
                    description={
                        <>
                            Bạn có chắc chắn muốn vô hiệu hóa{' '}
                            <span className="font-semibold text-slate-700 dark:text-slate-200">"{deleteUser.name}"</span>?
                            {' '}Tài khoản sẽ không thể đăng nhập cho đến khi được kích hoạt lại.
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
