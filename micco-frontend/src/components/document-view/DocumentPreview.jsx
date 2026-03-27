// src/components/document-view/DocumentPreview.jsx
import { Eye, File } from 'lucide-react';
import { formatBytes, formatDate, getExt, getCategoryLabel } from '../../utils/formatters';

// ── DocumentPreview ────────────────────────────────────────────────────────────
function DocumentPreview({ doc, previewUrl }) {
    const ext = doc?.type || getExt(doc?.name);
    const catLabel = getCategoryLabel(doc?.category);

    if (ext === 'PDF' && previewUrl) {
        return (
            <iframe src={previewUrl} title={doc.name} className="w-full h-full rounded border-0" />
        );
    }
    if ((ext === 'PNG' || ext === 'JPG') && previewUrl) {
        return (
            <div className="w-full h-full flex items-center justify-center p-10">
                <img src={previewUrl} alt={doc.name}
                    className="max-w-full max-h-full object-contain rounded-lg shadow-md" />
            </div>
        );
    }

    // Rich simulated document placeholder
    return (
        <div className="max-w-4xl mx-auto bg-white dark:bg-slate-900 shadow-2xl min-h-full p-12 rounded-lg relative">
            {/* Colored top accent */}
            <div className="absolute top-0 left-0 w-full h-1 bg-primary-600 dark:bg-primary-500 rounded-t-lg" />
            <div className="flex flex-col gap-8 pt-2">
                {/* Document header */}
                <div className="flex justify-between items-start">
                    <div>
                        <h2 className="text-2xl font-black text-primary-700 dark:text-primary-400 uppercase tracking-tight">
                            {catLabel}
                        </h2>
                        <p className="text-slate-400 dark:text-slate-500 font-medium text-sm mt-0.5">
                            {doc?.name}
                        </p>
                    </div>
                    <div className="text-right">
                        <p className="font-bold text-slate-700 dark:text-slate-200 text-sm">{ext}</p>
                        <p className="text-xs text-slate-400">{formatDate(doc?.created_at || doc?.date)}</p>
                    </div>
                </div>
                <div className="h-px bg-slate-100 dark:bg-slate-800" />
                {/* Stat cards */}
                <div className="grid grid-cols-3 gap-4">
                    {[
                        { label: 'Kích thước tệp', value: formatBytes(doc?.size), sub: `Định dạng ${ext}` },
                        { label: 'Danh mục', value: catLabel, sub: 'Loại tài liệu' },
                        { label: 'Người sở hữu', value: doc?.owner || '—', sub: 'Người tải lên' },
                    ].map((s) => (
                        <div key={s.label} className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-100 dark:border-slate-700">
                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">{s.label}</p>
                            <p className="text-base font-bold text-primary-700 dark:text-primary-400 mt-1 truncate">{s.value}</p>
                            <p className="text-[10px] text-slate-400 mt-0.5">{s.sub}</p>
                        </div>
                    ))}
                </div>
                {/* Body */}
                <div className="space-y-4">
                    <h3 className="font-bold text-lg text-slate-800 dark:text-slate-100">Tổng quan tài liệu</h3>
                    <p className="text-slate-500 dark:text-slate-400 leading-relaxed text-sm">
                        Tài liệu này được lưu trữ an toàn trong Micco Docs. Sử dụng các nút thao tác bên trên để
                        tải xuống, chia sẻ hoặc quản lý tệp này. Trợ lý AI có thể trả lời câu hỏi về nội dung tài liệu.
                    </p>
                    <div className="space-y-2 pt-2">
                        {[100, 90, 95, 75].map((w, i) => (
                            <div key={i} className="h-2.5 rounded-full bg-slate-100 dark:bg-slate-800" style={{ width: `${w}%` }} />
                        ))}
                    </div>
                    <div className="w-full aspect-video bg-slate-100 dark:bg-slate-800 rounded-xl flex items-center justify-center border border-slate-200 dark:border-slate-700 mt-4">
                        <div className="flex flex-col items-center gap-2 text-slate-300 dark:text-slate-600">
                            <Eye className="w-8 h-8" />
                            <p className="text-xs font-medium">Không hỗ trợ xem trước cho tệp {ext}</p>
                        </div>
                    </div>
                    <div className="space-y-2">
                        {[85, 70, 90].map((w, i) => (
                            <div key={i} className="h-2.5 rounded-full bg-slate-100 dark:bg-slate-800" style={{ width: `${w}%` }} />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default DocumentPreview;
