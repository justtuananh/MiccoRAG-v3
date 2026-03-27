import { useRef, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { File, Eye, Download, Share2, Trash2, MoreVertical } from 'lucide-react';
import { fileTypeIconMap, fileTypeColors, fileTypeBgColors, thumbnailBg } from './fileTypes';
import { getExt, formatDate, getCategoryLabel } from '../../utils/formatters';

/* ─── Portal Dropdown (same pattern as DocumentRow) ─── */
function CardDropdown({ anchorEl, onClose, children }) {
    const menuRef = useRef(null);
    const [style, setStyle] = useState({ opacity: 0 });

    useEffect(() => {
        if (!anchorEl) return;
        const rect = anchorEl.getBoundingClientRect();
        const MENU_W = 176;
        const MENU_H = 185;
        const vw = window.innerWidth;
        const vh = window.innerHeight;

        let left = rect.right - MENU_W;
        if (left < 8) left = 8;
        if (left + MENU_W > vw - 8) left = vw - MENU_W - 8;

        let top = rect.bottom + 4;
        if (top + MENU_H > vh - 8) top = rect.top - MENU_H - 4;

        setStyle({ top, left, opacity: 1 });
    }, [anchorEl]);

    useEffect(() => {
        const handler = (e) => {
            if (
                menuRef.current && !menuRef.current.contains(e.target) &&
                anchorEl && !anchorEl.contains(e.target)
            ) onClose();
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [anchorEl, onClose]);

    return createPortal(
        <div
            ref={menuRef}
            style={{ position: 'fixed', zIndex: 9999, width: 176, ...style }}
            className="bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-100 dark:border-gray-800 py-1 animate-fade-in"
            onClick={e => e.stopPropagation()}
        >
            {children}
        </div>,
        document.body
    );
}

/* ─── Placeholder thumbnail colours per file type ─── */
const thumbGradients = {
    PDF: 'from-amber-100 to-amber-200',
    DOCX: 'from-blue-100 to-blue-200',
    XLSX: 'from-emerald-100 to-emerald-200',
    PPTX: 'from-orange-100 to-orange-200',
    PNG: 'from-purple-100 to-purple-200',
    JPG: 'from-rose-100 to-rose-200',
    MP4: 'from-pink-100 to-pink-200',
    MD: 'from-slate-100 to-slate-200',
    ZIP: 'from-teal-100 to-teal-200',
};

export default function DocumentCard({ doc, onView, onDownload, onDelete }) {
    const ext = doc.type || getExt(doc.name);
    const Icon = fileTypeIconMap[ext] || File;
    const iconColor = fileTypeColors[ext] || 'text-gray-500';
    const iconBg = fileTypeBgColors[ext] || 'bg-gray-100 dark:bg-gray-800';
    const gradient = thumbGradients[ext] || 'from-gray-100 to-gray-200';

    const [menuOpen, setMenuOpen] = useState(false);
    const menuBtnRef = useRef(null);

    return (
        <div
            className="group bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden shadow-sm hover:shadow-lg transition-all duration-200 cursor-pointer flex flex-col"
            onClick={() => onView(doc)}
        >
            {/* ── Thumbnail ── */}
            <div className="relative w-full" style={{ paddingBottom: '50%' /* compact ratio */ }}>
                <div className="absolute inset-0">
                    {doc.thumbnail ? (
                        <img
                            src={`${import.meta.env.VITE_API_BASE_URL || ''}/api/documents/${doc.id}/thumbnail`}
                            alt={doc.name}
                            className="w-full h-full object-cover"
                            onError={(e) => { e.target.style.display = 'none'; }}
                        />
                    ) : (
                        <div className={`w-full h-full bg-gradient-to-br ${gradient} flex items-center justify-center`}>
                            <Icon className={`w-8 h-8 ${iconColor} opacity-40`} />
                        </div>
                    )}

                    {/* File-type badge — top right */}
                    <div className={`absolute top-2 right-2 w-6 h-6 rounded-md ${iconBg} flex items-center justify-center shadow-sm`}>
                        <Icon className={`w-3 h-3 ${iconColor}`} />
                    </div>
                </div>
            </div>

            {/* ── Card Footer ── */}
            <div className="px-2.5 py-2 flex flex-col gap-0.5">
                {/* Name */}
                <p
                    className="text-xs font-semibold text-gray-900 dark:text-white truncate leading-snug"
                    title={doc.name}
                >
                    {doc.name}
                </p>

                {/* Modified date + three-dot menu */}
                <div className="flex items-center justify-between mt-0.5">
                    <span style={{ fontSize: '10px' }} className="text-gray-400 dark:text-gray-500 leading-none">
                        Cập nhật {formatDate(doc.date || doc.created_at)}
                    </span>

                    <button
                        ref={menuBtnRef}
                        onClick={(e) => { e.stopPropagation(); setMenuOpen(v => !v); }}
                        className="p-1 rounded-md text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors -mr-1"
                    >
                        <MoreVertical className="w-3.5 h-3.5" />
                    </button>

                    {menuOpen && (
                        <CardDropdown anchorEl={menuBtnRef.current} onClose={() => setMenuOpen(false)}>
                            <button
                                onClick={() => { onView(doc); setMenuOpen(false); }}
                                className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                            >
                                <Eye className="w-4 h-4 text-gray-400" /> Xem
                            </button>
                            <button
                                onClick={() => { onDownload(doc); setMenuOpen(false); }}
                                className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                            >
                                <Download className="w-4 h-4 text-gray-400" /> Tải xuống
                            </button>
                            <button
                                className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                            >
                                <Share2 className="w-4 h-4 text-gray-400" /> Chia sẻ
                            </button>
                            <div className="my-1 border-t border-gray-100 dark:border-gray-800" />
                            <button
                                onClick={() => { onDelete(doc.id); setMenuOpen(false); }}
                                className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                            >
                                <Trash2 className="w-4 h-4" /> Xóa
                            </button>
                        </CardDropdown>
                    )}
                </div>
            </div>
        </div>
    );
}
