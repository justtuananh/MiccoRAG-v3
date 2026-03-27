// src/components/document-view/DocumentActionBar.jsx
import { Download, Share2, ExternalLink, Trash2, File } from 'lucide-react';
import { fileTypeIconMap, fileTypeColors } from '../documents/fileTypes';
export default function DocumentActionBar({ doc, catLabel, ext, previewUrl, onDownload, onShareClick, onDeleteClick }) {
    const Icon = fileTypeIconMap[ext] || File;
    const iconColor = fileTypeColors[ext] || 'text-slate-400';

    return (
        <div className="shrink-0 px-8 py-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center sticky top-0 z-10">
            <div className="flex flex-col min-w-0">
                <div className="flex items-center gap-3">
                    <Icon className={`w-5 h-5 ${iconColor} shrink-0`} />
                    <h1 className="text-xl font-bold text-slate-900 dark:text-white truncate max-w-lg">{doc?.name}</h1>
                    <span className="px-2 py-0.5 rounded bg-primary-600/10 dark:bg-primary-500/20 text-primary-700 dark:text-primary-400 text-[10px] font-bold uppercase tracking-wider shrink-0">
                        {catLabel}
                    </span>
                </div>
            </div>
            <div className="flex items-center gap-2 shrink-0 ml-4">
                <button onClick={onDownload} className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold rounded-lg transition-colors">
                    <Download className="w-4 h-4" /> Tải xuống
                </button>
                <button onClick={onShareClick} className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm font-semibold rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                    <Share2 className="w-4 h-4" /> Chia sẻ
                </button>
                {previewUrl && (
                    <a href={previewUrl} target="_blank" rel="noopener noreferrer"
                        className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm font-semibold rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                        <ExternalLink className="w-4 h-4" /> Mở
                    </a>
                )}
                <button onClick={onDeleteClick}
                    className="flex items-center justify-center w-10 h-10 bg-slate-100 dark:bg-slate-800 text-red-500 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                    title="Xóa tài liệu">
                    <Trash2 className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}
