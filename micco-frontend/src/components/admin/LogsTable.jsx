import { 
    Search, Download, ChevronLeft, ChevronRight, 
    History, Info, Monitor, Clock, Cpu
} from 'lucide-react';

export const LOG_PAGE_SIZE = 10;

function timeAgo(dateStr) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    const diff = Math.floor((Date.now() - date) / 1000);
    
    if (diff < 60) return 'vừa xong';
    if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`;
    
    return date.toLocaleString('vi-VN', { 
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
}

const METHOD_COLORS = {
    'hybrid': 'bg-violet-100 text-violet-700 dark:bg-violet-500/20 dark:text-violet-300',
    'vector': 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300',
    'graph': 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300',
};

export default function LogsTable({
    logs, total, page, totalPages,
    search, onSearchChange, onPageChange, onExport,
    onViewDetail
}) {
    const startRow = (page - 1) * LOG_PAGE_SIZE + 1;
    const endRow = Math.min(page * LOG_PAGE_SIZE, total);

    return (
        <section className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col h-[600px]">
            
            {/* Table toolbar */}
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
                <div className="flex items-center gap-2">
                    <History className="w-5 h-5 text-primary-600" />
                    <h3 className="font-bold text-lg text-slate-900 dark:text-white">Lịch sử hệ thống</h3>
                </div>
                
                <div className="flex items-center gap-2 flex-wrap">
                    {/* Search */}
                    <div className="relative flex items-center">
                        <Search className="absolute left-3 w-4 h-4 text-slate-400 pointer-events-none" />
                        <input
                            value={search}
                            onChange={e => onSearchChange(e.target.value)}
                            placeholder="Tìm kiếm log (IP, câu hỏi, phương thức)..."
                            className="pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none focus:ring-2 focus:ring-primary-600/30 focus:border-primary-600 w-64 transition-all"
                        />
                    </div>

                    <button
                        onClick={onExport}
                        className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400 text-sm font-medium px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors border border-slate-200 dark:border-slate-700"
                    >
                        <Download className="w-4 h-4" /> Xuất
                    </button>
                </div>
            </div>

            {/* Table Body */}
            <div className="flex-1 overflow-auto min-h-0 custom-scrollbar">
                <table className="w-full text-left border-collapse table-fixed">
                    <thead className="sticky top-0 z-10 bg-slate-50 dark:bg-slate-800/90 backdrop-blur-sm shadow-sm">
                        <tr>
                            <th className="w-[180px] px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Thời gian</th>
                            <th className="w-[120px] px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">IP / Method</th>
                            <th className="w-[100px] px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Độ trễ</th>
                            <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Câu hỏi/Trả lời</th>
                            <th className="w-[80px] px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-right">Chi tiết</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {logs.length === 0 && (
                            <tr>
                                <td colSpan={5} className="px-6 py-20 text-center">
                                    <Monitor className="w-12 h-12 text-slate-100 dark:text-slate-800 mx-auto mb-4" />
                                    <p className="text-slate-500 dark:text-slate-400 font-medium">Không tìm thấy dữ liệu lịch sử</p>
                                    <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Hệ thống chưa ghi nhận hoạt động nào khớp với tìm kiếm</p>
                                </td>
                            </tr>
                        )}
                        {logs.map((log) => (
                            <tr key={log.id} className="group hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                                {/* Time */}
                                <td className="px-6 py-4 align-top">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                                            {timeAgo(log.timestamp)}
                                        </span>
                                        <span className="text-[10px] text-slate-400 uppercase tracking-tighter mt-0.5">
                                            ID: #{log.id}
                                        </span>
                                    </div>
                                </td>
                                
                                {/* IP / Method */}
                                <td className="px-6 py-4 align-top">
                                    <div className="flex flex-col gap-1.5">
                                        <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                                            <Monitor className="w-3 h-3 opacity-60" />
                                            {log.ip_address || 'Unknown'}
                                        </div>
                                        <span className={`w-fit px-2 py-0.5 rounded text-[10px] font-bold uppercase ${METHOD_COLORS[log.method] || 'bg-slate-100 text-slate-600'}`}>
                                            {log.method}
                                        </span>
                                    </div>
                                </td>

                                {/* Latency */}
                                <td className="px-6 py-4 align-top">
                                    <div className="flex items-center gap-1.5">
                                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                                        <span className={`text-sm font-semibold ${log.response_time > 10 ? 'text-amber-500' : 'text-emerald-500'}`}>
                                            {log.response_time.toFixed(2)}s
                                        </span>
                                    </div>
                                </td>

                                {/* Q&A Snippet */}
                                <td className="px-6 py-4 align-top">
                                    <div className="space-y-1.5 overflow-hidden">
                                        <div className="flex gap-2">
                                            <span className="text-[10px] font-bold text-primary-600 bg-primary-50 dark:bg-primary-500/10 px-1 rounded h-fit mt-0.5 shrink-0">Q</span>
                                            <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-1 font-medium">{log.question}</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-500/10 px-1 rounded h-fit mt-0.5 shrink-0">A</span>
                                            <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1 whitespace-pre-wrap">{log.answer}</p>
                                        </div>
                                    </div>
                                </td>

                                {/* Detailed View */}
                                <td className="px-6 py-4 align-top text-right">
                                    <button 
                                        onClick={() => onViewDetail(log)}
                                        className="p-2 text-slate-400 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-all"
                                    >
                                        <Info className="w-4 h-4" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination footer */}
            <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 shrink-0">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                    {total > 0 ? `Hiển thị ${startRow} đến ${endRow} trong số ${total.toLocaleString()} log` : 'Không có kết quả'}
                </p>
                <div className="flex items-center gap-1.5">
                    <button
                        onClick={() => onPageChange(page - 1)}
                        disabled={page === 1}
                        className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                    >
                        <ChevronLeft className="w-3.5 h-3.5" /> Trước
                    </button>

                    <div className="flex items-center px-4 h-8 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm font-medium text-slate-700 dark:text-slate-300">
                        {page} / {totalPages}
                    </div>

                    <button
                        onClick={() => onPageChange(page + 1)}
                        disabled={page === totalPages}
                        className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                    >
                        Tiếp <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>
        </section>
    );
}

// ── Detail Modal Component ───────────────────────────────────────────────────
export function LogDetailModal({ log, onClose }) {
    if (!log) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white dark:bg-slate-900 w-full max-w-4xl max-h-[90vh] rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
                
                <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                    <div>
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                             Log Chi Tiết <span className="text-sm font-normal text-slate-400">#{log.id}</span>
                        </h3>
                        <p className="text-xs text-slate-500 mt-1 flex items-center gap-3">
                            <span className="flex items-center gap-1"><Monitor className="w-3 h-3"/> {log.ip_address}</span>
                            <span className="flex items-center gap-1"><Clock className="w-3 h-3"/> {new Date(log.timestamp).toLocaleString()}</span>
                            <span className="flex items-center gap-1"><Cpu className="w-3 h-3"/> {log.method}</span>
                        </p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-400 transition-colors">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                    <div className="space-y-2">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Câu hỏi</h4>
                        <div className="p-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 rounded-xl text-slate-800 dark:text-slate-200 font-medium">
                            {log.question}
                        </div>
                    </div>

                    <div className="space-y-2">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 text-emerald-500">Câu trả lời</h4>
                        <div className="p-4 bg-emerald-50/30 dark:bg-emerald-500/5 border border-emerald-100/50 dark:border-emerald-500/20 rounded-xl text-slate-700 dark:text-slate-300 whitespace-pre-wrap text-sm leading-relaxed">
                            {log.answer}
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 flex flex-col">
                             <span className="text-[10px] font-bold text-slate-400 uppercase">Thời gian phản hồi</span>
                             <span className="text-lg font-bold text-slate-900 dark:text-white">{log.response_time.toFixed(3)} giây</span>
                        </div>
                        <div className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 flex flex-col">
                             <span className="text-[10px] font-bold text-slate-400 uppercase">Workspace ID</span>
                             <span className="text-lg font-bold text-slate-900 dark:text-white">#{log.workspace_id}</span>
                        </div>
                    </div>
                </div>

                <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                    <button onClick={onClose} className="px-6 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-sm font-bold rounded-xl transition-transform active:scale-95"> Đóng </button>
                </div>
            </div>
        </div>
    );
}
