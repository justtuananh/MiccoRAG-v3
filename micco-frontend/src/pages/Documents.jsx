import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Upload, X, File, ChevronDown, CheckCircle2,
    ChevronLeft, ChevronRight, Trash2, Search,
    Loader2, RefreshCw, Play, Plus, Database,
    AlertCircle, Clock, Zap, FolderOpen, Eye, Edit3, Download, Lock
} from 'lucide-react';
import Breadcrumb from '../components/shared/Breadcrumb';
import { workspacesApi, ragDocumentsApi, ragProcessApi } from '../utils/api';
import { useAuth } from '../context/AuthContext';

// ─── Status config ────────────────────────────────────────────────────────────
const STATUS_CONFIG = {
    pending:    { label: 'Chờ xử lý',   color: 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400',    Icon: Clock },
    processing: { label: 'Đang xử lý',  color: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400',       Icon: Loader2 },
    parsing:    { label: 'Đang phân tích', color: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400',    Icon: Loader2 },
    indexing:   { label: 'Đang nạp dữ liệu',   color: 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400', Icon: Loader2 },
    indexed:    { label: 'Đã cập nhật kiến thức',     color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400', Icon: CheckCircle2 },
    failed:     { label: 'Lỗi',          color: 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400',           Icon: AlertCircle },
    pending_approval: { label: 'Chờ duyệt', color: 'bg-amber-50 text-amber-600 border border-amber-200', Icon: Lock },
};

function StatusBadge({ status, approvalStatus }) {
    const isPendingApproval = approvalStatus === 'pending';
    const cfg = STATUS_CONFIG[isPendingApproval ? 'pending_approval' : status?.toLowerCase()] || STATUS_CONFIG.pending;
    const Icon = cfg.Icon;
    const spinning = ['processing', 'parsing', 'indexing'].includes(status?.toLowerCase()) && !isPendingApproval;
    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
            <Icon className={`w-3 h-3 ${spinning ? 'animate-spin' : ''}`} />
            {cfg.label}
        </span>
    );
}

function formatBytes(bytes) {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(dateString) {
    if (!dateString) return '—';
    const date = new Date(dateString);
    const hh = String(date.getHours()).padStart(2, '0');
    const mm = String(date.getMinutes()).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const yy = String(date.getFullYear()).slice(-2);
    return `${hh}:${mm} ${dd}/${month}/${yy}`;
}

function formatVietnameseFilename(str) {
    if (!str) return '';
    const nameParts = str.split('.');
    let ext = '';
    let nameObj = str;
    if (nameParts.length > 1) {
        ext = '.' + nameParts.pop();
        nameObj = nameParts.join('.');
    }
    
    nameObj = nameObj
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/đ/g, "d")
        .replace(/Đ/g, "D")
        .toLowerCase()
        .replace(/\s+/g, '_')
        .replace(/[^a-z0-9_]/g, '');
        
    return nameObj + ext;
}

const ROWS_PER_PAGE = 10;

// ─── Main Component ───────────────────────────────────────────────────────────
export default function Documents() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const isAdmin = user?.role === 'Admin';

    // Workspaces
    const [workspaces, setWorkspaces] = useState([]);
    const [selectedWs, setSelectedWs] = useState(null); // workspace object
    const [wsLoading, setWsLoading] = useState(true);

    // Documents
    const [documents, setDocuments] = useState([]);
    const [docsLoading, setDocsLoading] = useState(false);
    const [search, setSearch] = useState('');

    // Upload
    const [showUpload, setShowUpload] = useState(false);
    const [stagedFiles, setStagedFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);
    const [uploadError, setUploadError] = useState('');
    const [visibility, setVisibility] = useState('internal');
    const fileInputRef = useRef(null);

    // Create workspace
    const [showNewWs, setShowNewWs] = useState(false);
    const [newWsName, setNewWsName] = useState('');
    const [creatingWs, setCreatingWs] = useState(false);

    // Actions
    const [processingIds, setProcessingIds] = useState(new Set());
    const [deleteTarget, setDeleteTarget] = useState(null);
    const [previewTarget, setPreviewTarget] = useState(null);
    const [previewTab, setPreviewTab] = useState('original');
    const [previewContent, setPreviewContent] = useState('');
    const [previewOriginalHTML, setPreviewOriginalHTML] = useState('');
    const [previewLoading, setPreviewLoading] = useState(false);

    // Pagination
    const [currentPage, setCurrentPage] = useState(1);

    // Polling for processing status
    const pollRef = useRef(null);

    // ─── Load workspaces ───────────────────────────────────────────────────────
    useEffect(() => {
        loadWorkspaces();
    }, []);

    const loadWorkspaces = async () => {
        setWsLoading(true);
        try {
            const res = await workspacesApi.list();
            if (res.ok) {
                const data = await res.json();
                setWorkspaces(data);
                if (data.length > 0) setSelectedWs(data[0]);
            }
        } catch (err) {
            console.error('Failed to load workspaces:', err);
        } finally {
            setWsLoading(false);
        }
    };

    // ─── Load documents when workspace changes ─────────────────────────────────
    useEffect(() => {
        if (selectedWs) {
            loadDocuments(selectedWs.id);
            setCurrentPage(1);
        }
    }, [selectedWs?.id]);

    const loadDocuments = async (wsId) => {
        setDocsLoading(true);
        try {
            const res = await ragDocumentsApi.list(wsId);
            if (res.ok) {
                const data = await res.json();
                setDocuments(data);
            }
        } catch (err) {
            console.error('Failed to load documents:', err);
        } finally {
            setDocsLoading(false);
        }
    };

    // ─── Polling for documents being processed ─────────────────────────────────
    useEffect(() => {
        const hasProcessing = documents.some(d =>
            ['processing', 'parsing', 'indexing', 'pending'].includes(d.status?.toLowerCase())
        );
        if (hasProcessing && selectedWs) {
            pollRef.current = setInterval(() => loadDocuments(selectedWs.id), 3000);
        } else {
            clearInterval(pollRef.current);
        }
        return () => clearInterval(pollRef.current);
    }, [documents, selectedWs?.id]);

    // ─── Create workspace ──────────────────────────────────────────────────────
    const handleCreateWorkspace = async () => {
        if (!newWsName.trim()) return;
        setCreatingWs(true);
        try {
            const res = await workspacesApi.create({ name: newWsName.trim(), description: '' });
            if (res.ok) {
                const ws = await res.json();
                setWorkspaces(prev => [...prev, ws]);
                setSelectedWs(ws);
                setNewWsName('');
                setShowNewWs(false);
            }
        } catch (err) {
            console.error('Failed to create workspace:', err);
        } finally {
            setCreatingWs(false);
        }
    };

    // ─── Upload ────────────────────────────────────────────────────────────────
    const stageFiles = (fileList) => {
        if (!fileList?.length) return;
        const filesArray = Array.from(fileList);
        setStagedFiles(prev => [...prev, ...filesArray]);
        setUploadSuccess(false);
    };

    const handleUpload = async () => {
        if (!stagedFiles.length || !selectedWs) return;
        setUploading(true);
        setUploadSuccess(false);
        setUploadError('');
        try {
            const results = await Promise.allSettled(
                stagedFiles.map(f => ragDocumentsApi.upload(selectedWs.id, f, { 
                    visibility,
                    department_id: user?.department_id 
                }))
            );

            const errors = [];
            for (let i = 0; i < results.length; i++) {
                const r = results[i];
                if (r.status === 'rejected') {
                    errors.push(`${stagedFiles[i].name}: ${r.reason?.message || 'Lỗi mạng'}`);
                } else if (!r.value.ok) {
                    const body = await r.value.json().catch(() => ({}));
                    errors.push(`${stagedFiles[i].name}: ${body.detail || `HTTP ${r.value.status}`}`);
                }
            }

            if (errors.length === 0) {
                setUploadSuccess(true);
                setStagedFiles([]);
                await loadDocuments(selectedWs.id);
                setTimeout(() => {
                    setShowUpload(false);
                    setUploadSuccess(false);
                }, 1500);
            } else {
                setUploadError(errors.join('\n'));
            }
        } catch (err) {
            console.error('Upload error:', err);
            setUploadError(`Lỗi kết nối: ${err.message}. Kiểm tra MiccoRAG-v2 server đang chạy ở port 8000.`);
        } finally {
            setUploading(false);
        }
    };

    // ─── Process document ──────────────────────────────────────────────────────
    const handleProcess = async (docId) => {
        setProcessingIds(prev => new Set(prev).add(docId));
        try {
            const res = await ragProcessApi.process(docId);
            if (res.ok) {
                await loadDocuments(selectedWs.id);
            } else {
                const err = await res.json().catch(() => ({}));
                alert(err.detail || 'Không thể xử lý tài liệu');
            }
        } catch (err) {
            console.error('Process error:', err);
        } finally {
            setProcessingIds(prev => {
                const next = new Set(prev);
                next.delete(docId);
                return next;
            });
        }
    };

    // ─── Process all pending ───────────────────────────────────────────────────
    const handleProcessAll = async () => {
        const pendingIds = documents
            .filter(d => ['pending', 'failed'].includes(d.status?.toLowerCase()))
            .map(d => d.id);
        if (!pendingIds.length) return;
        setDocsLoading(true);
        try {
            await ragProcessApi.processBatch(pendingIds);
            await loadDocuments(selectedWs.id);
        } catch (err) {
            console.error('Batch process error:', err);
        } finally {
            setDocsLoading(false);
        }
    };

    // ─── Delete ────────────────────────────────────────────────────────────────
    const handleDelete = async (docId) => {
        try {
            const res = await ragDocumentsApi.delete(docId);
            if (res.ok || res.status === 204) {
                setDocuments(prev => prev.filter(d => d.id !== docId));
            } else {
                const err = await res.json().catch(() => ({}));
                alert(err.detail || 'Xóa thất bại');
            }
        } catch (err) {
            console.error('Delete error:', err);
        }
        setDeleteTarget(null);
    };

    // ─── Edit & Preview ────────────────────────────────────────────────────────
    const handlePreview = async (doc) => {
        setPreviewTarget(doc);
        setPreviewTab('original');
        setPreviewLoading(true);
        setPreviewOriginalHTML('');
        
        try {
            // Load RAG Markdown
            const res = await ragDocumentsApi.markdown(doc.id);
            if (res.ok) {
                const text = await res.text();
                setPreviewContent(text);
            } else {
                setPreviewContent('*Không thể tải nội dung tài liệu (hoặc tài liệu chưa được xử lý)*');
            }

            // Load original DOCX if applicable for native preview
            if (['docx', 'doc'].includes(doc.file_type?.toLowerCase())) {
                setPreviewOriginalHTML('Đang tải bản xem trước...');
                try {
                    const docxRes = await fetch(ragDocumentsApi.downloadUrl(doc.id));
                    const arrayBuffer = await docxRes.arrayBuffer();
                    const mammoth = await import('mammoth');
                    const result = await mammoth.convertToHtml({ arrayBuffer });
                    setPreviewOriginalHTML(result.value || '<p>Tài liệu rỗng</p>');
                } catch (e) {
                    setPreviewOriginalHTML('<p class="text-red-500">Lỗi chuyển đổi DOCX hiển thị. Vui lòng tải xuống bản gốc.</p>');
                }
            }
        } catch (err) {
            setPreviewContent('*Lỗi kết nối khi tải tài liệu*');
        } finally {
            setPreviewLoading(false);
        }
    };

    const handleEditName = async (doc) => {
        const newName = prompt('Nhập tên tài liệu mới:', doc.original_filename);
        if (newName && newName.trim() !== doc.original_filename) {
            try {
                const formattedName = formatVietnameseFilename(newName.trim());
                const res = await ragDocumentsApi.update(doc.id, { original_filename: formattedName });
                if (res.ok) {
                    await loadDocuments(selectedWs.id);
                } else {
                    alert('Lỗi khi đổi tên tài liệu');
                }
            } catch (err) {
                alert('Lỗi kết nối khi đổi tên');
            }
        }
    };

    // ─── Filter + Paginate ─────────────────────────────────────────────────────
    const filtered = documents.filter(d =>
        d.original_filename?.toLowerCase().includes(search.toLowerCase())
    );
    const totalPages = Math.max(1, Math.ceil(filtered.length / ROWS_PER_PAGE));
    const pageDocs = filtered.slice((currentPage - 1) * ROWS_PER_PAGE, currentPage * ROWS_PER_PAGE);

    const pendingCount = documents.filter(d => ['pending', 'failed'].includes(d.status?.toLowerCase())).length;
    const indexedCount = documents.filter(d => d.status?.toLowerCase() === 'indexed').length;

    // ─── Drag & Drop ───────────────────────────────────────────────────────────
    const [dragActive, setDragActive] = useState(false);
    const handleDrag = useCallback((e) => {
        e.preventDefault(); e.stopPropagation();
        setDragActive(e.type === 'dragenter' || e.type === 'dragover');
    }, []);
    const handleDrop = useCallback((e) => {
        e.preventDefault(); setDragActive(false);
        stageFiles(e.dataTransfer?.files);
    }, []);

    // ─── Render ────────────────────────────────────────────────────────────────
    return (
        <div className="space-y-6">
            <Breadcrumb items={[{ label: 'Tổng quan', href: '/dashboard' }, { label: 'Tài liệu' }]} />

            {/* ─── Workspace Selector ─── */}
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4">
                <div className="flex items-center justify-between gap-4 flex-wrap">
                    <div className="flex items-center gap-3">
                        <Database className="w-5 h-5 text-primary-600 dark:text-secondary-400 flex-shrink-0" />
                        <div>
                            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Nhóm tài liệu</p>
                            {wsLoading ? (
                                <div className="h-8 w-40 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
                            ) : workspaces.length === 0 ? (
                                <p className="text-sm text-gray-400">Chưa có nhóm tài liệu nào</p>
                            ) : (
                                <div className="flex items-center gap-2 flex-wrap">
                                    {workspaces.map(ws => (
                                        <button
                                            key={ws.id}
                                            onClick={() => setSelectedWs(ws)}
                                            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                                                selectedWs?.id === ws.id
                                                    ? 'bg-primary-600 text-white shadow-sm'
                                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                                            }`}
                                        >
                                            {ws.name}
                                            <span className="ml-1.5 opacity-60 text-xs">{ws.document_count}</span>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {/* Quick stats */}
                        {selectedWs && (
                            <div className="hidden sm:flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 mr-2">
                                <span className="flex items-center gap-1">
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />{indexedCount} Đã xử lý
                                </span>
                                {pendingCount > 0 && (
                                    <span className="flex items-center gap-1">
                                        <Clock className="w-3.5 h-3.5 text-amber-500" />{pendingCount} Chờ xử lý
                                    </span>
                                )}
                            </div>
                        )}
                        {/* New workspace */}
                        {!showNewWs ? (
                            <button
                                onClick={() => setShowNewWs(true)}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dashed border-gray-300 dark:border-gray-600 text-xs text-gray-500 dark:text-gray-400 hover:border-primary-400 hover:text-primary-600 dark:hover:text-secondary-400 transition-colors"
                            >
                                <Plus className="w-3.5 h-3.5" /> Tạo nhóm tài liệu mới
                            </button>
                        ) : (
                            <div className="flex items-center gap-1.5">
                                <input
                                    type="text"
                                    value={newWsName}
                                    onChange={e => setNewWsName(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && handleCreateWorkspace()}
                                    placeholder="Tên nhóm tài liệu..."
                                    autoFocus
                                    className="px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-primary-500/30 w-36"
                                />
                                <button
                                    onClick={handleCreateWorkspace}
                                    disabled={creatingWs || !newWsName.trim()}
                                    className="px-2.5 py-1.5 rounded-lg bg-primary-600 text-white text-xs font-medium hover:bg-primary-700 disabled:opacity-50"
                                >
                                    {creatingWs ? '...' : 'Tạo'}
                                </button>
                                <button onClick={() => { setShowNewWs(false); setNewWsName(''); }} className="p-1.5 text-gray-400 hover:text-gray-600">
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* ─── Toolbar ─── */}
            {selectedWs && (
                <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
                        <div className="flex items-center gap-2 flex-1 max-w-sm">
                            <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <input
                                type="text"
                                placeholder="Tìm kiếm tài liệu..."
                                value={search}
                                onChange={e => { setSearch(e.target.value); setCurrentPage(1); }}
                                className="bg-transparent outline-none text-sm text-gray-700 dark:text-gray-300 w-full placeholder-gray-400"
                            />
                            {search && <button onClick={() => setSearch('')}><X className="w-4 h-4 text-gray-400 hover:text-gray-600" /></button>}
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => loadDocuments(selectedWs.id)}
                                className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                                title="Làm mới"
                            >
                                <RefreshCw className={`w-4 h-4 ${docsLoading ? 'animate-spin' : ''}`} />
                            </button>
                            {isAdmin && pendingCount > 0 && (
                                <button
                                    onClick={handleProcessAll}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-xs font-medium transition-colors"
                                >
                                    <Zap className="w-3.5 h-3.5" />
                                    Xử lý tất cả ({pendingCount})
                                </button>
                            )}
                            <button
                                onClick={() => setShowUpload(!showUpload)}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-xs font-semibold transition-colors"
                            >
                                <Upload className="w-3.5 h-3.5" />
                                {user?.role === 'Admin' ? 'Tải lên' : 'Tải lên & Đề xuất phê duyệt'}
                            </button>
                        </div>
                    </div>

                    {/* ─── Upload Modal ─── */}
                    {showUpload && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center">
                            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => { setShowUpload(false); setStagedFiles([]); setUploadSuccess(false); setUploadError(''); }} />
                            <div className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md mx-4 border border-gray-200 dark:border-gray-800 animate-fade-in overflow-hidden">
                                <div className="px-5 py-4 flex items-center justify-between bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                                    <h3 className="text-sm font-bold text-gray-900 dark:text-white">Tải lên vào "{selectedWs.name}"</h3>
                                    <button onClick={() => { setShowUpload(false); setStagedFiles([]); setUploadSuccess(false); }} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                                <div className="p-5 space-y-4">
                                    {uploadSuccess ? (
                                        <div className="py-8 text-center">
                                            <div className="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-500/20 flex items-center justify-center mx-auto mb-3">
                                                <CheckCircle2 className="w-7 h-7 text-emerald-500" />
                                            </div>
                                            <p className="font-semibold text-gray-900 dark:text-white">Tải lên thành công!</p>
                                            <p className="text-xs text-gray-400 mt-1">Nhấn "Phân tích" để index tài liệu vào RAG</p>
                                        </div>
                                    ) : (
                                        <>
                                            {/* Visibility Selector */}
                                            <div className="space-y-2">
                                                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Phạm vi truy cập</label>
                                                <div className="flex gap-3">
                                                    <button
                                                        onClick={() => setVisibility('internal')}
                                                        className={`flex-1 flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all ${visibility === 'internal' ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10' : 'border-gray-200 dark:border-gray-800 hover:border-gray-300'}`}
                                                    >
                                                        <Lock className={`w-5 h-5 ${visibility === 'internal' ? 'text-primary-600' : 'text-gray-400'}`} />
                                                        <div className="text-center">
                                                            <div className={`text-xs font-bold ${visibility === 'internal' ? 'text-primary-900 dark:text-primary-100' : 'text-gray-700'}`}>Nội bộ</div>
                                                            <div className="text-[10px] text-gray-400">Phòng ban</div>
                                                        </div>
                                                    </button>
                                                    <button
                                                        onClick={() => setVisibility('public')}
                                                        className={`flex-1 flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all ${visibility === 'public' ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10' : 'border-gray-200 dark:border-gray-800 hover:border-gray-300'}`}
                                                    >
                                                        <Eye className={`w-5 h-5 ${visibility === 'public' ? 'text-primary-600' : 'text-gray-400'}`} />
                                                        <div className="text-center">
                                                            <div className={`text-xs font-bold ${visibility === 'public' ? 'text-primary-900 dark:text-primary-100' : 'text-gray-700'}`}>Công khai</div>
                                                            <div className="text-[10px] text-gray-400">Toàn công ty</div>
                                                        </div>
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Drop zone */}
                                            <div
                                                onDragEnter={handleDrag} onDragLeave={handleDrag}
                                                onDragOver={handleDrag} onDrop={handleDrop}
                                                onClick={() => fileInputRef.current?.click()}
                                                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${dragActive ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10' : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 hover:bg-gray-50 dark:hover:bg-gray-800/50'}`}
                                            >
                                                <Upload className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                                                <p className="text-sm text-gray-500 dark:text-gray-400">Kéo thả hoặc <span className="text-primary-600 dark:text-secondary-400 font-medium">chọn tệp</span></p>
                                                <p className="text-xs text-gray-400 mt-1">PDF, DOCX, PPTX, TXT, MD — tối đa 50 MB</p>
                                                <input
                                                    ref={fileInputRef}
                                                    type="file"
                                                    multiple
                                                    accept=".pdf,.txt,.md,.docx,.pptx"
                                                    className="hidden"
                                                    onChange={e => { stageFiles(e.target.files); e.target.value = ''; }}
                                                />
                                            </div>

                                            {/* Staged files */}
                                            {stagedFiles.length > 0 && (
                                                <div className="space-y-2 max-h-40 overflow-y-auto">
                                                    {stagedFiles.map((f, i) => (
                                                        <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800">
                                                            <File className="w-4 h-4 text-gray-400 flex-shrink-0" />
                                                            <span className="flex-1 text-xs text-gray-700 dark:text-gray-300 truncate">{f.name}</span>
                                                            <span className="text-xs text-gray-400">{formatBytes(f.size)}</span>
                                                            <button onClick={() => setStagedFiles(prev => prev.filter((_, idx) => idx !== i))} className="text-gray-300 hover:text-red-500 transition-colors">
                                                                <X className="w-3.5 h-3.5" />
                                                            </button>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Upload error */}
                                            {uploadError && (
                                                <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30">
                                                    <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                                                    <pre className="text-xs text-red-700 dark:text-red-400 whitespace-pre-wrap font-sans">{uploadError}</pre>
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                                {!uploadSuccess && (
                                    <div className="px-5 py-3 flex justify-end gap-2 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                                        <button onClick={() => { setShowUpload(false); setStagedFiles([]); }} className="px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">Hủy</button>
                                        <button
                                            onClick={handleUpload}
                                            disabled={!stagedFiles.length || uploading}
                                            className="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
                                        >
                                            {uploading ? <><Loader2 className="w-4 h-4 animate-spin" />Đang tải...</> : <><Upload className="w-4 h-4" />{user?.role === 'Admin' ? 'Tải lên' : 'Đề xuất phê duyệt'} {stagedFiles.length > 1 ? `${stagedFiles.length} tệp` : ''}</>}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* ─── Documents Table ─── */}
                    {docsLoading && documents.length === 0 ? (
                        <div className="flex items-center justify-center py-16">
                            <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
                        </div>
                    ) : filtered.length === 0 ? (
                        <div className="py-16 text-center">
                            <FolderOpen className="w-12 h-12 text-gray-200 dark:text-gray-700 mx-auto mb-3" />
                            <p className="text-gray-500 dark:text-gray-400 font-medium">
                                {search ? 'Không tìm thấy tài liệu' : 'Workspace này chưa có tài liệu'}
                            </p>
                            {!search && (
                                <button
                                    onClick={() => setShowUpload(true)}
                                    className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors"
                                >
                                    <Upload className="w-4 h-4" />{user?.role === 'Admin' ? 'Tải lên tài liệu đầu tiên' : 'Đề xuất phê duyệt tài liệu đầu tiên'}
                                </button>
                            )}
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-gray-100 dark:border-gray-800">
                                        <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tên tệp</th>
                                        <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">Loại</th>
                                        <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">Phạm vi</th>
                                        <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Kích thước</th>
                                        <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Trạng thái</th>
                                        <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Ngày upload</th>
                                        <th className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Thao tác</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
                                    {pageDocs.map(doc => {
                                        const isProcessing = processingIds.has(doc.id) || ['processing', 'parsing', 'indexing'].includes(doc.status?.toLowerCase());
                                        const isApproved = doc.approval_status === 'approved';
                                        const canProcess = isApproved && isAdmin && ['pending', 'failed'].includes(doc.status?.toLowerCase()) && !processingIds.has(doc.id);
                                        return (
                                            <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors group">
                                                <td className="px-5 py-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-8 h-8 rounded-lg bg-primary-50 dark:bg-secondary-500/10 flex items-center justify-center flex-shrink-0">
                                                            <File className="w-4 h-4 text-primary-600 dark:text-secondary-400" />
                                                        </div>
                                                        <span className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-xs">
                                                            {doc.original_filename}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="px-5 py-3 hidden sm:table-cell">
                                                    <span className="text-xs font-medium uppercase text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">
                                                        {doc.file_type || '?'}
                                                    </span>
                                                </td>
                                                <td className="px-5 py-3 hidden sm:table-cell">
                                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 w-fit ${
                                                        doc.visibility === 'public' 
                                                        ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400' 
                                                        : 'bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400'
                                                    }`}>
                                                        {doc.visibility === 'public' ? (
                                                            <><Eye className="w-3 h-3" /> Công khai</>
                                                        ) : (
                                                            <><Lock className="w-3 h-3" /> Nội bộ</>
                                                        )}
                                                    </span>
                                                </td>
                                                <td className="px-5 py-3 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">
                                                    {formatBytes(doc.file_size)}
                                                </td>
                                                <td className="px-5 py-3">
                                                    <StatusBadge status={doc.status} approvalStatus={doc.approval_status} />
                                                    {doc.approval_status === 'pending' && (
                                                        <p className="text-[10px] text-amber-600 mt-1 font-medium">Chờ Admin phê duyệt để xử lý RAG</p>
                                                    )}
                                                    {doc.error_message && (
                                                        <p className="text-xs text-red-500 mt-1 max-w-xs truncate" title={doc.error_message}>
                                                            {doc.error_message}
                                                        </p>
                                                    )}
                                                </td>
                                                <td className="px-5 py-3 text-xs text-gray-500 dark:text-gray-400 hidden lg:table-cell font-mono">
                                                    {formatDate(doc.created_at)}
                                                </td>
                                                <td className="px-5 py-3">
                                                    <div className="flex items-center justify-end gap-1.5">
                                                        {canProcess && (
                                                            <button
                                                                onClick={() => handleProcess(doc.id)}
                                                                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-primary-50 hover:bg-primary-100 dark:bg-secondary-500/10 dark:hover:bg-secondary-500/20 text-primary-700 dark:text-secondary-400 text-xs font-medium transition-colors"
                                                                title="Phân tích và index"
                                                            >
                                                                <Play className="w-3 h-3" /> Phân tích
                                                            </button>
                                                        )}
                                                        {isProcessing && (
                                                            <span className="flex items-center gap-1 text-xs text-blue-500 px-2">
                                                                <Loader2 className="w-3 h-3 animate-spin" /> Đang xử lý...
                                                            </span>
                                                        )}
                                                        <button
                                                            onClick={() => handlePreview(doc)}
                                                            className="p-1.5 rounded-lg text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:text-primary-400 dark:hover:bg-primary-500/10 transition-colors"
                                                            title="Xem trước nội dung"
                                                        >
                                                            <Eye className="w-4 h-4" />
                                                        </button>
                                                        <button
                                                            onClick={() => handleEditName(doc)}
                                                            className="p-1.5 rounded-lg text-gray-400 hover:text-amber-600 hover:bg-amber-50 dark:hover:text-amber-400 dark:hover:bg-amber-500/10 transition-colors"
                                                            title="Đổi tên"
                                                        >
                                                            <Edit3 className="w-4 h-4" />
                                                        </button>
                                                        <button
                                                            onClick={() => setDeleteTarget(doc)}
                                                            className="p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                                                            title="Xóa"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Pagination */}
                    {filtered.length > ROWS_PER_PAGE && (
                        <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100 dark:border-gray-800">
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                {(currentPage - 1) * ROWS_PER_PAGE + 1}–{Math.min(currentPage * ROWS_PER_PAGE, filtered.length)} / {filtered.length}
                            </p>
                            <div className="flex items-center gap-1">
                                <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1} className="p-2 rounded border border-gray-200 dark:border-gray-700 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40">
                                    <ChevronLeft className="w-4 h-4" />
                                </button>
                                <span className="text-sm text-gray-500 px-2">{currentPage} / {totalPages}</span>
                                <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages} className="p-2 rounded border border-gray-200 dark:border-gray-700 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40">
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ─── No workspace selected ─── */}
            {!wsLoading && workspaces.length === 0 && (
                <div className="bg-white dark:bg-gray-900 rounded-xl border border-dashed border-gray-300 dark:border-gray-700 p-12 text-center">
                    <Database className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                    <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-2">Tạo workspace đầu tiên</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Workspace là không gian tổ chức tài liệu cho RAG chatbot</p>
                    <button
                        onClick={() => setShowNewWs(true)}
                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors"
                    >
                        <Plus className="w-4 h-4" />Tạo workspace
                    </button>
                </div>
            )}

            {/* ─── Delete Modal ─── */}
            {deleteTarget && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setDeleteTarget(null)} />
                    <div className="relative bg-white dark:bg-gray-900 rounded-xl p-6 max-w-sm w-full mx-4 shadow-xl border border-gray-200 dark:border-gray-800 animate-fade-in">
                        <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                            <Trash2 className="w-5 h-5 text-red-500" />
                        </div>
                        <h3 className="text-base font-bold text-gray-900 dark:text-white text-center mb-1">Xóa tài liệu</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-1 truncate px-4">"{deleteTarget.original_filename}"</p>
                        <p className="text-xs text-gray-400 text-center mb-5">Hành động này không thể hoàn tác và sẽ xóa tất cả dữ liệu đã index.</p>
                        <div className="flex gap-3">
                            <button onClick={() => setDeleteTarget(null)} className="flex-1 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">Hủy</button>
                            <button onClick={() => handleDelete(deleteTarget.id)} className="flex-1 py-2 rounded-lg bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition-colors">Xóa</button>
                        </div>
                    </div>
                </div>
            )}

            {/* ─── Preview Modal ─── */}
            {previewTarget && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => { setPreviewTarget(null); setPreviewContent(''); setPreviewOriginalHTML(''); }} />
                    <div className="relative bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-4xl max-h-[85vh] flex flex-col border border-gray-200 dark:border-gray-800 animate-fade-in overflow-hidden">
                        <div className="px-5 py-3 flex items-center justify-between bg-gray-50 dark:bg-gray-800 border-b border-gray-100 dark:border-gray-800">
                            <div className="flex items-center gap-3">
                                <h3 className="text-sm font-bold text-gray-900 dark:text-white truncate max-w-lg">{previewTarget.original_filename}</h3>
                                <a 
                                    href={ragDocumentsApi.downloadUrl(previewTarget.id)} 
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-secondary-50 dark:bg-secondary-900/30 text-secondary-600 dark:text-secondary-400 text-xs font-semibold hover:bg-secondary-100 transition-colors"
                                >
                                    <Download className="w-3.5 h-3.5" />
                                    Tải xuống
                                </a>
                            </div>
                            <button onClick={() => { setPreviewTarget(null); setPreviewContent(''); setPreviewOriginalHTML(''); }} className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white transition-colors">
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Tabs Navigation */}
                        <div className="flex border-b border-gray-200 dark:border-gray-800">
                            <button
                                onClick={() => setPreviewTab('original')}
                                className={`flex-1 py-3 text-sm font-medium border-b-2 transition-colors ${previewTab === 'original' ? 'border-primary-600 text-primary-600 dark:border-secondary-400 dark:text-secondary-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}`}
                            >
                                File gốc tải lên
                            </button>
                            <button
                                onClick={() => setPreviewTab('rag')}
                                className={`flex-1 py-3 text-sm font-medium border-b-2 transition-colors ${previewTab === 'rag' ? 'border-primary-600 text-primary-600 dark:border-secondary-400 dark:text-secondary-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}`}
                            >
                                Kết quả phân tích RAG
                            </button>
                        </div>

                        <div className="p-0 overflow-y-auto flex-1 bg-gray-50 dark:bg-gray-900/50">
                            {previewTab === 'original' ? (
                                ['pdf', 'txt', 'md'].includes(previewTarget.file_type?.toLowerCase()) ? (
                                    <iframe 
                                        src={ragDocumentsApi.downloadUrl(previewTarget.id)} 
                                        className="w-full h-full min-h-[500px] border-0 bg-white"
                                        title="File gốc"
                                    />
                                ) : ['docx', 'doc'].includes(previewTarget.file_type?.toLowerCase()) ? (
                                    <div className="p-8 max-w-4xl mx-auto bg-white dark:bg-gray-800 min-h-[500px] shadow-sm">
                                        {previewOriginalHTML === 'Đang tải bản xem trước...' ? (
                                            <div className="flex items-center justify-center py-20">
                                                <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
                                            </div>
                                        ) : (
                                            <div 
                                                className="prose max-w-none prose-sm sm:prose-base prose-slate dark:prose-invert" 
                                                dangerouslySetInnerHTML={{ __html: previewOriginalHTML }} 
                                            />
                                        )}
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center py-24 text-center h-full min-h-[500px] bg-white dark:bg-gray-900">
                                        <div className="w-16 h-16 rounded-full bg-primary-50 dark:bg-primary-500/10 flex items-center justify-center mb-4">
                                            <File className="w-8 h-8 text-primary-500" />
                                        </div>
                                        <h4 className="text-base font-bold text-gray-900 dark:text-white mb-2">
                                            Không thể xem trực tiếp tệp .{previewTarget.file_type?.toUpperCase()}
                                        </h4>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 max-w-sm px-4">
                                            Trình duyệt hiện tại không hỗ trợ xem trước định dạng này. Vui lòng tải xuống để đọc trên máy của bạn.
                                        </p>
                                        <a 
                                            href={ragDocumentsApi.downloadUrl(previewTarget.id)} 
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 hover:shadow transition-all"
                                        >
                                            <Download className="w-4 h-4" />
                                            Tải xuống ngay
                                        </a>
                                    </div>
                                )
                            ) : (
                                <div className="p-6">
                                    {previewLoading ? (
                                        <div className="flex items-center justify-center py-20">
                                            <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
                                        </div>
                                    ) : (
                                        <div className="prose prose-sm dark:prose-invert max-w-none">
                                            {previewContent && !previewContent.includes('*Không thể tải') ? (
                                                <pre className="whitespace-pre-wrap font-sans text-sm font-medium text-gray-900 dark:text-gray-100 leading-relaxed bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">{previewContent}</pre>
                                            ) : (
                                                <p className="text-gray-400 italic text-center py-10">{previewContent || 'Tài liệu trống hoặc chưa được index vào RAG.'}</p>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
