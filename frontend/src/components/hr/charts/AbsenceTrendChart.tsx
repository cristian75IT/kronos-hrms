
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

interface DataPoint {
    date: string;
    rate: number;
}

interface AbsenceTrendChartProps {
    data: DataPoint[];
    height?: number;
}

export function AbsenceTrendChart({ data, height = 300 }: AbsenceTrendChartProps) {
    // If no data, show empty state or mock
    const chartData = data.length > 0 ? data : [
        { date: '1', rate: 4 },
        { date: '5', rate: 3 },
        { date: '10', rate: 7 },
        { date: '15', rate: 2 },
        { date: '20', rate: 5 },
        { date: '25', rate: 8 },
        { date: '30', rate: 4 },
    ];

    return (
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Trend Assenteismo</h3>
            <p className="text-sm text-gray-500 mb-6">Tasso di assenza giornaliero negli ultimi 30 giorni</p>

            <div style={{ width: '100%', height: height }}>
                <ResponsiveContainer>
                    <AreaChart
                        data={chartData}
                        margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                    >
                        <defs>
                            <linearGradient id="colorRate" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis
                            dataKey="date"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                            unit="%"
                        />
                        <Tooltip
                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        />
                        <Area
                            type="monotone"
                            dataKey="rate"
                            stroke="#f43f5e"
                            strokeWidth={3}
                            fillOpacity={1}
                            fill="url(#colorRate)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
