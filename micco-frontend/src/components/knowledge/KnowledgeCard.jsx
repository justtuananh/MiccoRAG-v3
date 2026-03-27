import { BookOpen, Edit, Trash2, Tag, User, Clock, CheckCircle, AlertCircle, Loader2, Lock, Globe, XCircle } from 'lucide-react';

const statusConfig = {
    'Hoạt động': { label: 'Hoạt động', color: 'bg-green-50 text-green-700 dark:bg-green-500/10 dark:text-green-400' },
    'Bản nháp': { label: 'Bản nháp', color: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-500/10 dark:text-yellow-400' },
    'Lưu trữ': { label: 'Lưu trữ', color: 'bg-gray-100 text-gray-600 dark:bg-gray-500/10 dark:text-gray-400' },
};

const ingestConfig = {
    completed: { icon: CheckCircle, color: 'text-green-500', label: 'Đã đồng bộ' },
    processing: { icon: Loader2, color: 'text-blue-500 animate-spin', label: 'Đang xử lý' },
    pending: { icon: Clock, color: 'text-yellow-500', label: 'Chờ xử lý' },
    failed: { icon: AlertCircle, color: 'text-red-500', label: 'Lỗi' },
};

export default function KnowledgeCard({ entry, onEdit, onDelete, onView }) {
    const st = statusConfig[entry.status] || statusConfig['Hoạt động'];
    const ing = ingestConfig[entry.ingest_status] || ingestConfig.pending;
    const IngestIcon = ing.icon;

    const previewText = entry.content_text?.substring(0, 180) || '';

    return (
        <div
            className="group bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 hover:border-primary-300 dark:hover:border-secondary-500/50 hover:shadow-lg transition-all duration-200 cursor-pointer"
            onClick={() => onView?.(entry)}
        >
            <div className="p-5">
                {/* Header */}
                <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                        <div className="w-10 h-10 rounded-lg bg-primary-50 dark:bg-secondary-500/10 flex items-center justify-center flex-shrink-0">
                            <BookOpen className="w-5 h-5 text-primary-600 dark:text-secondary-400" />
                        </div>
                        <div className="min-w-0">
                            <h3
                                className="text-sm font-semibold text-gray-900 dark:text-white truncate transition-colors group-hover:text-primary-600 dark:group-hover:text-secondary-400"
                            >
                                {entry.title}
                            </h3>
                            <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 dark:text-gray-400">
                                <span className="flex items-center gap-1">
                                    <User className="w-3 h-3" />
                                    {entry.owner}
                                </span>
                                <span>·</span>
                                <span>{entry.category}</span>
                            </div>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                            onClick={(e) => { e.stopPropagation(); onEdit?.(entry); }}
                            className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-primary-600 dark:hover:text-secondary-400 transition-colors"
                            title="Chỉnh sửa"
                        >
                            <Edit className="w-4 h-4" />
                        </button>
                        <button
                            onClick={(e) => { e.stopPropagation(); onDelete?.(entry); }}
                            className="p-1.5 rounded-md hover:bg-red-50 dark:hover:bg-red-500/10 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                            title="Xóa"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Preview */}
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3 mb-3 leading-relaxed">
                    {previewText}{previewText.length >= 180 ? '...' : ''}
                </p>

                {/* Footer */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 flex-wrap">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${st.color}`}>
                            {st.label}
                        </span>
                        {entry.visibility === 'public' ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
                                <Globe className="w-2.5 h-2.5" />
                                Công khai
                            </span>
                        ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                                <Lock className="w-2.5 h-2.5" />
                                Nội bộ
                            </span>
                        )}
                        {entry.approval_status === 'pending_approval' && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400">
                                <Clock className="w-2.5 h-2.5" /> Chờ duyệt
                            </span>
                        )}
                        {entry.approval_status === 'rejected' && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400">
                                <XCircle className="w-2.5 h-2.5" /> Từ chối
                            </span>
                        )}
                        {entry.tags?.slice(0, 2).map((tag) => (
                            <span
                                key={tag}
                                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                            >
                                <Tag className="w-2.5 h-2.5" />
                                {tag}
                            </span>
                        ))}
                        {entry.tags?.length > 2 && (
                            <span className="text-xs text-gray-400">+{entry.tags.length - 2}</span>
                        )}
                    </div>
                    <div className="flex items-center gap-1 text-xs" title={ing.label}>
                        <IngestIcon className={`w-3.5 h-3.5 ${ing.color}`} />
                        <span className="text-gray-400 hidden sm:inline">{ing.label}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
