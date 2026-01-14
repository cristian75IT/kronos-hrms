
import {
    PieChart,
    Pie,
    Cell,
    ResponsiveContainer,
    Tooltip
} from 'recharts';

interface ComplianceData {
    name: string;
    value: number;
    color: string;
    [key: string]: string | number; // Index signature for recharts compatibility
}

interface CompliancePieChartProps {
    data: ComplianceData[];
    complianceRate: number;
}

export function CompliancePieChart({ data, complianceRate }: CompliancePieChartProps) {
    const defaultData = [
        { name: 'Compliant', value: 75, color: '#10b981' },
        { name: 'At Risk', value: 15, color: '#f59e0b' },
        { name: 'Critical', value: 10, color: '#ef4444' },
    ];

    const chartData = data.length > 0 ? data : defaultData;

    return (
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex flex-col items-center justify-center relative min-h-[300px]">
            <h3 className="text-lg font-bold text-gray-900 w-full mb-4">Stato Conformità</h3>

            <div className="relative w-full h-[200px]">
                <ResponsiveContainer>
                    <PieChart>
                        <Pie
                            data={chartData}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={85}
                            paddingAngle={5}
                            dataKey="value"
                            startAngle={90}
                            endAngle={-270}
                        >
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} strokeWidth={0} />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        />
                    </PieChart>
                </ResponsiveContainer>

                {/* Center Stats */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                    <span className="text-3xl font-black text-gray-900">{complianceRate}%</span>
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Rate</span>
                </div>
            </div>

            {/* Legend */}
            <div className="flex gap-4 mt-6">
                {chartData.map((entry) => (
                    <div key={entry.name} className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
                        <span className="text-xs font-medium text-gray-600">{entry.name}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
