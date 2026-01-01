/**
 * KRONOS - Approvals Management Page
 * Enterprise approval workflow interface
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import {
    Calendar,
    MapPin,
    FileText,
    Clock,
    CheckCircle,
    ArrowRight,
    Loader,
    User
} from 'lucide-react';
import { usePendingApprovals, usePendingTrips, usePendingReports } from '../hooks/useApi';
import type { LeaveRequest, BusinessTrip, ExpenseReport } from '../types';

type TabType = 'leaves' | 'trips' | 'expenses';

export function ApprovalsPage() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<TabType>('leaves');

    // Fetch data
    const { data: pendingLeaves, isLoading: loadingLeaves } = usePendingApprovals();
    const { data: pendingTrips, isLoading: loadingTrips } = usePendingTrips();
    const { data: pendingReports, isLoading: loadingReports } = usePendingReports();

    // Calculate counts
    const leavesCount = pendingLeaves?.length || 0;
    const tripsCount = pendingTrips?.length || 0;
    const reportsCount = pendingReports?.length || 0;
    const totalCount = leavesCount + tripsCount + reportsCount;

    const tabs = [
        { key: 'leaves' as TabType, label: 'Ferie e Permessi', icon: Calendar, count: leavesCount, color: 'from-indigo-500 to-purple-500' },
        { key: 'trips' as TabType, label: 'Trasferte', icon: MapPin, count: tripsCount, color: 'from-cyan-500 to-blue-500' },
        { key: 'expenses' as TabType, label: 'Note Spese', icon: FileText, count: reportsCount, color: 'from-emerald-500 to-green-500' },
    ];

    return (
        <div className="space-y-6 animate-fadeIn max-w-[1400px] mx-auto pb-8">
            {/* Enterprise Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Centro Approvazioni</h1>
                    <p className="text-sm text-gray-500 mt-1">Valuta e gestisci tutte le richieste del tuo team.</p>
                </div>

                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200 text-amber-700">
                        <span className="text-sm font-semibold">In Attesa:</span>
                        <span className="text-sm font-bold">{totalCount}</span>
                    </div>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="border-b border-gray-200">
                <div className="flex gap-6">
                    {tabs.map(tab => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={`group flex items-center gap-2 pb-3 border-b-2 transition-colors ${activeTab === tab.key
                                ? 'border-primary text-primary'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            <tab.icon size={18} />
                            <span className="font-medium text-sm">{tab.label}</span>
                            {tab.count > 0 && (
                                <span className={`ml-1 px-2 py-0.5 rounded-full text-xs font-bold ${activeTab === tab.key ? 'bg-primary/10 text-primary' : 'bg-gray-100 text-gray-600'
                                    }`}>
                                    {tab.count}
                                </span>
                            )}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content */}
            <div className="min-h-[400px]">
                {activeTab === 'leaves' && (
                    <LeavesApprovalsList requests={pendingLeaves} isLoading={loadingLeaves} navigate={navigate} />
                )}
                {activeTab === 'trips' && (
                    <TripsApprovalsList trips={pendingTrips} isLoading={loadingTrips} navigate={navigate} />
                )}
                {activeTab === 'expenses' && (
                    <ReportsApprovalsList reports={pendingReports} isLoading={loadingReports} navigate={navigate} />
                )}
            </div>
        </div>
    );
}

// Sub-components for lists
function LeavesApprovalsList({ requests, isLoading, navigate }: { requests: LeaveRequest[] | undefined; isLoading: boolean; navigate: (path: string) => void }) {
    if (isLoading) return <LoadingState />;

    const list = requests || [];
    if (list.length === 0) return <EmptyState label="Nessuna richiesta ferie in attesa" icon={Calendar} color="gray" />;

    return (
        <div className="grid gap-4">
            {list.map((req) => (
                <div
                    key={req.id}
                    onClick={() => navigate(`/leaves/${req.id}`)}
                    className="group flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-white rounded-lg border border-gray-200 hover:border-primary/50 hover:shadow-sm transition-all cursor-pointer"
                >
                    <div className="flex items-start gap-4">
                        <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-lg">
                            <Calendar size={24} />
                        </div>
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <h3 className="text-lg font-bold text-gray-900">{getLeaveTypeName(req.leave_type_code)}</h3>
                                <span className="px-2 py-0.5 rounded text-[0.65rem] font-bold uppercase bg-amber-50 text-amber-700 border border-amber-100">
                                    In Attesa
                                </span>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-gray-500">
                                <span className="flex items-center gap-1.5">
                                    <User size={14} />
                                    {req.user_id?.substring(0, 8)}...
                                </span>
                                <span className="flex items-center gap-1.5">
                                    <Calendar size={14} />
                                    {format(new Date(req.start_date), 'd MMM', { locale: it })} - {format(new Date(req.end_date), 'd MMM yyyy', { locale: it })}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center justify-between md:justify-end gap-6 pl-14 md:pl-0 border-t md:border-0 border-gray-100 pt-3 md:pt-0">
                        <div className="text-right">
                            <span className="block text-2xl font-bold text-gray-900">{req.days_requested}</span>
                            <span className="text-xs text-gray-400 uppercase font-semibold">Giorni</span>
                        </div>
                        <div className="hidden md:flex items-center gap-1 text-primary text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                            Valuta <ArrowRight size={16} />
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

function TripsApprovalsList({ trips, isLoading, navigate }: { trips: BusinessTrip[] | undefined; isLoading: boolean; navigate: (path: string) => void }) {
    if (isLoading) return <LoadingState />;

    const list = trips || [];
    if (list.length === 0) return <EmptyState label="Nessuna trasferta in attesa" icon={MapPin} color="gray" />;

    return (
        <div className="grid gap-4">
            {list.map((trip) => (
                <div
                    key={trip.id}
                    onClick={() => navigate(`/trips/${trip.id}`)}
                    className="group flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-white rounded-lg border border-gray-200 hover:border-primary/50 hover:shadow-sm transition-all cursor-pointer"
                >
                    <div className="flex items-start gap-4">
                        <div className="p-2.5 bg-cyan-50 text-cyan-600 rounded-lg">
                            <MapPin size={24} />
                        </div>
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <h3 className="text-lg font-bold text-gray-900">{trip.destination}</h3>
                                <span className="px-2 py-0.5 rounded text-[0.65rem] font-bold uppercase bg-amber-50 text-amber-700 border border-amber-100">
                                    In Attesa
                                </span>
                            </div>
                            <div className="text-sm text-gray-500 mb-2 line-clamp-1">{trip.purpose}</div>
                            <div className="flex items-center gap-4 text-sm text-gray-400">
                                <span className="flex items-center gap-1.5">
                                    <Calendar size={14} />
                                    {format(new Date(trip.start_date), 'd MMM', { locale: it })} - {format(new Date(trip.end_date), 'd MMM yyyy', { locale: it })}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center justify-between md:justify-end gap-6 pl-14 md:pl-0 border-t md:border-0 border-gray-100 pt-3 md:pt-0">
                        {trip.estimated_budget && (
                            <div className="text-right">
                                <span className="block text-xl font-bold text-gray-900">€{Number(trip.estimated_budget).toLocaleString('it-IT', { minimumFractionDigits: 2 })}</span>
                                <span className="text-xs text-gray-400 uppercase font-semibold">Stimati</span>
                            </div>
                        )}
                        <div className="hidden md:flex items-center gap-1 text-primary text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                            Valuta <ArrowRight size={16} />
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

function ReportsApprovalsList({ reports, isLoading, navigate }: { reports: ExpenseReport[] | undefined; isLoading: boolean; navigate: (path: string) => void }) {
    if (isLoading) return <LoadingState />;

    const list = reports || [];
    if (list.length === 0) return <EmptyState label="Nessuna nota spese in attesa" icon={FileText} color="gray" />;

    return (
        <div className="grid gap-4">
            {list.map((report) => (
                <div
                    key={report.id}
                    onClick={() => navigate(`/expenses/${report.id}`)}
                    className="group flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-white rounded-lg border border-gray-200 hover:border-primary/50 hover:shadow-sm transition-all cursor-pointer"
                >
                    <div className="flex items-start gap-4">
                        <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg">
                            <FileText size={24} />
                        </div>
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <h3 className="text-lg font-bold text-gray-900">{report.title}</h3>
                                <span className="px-2 py-0.5 rounded text-[0.65rem] font-bold uppercase bg-amber-50 text-amber-700 border border-amber-100">
                                    In Attesa
                                </span>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-gray-500">
                                <span className="flex items-center gap-1.5">
                                    <Clock size={14} />
                                    Creata il {format(new Date(report.created_at), 'd MMM yyyy', { locale: it })}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center justify-between md:justify-end gap-6 pl-14 md:pl-0 border-t md:border-0 border-gray-100 pt-3 md:pt-0">
                        <div className="text-right">
                            <span className="block text-xl font-bold text-gray-900">€{Number(report.total_amount).toLocaleString('it-IT', { minimumFractionDigits: 2 })}</span>
                            <span className="text-xs text-gray-400 uppercase font-semibold">Totale</span>
                        </div>
                        <div className="hidden md:flex items-center gap-1 text-primary text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                            Valuta <ArrowRight size={16} />
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

function LoadingState() {
    return (
        <div className="flex flex-col items-center justify-center p-16 gap-4">
            <Loader size={48} className="animate-spin text-primary" />
            <span className="text-sm font-black uppercase tracking-widest text-base-content/30">Caricamento...</span>
        </div>
    );
}

function EmptyState({ label, icon: Icon, color }: { label: string; icon: any; color: string }) {
    return (
        <div className="flex flex-col items-center justify-center p-16 text-center">
            <div className={`p-8 rounded-full bg-${color}-500/10 mb-6`}>
                <Icon size={64} className={`text-${color}-500/30`} />
            </div>
            <h3 className="text-2xl font-black tracking-tight text-base-content/80">{label}</h3>
            <p className="text-base-content/40 mt-2">Non ci sono elementi da approvare al momento.</p>
            <div className="flex items-center gap-2 mt-6 text-emerald-500">
                <CheckCircle size={20} />
                <span className="font-bold">Tutto in ordine!</span>
            </div>
        </div>
    );
}

function getLeaveTypeName(code: string): string {
    const types: Record<string, string> = {
        'FER': 'Ferie',
        'ROL': 'ROL - Riduzione Orario',
        'PER': 'Permessi Ex Festività',
        'MAL': 'Malattia',
        'LUT': 'Lutto',
        'MAT': 'Matrimonio',
        'L104': 'Legge 104',
        'DON': 'Donazione Sangue',
    };
    return types[code] || code;
}

export default ApprovalsPage;
