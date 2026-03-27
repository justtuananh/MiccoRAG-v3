// src/components/shared/ConfirmDeleteModal.jsx
import { useState } from 'react';
import { Trash2 } from 'lucide-react';

export default function ConfirmDeleteModal({ title, description, onClose, onConfirm }) {
    const [deleting, setDeleting] = useState(false);

    const handleConfirm = async () => {
        setDeleting(true);
        try {
            await onConfirm();
        } finally {
            setDeleting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
            <div className="relative bg-white dark:bg-slate-900 rounded-xl p-6 max-w-sm w-full mx-4 shadow-2xl border border-slate-200 dark:border-slate-800">
                <div className="w-11 h-11 rounded-xl bg-red-100 dark:bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                    <Trash2 className="w-5 h-5 text-red-500" />
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white text-center mb-1">
                    {title}
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 text-center mb-5">
                    {description}
                </p>
                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        disabled={deleting}
                        className="flex-1 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        Hủy
                    </button>
                    <button
                        onClick={handleConfirm}
                        disabled={deleting}
                        className="flex-1 py-2.5 rounded-lg bg-red-500 hover:bg-red-600 text-white text-sm font-semibold transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
                    >
                        {deleting && <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                        Xóa
                    </button>
                </div>
            </div>
        </div>
    );
}
