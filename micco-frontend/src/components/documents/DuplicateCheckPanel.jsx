import { Link } from 'react-router-dom';

export default function DuplicateCheckPanel({ result }) {
    const exact = result?.checked && result.match_type === 'exact';
    const similar = result?.checked && result.match_type === 'similar';
    const percent = typeof result?.similarity === 'number'
        ? Math.round(result.similarity * 100) : null;

    return (
        <section aria-label="Kiểm tra nội dung trùng" className="p-4 md:p-6 border-b border-slate-200 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-2">Kiểm tra nội dung trùng</h3>
            {!result?.checked ? (
                <p className="text-xs text-slate-600 dark:text-slate-300">Chưa có kết quả kiểm tra phần chữ của tài liệu này.</p>
            ) : exact ? (
                <p className="text-xs text-red-700 dark:text-red-300">Nội dung phần chữ trùng với tài liệu khác trong kho này. Tài liệu này không được lập chỉ mục.</p>
            ) : similar ? (
                <p className="text-xs text-amber-700 dark:text-amber-300">Nội dung phần chữ gần giống tài liệu khác trong kho này{percent !== null ? ` (${percent}%)` : ''}. Hãy kiểm tra thủ công; hệ thống không tự gộp tài liệu.</p>
            ) : (
                <p className="text-xs text-slate-600 dark:text-slate-300">Không phát hiện trùng phần chữ trong kho này.</p>
            )}
            {(exact || similar) && result.match && (
                <Link to={`/documents/${result.match.id}`} className="mt-2 inline-block text-xs font-semibold text-primary-600 dark:text-primary-400 hover:underline">
                    Xem tài liệu liên quan: {result.match.name}
                </Link>
            )}
            {(exact || similar) && !result.match && (
                <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Bạn không có quyền xem tài liệu liên quan.</p>
            )}
        </section>
    );
}
