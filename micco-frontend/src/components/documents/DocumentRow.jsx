import { useRef, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { File, Eye, Download, Share2, Trash2, MoreHorizontal, Clock, XCircle } from 'lucide-react';
import { fileTypeIconMap, fileTypeColors, fileTypeBgColors } from './fileTypes';
import { getExt, formatBytes, formatDate, getInitials, avatarColor, categoryColors, getCategoryLabel } from '../../utils/formatters';

function DropdownMenu({ anchorEl, onClose, children }) {
    const menuRef = useRef(null);
    const [style, setStyle] = useState({ opacity: 0 });

    useEffect(() => {
        if (!anchorEl) return;

        const rect = anchorEl.getBoundingClientRect();
        const MENU_WIDTH = 176; // w-44 = 11rem = 176px
        const MENU_HEIGHT = 180; // approximate

        const viewportW = window.innerWidth;
        const viewportH = window.innerHeight;

        // Position to the right of the button by default; shift left if it overflows
        let left = rect.right - MENU_WIDTH;
        if (left < 8) left = 8;
        if (left + MENU_WIDTH > viewportW - 8) left = viewportW - MENU_WIDTH - 8;

        // Position below the button; flip up if not enough room
        let top = rect.bottom + 4;
        if (top + MENU_HEIGHT > viewportH - 8) top = rect.top - MENU_HEIGHT - 4;

        setStyle({ top, left, opacity: 1 });
    }, [anchorEl]);

    // Close on outside click
    useEffect(() => {
        const handler = (e) => {
            if (menuRef.current && !menuRef.current.contains(e.target) &&
                anchorEl && !anchorEl.contains(e.target)) {
                onClose();
            }
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

export default function DocumentRow({ doc, openMenu, onToggleMenu, onView, onDownload, onDelete }) {
    const ext = doc.type || getExt(doc.name);
    const Icon = fileTypeIconMap[ext] || File;
    const iconColor = fileTypeColors[ext] || 'text-gray-500';
    const bgColor = fileTypeBgColors[ext] || 'bg-gray-100 dark:bg-gray-800';
    const catLabel = getCategoryLabel(doc.category);
    const catColor = categoryColors[catLabel] || categoryColors['Khác'];

    const btnRef = useRef(null);
    const isOpen = openMenu === doc.id;

    return (
        <tr className="hover:bg-gray-50 dark:hover:bg-gray-800/40 transition-colors">
            {/* Name */}
            <td className="px-6 py-4">
                <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-lg ${bgColor} flex items-center justify-center flex-shrink-0`}>
                        <Icon className={`w-4.5 h-4.5 ${iconColor}`} />
                    </div>
                    <div className="min-w-0">
                        <span className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[160px] lg:max-w-xs block" title={doc.name}>
                            {doc.name}
                        </span>
                        {doc.approval_status === 'pending' && (
                            <span className="inline-flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 mt-0.5">
                                <Clock className="w-3 h-3" /> Chờ duyệt
                            </span>
                        )}
                        {doc.approval_status === 'rejected' && (
                            <span className="inline-flex items-center gap-1 text-xs text-red-500 dark:text-red-400 mt-0.5">
                                <XCircle className="w-3 h-3" /> Từ chối
                            </span>
                        )}
                    </div>
                </div>
            </td>
            {/* Category */}
            <td className="px-6 py-4 hidden sm:table-cell">
                <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${catColor}`}>
                    {catLabel}
                </span>
            </td>
            {/* Date Modified */}
            <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">
                {formatDate(doc.date || doc.created_at)}
            </td>
            {/* Size */}
            <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">
                {formatBytes(doc.size)}
            </td>
            {/* Owner */}
            <td className="px-6 py-4 hidden lg:table-cell">
                <div className="flex items-center gap-2.5">
                    <div className={`w-7 h-7 rounded-full ${avatarColor(doc.owner)} flex items-center justify-center text-white text-xs font-semibold flex-shrink-0`}>
                        {getInitials(doc.owner)}
                    </div>
                    <span className="text-sm text-gray-700 dark:text-gray-300">{doc.owner || '—'}</span>
                </div>
            </td>
            {/* Actions — three-dot menu */}
            <td className="px-6 py-4 text-right">
                <button
                    ref={btnRef}
                    onClick={(e) => { e.stopPropagation(); onToggleMenu(doc.id); }}
                    className="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                    <MoreHorizontal className="w-4 h-4" />
                </button>

                {isOpen && (
                    <DropdownMenu anchorEl={btnRef.current} onClose={() => onToggleMenu(null)}>
                        <button onClick={() => { onView(doc); onToggleMenu(null); }} className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                            <Eye className="w-4 h-4 text-gray-400" /> Xem
                        </button>
                        <button onClick={() => { onDownload(doc); onToggleMenu(null); }} className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                            <Download className="w-4 h-4 text-gray-400" /> Tải xuống
                        </button>
                        <button className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                            <Share2 className="w-4 h-4 text-gray-400" /> Chia sẻ
                        </button>
                        <div className="my-1 border-t border-gray-100 dark:border-gray-800" />
                        <button onClick={() => { onDelete(doc.id); onToggleMenu(null); }} className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors">
                            <Trash2 className="w-4 h-4" /> Xóa
                        </button>
                    </DropdownMenu>
                )}
            </td>
        </tr>
    );
}
