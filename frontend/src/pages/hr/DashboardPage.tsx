
import { useEffect, useState } from 'react';
import {
    Users,
    Briefcase,
    AlertTriangle,
    FileText,
    Calendar,
    Download,
    CheckCircle
} from 'lucide-react';
import { hrReportingService } from '../../services/hrReporting.service';
import { EnterpriseKPICard } from '../../components/hr/EnterpriseKPICard';
import { AbsenceTrendChart } from '../../components/hr/charts/AbsenceTrendChart';
import { CompliancePieChart } from '../../components/hr/charts/CompliancePieChart';
import type { DashboardOverview } from '../../types';
import { format, subDays, startOfMonth } from 'date-fns';
import { it } from 'date-fns/locale';

export default function HRDashboardPage() {
    const [overview, setOverview] = useState<DashboardOverview | null>(null);
    const [trendData, setTrendData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [exporting, setExporting] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            // 1. Fetch Overview
            const data = await hrReportingService.getDashboardOverview();
            setOverview(data);

            // 2. Fetch Trend Data (Last 30 days)
            const end = new Date();


            // const trend = await hrReportingService.getAggregateAttendance({
            //     start_date: format(start, 'yyyy-MM-dd'),
            //     end_date: format(end, 'yyyy-MM-dd')
            // });

            // Map trend data if available, otherwise mock or calculate
            // The aggregate endpoint returns PER USER stats, not PER DAY stats.
            // We might need a specific endpoint for daily trend or calc it from daily snapshots if available.
            // For now, we will mock the trend data to demonstrate the UI until backend support implies daily stats.
            // In a real scenario, we'd add `get_daily_trend` to backend.
            const mockTrend = Array.from({ length: 30 }, (_, i) => ({
                date: format(subDays(end, 29 - i), 'dd/MM'),
                rate: Math.floor(Math.random() * 10) + 2 // Random 2-12%
            }));
            setTrendData(mockTrend);

        } catch (error) {
            console.error("Failed to load dashboard:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleExportLul = async () => {
        try {
            setExporting(true);
            const now = new Date();
            const prevMonth = subDays(startOfMonth(now), 1); // Last day of prev month
            const year = prevMonth.getFullYear();
            const month = prevMonth.getMonth() + 1;

            const blob = await hrReportingService.exportLul(year, month);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `LUL_KRONOS_${year}_${month.toString().padStart(2, '0')}.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Export failed:", error);
            alert("Errore durante l'export LUL");
        } finally {
            setExporting(false);
        }
    };

    if (loading) {
        return <div className="p-8 flex justify-center"><span className="loading loading-spinner loading-lg text-primary"></span></div>;
    }

    return (
        <div className="p-8 max-w-[1600px] mx-auto space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-black text-gray-900 tracking-tight">HR Console</h1>
                    <p className="text-gray-500 mt-1">Panoramica forza lavoro e conformità.</p>
                </div>

                <div className="flex gap-3">
                    <button
                        onClick={() => loadData()}
                        className="btn btn-ghost btn-sm text-gray-500"
                    >
                        Refresh
                    </button>
                    <button
                        onClick={handleExportLul}
                        disabled={exporting}
                        className="btn btn-primary gap-2 shadow-lg shadow-indigo-500/20"
                    >
                        {exporting ? <span className="loading loading-spinner loading-xs"></span> : <Download size={18} />}
                        Export LUL (Mese Scorso)
                    </button>
                </div>
            </div>

            {/* KPI Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <EnterpriseKPICard
                    title="Totale Dipendenti"
                    value={overview?.workforce.total_employees || 0}
                    subtitle="Attivi in organico"
                    icon={<Users size={24} />}
                    color="blue"
                    trend={2}
                    trendLabel="vs mese scorso"
                />
                <EnterpriseKPICard
                    title="Assenti Oggi"
                    value={overview?.workforce.on_leave || 0}
                    subtitle="Ferie, Malattia o Permessi"
                    icon={<Briefcase size={24} />}
                    color={(overview?.workforce.on_leave || 0) > 5 ? 'rose' : 'amber'}
                    trend={null}
                    invertTrend
                />
                <EnterpriseKPICard
                    title="In Attesa"
                    value={overview?.pending_approvals?.total ?? 0}
                    subtitle="Richieste da approvare"
                    icon={<FileText size={24} />}
                    color="purple"
                    badge={overview?.pending_approvals?.total && overview.pending_approvals.total > 0 ? `${overview.pending_approvals.total} New` : undefined}
                />
                <EnterpriseKPICard
                    title="Alert Attivi"
                    value={overview?.alerts.length || 0}
                    subtitle="Anomalie o Scadenze"
                    icon={<AlertTriangle size={24} />}
                    color="rose"
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Trend Chart (2 cols) */}
                <div className="lg:col-span-2">
                    <AbsenceTrendChart data={trendData} />
                </div>

                {/* Compliance Pie (1 col) */}
                <div>
                    <CompliancePieChart
                        data={[
                            { name: 'Compliant', value: 85, color: '#10b981' },
                            { name: 'Warning', value: 10, color: '#f59e0b' },
                            { name: 'Critical', value: 5, color: '#ef4444' },
                        ]} // Mocked for now, pending aggregation backend endpoint
                        complianceRate={92}
                    />
                </div>
            </div>

            {/* Recent Alerts / Quick Actions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Alerts List */}
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-lg font-bold text-gray-900">Ultimi Alert</h3>
                        <button className="text-sm text-primary font-medium hover:underline">Vedi tutti</button>
                    </div>

                    <div className="space-y-4">
                        {overview?.alerts && overview.alerts.length > 0 ? (
                            overview.alerts.slice(0, 5).map(alert => (
                                <div key={alert.id} className="flex gap-4 p-3 rounded-xl hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-100">
                                    <div className={`w-2 h-2 mt-2 rounded-full shrink-0 ${alert.severity === 'critical' ? 'bg-rose-500' :
                                        alert.severity === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
                                        }`} />
                                    <div>
                                        <h4 className="text-sm font-bold text-gray-900">{alert.type}</h4>
                                        <p className="text-xs text-gray-500 mt-0.5">{alert.title}</p>
                                        <div className="flex gap-2 mt-2">
                                            {alert.action_required && (
                                                <span className="text-[10px] font-bold bg-rose-50 text-rose-600 px-2 py-0.5 rounded-full">ACTION REQUIRED</span>
                                            )}
                                        </div>
                                    </div>
                                    <span className="ml-auto text-[10px] text-gray-400 font-medium whitespace-nowrap">
                                        {format(new Date(alert.created_at), 'dd MMM', { locale: it })}
                                    </span>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-8 text-gray-400">
                                <CheckCircle className="mx-auto mb-2 opacity-50" size={32} />
                                <p className="text-sm">Tutto tranquillo, nessun alert.</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Quick Actions Panel */}
                <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 rounded-2xl shadow-lg p-6 text-white relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-5 rounded-full -mr-10 -mt-10 blur-2xl"></div>

                    <h3 className="text-lg font-bold mb-2 relative z-10">Azioni Rapide</h3>
                    <p className="text-indigo-100 text-sm mb-6 relative z-10">Strumenti di gestione frequenti.</p>

                    <div className="grid grid-cols-2 gap-3 relative z-10">
                        <button className="btn bg-white/10 border-0 text-white hover:bg-white/20 h-auto py-4 flex flex-col gap-2">
                            <Calendar size={20} />
                            <span className="text-xs">Pianifica Turni</span>
                        </button>
                        <button className="btn bg-white/10 border-0 text-white hover:bg-white/20 h-auto py-4 flex flex-col gap-2">
                            <CheckCircle size={20} />
                            <span className="text-xs">Approva Ferie</span>
                        </button>
                        <button className="btn bg-white/10 border-0 text-white hover:bg-white/20 h-auto py-4 flex flex-col gap-2">
                            <FileText size={20} />
                            <span className="text-xs">Report Mensile</span>
                        </button>
                        <button className="btn bg-white/10 border-0 text-white hover:bg-white/20 h-auto py-4 flex flex-col gap-2">
                            <AlertTriangle size={20} />
                            <span className="text-xs">Gestisci Anomalie</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
