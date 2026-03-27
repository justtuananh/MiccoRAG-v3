import AnimatedCounter from '../shared/AnimatedCounter';

export default function DashboardStatCard({ label, value, icon: Icon, color, suffix, prefix, change }) {
    return (
        <div className="bg-white dark:bg-gray-900 rounded-lg p-5 border border-gray-200 dark:border-gray-800 card-hover">
            <div className="flex items-start justify-between mb-3">
                <div className={`w-9 h-9 rounded-md bg-gradient-to-br ${color} flex items-center justify-center`}>
                    <Icon className="w-4.5 h-4.5 text-white" />
                </div>
                <span className="text-xs font-semibold text-accent-600 dark:text-accent-400">
                    {change} ↗
                </span>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{label}</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                <AnimatedCounter target={value} suffix={suffix} prefix={prefix} />
            </p>
        </div>
    );
}
