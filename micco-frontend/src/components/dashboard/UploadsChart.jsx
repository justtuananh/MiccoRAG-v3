import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function UploadsChart({ data }) {
    return (
        <div className="bg-white dark:bg-gray-900 rounded-lg p-5 border border-gray-200 dark:border-gray-800">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-6">Lượt tải lên theo thời gian</h3>
            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                        <XAxis dataKey="month" stroke="#94A3B8" fontSize={12} />
                        <YAxis stroke="#94A3B8" fontSize={12} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1E293B', border: 'none',
                                borderRadius: '12px', color: '#fff', fontSize: '13px',
                            }}
                        />
                        <Line
                            type="monotone" dataKey="uploads" stroke="#4F46E5"
                            strokeWidth={3}
                            dot={{ r: 5, fill: '#4F46E5', strokeWidth: 2, stroke: '#fff' }}
                            activeDot={{ r: 7, fill: '#4F46E5' }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
