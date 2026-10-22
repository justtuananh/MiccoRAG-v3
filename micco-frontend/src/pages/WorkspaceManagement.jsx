import ModalFocus from '../components/shared/ModalFocus';
import TrashPanel from '../components/shared/TrashPanel';
/**
 * WorkspaceManagement.jsx
 * Trang quản lý Workspace: tạo, sửa, xóa workspace.
 * Mỗi user chỉ thấy workspace mình có quyền truy cập.
 */
import { useState, useEffect, useCallback } from 'react';
import {
  Plus, Search, MoreVertical, Edit2, Trash2,
  Lock, Building2, Globe, X, ChevronDown, FolderKanban, AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/authContextCore';

const VISIBILITY_CONFIG = {
  private:   { label: 'Cá nhân',   icon: Lock,      color: 'text-purple-600', bg: 'bg-purple-50',    badge: 'purple' },
  department: { label: 'Phòng ban', icon: Building2, color: 'text-blue-600',   bg: 'bg-blue-50',     badge: 'blue'   },
  public:     { label: 'Công khai', icon: Globe,     color: 'text-green-600',  bg: 'bg-green-50',    badge: 'green'  },
};

const VISIBILITY_OPTIONS = [
  { value: 'private',   label: '🔒 Cá nhân',    desc: 'Chỉ mình tôi truy cập được' },
  { value: 'department', label: '🏢 Phòng ban',  desc: 'Mọi người trong phòng ban truy cập' },
  { value: 'public',    label: '🌐 Công khai',  desc: 'Tất cả nhân viên đều truy cập được' },
];

const SEARCH_MODES = [
  { value: 'hybrid',       label: 'Hybrid (Vector + Keyword)' },
  { value: 'vector_only', label: 'Chỉ Vector Search' },
  { value: 'naive',       label: 'Naive (BM25)' },
  { value: 'local',       label: 'Local Search' },
  { value: 'global',      label: 'Global Search' },
];

export default function WorkspaceManagement() {
  const { authFetch, user } = useAuth();
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  // R5-2 pattern: distinguish "no workspaces yet" from "failed to load".
  const [loadError, setLoadError] = useState(null);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [editingWS, setEditingWS] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [openMenu, setOpenMenu] = useState(null);
  const [toast, setToast] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    name: '',
    description: '',
    visibility: 'private',
    search_mode: 'hybrid',
  });

  // ── Fetch ──────────────────────────────────────────────────────────
  const fetchWorkspaces = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authFetch('/api/v1/workspaces');
      if (res.ok) {
        const data = await res.json();
        setWorkspaces(data);
        setLoadError(null);
      } else if (res.status === 401) {
        // Session expired — authFetch already triggered logout()/redirect.
      } else {
        setLoadError('Không thể tải danh sách workspace. Vui lòng thử lại.');
      }
    } catch {
      setLoadError('Mất kết nối mạng. Vui lòng kiểm tra kết nối và thử lại.');
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  useEffect(() => { fetchWorkspaces(); }, [fetchWorkspaces]);

  // ── RBAC helpers ──────────────────────────────────────────────────
  const canCreateType = (visibility) => {
    if (visibility === 'public')   return user?.role === 'Admin';
    if (visibility === 'department') return ['Admin', 'Trưởng phòng'].includes(user?.role);
    return true; // private
  };

  const canModify = (ws) => {
    if (user?.role === 'Admin') return true;
    if (ws.visibility === 'private' && ws.owner_id === user?.id) return true;
    if (ws.visibility === 'department' && ws.department_id === user?.department_id && user?.role === 'Trưởng phòng') return true;
    return false;
  };

  const canDelete = (ws) => canModify(ws);

  // ── Filter ────────────────────────────────────────────────────────
  const filtered = workspaces.filter(ws => {
    const matchType = filterType === 'all' || ws.visibility === filterType;
    const matchSearch = !search ||
      ws.name.toLowerCase().includes(search.toLowerCase()) ||
      (ws.description || '').toLowerCase().includes(search.toLowerCase());
    return matchType && matchSearch;
  });

  // ── Form actions ─────────────────────────────────────────────────
  const openCreate = () => {
    setEditingWS(null);
    setForm({ name: '', description: '', visibility: 'private', search_mode: 'hybrid' });
    setShowModal(true);
  };

  const openEdit = (ws) => {
    setEditingWS(ws);
    setForm({
      name: ws.name || '',
      description: ws.description || '',
      visibility: ws.visibility || 'private',
      search_mode: ws.search_mode || 'hybrid',
    });
    setShowModal(true);
    setOpenMenu(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSubmitting(true);

    try {
      const method = editingWS ? 'PUT' : 'POST';
      const url = editingWS
        ? `/api/v1/workspaces/${editingWS.id}`
        : '/api/v1/workspaces';

      const payload = editingWS
        ? { name: form.name, description: form.description, search_mode: form.search_mode }
        : form;
      const res = await authFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setShowModal(false);
        setEditingWS(null);
        fetchWorkspaces();
        showToast(editingWS ? 'Đã cập nhật workspace!' : 'Đã tạo workspace mới!');
      } else {
        const err = await res.json();
        showToast(err.detail || 'Có lỗi xảy ra', 'error');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (ws) => {
    const res = await authFetch(`/api/v1/workspaces/${ws.id}`, { method: 'DELETE' });
    if (res.ok) {
      fetchWorkspaces();
      setShowDeleteConfirm(null);
      showToast('Đã xóa workspace!');
    } else {
      const err = await res.json();
      showToast(err.detail || 'Không thể xóa workspace', 'error');
    }
  };

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type, id: Date.now() });
    setTimeout(() => setToast(null), 3500);
  };

  // Close dropdown on outside click
  useEffect(() => {
    if (!openMenu) return;
    const handler = () => setOpenMenu(null);
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, [openMenu]);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            🗂️ Quản lý Workspace
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Tạo và quản lý không gian làm việc cho tài liệu & tri thức
          </p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition shadow-sm"
        >
          <Plus size={18} />
          Tạo mới
        </button>
      </div>

      <TrashPanel listPath="/api/v1/workspaces/trash" restorePath={id => `/api/v1/workspaces/${id}/restore`} onRestored={fetchWorkspaces} />
      {/* ── Toolbar ── */}
      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Tìm kiếm workspace..."
            className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 self-start">
          {[
            { key: 'all',        label: 'Tất cả' },
            { key: 'private',    label: '🔒 Cá nhân' },
            { key: 'department', label: '🏢 Phòng ban' },
            { key: 'public',     label: '🌐 Công khai' },
          ].map(f => (
            <button
              key={f.key}
              onClick={() => setFilterType(f.key)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition whitespace-nowrap ${
                filterType === f.key
                  ? 'bg-white dark:bg-gray-700 shadow text-primary-600 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Stats cards ── */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { key: 'private',   label: 'Cá nhân',   icon: Lock,      color: 'purple' },
          { key: 'department', label: 'Phòng ban', icon: Building2, color: 'blue'   },
          { key: 'public',   label: 'Công khai', icon: Globe,     color: 'green'  },
        ].map(stat => {
          const count = workspaces.filter(w => w.visibility === stat.key).length;
          const Icon = stat.icon;
          const colors = {
            purple: 'bg-purple-50 dark:bg-purple-950 border-purple-200 dark:border-purple-800 text-purple-600',
            blue:   'bg-blue-50   dark:bg-blue-950   border-blue-200   dark:border-blue-800   text-blue-600',
            green:  'bg-green-50  dark:bg-green-950  border-green-200  dark:border-green-800  text-green-600',
          };
          return (
            <div key={stat.key} className={`flex items-center gap-3 p-3 rounded-xl border ${colors[stat.color]}`}>
              <Icon size={20} />
              <div>
                <div className="text-lg font-bold">{count}</div>
                <div className="text-xs font-medium">{stat.label}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Table ── */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : loadError ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <AlertCircle size={48} className="mb-3 text-red-300 dark:text-red-500/40" />
            <p className="text-sm font-medium text-red-500 dark:text-red-400">{loadError}</p>
            <button onClick={fetchWorkspaces} className="mt-2 text-sm text-primary-600 hover:underline">
              Thử lại
            </button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <FolderKanban size={48} className="mb-3 opacity-40" />
            <p className="text-sm font-medium">Không có workspace nào</p>
            <button onClick={openCreate} className="mt-2 text-sm text-primary-600 hover:underline">
              Tạo workspace đầu tiên
            </button>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-800 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <th className="px-4 py-3">Tên</th>
                <th className="px-4 py-3">Loại</th>
                <th className="px-4 py-3">Mô tả</th>
                <th className="px-4 py-3 text-center">Tài liệu</th>
                <th className="px-4 py-3 text-center">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {filtered.map(ws => {
                const cfg = VISIBILITY_CONFIG[ws.visibility] || VISIBILITY_CONFIG.private;
                const Icon = cfg.icon;
                const canEdit = canModify(ws);
                const canDel = canDelete(ws);

                return (
                  <tr key={ws.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition">
                    {/* Name */}
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900 dark:text-white">{ws.name}</div>
                      {ws.department_name && (
                        <div className="text-xs text-gray-400 mt-0.5">{ws.department_name}</div>
                      )}
                    </td>

                    {/* Badge */}
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${cfg.bg} ${cfg.color}`}>
                        <Icon size={13} />
                        {cfg.label}
                      </span>
                    </td>

                    {/* Description */}
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-500 dark:text-gray-400 max-w-xs line-clamp-1">
                        {ws.description || '—'}
                      </span>
                    </td>

                    {/* Doc count */}
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center justify-center min-w-[2rem] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-sm font-medium text-gray-700 dark:text-gray-300">
                        {ws.indexed_count || 0}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-3 text-center">
                      {(canEdit || canDel) ? (
                        <div className="relative inline-block">
                          <button
                            aria-label="Thao tác kho tri thức"
                            onClick={(e) => { e.stopPropagation(); setOpenMenu(openMenu === ws.id ? null : ws.id); }}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 transition"
                          >
                            <MoreVertical size={18} />
                          </button>

                          {openMenu === ws.id && (
                            <div className="absolute right-0 top-10 z-20 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 py-1 min-w-[140px]">
                              {canEdit && (
                                <button
                                  onClick={() => openEdit(ws)}
                                  className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                                >
                                  <Edit2 size={15} />
                                  Sửa
                                </button>
                              )}
                              {canDel && (
                                <button
                                  onClick={() => { setShowDeleteConfirm(ws); setOpenMenu(null); }}
                                  className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-950 transition"
                                >
                                  <Trash2 size={15} />
                                  Xóa
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* ── Modal Tạo / Sửa ── */}
      {showModal && (
        <ModalFocus label="Tạo hoặc sửa kho tri thức" onClose={() => setShowModal(false)} className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
          <div
            className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                {editingWS ? '✏️ Sửa Workspace' : '➕ Tạo Workspace mới'}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400">
                <X size={20} />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* Tên */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                  Tên workspace <span className="text-red-500">*</span>
                </label>
                <input
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="VD: KB Kế toán, Tài liệu cá nhân..."
                  required
                  autoFocus
                />
              </div>

              {/* Loại workspace */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Loại workspace <span className="text-red-500">*</span>
                </label>
                {editingWS && <p className="text-xs text-amber-700 dark:text-amber-400 mb-2">Không thể đổi phạm vi của workspace đã tạo. Hãy tạo workspace mới với phạm vi phù hợp.</p>}
                <div className="space-y-2">
                  {VISIBILITY_OPTIONS.map(opt => {
                    // Chỉ dùng để hiển thị gợi ý — KHÔNG chặn lựa chọn của người dùng.
                    // Máy chủ mới là nơi quyết định (trả 403 kèm thông báo rõ ràng nếu
                    // không đủ quyền); tuyệt đối không âm thầm đổi lựa chọn về loại khác.
                    const allowed = canCreateType(opt.value);
                    return (
                      <label
                        key={opt.value}
                        className={`flex items-start gap-3 p-3 border rounded-xl cursor-pointer transition ${
                          form.visibility === opt.value
                            ? 'border-primary-500 bg-primary-50 dark:bg-primary-950'
                            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                        }`}
                      >
                        <input
                          type="radio"
                          name="visibility"
                          value={opt.value}
                          checked={form.visibility === opt.value}
                          onChange={() => setForm({ ...form, visibility: opt.value })}
                          disabled={!!editingWS}
                          className="mt-0.5 accent-primary-600"
                        />
                        <div>
                          <div className="font-medium text-sm text-gray-900 dark:text-white">{opt.label}</div>
                          <div className="text-xs text-gray-500 mt-0.5">{opt.desc}</div>
                          {!allowed && (
                            <div className="text-xs text-amber-600 dark:text-amber-500 mt-0.5">
                              ⚠️ Vai trò hiện tại của bạn có thể không đủ quyền tạo loại này — máy chủ sẽ báo lỗi khi lưu nếu không đủ quyền.
                            </div>
                          )}
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Mô tả */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">Mô tả</label>
                <textarea
                  value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none"
                  rows={2}
                  placeholder="Mô tả ngắn về mục đích sử dụng workspace..."
                />
              </div>

              {/* Search mode */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">Chế độ tìm kiếm</label>
                <div className="relative">
                  <select
                    value={form.search_mode}
                    onChange={e => setForm({ ...form, search_mode: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white appearance-none"
                  >
                    {SEARCH_MODES.map(m => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 font-medium text-gray-700 dark:text-gray-300 transition"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={submitting || !form.name.trim()}
                  className="flex-1 px-4 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition"
                >
                  {submitting ? 'Đang lưu...' : editingWS ? 'Lưu thay đổi' : 'Tạo mới'}
                </button>
              </div>
            </form>
          </div>
        </ModalFocus>
      )}

      {/* ── Delete Confirm ── */}
      {showDeleteConfirm && (
        <ModalFocus label="Xóa kho tri thức" onClose={() => setShowDeleteConfirm(null)} className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-100 dark:bg-red-950 mx-auto mb-4">
              <Trash2 size={24} className="text-red-600" />
            </div>
            <h2 className="text-lg font-bold text-center text-gray-900 dark:text-white mb-2">
              Xóa Workspace?
            </h2>
            <p className="text-sm text-gray-500 text-center mb-6">
              Workspace <strong>"{showDeleteConfirm.name}"</strong> sẽ được chuyển vào thùng rác và ngừng phục vụ hỏi đáp. Bạn có thể khôi phục trong 30 ngày.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="flex-1 px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 font-medium transition"
              >
                Hủy
              </button>
              <button
                onClick={() => handleDelete(showDeleteConfirm)}
                className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium transition"
              >
                Xóa
              </button>
            </div>
          </div>
        </ModalFocus>
      )}

      {/* ── Toast ── */}
      {toast && (
        <div className={`fixed bottom-6 right-6 px-4 py-3 rounded-xl shadow-lg z-50 text-white text-sm font-medium flex items-center gap-2 ${
          toast.type === 'error' ? 'bg-red-500' : 'bg-green-500'
        }`}>
          {toast.msg}
        </div>
      )}
    </div>
  );
}
