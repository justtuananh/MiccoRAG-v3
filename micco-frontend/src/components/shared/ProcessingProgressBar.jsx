import { Clock, FileSearch, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

// Trạng thái processing theo thứ tự — đồng bộ với Approvals.jsx
export const PROCESSING_STEPS = [
    { key: 'pending',    label: 'Chờ xử lý',       icon: Clock },
    { key: 'parsing',    label: 'Đang phân tích',   icon: FileSearch },
    { key: 'processing', label: 'Đang xử lý',       icon: Loader2 },
    { key: 'indexing',   label: 'Đang lập chỉ mục', icon: Loader2 },
    { key: 'indexed',    label: 'Hoàn tất',          icon: CheckCircle2 },
    { key: 'failed',     label: 'Thất bại',          icon: AlertCircle },
];

export function getStepIndex(status) {
    const idx = PROCESSING_STEPS.findIndex(
        (s) => s.key === (status?.toLowerCase?.() || status)
    );
    return idx === -1 ? 0 : idx;
}

/**
 * ProcessingProgressBar — hiển thị tiến trình xử lý tài liệu sau khi được duyệt.
 * Dùng cho cả trang admin (Approvals) và trang user (Documents, DocumentView).
 *
 * Props:
 *   status       — string: 'pending' | 'parsing' | 'processing' | 'indexing' | 'indexed' | 'failed'
 *   chunkCount   — number (optional)
 *   errorMessage — string (optional)
 *   compact      — boolean: nếu true thì render nhỏ gọn hơn (dùng trong danh sách)
 */
export default function ProcessingProgressBar({ status, chunkCount, errorMessage, compact = false }) {
    const stepIdx = getStepIndex(status);
    const isDone = status === 'indexed';
    const isFailed = status === 'failed';

    return (
        <div className={`flex items-center gap-3 ${compact ? 'mt-1' : 'mt-2'}`}>
            {/* Step dots */}
            <div className="flex items-center gap-1">
                {PROCESSING_STEPS.filter((s) => s.key !== 'pending').map((step, i) => {
                    const sIdx = i + 1; // offset from 'pending'
                    const isActive = sIdx === stepIdx;
                    const isPast = sIdx < stepIdx || isDone;
                    const StepIcon = step.icon;
                    return (
                        <div key={step.key} className="flex items-center gap-1">
                            <div
                                className={`${compact ? 'w-4 h-4' : 'w-5 h-5'} rounded-full flex items-center justify-center ${
                                    isDone
                                        ? 'bg-emerald-500'
                                        : isFailed && isActive
                                        ? 'bg-red-500'
                                        : isPast || isActive
                                        ? 'bg-primary-500'
                                        : 'bg-gray-200 dark:bg-gray-700'
                                }`}
                            >
                                <StepIcon
                                    className={`${compact ? 'w-2.5 h-2.5' : 'w-3 h-3'} ${
                                        isDone
                                            ? 'text-white'
                                            : isFailed && isActive
                                            ? 'text-white'
                                            : isPast || isActive
                                            ? 'text-white'
                                            : 'text-gray-400'
                                    } ${isActive && !isFailed ? 'animate-spin' : ''}`}
                                />
                            </div>
                            {i < PROCESSING_STEPS.length - 2 && (
                                <div
                                    className={`${compact ? 'w-3' : 'w-4'} h-0.5 ${
                                        isPast || isDone
                                            ? 'bg-primary-400'
                                            : 'bg-gray-200 dark:bg-gray-700'
                                    }`}
                                />
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Label */}
            <div className="flex items-center gap-1.5">
                {isDone ? (
                    <CheckCircle2 className={`${compact ? 'w-3 h-3' : 'w-3.5 h-3.5'} text-emerald-500`} />
                ) : isFailed ? (
                    <AlertCircle className={`${compact ? 'w-3 h-3' : 'w-3.5 h-3.5'} text-red-500`} />
                ) : (
                    <Loader2 className={`${compact ? 'w-3 h-3' : 'w-3.5 h-3.5'} text-primary-500 animate-spin`} />
                )}
                <span
                    className={`${compact ? 'text-[10px]' : 'text-xs'} font-medium ${
                        isDone
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : isFailed
                            ? 'text-red-600 dark:text-red-400'
                            : 'text-primary-600 dark:text-primary-400'
                    }`}
                >
                    {isDone
                        ? `Hoàn tất${chunkCount ? ` · ${chunkCount} chunks` : ''}`
                        : isFailed
                        ? `Lỗi: ${errorMessage || 'Xử lý thất bại'}`
                        : `${PROCESSING_STEPS[stepIdx]?.label || 'Đang xử lý'}${
                              chunkCount > 0 ? ` · ${chunkCount} chunks` : ''
                          }`}
                </span>
            </div>
        </div>
    );
}
