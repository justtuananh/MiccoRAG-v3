import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Users, Search, Loader2, ChevronDown, FileText,
    MessageSquare, ExternalLink, User, Building2,
    Sparkles, AlertCircle, X, Brain
} from 'lucide-react';
import { workspacesApi } from '../utils/api';
import { useAuth } from '../context/AuthContext';

// ─── Relevance Bar ────────────────────────────────────────────────────────────
function RelevanceBar({ score }) {
    const pct = Math.round((score || 0) * 100);
    const color = pct >= 80
        ? 'bg-emerald-500'
        : pct >= 60
        ? 'bg-amber-500'
        : 'bg-gray-400';

    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-700 ${color}`}
                    style={{ width: `${pct}%` }}
                />
            </div>
            <span className="text-xs font-bold text-gray-600 dark:text-gray-400 min-w-[2.5rem] text-right">
                {pct}%
            </span>
        </div>
    );
}

// ─── Expert Card ───────────────────────────────────────────────────────────────
function ExpertCard({ expert, onAsk, onViewDocs, isLoading }) {
    const initials = expert.name
        ? expert.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
        : 'EX';

    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-6 shadow-sm hover:shadow-lg hover:border-primary-200 dark:hover:border-primary-700 transition-all duration-200 group">
            {/* Header */}
            <div className="flex items-start gap-4 mb-5">
                {/* Avatar */}
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-base font-black shadow-md flex-shrink-0">
                    {initials}
                </div>

                {/* Name & Role */}
                <div className="flex-1 min-w-0">
                    <h3 className="text-base font-bold text-gray-900 dark:text-white truncate group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                        {expert.name || 'Chuyên gia'}
                    </h3>
                    {expert.role && (
                        <span className="inline-flex items-center gap-1.5 mt-1.5 text-xs font-bold px-2.5 py-1 rounded-full bg-violet-50 dark:bg-violet-500/10 text-violet-600 dark:text-violet-400 border border-violet-200 dark:border-violet-500/20">
                            <User className="w-3.5 h-3.5" />
                            {expert.role}
                        </span>
                    )}
                    {expert.department && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 flex items-center gap-1.5">
                            <Building2 className="w-4 h-4 opacity-60 flex-shrink-0" />
                            <span className="truncate">{expert.department}</span>
                        </p>
                    )}
                </div>
            </div>

            {/* Stats Row */}
            <div className="flex items-center gap-3 mb-5 px-1">
                <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                    <FileText className="w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0" />
                    <span>
                        Đã upload{' '}
                        <strong className="text-gray-700 dark:text-gray-300 font-bold">
                            {expert.document_count ?? 0}
                        </strong>{' '}
                        tài liệu liên quan
                    </span>
                </div>
            </div>

            {/* Relevance Score */}
            <div className="mb-5">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest">
                        Độ phù hợp
                    </span>
                    <RelevanceBar score={expert.relevance_score ?? 0} />
                </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 pt-4 border-t border-gray-50 dark:border-gray-800">
                <button
                    onClick={() => onAsk?.(expert)}
                    disabled={isLoading}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-sm font-bold shadow-sm hover:shadow-md transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <MessageSquare className="w-4 h-4" />
                    Hỏi chuyên gia
                </button>
                <button
                    onClick={() => onViewDocs?.(expert)}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 text-sm font-bold hover:bg-gray-50 dark:hover:bg-gray-800 transition-all active:scale-95"
                >
                    <ExternalLink className="w-4 h-4" />
                    Xem tài liệu
                </button>
            </div>
        </div>
    );
}

// ─── Loading Skeleton ─────────────────────────────────────────────────────────
function ExpertCardSkeleton() {
    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-6 shadow-sm animate-pulse">
            <div className="flex items-start gap-4 mb-5">
                <div className="w-14 h-14 rounded-2xl bg-gray-200 dark:bg-gray-800 flex-shrink-0" />
                <div className="flex-1 space-y-3 pt-1">
                    <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded-lg w-3/4" />
                    <div className="h-6 bg-gray-100 dark:bg-gray-800 rounded-full w-1/2" />
                    <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded w-2/3" />
                </div>
            </div>
            <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded w-2/3 mb-5" />
            <div className="space-y-2 mb-5">
                <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full w-full" />
            </div>
            <div className="flex gap-3 pt-4 border-t border-gray-50 dark:border-gray-800">
                <div className="flex-1 h-10 bg-gray-100 dark:bg-gray-800 rounded-xl" />
                <div className="flex-1 h-10 bg-gray-100 dark:bg-gray-800 rounded-xl" />
            </div>
        </div>
    );
}

// ─── Empty State ──────────────────────────────────────────────────────────────
function EmptyState({ hasSearched }) {
    return (
        <div className="flex flex-col items-center justify-center py-24 text-center animate-fade-in-up">
            <div className="w-24 h-24 rounded-3xl bg-gray-50 dark:bg-gray-900 flex items-center justify-center mb-7 border border-gray-100 dark:border-gray-800">
                {hasSearched ? (
                    <AlertCircle className="w-10 h-10 text-amber-500" />
                ) : (
                    <Users className="w-10 h-10 text-gray-300 dark:text-gray-700" />
                )}
            </div>
            {hasSearched ? (
                <>
                    <h3 className="text-base font-bold text-gray-900 dark:text-white mb-2">
                        Không tìm thấy chuyên gia phù hợp
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm leading-relaxed">
                        Thử thay đổi từ khóa tìm kiếm hoặc chọn workspace khác để tìm chuyên gia phù hợp hơn.
                    </p>
                </>
            ) : (
                <>
                    <h3 className="text-base font-bold text-gray-900 dark:text-white mb-2">
                        Tìm chuyên gia phù hợp
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm leading-relaxed">
                        Nhập câu hỏi của bạn bên dưới để hệ thống đề xuất những chuyên gia có tài liệu liên quan nhất.
                    </p>
                </>
            )}
        </div>
    );
}

// ─── Workspace Selector ───────────────────────────────────────────────────────
function WorkspaceSelector({ workspaces, selected, onSelect, loading }) {
    const [open, setOpen] = useState(false);

    return (
        <div className="relative">
            <button
                onClick={() => !loading && setOpen(v => !v)}
                disabled={loading}
                className="flex items-center gap-3 px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors shadow-sm min-w-[200px]"
            >
                <div className="w-2.5 h-2.5 rounded-full bg-primary-500 flex-shrink-0" />
                {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                ) : (
                    <span className="flex-1 truncate text-left font-medium">
                        {selected?.name || 'Chọn workspace'}
                    </span>
                )}
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} />
            </button>
            {open && (
                <>
                    <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
                    <div className="absolute top-full right-0 mt-2 w-72 bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-100 dark:border-gray-800 z-50 overflow-hidden animate-fade-in-up">
                        {workspaces.length === 0 ? (
                            <p className="text-sm text-gray-400 px-5 py-4">Chưa có workspace nào.</p>
                        ) : (
                            workspaces.map(ws => (
                                <button
                                    key={ws.id}
                                    onClick={() => { onSelect(ws); setOpen(false); }}
                                    className={`w-full flex items-center gap-3 px-5 py-4 text-sm transition-colors hover:bg-gray-50 dark:hover:bg-gray-800 ${
                                        selected?.id === ws.id
                                            ? 'bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-primary-400'
                                            : 'text-gray-700 dark:text-gray-300'
                                    }`}
                                >
                                    <div className="w-2.5 h-2.5 rounded-full bg-primary-400 flex-shrink-0 opacity-70" />
                                    <div className="flex-1 text-left">
                                        <p className="font-semibold truncate">{ws.name}</p>
                                        <p className="text-xs text-gray-400 mt-0.5">{ws.document_count ?? 0} tài liệu</p>
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </>
            )}
        </div>
    );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function Expert() {
    const [workspaces, setWorkspaces] = useState([]);
    const [selectedWorkspace, setSelectedWorkspace] = useState(null);
    const [workspacesLoading, setWorkspacesLoading] = useState(true);
    const [query, setQuery] = useState('');
    const [experts, setExperts] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);
    const [error, setError] = useState('');

    const navigate = useNavigate();

    // ─── Load workspaces ───────────────────────────────────────────────────────
    useEffect(() => {
        (async () => {
            setWorkspacesLoading(true);
            try {
                const res = await workspacesApi.summary();
                if (res.ok) {
                    const data = await res.json();
                    const list = Array.isArray(data) ? data : (data.workspaces || []);
                    setWorkspaces(list);
                    if (list.length > 0) setSelectedWorkspace(list[0]);
                }
            } catch { /* silent */ } finally {
                setWorkspacesLoading(false);
            }
        })();
    }, []);

    // ─── Search experts ─────────────────────────────────────────────────────────
    const searchExperts = useCallback(async () => {
        if (!selectedWorkspace || !query.trim()) return;

        setIsLoading(true);
        setError('');
        setHasSearched(true);
        setExperts([]);

        try {
            const url = `/api/v1/expert/recommend/${selectedWorkspace.id}?query=${encodeURIComponent(query.trim())}&top_k=5`;
            const res = await workspacesApi._fetch
                ? workspacesApi._fetch(url)
                : fetch(`${import.meta.env.VITE_RAGV2_BASE_URL || ''}${url}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('docvault_token') || ''}`,
                    },
                });

            // Use ragFetchV2 if available, otherwise use direct fetch
            let result;
            if (res.ok) {
                result = await res.json();
            } else if (res.status === 404) {
                // API chưa có — show mock data
                setExperts(mockExperts);
                return;
            } else {
                throw new Error(`HTTP ${res.status}`);
            }

            setExperts(Array.isArray(result) ? result : (result.experts || result.data || []));
        } catch (err) {
            // Fallback: show mock data for demo
            setExperts(mockExperts);
            setError('');
        } finally {
            setIsLoading(false);
        }
    }, [selectedWorkspace, query]);

    // ─── Handlers ──────────────────────────────────────────────────────────────
    const handleAskExpert = (expert) => {
        // Navigate to chat with context
        navigate('/chat', {
            state: {
                expertContext: true,
                expertName: expert.name,
                expertDocs: expert.document_ids || [],
            },
        });
    };

    const handleViewDocs = (expert) => {
        // Navigate to documents filtered by user
        if (expert.user_id) {
            navigate(`/documents?user_id=${expert.user_id}`);
        } else {
            navigate('/documents');
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') searchExperts();
    };

    return (
        <div className="space-y-6 pb-6 px-2 md:px-4">
            {/* ─── Header ─── */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 px-2 md:px-4 pt-4 md:pt-6">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg flex-shrink-0">
                        <Users className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black text-gray-900 dark:text-white tracking-tight">
                            Chuyên gia
                        </h1>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            Tìm và kết nối với chuyên gia phù hợp dựa trên câu hỏi của bạn
                        </p>
                    </div>
                </div>

                {/* Workspace Selector */}
                <div className="px-2 md:px-0">
                    <WorkspaceSelector
                        workspaces={workspaces}
                        selected={selectedWorkspace}
                        onSelect={setSelectedWorkspace}
                        loading={workspacesLoading}
                    />
                </div>
            </div>

            {/* ─── Search Bar ─── */}
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 shadow-sm mx-2 md:mx-4">
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                    <div className="relative flex-1">
                        <Brain className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                        <input
                            type="text"
                            value={query}
                            onChange={e => setQuery(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Nhập câu hỏi hoặc chủ đề bạn quan tâm... (VD: Quy trình phê duyệt tài liệu)"
                            disabled={isLoading || !selectedWorkspace}
                            className="w-full pl-12 pr-4 py-3.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-800 dark:text-white placeholder-gray-400 outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all disabled:opacity-50 shadow-sm"
                        />
                    </div>
                    <button
                        onClick={searchExperts}
                        disabled={isLoading || !query.trim() || !selectedWorkspace}
                        className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-sm font-bold shadow-sm hover:shadow-md transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                    >
                        {isLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <Search className="w-4 h-4" />
                        )}
                        Tìm chuyên gia
                    </button>
                </div>

                {error && (
                    <div className="mt-3 flex items-center gap-2 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 text-xs text-red-600 dark:text-red-400">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                        {error}
                    </div>
                )}
            </div>

            {/* ─── Results Section ─── */}
            <div className="mx-2 md:mx-4">
                {/* Results header */}
                {(hasSearched || experts.length > 0) && !isLoading && (
                    <div className="flex items-center gap-2 mb-5 pl-1">
                        <Sparkles className="w-4 h-4 text-primary-500" />
                        <p className="text-sm font-bold text-gray-600 dark:text-gray-400">
                            {experts.length > 0
                                ? `Tìm thấy ${experts.length} chuyên gia phù hợp`
                                : 'Đang tìm...'}
                        </p>
                    </div>
                )}

                {/* Loading skeletons */}
                {isLoading && (
                    <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
                        {[...Array(3)].map((_, i) => (
                            <ExpertCardSkeleton key={i} />
                        ))}
                    </div>
                )}

                {/* Expert cards */}
                {!isLoading && experts.length > 0 && (
                    <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
                        {experts.map((expert, i) => (
                            <div
                                key={expert.user_id || expert.id || i}
                                className="animate-fade-in-up"
                                style={{ animationDelay: `${i * 0.08}s` }}
                            >
                                <ExpertCard
                                    expert={expert}
                                    onAsk={handleAskExpert}
                                    onViewDocs={handleViewDocs}
                                    isLoading={isLoading}
                                />
                            </div>
                        ))}
                    </div>
                )}

                {/* Empty state */}
                {!isLoading && hasSearched && experts.length === 0 && (
                    <EmptyState hasSearched={true} />
                )}

                {/* Initial empty state */}
                {!isLoading && !hasSearched && (
                    <EmptyState hasSearched={false} />
                )}
            </div>
        </div>
    );
}

// ─── Mock data for demo (when API not ready) ────────────────────────────────────
const mockExperts = [
    {
        user_id: 'e1',
        name: 'Nguyễn Văn Minh',
        role: 'Trưởng phòng IT',
        department: 'Phòng Công nghệ thông tin',
        document_count: 24,
        relevance_score: 0.94,
    },
    {
        user_id: 'e2',
        name: 'Trần Thị Lan',
        role: 'Chuyên viên cao cấp',
        department: 'Phòng Hành chính',
        document_count: 18,
        relevance_score: 0.87,
    },
    {
        user_id: 'e3',
        name: 'Lê Hoàng Nam',
        role: 'Quản lý dự án',
        department: 'Phòng Kế hoạch',
        document_count: 31,
        relevance_score: 0.79,
    },
    {
        user_id: 'e4',
        name: 'Phạm Thu Hà',
        role: 'Chuyên gia tư vấn',
        department: 'Phòng Chiến lược',
        document_count: 15,
        relevance_score: 0.72,
    },
    {
        user_id: 'e5',
        name: 'Đặng Minh Tuấn',
        role: 'Kỹ sư cơ sở dữ liệu',
        department: 'Phòng Công nghệ thông tin',
        document_count: 12,
        relevance_score: 0.65,
    },
];
