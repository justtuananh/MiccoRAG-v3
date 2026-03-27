import { FileText, Clock, Eye, Download, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function RecentDocumentsTable({ docs }) {
    const navigate = useNavigate();
    return (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
            <div className="px-5 py-4 flex items-center justify-between border-b border-gray-200 dark:border-gray-800">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Tài liệu gần đây</h3>
                <button
                    onClick={() => navigate('/documents')}
                    className="text-sm text-primary-600 dark:text-secondary-400 hover:underline font-medium"
                >
                    Xem tất cả
                </button>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-gray-100 dark:border-gray-800">
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tên</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">Loại</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Kích thước</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Ngày</th>
                            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Hành động</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                        {docs.map((doc) => (
                            <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-3">
                                        <FileText className="w-5 h-5 text-primary-600 dark:text-primary-400 flex-shrink-0" />
                                        <span className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[200px] lg:max-w-none">
                                            {doc.name}
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 hidden sm:table-cell">
                                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-primary-600/10 text-primary-600 dark:bg-primary-600/20 dark:text-primary-400">
                                        {doc.type}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">{doc.size}</td>
                                <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 hidden lg:table-cell">
                                    <div className="flex items-center gap-1.5">
                                        <Clock className="w-3.5 h-3.5" />
                                        {doc.date}
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <div className="flex items-center justify-end gap-1">
                                        <button className="p-1.5 rounded-lg text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-gray-800 dark:hover:text-secondary-400 transition-colors">
                                            <Eye className="w-4 h-4" />
                                        </button>
                                        <button className="p-1.5 rounded-lg text-gray-400 hover:text-accent-500 hover:bg-accent-50 dark:hover:bg-gray-800 transition-colors">
                                            <Download className="w-4 h-4" />
                                        </button>
                                        <button className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-gray-800 transition-colors">
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
