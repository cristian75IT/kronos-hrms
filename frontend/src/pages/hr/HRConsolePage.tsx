import { useState, useEffect } from 'react';
import {
    LayoutDashboard,
    Users,
    Calendar,
    AlertTriangle,
    CheckCircle,
    ChevronRight,
    Target,
    Activity,
    Wallet,
    Plane,
    Building2,
    DollarSign
} from 'lucide-react';
import { hrReportingService } from '../../services/hrReporting.service';
import type { DashboardOverview, DailyAttendanceResponse } from '../../types';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { Link } from 'react-router-dom';
import { clsx } from 'clsx';

export function HRConsolePage() {
    const [overview, setOverview] = useState<DashboardOverview | null>(null);
    const [dailyStatus, setDailyStatus] = useState<DailyAttendanceResponse | null>(null);
    const [compliance, setCompliance] = useState<any | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const toast = useToast();

    useEffect(() => {
        loadAllData();
    }, []);

    const loadAllData = async () => {
        setIsLoading(true);
        try {
            const [overviewData, dailyData, complianceData] = await Promise.all([
                hrReportingService.getDashboardOverview(),
                hrReportingService.getDailyAttendance(new Date().toISOString().split('T')[0]),
                hrReportingService.getComplianceReport()
            ]);
            setOverview(overviewData);
            setDailyStatus(dailyData);
            setCompliance(complianceData);
        } catch (error) {
            console.error('Dashboard load error:', error);
            toast.error('Errore nel caricamento della dashboard');
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh]">
                <div className="animate-spin text-slate-800 mb-4">
                    <LayoutDashboard size={40} />
                </div>
                <p className="text-slate-500 font-medium">Caricamento Hub Aziendale...</p>
            </div>
        );
    }

    if (!overview) return null;

    const { workforce, alerts, pending_approvals } = overview;
    const absentees = dailyStatus?.items.filter(i => !i.status.includes('Presente')) || [];
    const trips = dailyStatus?.items.filter(i => i.status.includes('Trasferta')) || [];

    return (
        <div className="space-y-6 animate-fadeIn pb-12">
            {/* Enterprise Header */}
            <div className="relative overflow-hidden rounded-xl bg-white p-8 shadow-sm border border-slate-200">
                <div className="absolute top-0 right-0 p-8 opacity-5">
                    <Building2 size={240} className="text-slate-900" />
                </div>

                <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-slate-100 rounded-lg text-slate-700">
                                <Building2 size={24} />
                            </div>
                            <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                                Operational Hub
                            </h1>
                        </div>
                        <p className="text-slate-500 font-medium flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            Operatività Aziendale &bull; {format(new Date(), "EEEE d MMMM yyyy", { locale: it })}
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <Button variant="secondary" onClick={loadAllData} className="bg-white border-slate-200 text-slate-700 hover:bg-slate-50">
                            <Activity size={16} className="mr-2" />
                            Sync Dati
                        </Button>
                        <Link to="/hr/reports">
                            <Button variant="primary" className="bg-slate-900 hover:bg-slate-800 shadow-xl shadow-slate-200 text-white">
                                Reportistica
                                <ChevronRight size={16} className="ml-1" />
                            </Button>
                        </Link>
                    </div>
                </div>

                {/* Quick Stats Row */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-8 pt-8 border-t border-slate-100">
                    <StatItem
                        label="Forza Lavoro"
                        value={workforce?.total_employees}
                        sub="Dipendenti Totali"
                        trend={null}
                    />
                    <StatItem
                        label="Presenza Odierna"
                        value={workforce?.active_now}
                        sub={`${workforce?.absence_rate}% tasso assenza`}
                        trend={workforce?.active_now && workforce.total_employees ? Math.round((workforce.active_now / workforce.total_employees) * 100) : 0}
                        trendPositive={true}
                    />
                    <StatItem
                        label="In Trasferta"
                        value={trips.length}
                        sub="Missioni attive"
                        icon={<Plane size={14} className="text-sky-500" />}
                    />
                    <StatItem
                        label="Budget Mese"
                        value="€ 45.2k"
                        sub="Previsione spesa"
                        icon={<DollarSign size={14} className="text-emerald-500" />}
                        valueColor="text-emerald-700"
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Main Operations Column (2/3) */}
                <div className="lg:col-span-2 space-y-6">

                    {/* Who is Where Widget (Transparency) */}
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                            <h2 className="font-bold text-slate-800 flex items-center gap-2">
                                <Users size={18} className="text-slate-500" />
                                Stato Personale Oggi
                            </h2>
                            <Link to="/hr/reports" className="text-xs font-bold text-emerald-600 hover:text-emerald-700">
                                Vedi Report Completo &rarr;
                            </Link>
                        </div>

                        <div className="p-0">
                            {absentees.length === 0 && trips.length === 0 ? (
                                <div className="p-8 text-center text-slate-400">
                                    <CheckCircle size={48} className="mx-auto text-emerald-100 mb-2" />
                                    <p className="font-medium text-emerald-700">Tutti presenti in sede!</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-slate-50">
                                    {trips.map(trip => (
                                        <div key={trip.user_id} className="px-6 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-sky-100 flex items-center justify-center text-sky-700 text-xs font-bold ring-2 ring-white">
                                                    {(trip.full_name || '??').substring(0, 2)}
                                                </div>
                                                <div>
                                                    <p className="text-sm font-bold text-slate-900">{trip.full_name}</p>
                                                    <p className="text-xs text-sky-600 font-medium flex items-center gap-1">
                                                        <Plane size={10} /> In Missione
                                                    </p>
                                                </div>
                                            </div>
                                            <span className="text-xs font-medium bg-sky-50 text-sky-700 px-2.5 py-1 rounded-full border border-sky-100">
                                                Trasferta
                                            </span>
                                        </div>
                                    ))}
                                    {absentees.filter(a => !a.status.includes('Trasferta')).map(absentee => (
                                        <div key={absentee.user_id} className="px-6 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center text-amber-700 text-xs font-bold ring-2 ring-white">
                                                    {(absentee.full_name || '??').substring(0, 2)}
                                                </div>
                                                <div>
                                                    <p className="text-sm font-bold text-slate-900">{absentee.full_name}</p>
                                                    <p className="text-xs text-amber-600 font-medium">
                                                        {absentee.department || 'N/A'}
                                                    </p>
                                                </div>
                                            </div>
                                            <span className={clsx(
                                                "text-xs font-medium px-2.5 py-1 rounded-full border",
                                                absentee.status.includes('Malattia')
                                                    ? "bg-rose-50 text-rose-700 border-rose-100"
                                                    : "bg-amber-50 text-amber-700 border-amber-100"
                                            )}>
                                                {absentee.status}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Pending Approvals (Enterprise Style) */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Link to="/leaves" className="group p-5 bg-white border border-slate-200 rounded-xl hover:border-emerald-500 hover:shadow-md transition-all">
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                                    <Calendar size={20} />
                                </div>
                                {(pending_approvals?.leave_requests ?? 0) > 0 && (
                                    <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-2 py-1 rounded-full">
                                        {pending_approvals?.leave_requests}
                                    </span>
                                )}
                            </div>
                            <h3 className="font-bold text-slate-900 mb-1">Approvazione Ferie</h3>
                            <p className="text-xs text-slate-500">Gestione piano ferie e permessi</p>
                        </Link>

                        <Link to="/expenses" className="group p-5 bg-white border border-slate-200 rounded-xl hover:border-sky-500 hover:shadow-md transition-all">
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-2 bg-sky-50 text-sky-600 rounded-lg group-hover:bg-sky-600 group-hover:text-white transition-colors">
                                    <Wallet size={20} />
                                </div>
                                {(pending_approvals?.expense_reports ?? 0) > 0 && (
                                    <span className="bg-sky-100 text-sky-800 text-xs font-bold px-2 py-1 rounded-full">
                                        {pending_approvals?.expense_reports}
                                    </span>
                                )}
                            </div>
                            <h3 className="font-bold text-slate-900 mb-1">Note Spese</h3>
                            <p className="text-xs text-slate-500">Rimborsi e budget missioni</p>
                        </Link>
                    </div>

                </div>

                {/* Sidebar Column (1/3) */}
                <div className="space-y-6">

                    {/* Alerts Widget */}
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
                            <h2 className="font-bold text-slate-800 flex items-center gap-2">
                                <AlertTriangle size={18} className="text-slate-500" />
                                Avvisi Strategici
                            </h2>
                            {(alerts?.length ?? 0) > 0 && (
                                <span className="bg-rose-100 text-rose-700 text-xs font-bold px-2 py-0.5 rounded-full animate-pulse">
                                    {alerts?.length}
                                </span>
                            )}
                        </div>
                        <div className="p-0">
                            {(!alerts || alerts.length === 0) ? (
                                <div className="p-8 text-center">
                                    <p className="text-sm text-slate-400">Nessuna criticità rilevata.</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-slate-50">
                                    {alerts.slice(0, 5).map(alert => (
                                        <div key={alert.id} className="p-4 hover:bg-slate-50 transition-colors border-l-4 border-rose-500 bg-rose-50/10">
                                            <h4 className="text-sm font-bold text-slate-900">{alert.title}</h4>
                                            <p className="text-xs text-slate-600 mt-1">{alert.description}</p>
                                            {alert.employee_name && (
                                                <div className="mt-2 flex items-center gap-1 text-[10px] text-slate-400 font-medium uppercase tracking-wide">
                                                    <Users size={10} /> {alert.employee_name}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Compliance Mini-Card */}
                    <div className="bg-slate-900 rounded-xl p-6 text-white relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-8 opacity-10">
                            <Target size={100} />
                        </div>
                        <div className="relative z-10">
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Compliance</h3>
                            <div className="flex items-end justify-between mb-4">
                                <div>
                                    <span className="text-4xl font-black">{compliance?.statistics?.compliance_rate ?? 100}%</span>
                                    <p className="text-xs text-emerald-400 font-bold mt-1">Score Aziendale</p>
                                </div>
                                <div className={clsx(
                                    "p-2 rounded-lg",
                                    compliance?.compliance_status === 'OK' ? "bg-emerald-500/20 text-emerald-400" : "bg-amber-500/20 text-amber-400"
                                )}>
                                    {compliance?.compliance_status === 'OK' ? <CheckCircle size={24} /> : <AlertTriangle size={24} />}
                                </div>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between text-xs">
                                    <span className="text-slate-400">Dipendenti OK</span>
                                    <span className="font-bold">{compliance?.statistics?.employees_compliant ?? 0}</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                    <span className="text-slate-400">A Rischio</span>
                                    <span className="font-bold text-amber-400">{compliance?.statistics?.employees_at_risk ?? 0}</span>
                                </div>
                                <div className="w-full bg-slate-800 rounded-full h-1 mt-3">
                                    <div
                                        className="bg-emerald-500 h-1 rounded-full transition-all duration-1000"
                                        style={{ width: `${compliance?.statistics?.compliance_rate ?? 100}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}

function StatItem({ label, value, sub, icon, valueColor = "text-slate-900", trend, trendPositive }: any) {
    return (
        <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">{label}</p>
            <div className="flex items-center gap-2">
                <span className={`text-2xl font-black ${valueColor}`}>{value ?? '-'}</span>
                {icon && <span className="opacity-80">{icon}</span>}
            </div>
            <div className="flex items-center gap-2 mt-1">
                {trend !== null && trend !== undefined && (
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-sm ${trendPositive ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                        {trend}%
                    </span>
                )}
                <span className="text-[11px] font-medium text-slate-500 truncate max-w-[120px]" title={sub}>
                    {sub}
                </span>
            </div>
        </div>
    );
}

export default HRConsolePage;

