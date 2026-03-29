import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Trash2, CheckCircle2, Copy, Eye, Info,
    Upload, Download, Lock, File, Loader2, X, AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Breadcrumb from '../components/shared/Breadcrumb';
import { documentsApi } from '../utils/api';
import { formatBytes, formatDate, timeAgo, getInitials, avatarColor } from '../utils/formatters';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function MetaRow({ label, value }) {
    return (
        <div className="flex items-start justify-between gap-4 text-xs">
            <span className="text-slate-400 shrink-0">{label}</span>
            <span className="font-medium text-slate-800 dark:text-slate-200 text-right">{value}</span>
        </div>
    );
}

function formatBytesSimple(bytes) {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function DocumentView() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user, authFetch } = useAuth();

    const [doc, setDoc] = useState(null);
    const [versions, setVersions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [deleteModal, setDeleteModal] = useState(false);
    const [shareModal, setShareModal] = useState(false);
    const [copied, setCopied] = useState(false);

    // Version upload modal
    const [showUploadVersion, setShowUploadVersion] = useState(false);
    const [versionFile, setVersionFile] = useState(null);
    const [versionNote, setVersionNote] = useState('');
    const [uploadingVersion, setUploadingVersion] = useState(false);
    const [versionError, setVersionError] = useState('');

    // Preview URL
    const [previewUrl, setPreviewUrl] = useState(null);
    const previewUrlRef = useRef(null);

    const isAdmin = user?.role === 'Admin';
    const canEdit = isAdmin || doc?.uploader_id === user?.id;

    useEffect(() => {
        fetchDoc();
        return () => { if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current); };
    }, [id]);

    const fetchDoc = async () => {
        setLoading(true);
        try {
            const res = await documentsApi.get(id);
            if (!res.ok) { navigate('/documents'); return; }
            const data = await res.json();
            setDoc(data);
            // Load preview if applicable
            if (['pdf', 'png', 'jpg', 'jpeg'].includes((data.type || '').toLowerCase())) {
                fetchPreview(id, data.type);
            }
        } catch { navigate('/documents'); }
        finally { setLoading(false); }
    };

    const fetchVersions = async () => {
        try {
            const res = await documentsApi.listVersions(id);
            if (res.ok) {
                const data = await res.json();
                setVersions(Array.isArray(data) ? data : (data.items || []));
            }
        } catch { /* silent */ }
    };

    useEffect(() => {
        if (doc) fetchVersions();
    }, [doc?.id]);

    const fetchPreview = async (docId, type) => {
        try {
            const token = localStorage.getItem('docvault_token');
            const res = await fetch(documentsApi.downloadUrl(docId), {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) return;
            const blob = await res.blob();
            const mime = type?.toLowerCase() === 'pdf' ? 'application/pdf' : `image/${(type || 'png').toLowerCase()}`;
            const url = URL.createObjectURL(new Blob([blob], { type: mime }));
            if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
            previewUrlRef.current = url;
            setPreviewUrl(url);
        } catch { /* silent */ }
    };

    // ─── Actions ─────────────────────────────────────────────────────────────

    const handleDownload = async () => {
        try {
            const token = localStorage.getItem('docvault_token');
            const res = await fetch(documentsApi.downloadUrl(doc.id), {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) return;
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = doc.name || doc.original_filename || `doc-${doc.id}`;
            a.click();
            URL.revokeObjectURL(url);
        } catch { /* silent */ }
    };

    const handleDownloadVersion = async (versionId, label) => {
        try {
            const token = localStorage.getItem('docvault_token');
            const res = await fetch(documentsApi.downloadVersionUrl(doc.id, versionId), {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) return;
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${doc.name || `doc-${doc.id}`} (${label}).${(doc.type || 'bin').toLowerCase()}`;
            a.click();
            URL.revokeObjectURL(url);
        } catch { /* silent */ }
    };

    const handleDelete = async () => {
        try {
            const res = await documentsApi.delete(doc.id);
            if (res.ok || res.status === 204) navigate('/documents');
        } catch { /* silent */ }
        setDeleteModal(false);
    };

    const handleCopyLink = () => {
        navigator.clipboard.writeText(window.location.href);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleUploadVersion = async () => {
        if (!versionFile) return;
        setUploadingVersion(true);
        setVersionError('');
        try {
            const res = await documentsApi.uploadVersion(doc.id, versionFile, versionNote);
            if (res.ok) {
                setShowUploadVersion(false);
                setVersionFile(null);
                setVersionNote('');
                await fetchVersions();
            } else {
                const body = await res.json().catch(() => ({}));
                setVersionError(body.detail || `Lỗi ${res.status}`);
            }
        } catch (err) {
            setVersionError(`Lỗi kết nối: ${err.message}`);
        } finally {
            setUploadingVersion(false);
        }
    };

    // ─── Render ─────────────────────────────────────────────────────────────

    if (loading) {
        return (
            <>
                <Breadcrumb items={[
                    { label: 'Tổng quan', href: '/dashboard' },
                    { label: 'Tài liệu', href: '/documents' },
                    { label: '…' }
                ]} />
                <div className="flex items-center justify-center" style={{ height: 'calc(100vh - 6rem)' }}>
                    <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
                </div>
            </>
        );
    }

    const ext = (doc?.type || '').toUpperCase();
    const tags = Array.isArray(doc?.tags)
        ? doc.tags
        : (doc?.tags ? String(doc.tags).split(',').map(t => t.trim()).filter(Boolean) : []);

    const activity = [
        {
            icon: <Eye className="w-4 h-4" />,
            bg: 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400',
            user: doc?.owner || 'Người dùng',
            action: 'đã tải tài liệu này lên',
            time: doc?.date || doc?.created_at,
        },
        {
            icon: <Info className="w-4 h-4" />,
            bg: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400',
            user: 'Hệ thống',
            action: doc?.approval_status === 'approved' ? 'đã phê duyệt tài liệu này' : 'đang chờ phê duyệt',
            time: doc?.date || doc?.created_at,
        },
    ];

    return (
        <div className="-mx-4 lg:-mx-8 -mt-4 lg:-mt-8 flex flex-col" style={{ height: 'calc(100vh - 4rem)' }}>

            {/* ── Top bar ─────────────────────────────────────────── */}
            <div className="px-8 pt-3">
                <Breadcrumb items={[
                    { label: 'Tổng quan', href: '/dashboard' },
                    { label: 'Tài liệu', href: '/documents' },
                    { label: doc?.name || doc?.original_filename || '…' }
                ]} />
            </div>

            {/* ── Action Bar ───────────────────────────────────────── */}
            <div className="shrink-0 px-8 py-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
                <div className="flex flex-col min-w-0">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-primary-600/10 dark:bg-primary-500/10 flex items-center justify-center">
                            <File className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                        </div>
                        <h1 className="text-xl font-bold text-slate-900 dark:text-white truncate max-w-md">
                            {doc?.name || doc?.original_filename || `Tài liệu #${doc?.id}`}
                        </h1>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            doc?.visibility === 'public'
                                ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400'
                                : 'bg-blue-50 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400'
                        }`}>
                            {doc?.visibility === 'public' ? 'Công khai' : 'Nội bộ'}
                        </span>
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                        {doc?.department && <span>{doc.department}</span>}
                        {doc?.owner && <span>• {doc.owner}</span>}
                        <span>• {formatBytesSimple(doc?.size || doc?.size_bytes)}</span>
                    </div>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-4">
                    <button onClick={handleDownload}
                        className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold rounded-lg transition-colors">
                        <Download className="w-4 h-4" /> Tải xuống
                    </button>
                    <button onClick={() => setShareModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm font-semibold rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                        Chia sẻ
                    </button>
                    {previewUrl && (
                        <a href={previewUrl} target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm font-semibold rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                            <Eye className="w-4 h-4" /> Mở
                        </a>
                    )}
                    {canEdit && (
                        <button onClick={() => setDeleteModal(true)}
                            className="flex items-center justify-center w-10 h-10 bg-slate-100 dark:bg-slate-800 text-red-500 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                            title="Xóa tài liệu">
                            <Trash2 className="w-4 h-4" />
                        </button>
                    )}
                </div>
            </div>

            {/* ── Main body ─────────────────────────────────────────── */}
            <div className="flex flex-1 overflow-hidden">
                {/* Left: Preview */}
                <div className="flex-1 p-8 bg-slate-200 dark:bg-slate-950 overflow-y-auto flex items-center justify-center">
                    {previewUrl && ['pdf', 'png', 'jpg', 'jpeg'].includes((doc?.type || '').toLowerCase()) ? (
                        <iframe src={previewUrl} className="w-full h-full rounded-xl shadow-lg border-0 bg-white"
                            title={doc?.name} />
                    ) : (
                        <div className="text-center py-24">
                            <div className="w-20 h-20 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-4">
                                <File className="w-10 h-10 text-slate-400" />
                            </div>
                            <h4 className="text-base font-bold text-slate-700 dark:text-slate-200 mb-2">
                                {ext ? `${ext} — không thể xem trực tiếp` : 'Không có bản xem trước'}
                            </h4>
                            <p className="text-sm text-slate-400 mb-6">Tải xuống để đọc nội dung</p>
                            <button onClick={handleDownload}
                                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary-600 text-white text-sm font-semibold hover:bg-primary-700 transition-colors">
                                <Download className="w-4 h-4" /> Tải xuống
                            </button>
                        </div>
                    )}
                </div>

                {/* Right: Info sidebar */}
                <aside className="w-80 xl:w-96 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 flex flex-col overflow-y-auto shrink-0">

                    {/* ─ File Info ─ */}
                    <div className="p-6 border-b border-slate-200 dark:border-slate-800">
                        <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                            <Info className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                            Thông tin tệp
                        </h3>
                        <div className="space-y-3">
                            <MetaRow label="Kích thước" value={formatBytesSimple(doc?.size || doc?.size_bytes)} />
                            <MetaRow label="Loại" value={ext || '—'} />
                            <MetaRow label="Ngày tải lên" value={formatDate(doc?.date || doc?.created_at)} />
                            <MetaRow label="Chủ sở hữu" value={
                                <div className="flex items-center gap-2">
                                    <span>{doc?.owner || '—'}</span>
                                    {doc?.owner && (
                                        <div className={`w-5 h-5 rounded-full ${avatarColor(doc.owner)} flex items-center justify-center text-white text-[8px] font-bold`}>
                                            {getInitials(doc.owner).slice(0, 1)}
                                        </div>
                                    )}
                                </div>
                            } />
                            {doc?.department && <MetaRow label="Phòng ban" value={doc.department} />}
                            <MetaRow label="Phạm vi" value={
                                <span className={doc?.visibility === 'public' ? 'text-emerald-600' : 'text-blue-600'}>
                                    {doc?.visibility === 'public' ? 'Công khai' : 'Nội bộ'}
                                </span>
                            } />
                            <MetaRow label="Trạng thái" value={
                                <span className={`text-xs font-semibold ${
                                    doc?.approval_status === 'approved' ? 'text-emerald-600' :
                                    doc?.approval_status === 'rejected' ? 'text-red-600' : 'text-amber-600'
                                }`}>
                                    {doc?.approval_status === 'approved' ? 'Đã phê duyệt' :
                                     doc?.approval_status === 'rejected' ? 'Từ chối' : 'Chờ phê duyệt'}
                                </span>
                            } />
                            {tags.length > 0 && (
                                <div>
                                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-2">Thẻ</span>
                                    <div className="flex flex-wrap gap-1.5">
                                        {tags.map((tag, i) => (
                                            <span key={i} className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-[10px] font-medium text-slate-600 dark:text-slate-300">{tag}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* ─ Version History ─ */}
                    <div className="p-6 border-b border-slate-200 dark:border-slate-800">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <Eye className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                                Lịch sử phiên bản
                            </h3>
                            {canEdit && (
                                <button
                                    onClick={() => setShowUploadVersion(true)}
                                    className="flex items-center gap-1 text-primary-600 dark:text-primary-400 text-[10px] font-bold uppercase hover:underline"
                                >
                                    <Upload className="w-3 h-3" />
                                    Phiên bản mới
                                </button>
                            )}
                        </div>
                        <div className="space-y-4">
                            {versions.length > 0 ? (
                                versions.map((v, idx) => (
                                    <div key={v.id || v.version_label || idx} className="flex gap-3 relative group">
                                        {idx < versions.length - 1 && (
                                            <div className="absolute left-[7px] top-5 bottom-0 w-px bg-slate-100 dark:bg-slate-800" />
                                        )}
                                        <div className={`w-3.5 h-3.5 rounded-full shrink-0 z-10 mt-0.5 ring-4 ${
                                            v.is_current
                                                ? 'bg-primary-600 ring-primary-600/15 dark:ring-primary-500/20'
                                                : 'bg-slate-200 dark:bg-slate-700 ring-transparent'
                                        }`} />
                                        <div className="flex-1 pb-1">
                                            <div className="flex items-center justify-between">
                                                <p className="text-xs font-bold text-slate-800 dark:text-slate-200">
                                                    {v.version_label}
                                                    {v.is_current && (
                                                        <span className="ml-2 text-emerald-500 dark:text-emerald-400 font-normal text-[10px]">Hiện tại</span>
                                                    )}
                                                </p>
                                                <button
                                                    onClick={() => handleDownloadVersion(v.id, v.version_label)}
                                                    className="opacity-0 group-hover:opacity-100 p-1 rounded text-slate-400 hover:text-primary-600 dark:hover:text-primary-400 transition-all"
                                                    title="Tải phiên bản này"
                                                >
                                                    <Download className="w-3 h-3" />
                                                </button>
                                            </div>
                                            {v.change_note && (
                                                <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 italic">{v.change_note}</p>
                                            )}
                                            <p className="text-[10px] text-slate-400 mt-0.5">
                                                {timeAgo(v.created_at)} bởi {v.created_by_name || '—'}
                                            </p>
                                            {v.size && (
                                                <p className="text-[10px] text-slate-400">{v.size}</p>
                                            )}
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <p className="text-xs text-slate-400 italic text-center py-2">Chưa có lịch sử phiên bản</p>
                            )}
                        </div>
                    </div>

                    {/* ─ Activity Log ─ */}
                    <div className="p-6 flex-1">
                        <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                            <Info className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                            Nhật ký hoạt động
                        </h3>
                        <div className="space-y-5">
                            {activity.map((item, idx) => (
                                <div key={idx} className="flex items-start gap-3">
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${item.bg}`}>
                                        {item.icon}
                                    </div>
                                    <div>
                                        <p className="text-xs text-slate-700 dark:text-slate-300">
                                            <strong className="text-slate-900 dark:text-white">{item.user}</strong>{' '}{item.action}
                                        </p>
                                        <p className="text-[10px] text-slate-400 mt-0.5">{timeAgo(item.time)}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </aside>
            </div>

            {/* ── Footer ──────────────────────────────────────────── */}
            <footer className="shrink-0 h-8 bg-slate-100 dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 px-6 flex items-center justify-between text-[10px] text-slate-400">
                <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-emerald-500" /> Đã lưu
                    </span>
                    {doc?.id && <span>ID: DOC-{String(doc.id).padStart(4, '0')}</span>}
                </div>
                <div className="flex items-center gap-4">
                    <button onClick={handleCopyLink}
                        className="flex items-center gap-1 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
                        {copied ? <CheckCircle2 className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                        {copied ? 'Đã sao chép!' : 'Sao chép liên kết'}
                    </button>
                    <span className="text-slate-300 dark:text-slate-600">Enterprise Docs</span>
                </div>
            </footer>

            {/* ── Delete Modal ──────────────────────────────────────── */}
            {deleteModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setDeleteModal(false)} />
                    <div className="relative bg-white dark:bg-slate-900 rounded-xl p-6 max-w-sm w-full mx-4 shadow-2xl border border-slate-200 dark:border-slate-800">
                        <div className="w-11 h-11 rounded-xl bg-red-100 dark:bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                            <Trash2 className="w-5 h-5 text-red-500" />
                        </div>
                        <h3 className="text-base font-bold text-slate-900 dark:text-white text-center mb-1">Xóa tài liệu</h3>
                        <p className="text-sm text-slate-500 dark:text-slate-400 text-center mb-5">
                            Bạn có chắc chắn muốn xóa <span className="font-semibold text-slate-700 dark:text-slate-200">"{doc?.name || doc?.original_filename}"</span>?
                        </p>
                        <div className="flex gap-3">
                            <button onClick={() => setDeleteModal(false)}
                                className="flex-1 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                                Hủy
                            </button>
                            <button onClick={handleDelete}
                                className="flex-1 py-2.5 rounded-lg bg-red-500 hover:bg-red-600 text-white text-sm font-semibold transition-colors">
                                Xóa
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Share Modal ──────────────────────────────────────── */}
            {shareModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShareModal(false)} />
                    <div className="relative bg-white dark:bg-slate-900 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl border border-slate-200 dark:border-slate-800">
                        <div className="flex items-center justify-between mb-5">
                            <h3 className="text-base font-bold text-slate-900 dark:text-white">Chia sẻ tài liệu</h3>
                            <button onClick={() => setShareModal(false)}
                                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                                ✕
                            </button>
                        </div>
                        <div className="mb-4">
                            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Liên kết tài liệu</label>
                            <div className="flex gap-2">
                                <input readOnly value={window.location.href}
                                    className="flex-1 px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 outline-none" />
                                <button onClick={handleCopyLink}
                                    className="px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold transition-colors flex items-center gap-1.5">
                                    {copied ? <CheckCircle2 className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                    {copied ? 'Đã chép!' : 'Sao chép'}
                                </button>
                            </div>
                        </div>
                        <p className="text-xs text-slate-400 text-center border-t border-slate-100 dark:border-slate-800 pt-4">
                            Chia sẻ với bất kỳ ai trong tổ chức của bạn có quyền truy cập.
                        </p>
                    </div>
                </div>
            )}

            {/* ── Upload Version Modal ─────────────────────────────── */}
            {showUploadVersion && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => { setShowUploadVersion(false); setVersionFile(null); setVersionNote(''); setVersionError(''); }} />
                    <div className="relative bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-md mx-4 shadow-2xl border border-slate-200 dark:border-slate-800">
                        <div className="flex items-center justify-between mb-5">
                            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <Upload className="w-4 h-4 text-primary-600" />
                                Tải lên phiên bản mới
                            </h3>
                            <button onClick={() => { setShowUploadVersion(false); setVersionFile(null); setVersionNote(''); }}
                                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            {/* Current version info */}
                            {versions.find(v => v.is_current) && (
                                <div className="px-3 py-2.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-800 text-xs">
                                    <span className="text-slate-500 dark:text-slate-400">Phiên bản hiện tại: </span>
                                    <span className="font-bold text-slate-700 dark:text-slate-200">
                                        {versions.find(v => v.is_current)?.version_label}
                                    </span>
                                </div>
                            )}

                            {/* File input */}
                            <div>
                                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Chọn tệp</label>
                                <input
                                    type="file"
                                    accept=".pdf,.docx,.pptx,.txt,.md,.xlsx"
                                    onChange={e => setVersionFile(e.target.files?.[0] || null)}
                                    className="w-full text-sm text-slate-600 dark:text-slate-300 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-primary-50 dark:file:bg-primary-500/20 file:text-primary-700 dark:file:text-primary-400 hover:file:bg-primary-100 dark:hover:file:bg-primary-500/30 cursor-pointer"
                                />
                            </div>

                            {/* Change note */}
                            <div>
                                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Ghi chú thay đổi</label>
                                <textarea
                                    rows={3}
                                    value={versionNote}
                                    onChange={e => setVersionNote(e.target.value)}
                                    placeholder="Mô tả thay đổi trong phiên bản mới..."
                                    className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 outline-none focus:ring-2 focus:ring-primary-600/30 resize-none"
                                />
                            </div>

                            {/* Error */}
                            {versionError && (
                                <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30">
                                    <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                                    <p className="text-xs text-red-700 dark:text-red-400">{versionError}</p>
                                </div>
                            )}
                        </div>

                        <div className="flex gap-3 mt-5">
                            <button onClick={() => { setShowUploadVersion(false); setVersionFile(null); setVersionNote(''); setVersionError(''); }}
                                className="flex-1 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                                Hủy
                            </button>
                            <button
                                onClick={handleUploadVersion}
                                disabled={!versionFile || uploadingVersion}
                                className="flex-1 py-2.5 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
                            >
                                {uploadingVersion ? (
                                    <><Loader2 className="w-4 h-4 animate-spin" /> Đang tải...</>
                                ) : (
                                    <><Upload className="w-4 h-4" /> Tải lên</>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
