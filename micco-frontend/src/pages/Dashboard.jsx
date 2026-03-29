import { useState, useEffect, useCallback } from 'react';
import {
    FileText, HardDrive, Upload, Database, Layers,
    CheckCircle2, Clock, AlertCircle, RefreshCw, Server
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Breadcrumb from '../components/shared/Breadcrumb';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend, AreaChart, Area
} from 'recharts';

// ─── Animated counter ─────────────────────────────────────────────────────────
function AnimatedNumber({ value, suffix = '', prefix = '' }) {
    const [display, setDisplay] = useState(0);
    useEffect(() => {
        if (value === 0) { setDisplay(0); return; }
        let start = 0;
        const step = value / 30;
        const timer = setInterval(() => {
            start += step;
            if (start >= value) { clearInterval(timer); setDisplay(value); }
            else setDisplay(Math.floor(start));
        }, 25);
        return () => clearInterval(timer);
    }, [value]);
    return <span>{prefix}{display.toLocaleString('vi-VN')}{suffix}</span>;
}

// ─── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, numValue, icon: Icon, gradient, suffix = '', prefix = '', sub }) {
    return (
        <div className="relative bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 overflow-hidden shadow-sm transition-all group">
            <div className={`absolute top-0 right-0 w-28 h-28 rounded-bl-full opacity-5 bg-gradient-to-br ${gradient}`} />
            <div className="flex items-start gap-4">
                <div className={`w-12 h-12 rounded-2xl flex-shrink-0 flex items-center justify-center bg-gradient-to-br ${gradient} shadow-md`}>
                    <Icon className="w-5 h-5 text-white" />
                </div>
                <div className="min-w-0">
                    <p className="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-1">{label}</p>
                    <p className="text-2xl font-black text-gray-900 dark:text-white truncate">
                        {numValue !== undefined
                            ? <AnimatedNumber value={numValue} suffix={suffix} prefix={prefix} />
                            : value
                        }
                    </p>
                    {sub && <p className="text-xs text-gray-400 dark:text-gray-500 truncate mt-1">{sub}</p>}
                </div>
            </div>
        </div>
    );
}

// ─── Status Badge ─────────────────────────────────────────────────────────────
const STATUS_CFG = {
    indexed: { label: 'Đã lập chỉ mục', color: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-500/10 dark:text-emerald-400' },
    processing: { label: 'Đang xử lý', color: 'text-amber-600 bg-amber-50 dark:bg-amber-500/10 dark:text-amber-400' },
    pending: { label: 'Chờ xử lý', color: 'text-gray-500 bg-gray-100 dark:bg-gray-700 dark:text-gray-400' },
    failed: { label: 'Lỗi', color: 'text-red-600 bg-red-50 dark:bg-red-500/10 dark:text-red-400' },
    parsing: { label: 'Phân tích', color: 'text-blue-600 bg-blue-50 dark:bg-blue-500/10 dark:text-blue-400' },
    indexing: { label: 'Lập chỉ mục', color: 'text-violet-600 bg-violet-50 dark:bg-violet-500/10 dark:text-violet-400' },
};
function StatusBadge({ status }) {
    const cfg = STATUS_CFG[status] || { label: status, color: 'text-gray-500 bg-gray-100' };
    return <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${cfg.color}`}>{cfg.label}</span>;
}

// ─── Custom Tooltip ───────────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label, unit = '' }) {
    if (!active || !payload?.length) return null;
    return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg px-3 py-2 text-xs">
            <p className="font-semibold text-gray-700 dark:text-gray-200 mb-1">{label}</p>
            {payload.map((p, i) => (
                <p key={i} style={{ color: p.color }} className="font-medium">
                    {p.name}: {p.value}{unit}
                </p>
            ))}
        </div>
    );
}

export default function Dashboard() {
    const { authFetch } = useAuth();
    const [stats, setStats] = useState(null);
    const [uploadsData, setUploadsData] = useState([]);
    const [statusData, setStatusData] = useState([]);
    const [workspaceData, setWorkspaceData] = useState([]);
    const [recentDocs, setRecentDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [lastRefresh, setLastRefresh] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');

    const fetchAll = useCallback(async () => {
        setLoading(true);
        try {
            const [statsRes, uploadsRes, statusRes, wsRes, docsRes] = await Promise.all([
                authFetch('/api/dashboard/stats'),
                authFetch('/api/dashboard/uploads-over-time'),
                authFetch('/api/dashboard/document-status'),
                authFetch('/api/dashboard/workspace-stats'),
                authFetch('/api/dashboard/recent-documents'),
            ]);

            if (statsRes.ok) setStats(await statsRes.json());
            if (uploadsRes.ok) setUploadsData(await uploadsRes.json());
            if (statusRes.ok) setStatusData(await statusRes.json());
            if (wsRes.ok) setWorkspaceData(await wsRes.json());
            if (docsRes.ok) setRecentDocs(await docsRes.json());
            setLastRefresh(new Date());
        } catch (err) {
            console.error('Dashboard fetch error:', err);
        } finally {
            setLoading(false);
        }
    }, [authFetch]);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    const statCards = stats ? [
        {
            label: 'Tổng tài liệu',
            numValue: stats.totalFiles,
            icon: FileText,
            gradient: 'from-indigo-500 to-purple-600',
            sub: `${stats.indexedDocs || 0} đã lập chỉ mục`,
        },
        {
            label: 'Dung lượng',
            value: stats.storageUsed,
            icon: HardDrive,
            gradient: 'from-violet-500 to-purple-600',
            sub: `${stats.totalChunks?.toLocaleString('vi-VN') || 0} chunks`,
        },
        {
            label: 'Tải lên 7 ngày',
            numValue: stats.recentUploads,
            icon: Upload,
            gradient: 'from-emerald-500 to-teal-600',
            sub: 'tài liệu gần đây',
        },
        {
            label: 'Workspaces',
            numValue: stats.totalWorkspaces,
            icon: Database,
            gradient: 'from-amber-500 to-orange-500',
            sub: `${stats.teamMembers} người dùng`,
        },
    ] : [];

    return (
        <div className="space-y-6 pb-6 px-2 md:px-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 px-2 md:px-2 pt-4 md:pt-6">
                <div>
                    <h1 className="text-2xl font-black text-gray-900 dark:text-white tracking-tight">Tổng quan hệ thống</h1>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Cập nhật {lastRefresh?.toLocaleTimeString('vi-VN')}
                    </p>
                </div>
                <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl w-fit">
                    {[
                        { id: 'overview', label: 'Thống kê' },
                        { id: 'activity', label: 'Hoạt động' }
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${activeTab === tab.id
                                ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-white shadow-sm'
                                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                    <div className="w-px h-4 bg-gray-200 dark:bg-gray-700 mx-1" />
                    <button
                        onClick={fetchAll}
                        disabled={loading}
                        className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {activeTab === 'overview' ? (
                <>
                    {/* Stat Cards */}
                    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5 px-2 md:px-2">
                        {loading && !stats ? (
                            [...Array(4)].map((_, i) => (
                                <div key={i} className="h-24 bg-gray-100 dark:bg-gray-800 rounded-2xl animate-pulse" />
                            ))
                        ) : (
                            statCards.map(c => <StatCard key={c.label} {...c} />)
                        )}
                    </div>

                    {/* Row 1 Charts */}
                    <div className="grid lg:grid-cols-3 gap-5 px-2 md:px-2">
                        <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 shadow-sm">
                            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Lượt tải lên</h3>
                            <ResponsiveContainer width="100%" height={200}>
                                <AreaChart data={uploadsData} margin={{ top: 5, right: 10, left: -30, bottom: 0 }}>
                                    <XAxis dataKey="month" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <YAxis hide />
                                    <Tooltip content={<CustomTooltip unit=" tài liệu" />} />
                                    <Area type="monotone" dataKey="uploads" stroke="#6366f1" strokeWidth={2} fill="#6366f1" fillOpacity={0.1} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="lg:col-span-1 bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 shadow-sm">
                            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Trạng thái</h3>
                            <ResponsiveContainer width="100%" height={200}>
                                <PieChart>
                                    <Pie data={statusData} dataKey="count" nameKey="status" innerRadius={50} outerRadius={75} paddingAngle={4}>
                                        {statusData.map((entry, i) => <Cell key={i} fill={entry.fill} stroke="transparent" />)}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Workspace Chart */}
                    {workspaceData.length > 0 && (
                        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 shadow-sm mx-2 md:mx-2">
                            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Workspace</h3>
                            <ResponsiveContainer width="100%" height={180}>
                                <BarChart data={workspaceData} margin={{ top: 5, right: 10, left: -30, bottom: 0 }}>
                                    <XAxis dataKey="workspace" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <YAxis hide />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Bar dataKey="documents" name="Tài liệu" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={24} />
                                    <Bar dataKey="chunks" name="Chunks" fill="#10b981" radius={[4, 4, 0, 0]} barSize={24} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </>
            ) : (
                <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm overflow-hidden mx-2 md:mx-2">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30">
                                    {['Tên tài liệu', 'Loại', 'Workspace', 'Kích thước', 'Trạng thái'].map(h => (
                                        <th key={h} className="px-5 py-2.5 text-[10px] font-bold text-gray-400 uppercase tracking-widest">{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50 dark:divide-gray-800/50 text-xs">
                                {recentDocs.map(doc => (
                                    <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/40 transition-colors">
                                        <td className="px-5 py-2 font-medium text-gray-900 dark:text-gray-100 truncate max-w-[200px]">{doc.name}</td>
                                        <td className="px-5 py-2">
                                            <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 uppercase">{doc.type}</span>
                                        </td>
                                        <td className="px-5 py-2 text-gray-500 truncate max-w-[120px]">{doc.workspace}</td>
                                        <td className="px-5 py-2 text-gray-500">{doc.size}</td>
                                        <td className="px-5 py-2"><StatusBadge status={doc.status} /></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
