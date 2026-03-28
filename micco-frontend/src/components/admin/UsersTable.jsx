import {
    Search, Download, ChevronLeft, ChevronRight,
    Edit3, Trash2, MoreVertical, Users,
} from 'lucide-react';
import { ROLES } from './UserModal';
import { getInitials } from '../../utils/formatters';

// ── helpers ────────────────────────────────────────────────────────────────────
const avatarPalette = [
    'bg-primary-600', 'bg-emerald-500', 'bg-violet-500',
    'bg-orange-500', 'bg-teal-500', 'bg-rose-500', 'bg-amber-500',
];
function avatarBg(name = '') {
    let h = 0; for (const c of name) h += c.charCodeAt(0);
    return avatarPalette[h % avatarPalette.length];
}
function timeAgo(dateStr) {
    if (!dateStr) return '—';
    const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000);
    if (diff < 60) return 'vừa xong';
    if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`;
    if (diff < 86400 * 7) return `${Math.floor(diff / 86400)} ngày trước`;
    return new Date(dateStr).toLocaleDateString('vi-VN', { day: 'numeric', month: 'numeric', year: 'numeric' });
}

const ROLE_COLORS = {
    'Admin': 'bg-primary-600/10 text-primary-700 dark:bg-primary-500/20 dark:text-primary-300',
    'Trưởng phòng': 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300',
    'Nhân viên': 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
};
export const PAGE_SIZE = 10;

// ── Component ──────────────────────────────────────────────────────────────────
export default function UsersTable({
    users, total, page, totalPages,
    search, roleFilter, openMenu, currentUserId,
    onSearchChange, onRoleFilterChange, onExport,
    onPageChange, onOpenMenu,
    onEdit, onDelete,
    isActive,
}) {
    const startRow = (page - 1) * PAGE_SIZE + 1;
    const endRow = Math.min(page * PAGE_SIZE, total);

    return (
        <section className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">

            {/* Table toolbar */}
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <h3 className="font-bold text-lg text-slate-900 dark:text-white">Quản lý người dùng</h3>
                <div className="flex items-center gap-2 flex-wrap">
                    {/* Search */}
                    <div className="relative flex items-center">
                        <Search className="absolute left-3 w-4 h-4 text-slate-400 pointer-events-none" />
                        <input
                            value={search}
                            onChange={e => onSearchChange(e.target.value)}
                            placeholder="Tìm kiếm người dùng..."
                            className="pl-9 pr-3 py-1.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none focus:ring-2 focus:ring-primary-600/30 focus:border-primary-600 w-48 transition-all"
                        />
                    </div>
                    {/* Role filter */}
                    <select
                        value={roleFilter}
                        onChange={e => onRoleFilterChange(e.target.value)}
                        className="py-1.5 pl-3 pr-8 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 outline-none focus:ring-2 focus:ring-primary-600/30 cursor-pointer appearance-none"
                    >
                        {ROLES.map(r => <option key={r} value={r}>{r === 'Tất cả' ? 'Tất cả vai trò' : r}</option>)}

                    </select>
                    <button
                        onClick={onExport}
                        className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400 text-sm font-medium px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors border border-slate-200 dark:border-slate-700"
                    >
                        <Download className="w-4 h-4" /> Xuất
                    </button>
                </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-slate-50 dark:bg-slate-800/50">
                            <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Tên</th>
                            <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Vai trò</th>
                            <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Phòng ban</th>
                            <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Trạng thái</th>
                            <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Ngày tham gia</th>
                            <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {users.length === 0 && (
                            <tr>
                                <td colSpan={6} className="px-6 py-14 text-center">
                                    <Users className="w-10 h-10 text-slate-200 dark:text-slate-700 mx-auto mb-3" />
                                    <p className="text-slate-500 dark:text-slate-400 font-medium text-sm">Không tìm thấy người dùng</p>
                                    <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Hãy điều chỉnh bộ lọc hoặc tìm kiếm</p>
                                </td>
                            </tr>
                        )}
                        {users.map((u) => {
                            const active = isActive(u);
                            const isSelf = u.id === currentUserId;
                            return (
                                <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                                    {/* Name */}
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-10 h-10 rounded-full ${isSelf ? 'bg-primary-600' : avatarBg(u.name)} flex items-center justify-center text-white font-bold text-sm shrink-0`}>
                                                {getInitials(u.name)}
                                            </div>
                                            <div>
                                                <p className="text-sm font-semibold text-slate-900 dark:text-white">
                                                    {u.name}
                                                    {isSelf && <span className="ml-2 text-[10px] font-bold text-primary-600 dark:text-primary-400 uppercase">(bạn)</span>}
                                                </p>
                                                <p className="text-xs text-slate-500 dark:text-slate-400">{u.email}</p>
                                            </div>
                                        </div>
                                    </td>
                                    {/* Role */}
                                    <td className="px-6 py-4">
                                        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${ROLE_COLORS[u.role] || ROLE_COLORS['Nhân viên']}`}>
                                            {u.role}
                                        </span>
                                    </td>
                                    {/* Department */}
                                    <td className="px-6 py-4">
                                        {u.department_name ? (
                                            <span className="text-sm text-slate-700 dark:text-slate-300">{u.department_name}</span>
                                        ) : (
                                            <span className="text-xs text-slate-400 italic">Chưa phân</span>
                                        )}
                                    </td>
                                    {/* Status */}
                                    <td className="px-6 py-4">
                                        <span className={`flex items-center gap-1.5 text-xs font-semibold ${active ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400 dark:text-slate-500'}`}>
                                            <span className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                                            {active ? 'Hoạt động' : 'Không hoạt động'}
                                        </span>
                                    </td>
                                    {/* Joined */}
                                    <td className="px-6 py-4 text-sm text-slate-500 dark:text-slate-400">
                                        {timeAgo(u.created_at)}
                                    </td>
                                    {/* Actions */}
                                    <td className="px-6 py-4 text-right relative">
                                        <button
                                            onClick={e => { e.stopPropagation(); onOpenMenu(openMenu === u.id ? null : u.id); }}
                                            className="text-slate-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors p-1 rounded"
                                        >
                                            <MoreVertical className="w-4 h-4" />
                                        </button>
                                        {openMenu === u.id && (
                                            <div className="absolute right-6 top-10 z-20 w-40 bg-white dark:bg-slate-900 rounded-xl shadow-xl border border-slate-100 dark:border-slate-800 py-1 text-left" onClick={e => e.stopPropagation()}>
                                                <button
                                                    onClick={() => { onEdit(u); onOpenMenu(null); }}
                                                    className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                                                >
                                                    <Edit3 className="w-4 h-4 text-slate-400" /> Chỉnh sửa
                                                </button>
                                                {!isSelf && (
                                                    <>
                                                        <div className="my-1 border-t border-slate-100 dark:border-slate-800" />
                                                        <button
                                                            onClick={() => { onDelete(u); onOpenMenu(null); }}
                                                            className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                                                        >
                                                            <Trash2 className="w-4 h-4" /> Xóa
                                                        </button>
                                                    </>
                                                )}
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Pagination footer */}
            <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                    {total > 0 ? `Hiển thị ${startRow} đến ${endRow} trong số ${total.toLocaleString()} kết quả` : 'Không có kết quả'}
                </p>
                <div className="flex items-center gap-1.5">
                    <button
                        onClick={() => onPageChange(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                    >
                        <ChevronLeft className="w-3.5 h-3.5" /> Trước
                    </button>

                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let p;
                        if (totalPages <= 5) p = i + 1;
                        else if (page <= 3) p = i + 1;
                        else if (page >= totalPages - 2) p = totalPages - 4 + i;
                        else p = page - 2 + i;
                        return (
                            <button
                                key={p}
                                onClick={() => onPageChange(p)}
                                className={`w-8 h-8 rounded-lg border text-sm font-medium transition-colors ${page === p
                                        ? 'bg-primary-600 border-primary-600 text-white'
                                        : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
                                    }`}
                            >
                                {p}
                            </button>
                        );
                    })}

                    <button
                        onClick={() => onPageChange(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                    >
                        Tiếp <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>
        </section>
    );
}
