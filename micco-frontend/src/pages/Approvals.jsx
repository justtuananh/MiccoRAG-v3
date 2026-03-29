import { useState, useEffect, useCallback, useRef } from 'react';
import {
    ClipboardCheck, FileText, BookOpen, Check, X,
    Clock, Globe, Lock, ChevronDown, Loader2, RefreshCw,
    Eye, Tag, User, Building2, AlertCircle, CheckCircle2, FileSearch,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { approvalsApi } from '../utils/api';
import Breadcrumb from '../components/shared/Breadcrumb';

const PREVIEWABLE = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp', 'docx', 'txt', 'md'];
const MIME_MAP = {
    pdf: 'application/pdf',
    jpg: 'image/jpeg', jpeg: 'image/jpeg',
    png: 'image/png', gif: 'image/gif', webp: 'image/webp',
};

// Trạng thái processing theo thứ tự
const PROCESSING_STEPS = [
    { key: 'pending',    label: 'Chờ xử lý',    icon: Clock },
    { key: 'parsing',    label: 'Đang phân tích', icon: FileSearch },
    { key: 'processing', label: 'Đang xử lý',    icon: Loader2 },
    { key: 'indexing',   label: 'Đang lập chỉ mục', icon: Loader2 },
    { key: 'indexed',   label: 'Hoàn tất',       icon: CheckCircle2 },
    { key: 'failed',    label: 'Thất bại',       icon: AlertCircle },
];

const getStepIndex = (status) => {
    const idx = PROCESSING_STEPS.findIndex(s => s.key === (status?.toLowerCase?.() || status));
    return idx === -1 ? 0 : idx;
};

export default function Approvals() {
    const { authFetch } = useAuth();
    const [tab, setTab] = useState('documents');
    const [data, setData] = useState({ documents: [], knowledge: [] });
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(null);
    const [rejectModal, setRejectModal] = useState(null);
    const [rejectNote, setRejectNote] = useState('');
    const [toast, setToast] = useState(null);
    const [preview, setPreview] = useState(null);
    const [previewLoading, setPreviewLoading] = useState(null);

    // Map docId → processing state after approval
    // { status, chunk_count, error_message, updated_at }
    const [processingState, setProcessingState] = useState({});
    // List of docIds being processed (shown in a separate "Processing" section)
    const [processingDocs, setProcessingDocs] = useState([]);
    const pollingRef = useRef({});

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const fetchPending = useCallback(async () => {
        setLoading(true);
        try {
            const res = await authFetch('/api/approvals/pending');
            if (res.ok) setData(await res.json());
        } catch { /* silent */ }
        finally { setLoading(false); }
    }, [authFetch]);

    // Poll processing status for a document
    const startPolling = useCallback((docId) => {
        if (pollingRef.current[docId]) return; // already polling
        pollingRef.current[docId] = true;

        const poll = async () => {
            if (!pollingRef.current[docId]) return;
            try {
                const res = await approvalsApi.getDocumentStatus(docId);
                if (res.ok) {
                    const st = await res.json();
                    setProcessingState(prev => ({ ...prev, [docId]: st }));
                    // Stop polling when done or failed
                    if (st.status === 'indexed' || st.status === 'failed') {
                        pollingRef.current[docId] = false;
                        // Remove from processing list after short delay (so user sees completion)
                        setTimeout(() => {
                            setProcessingDocs(prev => prev.filter(d => d.id !== docId));
                            setProcessingState(prev => {
                                const next = { ...prev };
                                delete next[docId];
                                return next;
                            });
                        }, 3000);
                        return;
                    }
                }
            } catch { /* silent */ }
            if (pollingRef.current[docId]) {
                setTimeout(poll, 3000);
            }
        };
        poll();
    }, []);

    const stopPolling = useCallback((docId) => {
        pollingRef.current[docId] = false;
    }, []);

    useEffect(() => {
        return () => {
            // Cleanup all polling on unmount
            Object.keys(pollingRef.current).forEach(id => {
                pollingRef.current[id] = false;
            });
        };
    }, []);

    useEffect(() => { fetchPending(); }, [fetchPending]);

    // Cleanup blob URLs on unmount
    useEffect(() => {
        return () => { if (preview?.blobUrl) URL.revokeObjectURL(preview.blobUrl); };
    }, [preview]);

    const handlePreview = async (type, item) => {
        setPreviewLoading(`${type}-${item.id}`);
        try {
            if (type === 'knowledge') {
                const res = await authFetch(`/api/knowledge/${item.id}`);
                if (res.ok) {
                    const full = await res.json();
                    setPreview({ item, type, html: full.content_html || full.content_text });
                }
            } else {
                const ext = (item.file_type || '').toLowerCase();
                const canEmbed = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext);
                const isTextBased = ['docx', 'txt', 'md'].includes(ext);

                if (canEmbed) {
                    const res = await authFetch(`/api/documents/${item.id}/download`);
                    if (res.ok) {
                        const mime = MIME_MAP[ext] || 'application/octet-stream';
                        const blob = new Blob([await res.arrayBuffer()], { type: mime });
                        const blobUrl = URL.createObjectURL(blob);
                        setPreview({ item, type, blobUrl, ext });
                    }
                } else if (isTextBased) {
                    const res = await authFetch(`/api/approvals/documents/${item.id}/preview`);
                    if (res.ok) {
                        const data = await res.json();
                        setPreview({ item, type, text: data.content, ext });
                    }
                } else {
                    // Not previewable — show metadata only
                    setPreview({ item, type, ext });
                }
            }
        } catch { showToast('Không thể tải xem trước', 'error'); }
        finally { setPreviewLoading(null); }
    };

    const closePreview = () => {
        if (preview?.blobUrl) URL.revokeObjectURL(preview.blobUrl);
        setPreview(null);
    };

    const handleApprove = async (type, id) => {
        setActionLoading(`${type}-${id}`);
        try {
            const res = await authFetch(`/api/approvals/${type}/${id}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}),
            });
            if (res.ok) {
                const json = await res.json();
                closePreview();
                if (type === 'documents') {
                    showToast(json.message || 'Đã phê duyệt — đang xử lý tài liệu...', 'success');
                    // Move doc from pending list → processing list
                    const doc = data.documents.find(d => d.id === id);
                    if (doc) {
                        setProcessingDocs(prev => [...prev, doc]);
                    }
                    setData(prev => ({
                        ...prev,
                        documents: prev.documents.filter(d => d.id !== id),
                    }));
                    // Start polling processing status
                    setProcessingState(prev => ({ ...prev, [id]: { status: 'processing', chunk_count: 0 } }));
                    startPolling(id);
                } else {
                    showToast(json.message || 'Đã phê duyệt thành công');
                    setData(prev => ({
                        ...prev,
                        knowledge: prev.knowledge.filter(k => k.id !== id),
                    }));
                }
            } else {
                const err = await res.json();
                showToast(err.detail || 'Thao tác thất bại', 'error');
            }
        } catch { showToast('Có lỗi xảy ra', 'error'); }
        finally { setActionLoading(null); }
    };

    const handleReject = async () => {
        if (!rejectModal) return;
        const { type, id } = rejectModal;
        setActionLoading(`${type}-${id}`);
        try {
            const res = await authFetch(`/api/approvals/${type}/${id}/reject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ note: rejectNote }),
            });
            if (res.ok) {
                showToast('Đã từ chối');
                setRejectModal(null);
                setRejectNote('');
                closePreview();
                fetchPending();
            } else {
                const err = await res.json();
                showToast(err.detail || 'Thao tác thất bại', 'error');
            }
        } catch { showToast('Có lỗi xảy ra', 'error'); }
        finally { setActionLoading(null); }
    };

    const docCount = data.documents.length;
    const knCount = data.knowledge.length;
    const totalPending = docCount + knCount;

    return (
        <div className="space-y-6 px-2 md:px-4">
            <div className="px-2 pt-4">
                <Breadcrumb items={[
                    { label: 'Tổng quan', href: '/dashboard' },
                    { label: 'Phê duyệt' },
                ]} />
            </div>

            {/* Toast */}
            {toast && (
                <div className={`fixed top-6 right-6 z-[70] flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-xl border text-sm font-medium
                    ${toast.type === 'error'
                        ? 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700 text-red-700 dark:text-red-300'
                        : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200'
                    }`}>
                    {toast.type === 'error'
                        ? <X className="w-4 h-4 text-red-500" />
                        : <Check className="w-4 h-4 text-emerald-500" />
                    }
                    {toast.msg}
                </div>
            )}

            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <ClipboardCheck className="w-7 h-7 text-primary-600 dark:text-secondary-400" />
                        Phê duyệt nội dung
                    </h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        Xem xét và phê duyệt tài liệu, tri thức trước khi đồng bộ AI
                    </p>
                </div>
                <button
                    onClick={fetchPending}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Làm mới
                </button>
            </div>

            {/* Tabs */}
            <div className="flex items-center gap-1 border-b border-gray-200 dark:border-gray-800">
                <button
                    onClick={() => setTab('documents')}
                    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                        tab === 'documents'
                            ? 'border-primary-600 text-primary-600 dark:text-secondary-400 dark:border-secondary-400'
                            : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                    }`}
                >
                    <FileText className="w-4 h-4" />
                    Tài liệu
                    {docCount > 0 && (
                        <span className="px-1.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400">
                            {docCount}
                        </span>
                    )}
                </button>
                <button
                    onClick={() => setTab('knowledge')}
                    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                        tab === 'knowledge'
                            ? 'border-primary-600 text-primary-600 dark:text-secondary-400 dark:border-secondary-400'
                            : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                    }`}
                >
                    <BookOpen className="w-4 h-4" />
                    Tri thức
                    {knCount > 0 && (
                        <span className="px-1.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400">
                            {knCount}
                        </span>
                    )}
                </button>
            </div>

            {/* Content */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
                </div>
            ) : (
                <div className="space-y-6">
                    {/* Section: Đang xử lý */}
                    {processingDocs.length > 0 && tab === 'documents' && (
                        <div className="px-2">
                            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                                <Loader2 className="w-4 h-4 text-primary-500 animate-spin" />
                                Đang xử lý
                            </h3>
                            <div className="space-y-3">
                                {processingDocs.map(doc => (
                                    <ApprovalCard
                                        key={doc.id}
                                        item={doc}
                                        type="documents"
                                        actionLoading={null}
                                        previewLoading={null}
                                        processingStatus={processingState[doc.id]}
                                        onPreview={null}
                                        onApprove={null}
                                        onReject={null}
                                    />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Section: Chờ phê duyệt */}
                    <div className="px-2">
                        {totalPending === 0 && processingDocs.length === 0 && (
                            <div className="text-center py-20">
                                <div className="w-16 h-16 rounded-full bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
                                    <Check className="w-8 h-8 text-emerald-500" />
                                </div>
                                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">Không có gì cần phê duyệt</h3>
                                <p className="text-sm text-gray-500 dark:text-gray-400">Tất cả nội dung đã được xử lý</p>
                            </div>
                        )}
                        {tab === 'documents' && (
                            data.documents.length > 0 ? (
                                <>
                                    <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                                        <Clock className="w-4 h-4 text-amber-500" />
                                        Chờ phê duyệt
                                    </h3>
                                    <div className="space-y-3">
                                        {data.documents.map(doc => (
                                            <ApprovalCard
                                                key={doc.id}
                                                item={doc}
                                                type="documents"
                                                actionLoading={actionLoading}
                                                previewLoading={previewLoading}
                                                processingStatus={null}
                                                onPreview={() => handlePreview('documents', doc)}
                                                onApprove={() => handleApprove('documents', doc.id)}
                                                onReject={() => { setRejectModal({ type: 'documents', id: doc.id }); setRejectNote(''); }}
                                            />
                                        ))}
                                    </div>
                                </>
                            ) : processingDocs.length === 0 && (
                                <p className="text-center py-8 text-sm text-gray-400">Không có tài liệu chờ phê duyệt</p>
                            )
                        )}
                        {tab === 'knowledge' && (
                            data.knowledge.length > 0 ? (
                                <>
                                    <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                                        <Clock className="w-4 h-4 text-amber-500" />
                                        Chờ phê duyệt
                                    </h3>
                                    <div className="space-y-3">
                                        {data.knowledge.map(entry => (
                                            <ApprovalCard
                                                key={entry.id}
                                                item={entry}
                                                type="knowledge"
                                                actionLoading={actionLoading}
                                                previewLoading={previewLoading}
                                                onPreview={() => handlePreview('knowledge', entry)}
                                                onApprove={() => handleApprove('knowledge', entry.id)}
                                                onReject={() => { setRejectModal({ type: 'knowledge', id: entry.id }); setRejectNote(''); }}
                                            />
                                        ))}
                                    </div>
                                </>
                            ) : (
                                <p className="text-center py-8 text-sm text-gray-400">Không có tri thức chờ phê duyệt</p>
                            )
                        )}
                    </div>
                </div>
            )}

            {/* Preview Modal */}
            {preview && (
                <PreviewModal
                    preview={preview}
                    actionLoading={actionLoading}
                    onClose={closePreview}
                    onApprove={() => handleApprove(preview.type, preview.item.id)}
                    onReject={() => { setRejectModal({ type: preview.type, id: preview.item.id }); setRejectNote(''); }}
                />
            )}

            {/* Reject Modal */}
            {rejectModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-800 p-6 max-w-md w-full mx-4">
                        <h3 className="text-base font-bold text-gray-900 dark:text-white mb-1">Từ chối nội dung</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Nhập lý do từ chối (tuỳ chọn) để thông báo cho người tải lên.</p>
                        <textarea
                            value={rejectNote}
                            onChange={(e) => setRejectNote(e.target.value)}
                            placeholder="Lý do từ chối..."
                            rows={3}
                            className="w-full px-3 py-2.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 resize-none mb-4"
                        />
                        <div className="flex gap-3">
                            <button
                                onClick={() => setRejectModal(null)}
                                className="flex-1 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                            >
                                Hủy
                            </button>
                            <button
                                onClick={handleReject}
                                disabled={!!actionLoading}
                                className="flex-1 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-semibold transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
                            >
                                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <X className="w-4 h-4" />}
                                Từ chối
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}


// ─── Preview Modal ────────────────────────────────────────────

function PreviewModal({ preview, actionLoading, onClose, onApprove, onReject }) {
    const { item, type, blobUrl, html, text, ext } = preview;
    const isDoc = type === 'documents';
    const title = isDoc ? item.name : item.title;
    const isLoading = actionLoading === `${type}-${item.id}`;

    const isImage = ext && ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext);
    const isPdf = ext === 'pdf';

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-800 flex flex-col w-full max-w-4xl max-h-[90vh]">

                {/* Header */}
                <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        isDoc ? 'bg-blue-50 dark:bg-blue-500/10' : 'bg-primary-50 dark:bg-secondary-500/10'
                    }`}>
                        {isDoc
                            ? <FileText className="w-4.5 h-4.5 text-blue-600 dark:text-blue-400" />
                            : <BookOpen className="w-4.5 h-4.5 text-primary-600 dark:text-secondary-400" />
                        }
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{title}</p>
                        <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                            <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10 px-2 py-0.5 rounded-md">
                                <User className="w-3 h-3" />{item.owner}
                            </span>
                            {item.department && (
                                <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                                    <Building2 className="w-3 h-3" />{item.department}
                                </span>
                            )}
                            {item.visibility === 'public' ? (
                                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
                                    <Globe className="w-2.5 h-2.5" /> Công khai
                                </span>
                            ) : (
                                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                                    <Lock className="w-2.5 h-2.5" /> Nội bộ
                                </span>
                            )}
                            {isDoc && item.size && (
                                <span className="text-xs text-gray-400">{item.size}</span>
                            )}
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors flex-shrink-0"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-auto min-h-0">
                    {/* Knowledge: render HTML */}
                    {!isDoc && html && (
                        <div
                            className="prose prose-sm dark:prose-invert max-w-none p-6"
                            dangerouslySetInnerHTML={{ __html: html }}
                        />
                    )}
                    {!isDoc && !html && (
                        <div className="flex items-center justify-center h-40 text-sm text-gray-400">
                            Không có nội dung để hiển thị
                        </div>
                    )}

                    {/* Document: embed PDF / image */}
                    {isDoc && blobUrl && isPdf && (
                        <iframe
                            src={blobUrl}
                            className="w-full h-full min-h-[60vh]"
                            title={title}
                        />
                    )}
                    {isDoc && blobUrl && isImage && (
                        <div className="flex items-center justify-center p-6 bg-gray-50 dark:bg-gray-950 min-h-[40vh]">
                            <img src={blobUrl} alt={title} className="max-w-full max-h-[60vh] rounded-lg shadow-md object-contain" />
                        </div>
                    )}

                    {/* Document: Text preview for DOCX/TXT/MD */}
                    {isDoc && text && (
                        <div className="p-6">
                            <div className="bg-gray-50 dark:bg-gray-950 rounded-xl border border-gray-100 dark:border-gray-800 p-6">
                                <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 font-sans leading-relaxed">
                                    {text}
                                </pre>
                            </div>
                        </div>
                    )}

                    {/* Document: not previewable */}
                    {isDoc && !blobUrl && !text && (
                        <div className="flex flex-col items-center justify-center py-16 gap-3 text-center px-6">
                            <div className="w-14 h-14 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                                <FileText className="w-7 h-7 text-gray-400" />
                            </div>
                            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                Không hỗ trợ xem trước loại tệp <span className="uppercase font-bold">.{ext || item.file_type}</span>
                            </p>
                            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-gray-500 dark:text-gray-400 mt-2">
                                <span className="text-right font-medium text-gray-700 dark:text-gray-300">Tên tệp:</span>
                                <span className="text-left">{item.name}</span>
                                <span className="text-right font-medium text-gray-700 dark:text-gray-300">Danh mục:</span>
                                <span className="text-left">{item.category}</span>
                                {item.size && <><span className="text-right font-medium text-gray-700 dark:text-gray-300">Kích thước:</span><span className="text-left">{item.size}</span></>}
                                <span className="text-right font-medium text-gray-700 dark:text-gray-300">Người tải:</span>
                                <span className="text-left">{item.owner}</span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer: knowledge tags */}
                {!isDoc && item.tags?.length > 0 && (
                    <div className="px-5 py-3 border-t border-gray-100 dark:border-gray-800 flex items-center gap-2 flex-wrap flex-shrink-0">
                        <Tag className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                        {item.tags.map(t => (
                            <span key={t} className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">{t}</span>
                        ))}
                    </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-gray-200 dark:border-gray-800 flex-shrink-0">
                    <button
                        onClick={onReject}
                        disabled={isLoading}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm font-medium hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors disabled:opacity-50"
                    >
                        <X className="w-4 h-4" />
                        Từ chối
                    </button>
                    <button
                        onClick={onApprove}
                        disabled={isLoading}
                        className="flex items-center gap-2 px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition-colors disabled:opacity-50"
                    >
                        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                        Phê duyệt
                    </button>
                </div>
            </div>
        </div>
    );
}


// ─── Approval Card ────────────────────────────────────────────

function ApprovalCard({ item, type, actionLoading, previewLoading, processingStatus, onPreview, onApprove, onReject }) {
    const [expanded, setExpanded] = useState(false);
    const isDoc = type === 'documents';
    const isLoading = actionLoading === `${type}-${item.id}`;
    const isPreviewLoading = previewLoading === `${type}-${item.id}`;
    const isProcessing = !!processingStatus;

    // Show pending approval badge
    const isPending = !isProcessing && item.approval_status !== 'approved';

    return (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
            <div className="p-4 flex items-start gap-4">
                {/* Icon */}
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    isDoc ? 'bg-blue-50 dark:bg-blue-500/10' : 'bg-primary-50 dark:bg-secondary-500/10'
                }`}>
                    {isDoc
                        ? <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        : <BookOpen className="w-5 h-5 text-primary-600 dark:text-secondary-400" />
                    }
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                                {isDoc ? item.name : item.title}
                            </p>
                            <div className="flex items-center gap-2 mt-1 flex-wrap">
                                <span className="text-xs text-gray-500 dark:text-gray-400">{item.category}</span>
                                <span className="text-gray-300 dark:text-gray-600">·</span>
                                <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10 px-1.5 py-0.5 rounded-md">
                                    <User className="w-3 h-3" />
                                    {item.owner}
                                </span>
                                {item.department && (
                                    <>
                                        <span className="text-gray-300 dark:text-gray-600">·</span>
                                        <span className="text-xs text-gray-500 dark:text-gray-400">{item.department}</span>
                                    </>
                                )}
                                <span className="text-gray-300 dark:text-gray-600">·</span>
                                <span className="text-xs text-gray-400">
                                    {item.created_at ? new Date(item.created_at).toLocaleString('vi-VN') : '—'}
                                </span>
                            </div>

                            {/* Processing status bar — shown after approval */}
                            {isDoc && isProcessing && (
                                <ProcessingProgressBar
                                    status={processingStatus.status}
                                    chunkCount={processingStatus.chunk_count}
                                    errorMessage={processingStatus.error_message}
                                />
                            )}

                            {/* Pending badge — shown before approval */}
                            {!isProcessing && (
                                <div className="flex items-center gap-2 mt-1.5">
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400">
                                        <Clock className="w-3 h-3" />
                                        Chờ phê duyệt
                                    </span>
                                    {item.visibility === 'public' ? (
                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
                                            <Globe className="w-3 h-3" /> Công khai
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                                            <Lock className="w-3 h-3" /> Nội bộ
                                        </span>
                                    )}
                                    {isDoc && item.size && (
                                        <span className="text-xs text-gray-400">{item.size}</span>
                                    )}
                                </div>
                            )}

                            {/* Short text preview for knowledge */}
                            {!isDoc && item.content_text && (
                                <div className="mt-2">
                                    <p className={`text-xs text-gray-500 dark:text-gray-400 leading-relaxed ${!expanded ? 'line-clamp-2' : ''}`}>
                                        {item.content_text}
                                    </p>
                                    {item.content_text.length > 120 && (
                                        <button
                                            onClick={() => setExpanded(!expanded)}
                                            className="text-xs text-primary-600 dark:text-secondary-400 mt-0.5 flex items-center gap-1"
                                        >
                                            {expanded ? 'Thu gọn' : 'Xem thêm'}
                                            <ChevronDown className={`w-3 h-3 transition-transform ${expanded ? 'rotate-180' : ''}`} />
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Action buttons — hidden when processing */}
                        {!isProcessing && onApprove && (
                            <div className="flex items-center gap-2 flex-shrink-0">
                                <button
                                    onClick={onPreview}
                                    disabled={isPreviewLoading}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 text-xs font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
                                    title="Xem trước"
                                >
                                    {isPreviewLoading
                                        ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                        : <Eye className="w-3.5 h-3.5" />
                                    }
                                    Xem trước
                                </button>
                                <button
                                    onClick={onReject}
                                    disabled={isLoading}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-xs font-medium hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors disabled:opacity-50"
                                >
                                    <X className="w-3.5 h-3.5" />
                                    Từ chối
                                </button>
                                <button
                                    onClick={onApprove}
                                    disabled={isLoading}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium transition-colors disabled:opacity-50"
                                >
                                    {isLoading
                                        ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                        : <Check className="w-3.5 h-3.5" />
                                    }
                                    Phê duyệt
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}


// ─── Processing Progress Bar ─────────────────────────────────────────────

function ProcessingProgressBar({ status, chunkCount, errorMessage }) {
    const stepIdx = getStepIndex(status);
    const isDone = status === 'indexed';
    const isFailed = status === 'failed';

    return (
        <div className="mt-2 flex items-center gap-3">
            {/* Step dots */}
            <div className="flex items-center gap-1">
                {PROCESSING_STEPS.filter(s => s.key !== 'pending').map((step, i) => {
                    const sIdx = i + 1; // offset from 'pending'
                    const isActive = sIdx === stepIdx;
                    const isPast = sIdx < stepIdx || isDone;
                    const StepIcon = step.icon;
                    return (
                        <div key={step.key} className="flex items-center gap-1">
                            <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                                isDone
                                    ? 'bg-emerald-500'
                                    : isFailed && isActive
                                    ? 'bg-red-500'
                                    : isPast || isActive
                                    ? 'bg-primary-500'
                                    : 'bg-gray-200 dark:bg-gray-700'
                            }`}>
                                <StepIcon className={`w-3 h-3 ${
                                    isDone ? 'text-white' : isFailed && isActive ? 'text-white' : isPast || isActive ? 'text-white' : 'text-gray-400'
                                } ${isActive && !isFailed ? 'animate-spin' : ''}`} />
                            </div>
                            {i < PROCESSING_STEPS.length - 2 && (
                                <div className={`w-4 h-0.5 ${isPast || isDone ? 'bg-primary-400' : 'bg-gray-200 dark:bg-gray-700'}`} />
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Label */}
            <div className="flex items-center gap-1.5">
                {isDone ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                ) : isFailed ? (
                    <AlertCircle className="w-3.5 h-3.5 text-red-500" />
                ) : (
                    <Loader2 className="w-3.5 h-3.5 text-primary-500 animate-spin" />
                )}
                <span className={`text-xs font-medium ${
                    isDone ? 'text-emerald-600 dark:text-emerald-400'
                    : isFailed ? 'text-red-600 dark:text-red-400'
                    : 'text-primary-600 dark:text-primary-400'
                }`}>
                    {isDone
                        ? `Hoàn tất · ${chunkCount} chunks`
                        : isFailed
                        ? `Lỗi: ${errorMessage || 'Xử lý thất bại'}`
                        : `${PROCESSING_STEPS[stepIdx]?.label || 'Đang xử lý'}${chunkCount > 0 ? ` · ${chunkCount} chunks` : ''}`
                    }
                </span>
            </div>
        </div>
    );
}
