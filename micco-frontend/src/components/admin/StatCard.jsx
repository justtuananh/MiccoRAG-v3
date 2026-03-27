import { TrendingUp, TrendingDown } from 'lucide-react';

export default function StatCard({ icon: Icon, label, value, change, positive }) {
    return (
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between mb-4">
                <span className="text-primary-700 dark:text-primary-400 bg-primary-600/10 dark:bg-primary-500/20 p-2 rounded-lg">
                    <Icon className="w-5 h-5" />
                </span>
                <span className={`text-sm font-medium flex items-center gap-0.5 ${positive ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-500 dark:text-rose-400'}`}>
                    {change}
                    {positive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                </span>
            </div>
            <h3 className="text-slate-500 dark:text-slate-400 text-sm font-medium">{label}</h3>
            <p className="text-3xl font-bold mt-1 text-slate-900 dark:text-white">{value}</p>
        </div>
    );
}
