import ModalFocus from '../components/shared/ModalFocus';
import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
    Upload, X, File, Image,
    ChevronDown, CheckCircle2, AlertCircle,
    ChevronLeft, ChevronRight, Trash2, Search, Building2,
    Lock, Globe, MoreHorizontal, Eye, Download, Share2, Clock, XCircle, Square, CheckSquare, User
} from 'lucide-react';
import { useAuth } from '../context/authContextCore';
import { fileTypeIconMap, fileTypeColors, fileTypeBgColors } from '../components/documents/fileTypes';
import DocumentsToolbar from '../components/documents/DocumentsToolbar';
import DocumentRow from '../components/documents/DocumentRow';
import DocumentCard from '../components/documents/DocumentCard';
import Breadcrumb from '../components/shared/Breadcrumb';
import { formatBytes, getExt } from '../utils/formatters';
import { approvalsApi } from '../utils/api';

const categories = ['All', 'Tài liệu', 'Hợp đồng', 'Báo cáo', 'Biên bản', 'Quy trình', 'Khác'];
const ROWS_PER_PAGE = 5;
// Phải khớp với ALLOWED_EXTENSIONS ở backend (api_compat/documents.py)
const ALLOWED_UPLOAD_EXTENSIONS = ['pdf', 'txt', 'md', 'docx', 'pptx'];
const ALLOWED_UPLOAD_ACCEPT = ALLOWED_UPLOAD_EXTENSIONS.map(ext => `.${ext}`).join(',');
const ALLOWED_UPLOAD_HINT = 'PDF, TXT, DOCX, PPTX, MD — Tối đa 50MB';
const normalizeSearch = value => String(value || '').toLocaleLowerCase('vi').replace(/đ/g, 'd').normalize('NFD').replace(/[\u0300-\u036f]/g, '');

// R5-2: shared "no rows" state for both the table and grid views — renders
// a connection/server error (with retry) instead of the empty-state copy
// when the list failed to load, so "no results" is never confused with
// "couldn't reach the server".
function DocumentsListState({ loadError, onRetry, subtitle }) {
    if (loadError) {
        return (
            <>
                <AlertCircle className="w-12 h-12 text-red-300 dark:text-red-500/40 mx-auto mb-3" />
                <p className="text-red-500 dark:text-red-400 font-medium">{loadError}</p>
                <button
                    onClick={onRetry}
                    className="mt-3 inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold text-primary-600 dark:text-primary-400 hover:underline"
                >
                    Thử lại
                </button>
            </>
        );
    }
    return (
        <>
            <Search className="w-12 h-12 text-gray-200 dark:text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400 font-medium">Không tìm thấy tài liệu</p>
            {subtitle && <p className="text-sm text-gray-400 dark:text-gray-500">{subtitle}</p>}
        </>
    );
}

export default function Documents() {
    const { user, authFetch, refreshApprovals } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [documents, setDocuments] = useState([]);
    const [trashOpen, setTrashOpen] = useState(false);
    const [deletedDocuments, setDeletedDocuments] = useState([]);
    const [trashLoading, setTrashLoading] = useState(false);
    // R5-2: distinguish "genuinely empty" (documents === [] with no error)
    // from "failed to load" (network/server error) so we don't show
    // "Không tìm thấy tài liệu" when the list simply failed to load.
    const [loadError, setLoadError] = useState(null);
    const [listLoading, setListLoading] = useState(true);
    const [departments, setDepartments] = useState([]);
    const [selectedDeptId, setSelectedDeptId] = useState(null);
    const [view, setView] = useState('table');
    const [search, setSearch] = useState('');
    const [typeFilter, setTypeFilter] = useState('All');
    const [categoryFilter, setCategoryFilter] = useState('All');
    const [tagFilter, setTagFilter] = useState('');
    const [statusFilter, setStatusFilter] = useState('All');
    const [filtersOpen, setFiltersOpen] = useState(false);
    const [sortOrder, setSortOrder] = useState('newest');
    const [dragActive, setDragActive] = useState(false);
    const [showUpload, setShowUpload] = useState(false);
    const [deleteTarget, setDeleteTarget] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadCategory, setUploadCategory] = useState('Tài liệu');
    const [uploadTags, setUploadTags] = useState([]);
    const [uploadThumbnail, setUploadThumbnail] = useState(null);
    const [uploadVisibility, setUploadVisibility] = useState('internal');
    const uploadReceiptRef = useRef(null);
    const [effectiveFrom, setEffectiveFrom] = useState('');
    const [sameNameAction, setSameNameAction] = useState('');
    const [effectiveUntil, setEffectiveUntil] = useState('');
    const [uploadTagInput, setUploadTagInput] = useState('');
    const [stagedFiles, setStagedFiles] = useState([]);
    const [uploadSuccess, setUploadSuccess] = useState(false);
    const [uploadError, setUploadError] = useState('');
    const [openMenu, setOpenMenu] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [toast, setToast] = useState(null);
    const [selectedIds, setSelectedIds] = useState(new Set());
    const [showBulkDeleteModal, setShowBulkDeleteModal] = useState(false);
    const [uploaderFilterId, setUploaderFilterId] = useState(null);
    const canPollApprovalStatus = ['Admin', 'Trưởng phòng'].includes(user?.role);

    // Processing status polling state
    const [processingState, setProcessingState] = useState({});
    // Refs for polling
    const pollingRef = useRef({});
    const listRefreshRef = useRef(null);
    // Stable ref so the auto-refresh timer can always call the latest fetchDocuments
    const fetchDocumentsRef = useRef(null);
    const fetchSeqRef = useRef(0);
    // Map docId → original_filename for completion notifications
    const docNamesRef = useRef({});

    // Toast helper — duration optional, default 3.5s, use 6000 for important notifications
    const showToast = (msg, type = 'success', duration = 3500) => {
        setToast({ msg, type, id: Date.now() });
        setTimeout(() => setToast(null), duration);
    };

    // Fetch departments for filter tabs
    useEffect(() => {
        authFetch('/api/auth/departments')
            .then(r => r.ok ? r.json() : [])
            .then(setDepartments)
            .catch(() => {});
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const userIdParam = params.get('user_id');
        const parsed = userIdParam ? Number.parseInt(userIdParam, 10) : NaN;
        setUploaderFilterId(Number.isFinite(parsed) ? parsed : null);
    }, [location.search]);

    // Run fetchDocuments on filter change
    useEffect(() => {
        if (listRefreshRef.current) {
            clearTimeout(listRefreshRef.current);
            listRefreshRef.current = null;
        }
        fetchDocuments();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [typeFilter, categoryFilter, selectedDeptId]);

    useEffect(() => { setCurrentPage(1); }, [search, typeFilter, categoryFilter, tagFilter, statusFilter, selectedDeptId, uploaderFilterId]);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handler = () => setOpenMenu(null);
        document.addEventListener('click', handler);
        return () => document.removeEventListener('click', handler);
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        const polling = pollingRef.current;
        const listRefresh = listRefreshRef;
        return () => {
            if (listRefresh.current) clearTimeout(listRefresh.current);
            Object.keys(polling).forEach(id => { polling[id] = false; });
        };
    }, []);

    // ------------------------------------------------------------------
    // ------------------------------------------------------------------
    // Per-document processing status polling (3s interval)
    // ------------------------------------------------------------------
    const startPolling = useCallback((docId, docName) => {
        if (!canPollApprovalStatus) return;
        if (pollingRef.current[docId]) return;
        pollingRef.current[docId] = true;
        // Store name for the completion toast
        if (docName) docNamesRef.current[docId] = docName;

        const poll = async () => {
            if (!pollingRef.current[docId]) return;
            try {
                const res = await approvalsApi.getDocumentStatus(docId);
                if (res.ok) {
                    const st = await res.json();
                    setProcessingState(prev => ({ ...prev, [docId]: st }));
                    if (st.status === 'indexed' || st.status === 'failed') {
                        pollingRef.current[docId] = false;

                        // 🔔 Notify user of completion
                        const name = docNamesRef.current[docId] || `Tài liệu #${docId}`;
                        if (st.status === 'indexed') {
                            showToast(`✅ "${name}" đã xử lý xong và sẵn sàng sử dụng!`, 'success', 6000);
                        } else {
                            showToast(`❌ "${name}" xử lý thất bại. Vui lòng thử lại.`, 'error', 6000);
                        }

                        // Refresh list after 1s so status updates in the table
                        setTimeout(() => {
                            if (fetchDocumentsRef.current) fetchDocumentsRef.current();
                        }, 1000);

                        // Clear progress bar after 5s
                        setTimeout(() => {
                            setProcessingState(prev => {
                                const next = { ...prev };
                                delete next[docId];
                                return next;
                            });
                        }, 5000);
                        return;
                    }
                } else if (res.status === 403 || res.status === 404) {
                    pollingRef.current[docId] = false;
                    return;
                }
            } catch { /* silent */ }
            if (pollingRef.current[docId]) setTimeout(poll, 3000);
        };
        poll();
    }, [canPollApprovalStatus]);

    // ------------------------------------------------------------------
    // Fetch document list
    // ------------------------------------------------------------------
    const fetchDocuments = async () => {
        const requestSeq = ++fetchSeqRef.current;
        setListLoading(true);
        try {
            const params = new URLSearchParams();
            if (typeFilter !== 'All') params.append('type', typeFilter);
            if (categoryFilter !== 'All') params.append('category', categoryFilter);
            if (selectedDeptId !== null) params.append('department_id', selectedDeptId);
            const qs = params.toString();
            const res = await authFetch(`/api/documents${qs ? '?' + qs : ''}`);
            if (requestSeq !== fetchSeqRef.current) return;
            if (res.ok) {
                const data = await res.json();
                if (requestSeq !== fetchSeqRef.current) return;
                const docs = Array.isArray(data) ? data : (data.items || []);
                setDocuments(docs);
                setLoadError(null);

                // Start per-document polling for approved+processing docs
                docs.forEach(doc => {
                    const name = doc.name || doc.original_filename || `Tài liệu #${doc.id}`;
                    // Always update the name ref in case it wasn't stored yet
                    docNamesRef.current[doc.id] = name;
                    if (
                        canPollApprovalStatus &&
                        doc.approval_status === 'approved' &&
                        ['parsing', 'processing', 'indexing'].includes(doc.status)
                    ) {
                        startPolling(doc.id, name);
                    }
                });

                // Schedule a list refresh while there are pending or processing docs.
                // This lets user see the progress bar appear after admin approval
                // without manual page reload.
                const needsRefresh = docs.some(doc =>
                    doc.approval_status === 'pending' ||
                    (doc.approval_status === 'approved' &&
                     ['parsing', 'processing', 'indexing'].includes(doc.status))
                );
                if (listRefreshRef.current) {
                    clearTimeout(listRefreshRef.current);
                    listRefreshRef.current = null;
                }
                if (needsRefresh) {
                    listRefreshRef.current = setTimeout(() => {
                        if (fetchDocumentsRef.current) fetchDocumentsRef.current();
                    }, 8000);
                }
            } else if (res.status === 401) {
                // Session expired — authFetch already triggered logout(),
                // which unmounts this page via ProtectedRoute. Don't flash
                // a connection-error message during that redirect.
            } else {
                setDocuments([]);
                setLoadError('Không thể tải danh sách tài liệu. Vui lòng thử lại.');
            }
        } catch (err) {
            if (requestSeq !== fetchSeqRef.current) return;
            console.error('Failed to fetch documents:', err);
            setDocuments([]);
            setLoadError('Mất kết nối mạng. Vui lòng kiểm tra kết nối và thử lại.');
        } finally {
            if (requestSeq === fetchSeqRef.current) setListLoading(false);
        }
    };

    // Always keep the ref pointing to the latest fetchDocuments closure
    fetchDocumentsRef.current = fetchDocuments;


    const filteredDocs = documents.filter((doc) => {
        const name = doc.name || doc.original_filename || '';
        const matchesSearch = normalizeSearch(name).includes(normalizeSearch(search));
        if (!matchesSearch) return false;

        const tags = Array.isArray(doc.tags) ? doc.tags : String(doc.tags || '').split(',');
        if (tagFilter && !tags.some(tag => normalizeSearch(tag).includes(normalizeSearch(tagFilter)))) return false;
        const status = String(doc.status || '').toLowerCase();
        const approval = String(doc.approval_status || '').toLowerCase();
        if (statusFilter === 'pending' && !approval.startsWith('pending')) return false;
        if (statusFilter === 'rejected' && approval !== 'rejected') return false;
        if (statusFilter === 'processing' && !['parsing', 'processing', 'indexing', 'pending'].includes(status)) return false;
        if (['indexed', 'failed'].includes(statusFilter) && status !== statusFilter) return false;

        if (uploaderFilterId !== null) {
            const uploaderId = Number(doc.uploader_id);
            return Number.isInteger(uploaderId) && uploaderId === uploaderFilterId;
        }

        return true;
    }).sort((a, b) => sortOrder === 'name'
        ? normalizeSearch(a.name || a.original_filename).localeCompare(normalizeSearch(b.name || b.original_filename), 'vi')
        : new Date(b.created_at || 0) - new Date(a.created_at || 0));

    // Pagination
    const totalPages = Math.max(1, Math.ceil(filteredDocs.length / ROWS_PER_PAGE));
    const pageDocs = filteredDocs.slice((currentPage - 1) * ROWS_PER_PAGE, currentPage * ROWS_PER_PAGE);

    const handleDrag = useCallback((e) => {
        e.preventDefault(); e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
        else setDragActive(false);
    }, []);

    const stageFiles = (fileList) => {
        if (!fileList?.length) return;
        const incoming = Array.from(fileList);
        const accepted = [];
        const rejectedNames = [];
        for (const file of incoming) {
            const ext = getExt(file.name).toLowerCase();
            if (ALLOWED_UPLOAD_EXTENSIONS.includes(ext)) {
                accepted.push(file);
            } else {
                rejectedNames.push(file.name);
            }
        }
        if (accepted.length) {
            setStagedFiles(prev => [...prev, ...accepted]);
        }
        setUploadSuccess(false);
        if (rejectedNames.length) {
            setUploadError(`Định dạng file không được hỗ trợ: ${rejectedNames.join(', ')}. Chỉ chấp nhận ${ALLOWED_UPLOAD_HINT}.`);
        } else {
            setUploadError('');
        }
    };

    const removeStagedFile = (index) => setStagedFiles(prev => prev.filter((_, i) => i !== index));

    const handleUpload = async () => {
        if (!stagedFiles.length || !effectiveFrom || (effectiveUntil && effectiveUntil < effectiveFrom)) return;
        setUploading(true);
        setUploadSuccess(false);
        setUploadError('');
        try {
            const formData = new FormData();
            for (const file of stagedFiles) formData.append('files', file);
            formData.append('category', uploadCategory);
            formData.append('visibility', uploadVisibility);
            formData.append('effective_from', effectiveFrom);
            if (sameNameAction) formData.append('same_name_action', sameNameAction);
            if (effectiveUntil) formData.append('effective_until', effectiveUntil);
            if (uploadTags.length) formData.append('tags', uploadTags.join(','));
            if (uploadThumbnail) formData.append('thumbnail', uploadThumbnail);
            const fingerprint = JSON.stringify({ files: stagedFiles.map(file => [file.name, file.size, file.lastModified]), sameNameAction, category: uploadCategory, visibility: uploadVisibility, effectiveFrom, effectiveUntil, tags: uploadTags, thumbnail: uploadThumbnail && [uploadThumbnail.name, uploadThumbnail.size, uploadThumbnail.lastModified] });
            if (uploadReceiptRef.current?.fingerprint !== fingerprint) {
                uploadReceiptRef.current = { fingerprint, key: crypto.randomUUID() };
            }
            const res = await authFetch('/api/documents/upload', { method: 'POST', body: formData, headers: { 'Idempotency-Key': uploadReceiptRef.current.key } });
            if (res.ok) {
                const createdDocs = await res.json().catch(() => []);
                uploadReceiptRef.current = null;
                await fetchDocuments();
                refreshApprovals();
                // Server trả về mảng document vừa tạo, mỗi item có approval_status
                // ("approved" khi Admin/Trưởng phòng tự duyệt, "pending"/"pending_org"
                // khi Nhân viên upload và cần chờ duyệt) — phân nhánh toast theo đó.
                const anyPending = Array.isArray(createdDocs) &&
                    createdDocs.some(d => d.approval_status && d.approval_status !== 'approved');
                showToast(
                    anyPending
                        ? `Tải lên ${stagedFiles.length} tài liệu thành công! Đang chờ phê duyệt.`
                        : `Tải lên ${stagedFiles.length} tài liệu thành công`
                );
                setUploadSuccess(true);
                setStagedFiles([]);
                setTimeout(() => {
                    setShowUpload(false);
                    setUploadCategory('Tài liệu');
                    setUploadTags([]);
                    setUploadTagInput('');
                    setUploadThumbnail(null);
                    setUploadVisibility('internal');
                    setEffectiveFrom('');
                    setEffectiveUntil('');
                    setUploadSuccess(false);
                }, 1500);
            } else {
                const err = await res.json().catch(() => ({}));
                setUploadError(err.detail || `Lỗi ${res.status}`);
                showToast(err.detail || `Tải lên thất bại (${res.status})`, 'error');
            }
        } catch (err) {
            setUploadError(`Lỗi kết nối: ${err.message}`);
            showToast(`Lỗi kết nối: ${err.message}`, 'error');
        } finally {
            setUploading(false);
        }
    };

    const handleThumbnailSelect = (e) => {
        const file = e.target.files?.[0];
        if (file) setUploadThumbnail(file);
    };

    const handleDrop = useCallback((e) => {
        e.preventDefault(); setDragActive(false);
        stageFiles(e.dataTransfer?.files);
    }, []);

    const handleFileInput = (e) => { stageFiles(e.target.files); e.target.value = ''; };

    const closeUploadPanel = () => {
        setShowUpload(false); setStagedFiles([]); setUploadCategory('Tài liệu'); setUploadTags([]); setUploadTagInput('');
        setUploadThumbnail(null); setUploadVisibility('internal'); setUploadSuccess(false); setUploadError('');
    };

    const handleDelete = async (id) => {
        try {
            const res = await authFetch(`/api/documents/${id}`, { method: 'DELETE' });
            if (res.ok) {
                const docName = documents.find(d => d.id === id)?.name || 'Tài liệu';
                setDocuments(prev => prev.filter(d => d.id !== id));
                showToast(`Đã xóa "${docName}" thành công`);
            } else {
                const err = await res.json().catch(() => ({}));
                showToast(err.detail || 'Xóa thất bại', 'error');
            }
        } catch (err) {
            console.error('Delete failed:', err);
            showToast('Có lỗi xảy ra khi xóa', 'error');
        }
        setDeleteTarget(null);
    };

    const loadTrash = async () => {
        setTrashLoading(true);
        try {
            const res = await authFetch('/api/documents?include_deleted=true');
            if (!res.ok) throw new Error();
            const data = await res.json();
            setDeletedDocuments(Array.isArray(data) ? data : (data.items || []));
            setTrashOpen(true);
        } catch {
            showToast('Không thể tải thùng rác', 'error');
        } finally {
            setTrashLoading(false);
        }
    };

    const restoreDocument = async (id) => {
        try {
            const res = await authFetch(`/api/documents/${id}/restore`, { method: 'POST' });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Khôi phục thất bại');
            await fetchDocuments();
            await loadTrash();
            showToast('Đã khôi phục tài liệu');
        } catch (err) {
            showToast(err.message || 'Khôi phục thất bại', 'error');
        }
    };

    const toggleSelect = (id) => {
        setSelectedIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    const toggleSelectAll = () => {
        if (selectedIds.size === pageDocs.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(pageDocs.map(d => d.id)));
        }
    };

    const clearSelection = () => setSelectedIds(new Set());

    const handleBulkDelete = async () => {
        const ids = Array.from(selectedIds);
        let successCount = 0;
        let failCount = 0;
        for (const id of ids) {
            try {
                const res = await authFetch(`/api/documents/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    successCount++;
                } else {
                    failCount++;
                }
            } catch {
                failCount++;
            }
        }
        setDocuments(prev => prev.filter(d => !selectedIds.has(d.id)));
        setSelectedIds(new Set());
        setShowBulkDeleteModal(false);
        if (successCount > 0) showToast(`Đã xóa ${successCount} tài liệu thành công${failCount > 0 ? `, ${failCount} thất bại` : ''}`);
        else showToast('Xóa thất bại', 'error');
    };

    const handleDownload = async (doc) => {
        try {
            const res = await authFetch(`/api/documents/${doc.id}/download`);
            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a'); a.href = url; a.download = doc.name || doc.original_filename || 'document'; a.click();
                window.URL.revokeObjectURL(url);
                showToast(`Đã tải "${doc.name || doc.original_filename || 'tài liệu'}"`);
            } else {
                showToast('Tải xuống thất bại', 'error');
            }
        } catch (err) {
            console.error('Download failed:', err);
            showToast('Tải xuống thất bại', 'error');
        }
    };

    const totalStagedSize = stagedFiles.reduce((sum, f) => sum + f.size, 0);

    return (
        <div className="space-y-6 px-2 md:px-4">
            <div className="px-2 pt-4">
                <Breadcrumb items={[
                    { label: 'Tổng quan', href: '/dashboard' },
                    { label: 'Tài liệu' },
                ]} />
            </div>

            {/* ── Toast Notification ─────────────────────────────────── */}
            {toast && (
                <div
                    key={toast.id}
                    className={`fixed top-20 right-6 z-[100] flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-2xl border text-sm font-semibold animate-slide-in-right
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

            <div className="mx-2">
                <button type="button" onClick={() => trashOpen ? setTrashOpen(false) : loadTrash()}
                    className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary-600">
                    {trashOpen ? 'Ẩn thùng rác' : 'Thùng rác (lưu 30 ngày)'}
                </button>
                {trashOpen && (
                    <div className="mt-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
                        {trashLoading ? <p className="text-sm text-gray-500">Đang tải...</p>
                            : deletedDocuments.length === 0 ? <p className="text-sm text-gray-500">Thùng rác trống</p>
                                : deletedDocuments.map(item => (
                                    <div key={item.id} className="flex items-center justify-between gap-3 py-2 text-sm">
                                        <span className="truncate">{item.name || item.original_filename}</span>
                                        <button type="button" onClick={() => restoreDocument(item.id)} className="text-primary-600 font-semibold">Khôi phục</button>
                                    </div>
                                ))}
                    </div>
                )}
            </div>

            {/* ══════════════ Department Filter ══════════════ */}
            {departments.length > 0 && (
                <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 mx-2 px-5 py-4">
                    <div className="flex items-center gap-3 overflow-x-auto scrollbar-hide">
                        <Building2 className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex-shrink-0 mr-1">Phòng ban:</span>
                        <button
                            onClick={() => setSelectedDeptId(null)}
                            className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                                selectedDeptId === null
                                    ? 'bg-primary-600 text-white shadow-sm'
                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                            }`}
                        >
                            Tất cả
                        </button>
                        {departments.map(dept => (
                            <button
                                key={dept.id}
                                onClick={() => setSelectedDeptId(dept.id)}
                                className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                                    selectedDeptId === dept.id
                                        ? 'bg-primary-600 text-white shadow-sm'
                                        : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                                }`}
                            >
                                {dept.name}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* ══════════════ All Documents ══════════════ */}
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden mx-2">

                {/* Table Header Bar */}
                <DocumentsToolbar
                    search={search}
                    onSearchChange={setSearch}
                    view={view}
                    onViewChange={setView}
                    onUploadClick={() => setShowUpload(!showUpload)}
                    filtersOpen={filtersOpen}
                    onToggleFilters={() => setFiltersOpen(open => !open)}
                    typeFilter={typeFilter}
                    onTypeFilterChange={setTypeFilter}
                    categoryFilter={categoryFilter}
                    onCategoryFilterChange={setCategoryFilter}
                    tagFilter={tagFilter}
                    onTagFilterChange={setTagFilter}
                    statusFilter={statusFilter}
                    onStatusFilterChange={setStatusFilter}
                    sortOrder={sortOrder}
                    onSortOrderChange={setSortOrder}
                    categories={categories}
                />

                {/* ─── Upload Modal ─── */}
                {showUpload && (
                    <ModalFocus label="Tải lên tài liệu" onClose={closeUploadPanel} className="fixed inset-0 z-50 flex items-center justify-center">
                        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={closeUploadPanel} />
                        <div className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden flex flex-col border border-gray-200 dark:border-gray-800 animate-fade-in">
                            {/* Header */}
                            <div className="px-6 py-4 flex items-center justify-between bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                                <div className="flex items-center gap-3">
                                    <div className="w-9 h-9 rounded-xl bg-primary-600/10 flex items-center justify-center">
                                        <Upload className="w-4 h-4 text-primary-600" />
                                    </div>
                                    <div>
                                        <h3 className="text-base font-bold text-gray-900 dark:text-white">Tải lên tài liệu</h3>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">Kéo & thả hoặc nhấp để chọn tệp</p>
                                    </div>
                                </div>
                                <button onClick={closeUploadPanel} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Body */}
                            <div className="flex-1 overflow-y-auto p-6 space-y-5">
                                {uploadSuccess ? (
                                    <div className="py-8 text-center">
                                        <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-500/20 flex items-center justify-center mx-auto mb-4">
                                            <CheckCircle2 className="w-8 h-8 text-green-600" />
                                        </div>
                                        <p className="text-lg font-semibold text-gray-900 dark:text-white">Tải lên thành công!</p>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Tài liệu của bạn đã được tải lên thành công.</p>
                                    </div>
                                ) : (
                                    <>
                                        {/* Drop Zone */}
                                        <div
                                            onDragEnter={handleDrag}
                                            onDragLeave={handleDrag}
                                            onDragOver={handleDrag}
                                            onDrop={handleDrop}
                                            onClick={() => document.getElementById('file-input-upload')?.click()}
                                            className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
                                                dragActive
                                                    ? 'border-primary-600 bg-primary-600/5'
                                                    : 'border-gray-200 dark:border-gray-700 hover:border-primary-600/50'
                                            }`}
                                        >
                                            <div className="w-12 h-12 rounded-2xl bg-primary-600/10 flex items-center justify-center mx-auto mb-3">
                                                <Upload className={`w-6 h-6 transition-colors ${dragActive ? 'text-primary-600' : 'text-gray-400'}`} />
                                            </div>
                                            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                                {dragActive ? 'Thả tệp vào đây' : 'Kéo thả tệp hoặc nhấp để chọn'}
                                            </p>
                                            <p className="text-xs text-gray-400">{ALLOWED_UPLOAD_HINT}</p>
                                            <input
                                                id="file-input-upload"
                                                type="file"
                                                multiple
                                                accept={ALLOWED_UPLOAD_ACCEPT}
                                                className="hidden"
                                                onChange={handleFileInput}
                                            />
                                        </div>

                                        {/* Staged Files */}
                                        {stagedFiles.length > 0 && (
                                            <div>
                                                <div className="flex items-center justify-between mb-3">
                                                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                                                        Tệp đã chọn <span className="text-xs font-normal text-gray-400">({stagedFiles.length} • {formatBytes(totalStagedSize)})</span>
                                                    </h4>
                                                    <button onClick={() => setStagedFiles([])} className="text-xs text-red-500 hover:text-red-600 font-medium">Xóa tất cả</button>
                                                </div>
                                                <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                                                    {stagedFiles.map((file, index) => {
                                                        const ext = getExt(file.name);
                                                        const Icon = fileTypeIconMap[ext] || File;
                                                        return (
                                                            <div key={`${file.name}-${index}`} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 group">
                                                                <div className={`w-10 h-10 rounded-xl ${fileTypeBgColors[ext] || 'bg-gray-100'} flex items-center justify-center flex-shrink-0`}>
                                                                    <Icon className={`w-5 h-5 ${fileTypeColors[ext] || 'text-gray-500'}`} />
                                                                </div>
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{file.name}</p>
                                                                    <p className="text-xs text-gray-400">{formatBytes(file.size)} • {ext}</p>
                                                                </div>
                                                                <button onClick={(e) => { e.stopPropagation(); removeStagedFile(index); }} className="p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors">
                                                                    <X className="w-4 h-4" />
                                                                </button>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        )}

                                        {/* Upload Error */}
                                        {uploadError && (
                                            <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30">
                                                <XCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                                                <p className="text-xs text-red-700 dark:text-red-400">{uploadError}</p>
                                            </div>
                                        )}

                                        {/* Document Info */}
                                        <div className="border-t border-gray-100 dark:border-gray-800 pt-5">
                                            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Thông tin tài liệu</h4>
                                            <div className="space-y-4">
                                                {/* Category */}
                                                <div>
                                                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Danh mục</label>
                                                    <div className="relative">
                                                        <select
                                                            value={uploadCategory}
                                                            onChange={(e) => setUploadCategory(e.target.value)}
                                                            className="w-full px-3 py-2.5 text-sm rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-primary-500/30 cursor-pointer appearance-none"
                                                        >
                                                            {categories.filter(c => c !== 'All').map(cat => (
                                                                <option key={cat} value={cat}>{cat}</option>
                                                            ))}
                                                        </select>
                                                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                                                    </div>
                                                </div>

                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                                    <label className="text-xs font-semibold text-gray-500">Ngày hiệu lực *
                                                        <input type="date" required value={effectiveFrom} onChange={e => setEffectiveFrom(e.target.value)}
                                                            className="block w-full mt-2 px-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white" />
                                                    </label>
                                                    <label className="text-xs font-semibold text-gray-500">Ngày hết hiệu lực (nếu có)
                                                        <input type="date" min={effectiveFrom || undefined} value={effectiveUntil} onChange={e => setEffectiveUntil(e.target.value)}
                                                            className="block w-full mt-2 px-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white" />
                                                    </label>
                                                </div>
                                                <label className="block text-xs mb-3">Nếu tên tệp đã tồn tại
                                                    <select value={sameNameAction} onChange={e => setSameNameAction(e.target.value)} className="block w-full border rounded-lg p-2 mt-1 dark:bg-gray-800">
                                                        <option value="">Dừng để kiểm tra hoặc thêm phiên bản mới</option>
                                                        <option value="new_document">Tôi chọn tạo tài liệu riêng</option>
                                                    </select>
                                                </label>
                                                {effectiveUntil && effectiveUntil < effectiveFrom && <p className="text-xs text-red-600">Ngày hết hiệu lực phải từ ngày hiệu lực trở đi.</p>}

                                                {/* Visibility */}
                                                <div>
                                                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Chế độ hiển thị</label>
                                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                                        <button
                                                            type="button"
                                                            onClick={() => setUploadVisibility('personal')}
                                                            className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border-2 text-sm font-medium transition-all ${
                                                                uploadVisibility === 'personal'
                                                                    ? 'border-violet-600 bg-violet-600/5 text-violet-700 dark:text-violet-400 dark:border-violet-500 dark:bg-violet-500/10'
                                                                    : 'border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600'
                                                            }`}
                                                        >
                                                            <User className="w-4 h-4" />
                                                            Cá nhân
                                                        </button>
                                                        <button
                                                            type="button"
                                                            onClick={() => setUploadVisibility('internal')}
                                                            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border-2 text-sm font-medium transition-all ${
                                                                uploadVisibility === 'internal'
                                                                    ? 'border-primary-600 bg-primary-600/5 text-primary-700 dark:text-primary-400 dark:border-primary-500 dark:bg-primary-500/10'
                                                                    : 'border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600'
                                                            }`}
                                                        >
                                                            <Lock className="w-4 h-4" />
                                                            Nội bộ
                                                        </button>
                                                        <button
                                                            type="button"
                                                            onClick={() => setUploadVisibility('public')}
                                                            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border-2 text-sm font-medium transition-all ${
                                                                uploadVisibility === 'public'
                                                                    ? 'border-emerald-600 bg-emerald-600/5 text-emerald-700 dark:text-emerald-400 dark:border-emerald-500 dark:bg-emerald-500/10'
                                                                    : 'border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600'
                                                            }`}
                                                        >
                                                            <Globe className="w-4 h-4" />
                                                            Công khai
                                                        </button>
                                                    </div>
                                                    <p className="text-xs text-gray-400 mt-1.5">
                                                        {uploadVisibility === 'personal'
                                                            ? 'Chỉ bạn có thể xem tài liệu này và tài liệu sẽ vào workspace cá nhân'
                                                            : uploadVisibility === 'internal'
                                                            ? 'Chỉ thành viên trong phòng ban mới xem được'
                                                            : 'Tất cả tài khoản đều có thể xem'}
                                                    </p>
                                                </div>

                                                {/* Tags */}
                                                <div>
                                                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Thẻ</label>
                                                    <div className="flex flex-wrap items-center gap-1.5 p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 min-h-[42px]">
                                                        {uploadTags.map((tag) => (
                                                            <span key={tag} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary-50 text-primary-700 dark:bg-primary-500/20 dark:text-primary-400">
                                                                {tag}
                                                                <button type="button" onClick={() => setUploadTags(uploadTags.filter(t => t !== tag))} className="hover:text-red-500 transition-colors">
                                                                    <X className="w-3 h-3" />
                                                                </button>
                                                            </span>
                                                        ))}
                                                        <input
                                                            type="text"
                                                            value={uploadTagInput}
                                                            onChange={(e) => setUploadTagInput(e.target.value)}
                                                            onKeyDown={(e) => {
                                                                if (e.key === 'Enter' || e.key === ',') {
                                                                    e.preventDefault();
                                                                    const t = uploadTagInput.replace(/,+$/, '').trim();
                                                                    if (t && !uploadTags.includes(t)) setUploadTags([...uploadTags, t]);
                                                                    setUploadTagInput('');
                                                                }
                                                            }}
                                                            placeholder={uploadTags.length === 0 ? 'Nhấn Enter hoặc , để thêm thẻ...' : ''}
                                                            className="flex-1 min-w-[120px] bg-transparent outline-none text-sm text-gray-900 dark:text-white placeholder-gray-400"
                                                        />
                                                    </div>
                                                </div>

                                                {/* Thumbnail */}
                                                <div>
                                                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Ảnh bìa</label>
                                                    <div className="flex items-center gap-4">
                                                        {uploadThumbnail ? (
                                                            <div className="relative">
                                                                <img src={URL.createObjectURL(uploadThumbnail)} alt="Thumbnail" className="w-16 h-16 rounded-lg object-cover border border-gray-200 dark:border-gray-700" />
                                                                <button
                                                                    onClick={() => setUploadThumbnail(null)}
                                                                    className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600"
                                                                >
                                                                    <X className="w-3 h-3" />
                                                                </button>
                                                            </div>
                                                        ) : (
                                                            <label className="w-16 h-16 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 flex flex-col items-center justify-center cursor-pointer hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-500/10 transition-colors">
                                                                <Image className="w-5 h-5 text-gray-400" />
                                                                <input type="file" accept="image/*" onChange={handleThumbnailSelect} className="hidden" />
                                                            </label>
                                                        )}
                                                        <span className="text-xs text-gray-400">Chọn ảnh bìa cho tài liệu này</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>

                            {/* Footer */}
                            {!uploadSuccess && (
                                <div className="px-6 py-4 flex items-center justify-end gap-3 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                                    <button onClick={closeUploadPanel} className="px-5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                        Hủy
                                    </button>
                                    <button
                                        onClick={handleUpload}
                                        disabled={!stagedFiles.length || !effectiveFrom || !!(effectiveUntil && effectiveUntil < effectiveFrom) || uploading}
                                        className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    >
                                        {uploading ? (
                                            <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Đang tải...</>
                                        ) : (
                                            <><Upload className="w-4 h-4" />Tải lên {stagedFiles.length > 0 ? `${stagedFiles.length} tệp` : ''}</>
                                        )}
                                    </button>
                                </div>
                            )}
                        </div>
                    </ModalFocus>
                )}

                {/* ─── Table View ─── */}
                {view === 'table' && (
                    <div className="overflow-x-auto relative">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30">
                                    <th className="pl-6 pr-2 py-4 w-10">
                                        <button
                                            onClick={toggleSelectAll}
                                            aria-pressed={selectedIds.size === pageDocs.length && pageDocs.length > 0}
                                            className="text-gray-400 hover:text-primary-600 transition-colors"
                                            title={selectedIds.size === pageDocs.length && pageDocs.length > 0 ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
                                        >
                                            {selectedIds.size === pageDocs.length && pageDocs.length > 0
                                                ? <CheckSquare className="w-4 h-4 text-primary-600" />
                                                : <Square className="w-4 h-4" />}
                                        </button>
                                    </th>
                                    <th className="px-4 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tên</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">Danh mục</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Ngày sửa</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Kích thước</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Người sở hữu</th>
                                    <th className="px-6 py-4 text-right text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
                                {listLoading && (
                                    <tr><td colSpan={7} className="px-6 py-14 text-center text-sm text-gray-500">Đang tải tài liệu...</td></tr>
                                )}
                                {!listLoading && pageDocs.length === 0 && (
                                    <tr>
                                        <td colSpan={7}>
                                            <div className="px-6 py-14 text-center">
                                                <DocumentsListState
                                                    loadError={loadError}
                                                    onRetry={fetchDocuments}
                                                    subtitle="Hãy điều chỉnh tìm kiếm hoặc bộ lọc"
                                                />
                                            </div>
                                        </td>
                                    </tr>
                                )}
                                {!listLoading && pageDocs.map((doc) => (
                                    <tr
                                        key={doc.id}
                                        className={`transition-colors ${
                                            selectedIds.has(doc.id)
                                                ? 'bg-primary-50/60 dark:bg-primary-500/10'
                                                : 'hover:bg-gray-50/50 dark:hover:bg-gray-800/40'
                                        }`}
                                    >
                                        <td className="pl-6 pr-2 py-4 w-10">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); toggleSelect(doc.id); }}
                                                className="text-gray-300 hover:text-primary-600 transition-colors"
                                            >
                                                {selectedIds.has(doc.id)
                                                    ? <CheckSquare className="w-4 h-4 text-primary-600" />
                                                    : <Square className="w-4 h-4" />}
                                            </button>
                                        </td>
                                        <DocumentRow
                                            doc={doc}
                                            openMenu={openMenu}
                                            onToggleMenu={(id) => setOpenMenu(openMenu === id ? null : id)}
                                            onView={(d) => navigate(`/documents/${d.id}`)}
                                            onDownload={handleDownload}
                                            onDelete={(id) => setDeleteTarget(id)}
                                            tableRowClassName="px-4 py-4"
                                            renderAsTableCells
                                            processingStatus={processingState[doc.id]}
                                        />
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* ─── Grid View ─── */}
                {view === 'grid' && (
                    <div className="p-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                        {listLoading && <div className="col-span-full py-14 text-center text-sm text-gray-500">Đang tải tài liệu...</div>}
                        {!listLoading && pageDocs.length === 0 && (
                            <div className="col-span-full py-14 text-center">
                                <DocumentsListState loadError={loadError} onRetry={fetchDocuments} />
                            </div>
                        )}
                        {!listLoading && pageDocs.map((doc) => (
                            <DocumentCard
                                key={doc.id}
                                doc={doc}
                                onView={(d) => navigate(`/documents/${d.id}`)}
                                onDownload={handleDownload}
                                onDelete={(id) => setDeleteTarget(id)}
                            />
                        ))}
                    </div>
                )}

                {/* ─── Pagination ─── */}
                {!listLoading && filteredDocs.length > 0 && (
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-6 py-4 border-t border-gray-100 dark:border-gray-800">
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            Hiển thị {Math.min((currentPage - 1) * ROWS_PER_PAGE + 1, filteredDocs.length)} đến{' '}
                            {Math.min(currentPage * ROWS_PER_PAGE, filteredDocs.length)} trong số {filteredDocs.length} tài liệu
                        </p>
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="p-2 rounded border border-gray-200 dark:border-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                            >
                                <ChevronLeft className="w-4 h-4" />
                            </button>
                            {Array.from({ length: totalPages }, (_, i) => i + 1)
                                .filter(p => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1)
                                .reduce((acc, p, idx, arr) => {
                                    if (idx > 0 && p - arr[idx - 1] > 1) acc.push('...');
                                    acc.push(p);
                                    return acc;
                                }, [])
                                .map((p, i) =>
                                    p === '...' ? (
                                        <span key={`dots-${i}`} className="px-2 text-gray-400 text-sm">…</span>
                                    ) : (
                                        <button
                                            key={p}
                                            onClick={() => setCurrentPage(p)}
                                            className={`w-8 h-8 rounded text-sm font-medium transition-colors ${currentPage === p
                                                ? 'bg-primary-600 text-white'
                                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700'
                                                }`}
                                        >
                                            {p}
                                        </button>
                                    )
                                )
                            }
                            <button
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="p-2 rounded border border-gray-200 dark:border-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                            >
                                <ChevronRight className="w-4 h-4" />
                            </button>
                            <span className="ml-2 text-sm text-gray-400 hidden sm:inline">
                                Trang {currentPage} / {totalPages}
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {/* ─── Delete Modal (single) ─── */}
            {deleteTarget && (
                <ModalFocus label="Xóa tài liệu" onClose={() => setDeleteTarget(null)} className="fixed inset-0 z-50 flex items-center justify-center">
                    <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setDeleteTarget(null)} />
                    <div className="relative bg-white dark:bg-gray-900 rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl border border-gray-200 dark:border-gray-800 animate-fade-in">
                        <div className="w-10 h-10 rounded-md bg-red-100 dark:bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                            <Trash2 className="w-5 h-5 text-red-500" />
                        </div>
                        <h3 className="text-base font-bold text-gray-900 dark:text-white text-center mb-2">Xóa tài liệu</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-5">Bạn có chắc chắn muốn xóa tài liệu này không? Nội dung ngừng được dùng để hỏi đáp và có thể khôi phục trong thùng rác trong 30 ngày.</p>
                        <div className="flex gap-3">
                            <button onClick={() => setDeleteTarget(null)} className="flex-1 px-4 py-2 rounded-md border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">Hủy</button>
                            <button onClick={() => handleDelete(deleteTarget)} className="flex-1 px-4 py-2 rounded-md bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition-colors">Xóa</button>
                        </div>
                    </div>
                </ModalFocus>
            )}

            {/* ─── Bulk Delete Modal ─── */}
            {showBulkDeleteModal && (
                <ModalFocus label="Xóa các tài liệu đã chọn" onClose={() => setShowBulkDeleteModal(false)} className="fixed inset-0 z-50 flex items-center justify-center">
                    <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShowBulkDeleteModal(false)} />
                    <div className="relative bg-white dark:bg-gray-900 rounded-xl p-6 max-w-sm w-full mx-4 shadow-2xl border border-gray-200 dark:border-gray-800 animate-fade-in">
                        <div className="w-12 h-12 rounded-xl bg-red-100 dark:bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                            <Trash2 className="w-6 h-6 text-red-500" />
                        </div>
                        <h3 className="text-base font-bold text-gray-900 dark:text-white text-center mb-1">Xóa {selectedIds.size} tài liệu</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-5">
                            Bạn có chắc muốn xóa <span className="font-semibold text-red-500">{selectedIds.size}</span> tài liệu đã chọn? Nội dung ngừng được dùng để hỏi đáp và có thể khôi phục trong thùng rác trong 30 ngày.
                        </p>
                        <div className="flex gap-3">
                            <button onClick={() => setShowBulkDeleteModal(false)} className="flex-1 px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">Hủy</button>
                            <button onClick={handleBulkDelete} className="flex-1 px-4 py-2.5 rounded-lg bg-red-500 hover:bg-red-600 text-white text-sm font-semibold transition-colors">Xóa tất cả</button>
                        </div>
                    </div>
                </ModalFocus>
            )}

            {/* ─── Floating Selection Action Bar ─── */}
            {selectedIds.size > 0 && (
                <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 animate-slide-up">
                    <div className="flex items-center gap-3 bg-gray-900 dark:bg-gray-950 text-white px-5 py-3 rounded-2xl shadow-2xl border border-gray-700">
                        <span className="text-sm font-semibold text-gray-100">
                            Đã chọn <span className="text-primary-400">{selectedIds.size}</span> tài liệu
                        </span>
                        <div className="w-px h-5 bg-gray-600" />
                        <button
                            onClick={() => setShowBulkDeleteModal(true)}
                            className="flex items-center gap-2 px-4 py-1.5 rounded-xl bg-red-500 hover:bg-red-600 text-white text-sm font-semibold transition-colors"
                        >
                            <Trash2 className="w-4 h-4" />
                            Xóa {selectedIds.size} mục
                        </button>
                        <button
                            onClick={clearSelection}
                            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 transition-colors"
                            title="Bỏ chọn"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
