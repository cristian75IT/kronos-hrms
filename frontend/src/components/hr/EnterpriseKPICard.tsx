
import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface EnterpriseKPICardProps {
    title: string;
    value: string | number;
    subtitle: string;
    icon: React.ReactNode;
    color: 'blue' | 'amber' | 'purple' | 'emerald' | 'rose';
    badge?: string;
    trend?: number | null;
    trendLabel?: string;
    invertTrend?: boolean;
}

export function EnterpriseKPICard({ title, value, subtitle, icon, color, badge, trend, trendLabel, invertTrend }: EnterpriseKPICardProps) {
    const colorMap = {
        blue: { bg: 'bg-blue-50', ring: 'ring-blue-100', icon: 'text-blue-600', badge: 'bg-blue-500' },
        amber: { bg: 'bg-amber-50', ring: 'ring-amber-100', icon: 'text-amber-600', badge: 'bg-amber-500' },
        purple: { bg: 'bg-purple-50', ring: 'ring-purple-100', icon: 'text-purple-600', badge: 'bg-purple-500' },
        emerald: { bg: 'bg-emerald-50', ring: 'ring-emerald-100', icon: 'text-emerald-600', badge: 'bg-emerald-500' },
        rose: { bg: 'bg-rose-50', ring: 'ring-rose-100', icon: 'text-rose-600', badge: 'bg-rose-500' },
    };
    const c = colorMap[color];

    return (
        <div className={`relative overflow-hidden bg-white p-5 rounded-2xl shadow-sm border border-gray-100 ring-1 ${c.ring} hover:shadow-lg hover:scale-[1.02] transition-all duration-300 group`}>
            {/* Background Glow */}
            <div className={`absolute -right-6 -bottom-6 h-24 w-24 ${c.bg} rounded-full blur-2xl opacity-50 group-hover:opacity-80 transition-opacity`} />

            <div className="relative z-10 flex items-start gap-4">
                <div className={`p-3 rounded-xl ${c.bg} ${c.icon} shrink-0 shadow-sm`}>
                    {icon}
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-wide">{title}</p>
                        {badge && (
                            <span className={`text-[8px] font-bold ${c.badge} text-white px-1.5 py-0.5 rounded-full animate-pulse`}>
                                {badge}
                            </span>
                        )}
                    </div>
                    <h3 className="text-3xl font-black text-gray-900 leading-none mb-1 tracking-tight">{value}</h3>
                    <div className="flex items-center gap-2">
                        <p className="text-[11px] text-gray-500 font-medium">{subtitle}</p>
                        {trend !== null && trend !== undefined && (
                            <span className={`flex items-center gap-0.5 text-[10px] font-bold ${invertTrend
                                ? (trend > 5 ? 'text-rose-600' : 'text-emerald-600')
                                : 'text-blue-600'
                                }`}>
                                {invertTrend ? (
                                    trend > 5 ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />
                                ) : (
                                    <ArrowUpRight size={10} />
                                )}
                                {trend}% {trendLabel}
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
