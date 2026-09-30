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
