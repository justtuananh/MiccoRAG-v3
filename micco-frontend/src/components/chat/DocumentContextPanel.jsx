// src/components/chat/DocumentContextPanel.jsx
import { CheckSquare, Square, BookOpen } from 'lucide-react';

export default function DocumentContextPanel({ documents, selectedDocs, onToggle, showDocs }) {
    return (
        <div className={`${showDocs ? 'w-80 flex-shrink-0' : 'w-0'} transition-all duration-300 overflow-hidden hidden lg:block`}>
            <div className="h-full bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 flex flex-col">
                <div className="p-4 border-b border-gray-100 dark:border-gray-800">
                    <div className="flex items-center gap-2 mb-1">
                        <BookOpen className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                        <h3 className="font-bold text-gray-900 dark:text-white text-sm">Ngữ cảnh tài liệu</h3>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                        Chọn tài liệu để AI tham khảo
                    </p>
                </div>

                <div className="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin">
                    {documents.map((doc) => (
                        <button
                            key={doc.id}
                            onClick={() => onToggle(doc.id)}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200 ${selectedDocs.has(doc.id)
                                ? 'bg-primary-600/10 dark:bg-primary-600/20 border border-primary-600/30'
                                : 'hover:bg-gray-50 dark:hover:bg-gray-800 border border-transparent'
                                }`}
                        >
                            {selectedDocs.has(doc.id) ? (
                                <CheckSquare className="w-4 h-4 text-primary-600 dark:text-primary-400 flex-shrink-0" />
                            ) : (
                                <Square className="w-4 h-4 text-gray-300 dark:text-gray-600 flex-shrink-0" />
                            )}
                            <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-gray-900 dark:text-white truncate">
                                    {doc.name}
                                </p>
                                <p className="text-[10px] text-gray-500 dark:text-gray-400">
                                    {doc.type} • {doc.size}
                                </p>
                            </div>
                        </button>
                    ))}
                </div>

                <div className="p-3 border-t border-gray-100 dark:border-gray-800">
                    <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                        {selectedDocs.size} tài liệu được chọn
                    </p>
                </div>
            </div>
        </div>
    );
}
