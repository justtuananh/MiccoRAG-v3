import { useState, useEffect, useRef, useCallback } from 'react';
import {
    Clock, FileSearch, Loader2, CheckCircle2, XCircle, AlertCircle,
    RefreshCw, File, ChevronDown, X, Wifi, WifiOff
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Breadcrumb from '../components/shared/Breadcrumb';

// Trạng thái processing theo thứ tự
const PROCESSING_STEPS = [
    { key: 'pending',    label: 'Chờ xử lý',    icon: Clock },
    { key: 'parsing',    label: 'Đang phân tích', icon: FileSearch },
    { key: 'processing', label: 'Đang xử lý',    icon: Loader2 },
    { key: 'indexing',   label: 'Đang lập chỉ mục', icon: Loader2 },
    { key: 'indexed',    label: 'Hoàn tất',      icon: CheckCircle2 },
    { key: 'failed',     label: 'Thất bại',       icon: AlertCircle },
];

const getStepIndex = (status) => {
    const idx = PROCESSING_STEPS.findIndex(s => s.key === (status?.toLowerCase?.() || status));
    return idx === -1 ? 0 : idx;
};

function ProcessingProgressBar({ status, chunkCount, errorMessage }) {
    const stepIdx = getStepIndex(status);
    const isDone = status === 'indexed';
    const isFailed = status === 'failed';

    return (
        <div className="flex items-center gap-3">
            {/* Step dots */}
            <div className="flex items-center gap-1">
                {PROCESSING_STEPS.filter(s => s.key !== 'pending').map((step, i) => {
                    const sIdx = i + 1;
                    const isActive = sIdx === stepIdx;
                    const isPast = sIdx < stepIdx || isDone;
                    const StepIcon = step.icon;
                    return (
                        <div key={step.key} className="flex items-center gap-1">
                            <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                                isDone
                                    ? 'bg-emerald-500'
                                    : isFailed && isActive
                                    ? 'bg-red-500'
                                    : isPast || isActive
                                    ? 'bg-primary-500'
                                    : 'bg-gray-200 dark:bg-gray-700'
                            }`}>
                                <StepIcon className={`w-3 h-3 ${
                                    isDone ? 'text-white'
                                        : isFailed && isActive ? 'text-white'
                                        : isPast || isActive ? 'text-white'
                                        : 'text-gray-400'
                                } ${isActive && !isFailed ? 'animate-spin' : ''}`} />
                            </div>
                            {i < PROCESSING_STEPS.filter(s => s.key !== 'pending').length - 1 && (
                                <div className={`w-5 h-0.5 ${isPast || isDone ? 'bg-primary-400' : 'bg-gray-200 dark:bg-gray-700'}`} />
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Label */}
            <div className="flex items-center gap-1.5">
                {isDone ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                ) : isFailed ? (
                    <XCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                ) : (
                    <Loader2 className="w-3.5 h-3.5 text-primary-500 animate-spin flex-shrink-0" />
                )}
                <span className={`text-xs font-medium whitespace-nowrap ${
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

function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function timeAgo(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return `${diffSec}s trước`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin} phút trước`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h trước`;
    const diffDay = Math.floor(diffHr / 24);
    return `${diffDay} ngày trước`;
}

export default function ProcessingStatus() {
    const { authFetch } = useAuth();
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [isOnline, setIsOnline] = useState(navigator.onLine);
    const pollingRef = useRef(null);

    const fetchDocs = useCallback(async () => {
        try {
            const res = await authFetch('/api/documents/processing-status');
            if (res.ok) {
                const data = await res.json();
                setDocs(data.items || []);
            }
        } catch (_) {}
    }, [authFetch]);

    const handleRefresh = async () => {
        setRefreshing(true);
        await fetchDocs();
        setRefreshing(false);
    };

    // Initial load
    useEffect(() => {
        setLoading(true);
        fetchDocs().finally(() => setLoading(false));
    }, [fetchDocs]);

    // Polling: 5s when docs are processing, 30s when all done
    useEffect(() => {
        const hasActive = docs.some(d => !['indexed', 'failed'].includes(d.status));
        const interval = hasActive ? 5000 : 30000;

        pollingRef.current = setInterval(() => {
            fetchDocs();
        }, interval);

        return () => clearInterval(pollingRef.current);
    }, [docs, fetchDocs]);

    // Network status
    useEffect(() => {
        const onOnline = () => setIsOnline(true);
        const onOffline = () => setIsOnline(false);
        window.addEventListener('online', onOnline);
        window.addEventListener('offline', onOffline);
        return () => {
            window.removeEventListener('online', onOnline);
            window.removeEventListener('offline', onOffline);
        };
    }, []);

    // Live indicator: pulsing dot
    const hasActive = docs.some(d => !['indexed', 'failed'].includes(d.status));

    // Stats
    const total = docs.length;
    const done = docs.filter(d => d.status === 'indexed').length;
    const failed = docs.filter(d => d.status === 'failed').length;
    const processing = total - done - failed;

    return (
        <div className="space-y-6 px-2 md:px-4">
            <div className="px-2 pt-4">
                <Breadcrumb items={[
                    { label: 'Tổng quan', href: '/dashboard' },
                    { label: 'Tiến trình xử lý' },
                ]} />
            </div>

            {/* ── Header ── */}
            <div className="flex items-center justify-between px-2">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        Tiến trình xử lý
                    </h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        Theo dõi trạng thái xử lý tài liệu trong phòng ban của bạn
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    {/* Live status */}
                    <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border ${
                        hasActive
                            ? 'bg-green-50 border-green-200 text-green-700 dark:bg-green-500/10 dark:border-green-500/30 dark:text-green-400'
                            : 'bg-gray-50 border-gray-200 text-gray-500 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400'
                    }`}>
                        <span className={`w-2 h-2 rounded-full ${hasActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                        {hasActive ? 'Đang xử lý' : 'Đã hoàn tất'}
                    </div>

                    {/* Online status */}
                    {!isOnline && (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-red-50 border border-red-200 text-red-600 dark:bg-red-500/10 dark:border-red-500/30 dark:text-red-400">
                            <WifiOff className="w-3 h-3" />
                            Offline
                        </div>
                    )}

                    {/* Refresh */}
                    <button
                        onClick={handleRefresh}
                        disabled={refreshing}
                        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                        Làm mới
                    </button>
                </div>
            </div>

            {/* ── Stats ── */}
            <div className="grid grid-cols-3 gap-5 px-2">
                <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5 flex items-center gap-4 shadow-sm">
                    <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                        <Clock className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                        <p className="text-2xl font-black text-gray-900 dark:text-white">{processing}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Đang xử lý</p>
                    </div>
                </div>
                <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5 flex items-center gap-4 shadow-sm">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                        <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div>
                        <p className="text-2xl font-black text-gray-900 dark:text-white">{done}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Hoàn tất</p>
                    </div>
                </div>
                <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5 flex items-center gap-4 shadow-sm">
                    <div className="w-12 h-12 rounded-2xl bg-red-100 dark:bg-red-500/20 flex items-center justify-center flex-shrink-0">
                        <XCircle className="w-6 h-6 text-red-600" />
                    </div>
                    <div>
                        <p className="text-2xl font-black text-gray-900 dark:text-white">{failed}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Thất bại</p>
                    </div>
                </div>
            </div>

            {/* ── Document List ── */}
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden mx-2 shadow-sm">
                <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
                    <h3 className="text-sm font-bold text-gray-700 dark:text-gray-300">
                        Tài liệu đang xử lý
                    </h3>
                    <span className="text-xs text-gray-400">{total} tài liệu</span>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-16">
                        <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
                    </div>
                ) : docs.length === 0 ? (
                    <div className="py-16 text-center">
                        <div className="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-4">
                            <CheckCircle2 className="w-8 h-8 text-gray-300 dark:text-gray-600" />
                        </div>
                        <p className="text-base font-semibold text-gray-500 dark:text-gray-400">
                            Không có tài liệu nào đang xử lý
                        </p>
                        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                            Tất cả tài liệu đã được xử lý hoặc chưa có tài liệu nào
                        </p>
                    </div>
                ) : (
                    <div className="divide-y divide-gray-50 dark:divide-gray-800">
                        {docs.map((doc) => (
                            <div key={doc.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                <div className="flex items-center justify-between gap-4">
                                    {/* File info */}
                                    <div className="flex items-center gap-3 flex-1 min-w-0">
                                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                                            doc.status === 'failed'
                                                ? 'bg-red-100 dark:bg-red-500/20'
                                                : doc.status === 'indexed'
                                                ? 'bg-emerald-100 dark:bg-emerald-500/20'
                                                : 'bg-primary-100 dark:bg-primary-500/20'
                                        }`}>
                                            <File className={`w-5 h-5 ${
                                                doc.status === 'failed'
                                                    ? 'text-red-500'
                                                    : doc.status === 'indexed'
                                                    ? 'text-emerald-500'
                                                    : 'text-primary-500'
                                            }`} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                                                {doc.name}
                                            </p>
                                            <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                                                <span className="text-xs text-gray-400">
                                                    {doc.uploader_name}
                                                </span>
                                                {doc.department_name && (
                                                    <>
                                                        <span className="text-gray-300 dark:text-gray-600 text-xs">·</span>
                                                        <span className="text-xs text-gray-400">{doc.department_name}</span>
                                                    </>
                                                )}
                                                <span className="text-gray-300 dark:text-gray-600 text-xs">·</span>
                                                <span className="text-xs text-gray-400">
                                                    {doc.file_type?.toUpperCase()} · {formatBytes(doc.file_size)}
                                                </span>
                                                <span className="text-gray-300 dark:text-gray-600 text-xs">·</span>
                                                <span className="text-xs text-gray-400">
                                                    {timeAgo(doc.created_at)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Progress bar */}
                                    <div className="flex-shrink-0 w-80">
                                        <ProcessingProgressBar
                                            status={doc.status}
                                            chunkCount={doc.chunk_count}
                                            errorMessage={doc.error_message}
                                        />
                                    </div>
                                </div>

                                {/* Error detail */}
                                {doc.status === 'failed' && doc.error_message && (
                                    <div className="mt-2 ml-13 flex items-start gap-2 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20">
                                        <AlertCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0 mt-0.5" />
                                        <p className="text-xs text-red-600 dark:text-red-400">{doc.error_message}</p>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
