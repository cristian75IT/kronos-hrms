import { useState, useEffect } from 'react';
import {
    LayoutDashboard,
    Users,
    Calendar,
    AlertTriangle,
    CheckCircle,
    Briefcase,
    TrendingDown,
    Clock,
    FileText,
    Info,
    X
} from 'lucide-react';
import { hrReportingService } from '../../services/hrReporting.service';
import type { DashboardOverview } from '../../types';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { Link } from 'react-router-dom';

export function HRConsolePage() {
    const [overview, setOverview] = useState<DashboardOverview | null>(null);
    const [compliance, setCompliance] = useState<any | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [showComplianceModal, setShowComplianceModal] = useState(false);
    const toast = useToast();

    useEffect(() => {
        loadDashboard();
        loadCompliance();
    }, []);

    const loadCompliance = async () => {
        try {
            const data = await hrReportingService.getComplianceReport();
            setCompliance(data);
        } catch (error) {
            console.error('Compliance error:', error);
        }
    };

    const loadDashboard = async () => {
        setIsLoading(true);
        try {
            const data = await hrReportingService.getDashboardOverview();
            setOverview(data);
        } catch (error) {
            console.error(error);
            toast.error('Errore nel caricamento della dashboard HR');
        } finally {
            setIsLoading(false);
        }
    };

    const handleAcknowledgeAlert = async (id: string) => {
        try {
            await hrReportingService.acknowledgeAlert(id);
            toast.success('Alert preso in carico');
            loadDashboard(); // Reload to update UI
        } catch (error) {
            toast.error('Errore durante l\'aggiornamento dell\'alert');
        }
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh]">
                <div className="animate-spin text-indigo-600 mb-4">
                    <LayoutDashboard size={40} />
                </div>
                <p className="text-gray-500 font-medium">Caricamento Console HR...</p>
            </div>
        );
    }

    if (!overview) return null;

    const { workforce, alerts, pending_approvals } = overview;

    return (
        <div className="space-y-6 animate-fadeIn pb-12">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <LayoutDashboard className="text-indigo-600" />
                        Console HR
                    </h1>
                    <p className="text-sm text-gray-500">Panoramica in tempo reale e gestione operativa</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="secondary" onClick={loadDashboard}>
                        Aggiorna
                    </Button>
                    <Link to="/hr/reports">
                        <Button variant="primary">
                            Visualizza Report
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Quick Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <DashboardCard
                    title="Forza Lavoro (Live)"
                    value={workforce?.active_now ?? 0}
                    subtitle={`Su ${workforce?.total_employees ?? 0} dipendenti totali`}
                    icon={<Users className="text-blue-600" />}
                    color="bg-blue-50"
                />
                <DashboardCard
                    title="Assenti Oggi"
                    value={(workforce?.on_leave ?? 0) + (workforce?.sick_leave ?? 0)}
                    subtitle={`${workforce?.sick_leave ?? 0} in malattia`}
                    icon={<Calendar className="text-orange-600" />}
                    color="bg-orange-50"
                />
                <DashboardCard
                    title="In Trasferta"
                    value={workforce?.on_trip ?? 0}
                    subtitle="Attualmente in missione"
                    icon={<Briefcase className="text-purple-600" />}
                    color="bg-purple-50"
                />
                <DashboardCard
                    title="Tasso Assenze"
                    value={`${workforce?.absence_rate ?? 0}%`}
                    subtitle="Media ultimi 30 giorni"
                    icon={<TrendingDown className="text-green-600" />}
                    color="bg-green-50"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Main Content Column (2/3) */}
                <div className="lg:col-span-2 space-y-6">

                    {/* Alerts Section */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                            <h2 className="font-bold text-gray-900 flex items-center gap-2">
                                <AlertTriangle className="text-amber-500" size={18} />
                                Avvisi e Scadenze
                            </h2>
                            <span className="bg-amber-100 text-amber-800 text-xs font-bold px-2 py-0.5 rounded-full">
                                {alerts?.length ?? 0} Attivi
                            </span>
                        </div>
                        <div className="divide-y divide-gray-50">
                            {(!alerts || alerts.length === 0) ? (
                                <div className="p-8 text-center text-gray-400 italic">
                                    Nessun avviso attivo. Tutto tranquillo!
                                </div>
                            ) : (
                                alerts.map(alert => (
                                    <div key={alert.id} className="p-4 hover:bg-gray-50 transition-colors flex items-start gap-4">
                                        <div className={`mt-1 p-1.5 rounded-md shrink-0 ${alert.severity === 'critical' ? 'bg-red-100 text-red-600' :
                                            alert.severity === 'warning' ? 'bg-amber-100 text-amber-600' :
                                                'bg-blue-100 text-blue-600'
                                            }`}>
                                            <AlertTriangle size={16} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex justify-between items-start">
                                                <h3 className="text-sm font-bold text-gray-900">{alert.title}</h3>
                                                <span className="text-[10px] text-gray-400">
                                                    {format(new Date(alert.created_at), 'd MMM', { locale: it })}
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-600 mt-0.5">{alert.description}</p>
                                            {alert.employee_name && (
                                                <div className="mt-2 flex items-center gap-2">
                                                    <span className="bg-gray-100 text-gray-600 text-[10px] font-medium px-1.5 py-0.5 rounded flex items-center gap-1">
                                                        <Users size={10} /> {alert.employee_name}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                        {alert.action_required && !alert.is_acknowledged && (
                                            <button
                                                onClick={() => handleAcknowledgeAlert(alert.id)}
                                                className="self-center px-3 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg border border-transparent hover:border-indigo-200 transition-all"
                                            >
                                                Presa visione
                                            </button>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Actions / Quick Links */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Link to="/leaves" className="group p-4 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all hover:border-indigo-300">
                            <h3 className="font-bold text-gray-900 mb-1 group-hover:text-indigo-600 transition-colors">Gestione ferie</h3>
                            <p className="text-xs text-gray-500">Approva richieste e controlla piani ferie</p>
                        </Link>
                        <Link to="/expenses" className="group p-4 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all hover:border-indigo-300">
                            <h3 className="font-bold text-gray-900 mb-1 group-hover:text-indigo-600 transition-colors">Note spese</h3>
                            <p className="text-xs text-gray-500">Verifica budget e approva rimborsi</p>
                        </Link>
                        <Link to="/admin/users" className="group p-4 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all hover:border-indigo-300">
                            <h3 className="font-bold text-gray-900 mb-1 group-hover:text-indigo-600 transition-colors">Anagrafica</h3>
                            <p className="text-xs text-gray-500">Gestisci contratti e dipendenti</p>
                        </Link>
                    </div>

                </div>

                {/* Sidebar Column (1/3) */}
                <div className="space-y-6">

                    {/* Pending Approvals Widget */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
                            <h2 className="font-bold text-gray-900 flex items-center gap-2">
                                <Clock className="text-indigo-600" size={18} />
                                In Attesa
                            </h2>
                        </div>
                        <div className="p-4 space-y-3">
                            <ApprovalItem
                                label="Richieste Ferie"
                                count={pending_approvals?.leave_requests ?? 0}
                                icon={<Calendar size={14} />}
                                href="/leaves"
                            />
                            <ApprovalItem
                                label="Note Spese"
                                count={pending_approvals?.expense_reports ?? 0}
                                icon={<FileText size={14} />}
                                href="/expenses"
                            />
                            <ApprovalItem
                                label="Missioni"
                                count={pending_approvals?.trip_requests ?? 0}
                                icon={<Briefcase size={14} />}
                                href="/trips" // Assuming trips page exists or redirect to relevant page
                            />
                        </div>
                        {/* Oldest request logic removed as not currently supported by backend */}
                    </div>

                    {/* Compliance Widget */}
                    <div className="bg-gradient-to-br from-indigo-900 to-indigo-800 rounded-xl shadow-sm p-6 text-white overflow-hidden relative group">
                        <div className="absolute -right-6 -top-6 text-white/5 group-hover:text-white/10 transition-colors">
                            <CheckCircle size={120} />
                        </div>

                        <div className="relative z-10">
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-2 bg-white/10 rounded-lg backdrop-blur-sm">
                                    <CheckCircle size={20} className={
                                        compliance?.compliance_status === 'OK' ? 'text-emerald-400' :
                                            compliance?.compliance_status === 'WARNING' ? 'text-amber-400' : 'text-red-400'
                                    } />
                                </div>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${compliance?.compliance_status === 'OK' ? 'border-emerald-400/30 text-emerald-400 bg-emerald-400/10' :
                                    compliance?.compliance_status === 'WARNING' ? 'border-amber-400/30 text-amber-400 bg-amber-400/10' :
                                        'border-red-400/30 text-red-400 bg-red-400/10'
                                    }`}>
                                    {compliance?.compliance_status || 'CHECKING...'}
                                </span>
                            </div>

                            <h3 className="font-bold text-lg mb-1">Compliance HR</h3>
                            <p className="text-indigo-200 text-sm mb-4">
                                {compliance?.period ? `Monitoraggio ${compliance.period}` : 'Verifica periodica'}
                            </p>

                            <div className="grid grid-cols-2 gap-3 mb-6">
                                <div className="bg-white/5 p-3 rounded-xl border border-white/10">
                                    <span className="block text-2xl font-black">{compliance?.statistics?.compliance_rate ?? 0}%</span>
                                    <span className="text-[10px] text-indigo-300 uppercase font-bold tracking-wider">Generale</span>
                                </div>
                                <div className="bg-white/5 p-3 rounded-xl border border-white/10">
                                    <span className="block text-2xl font-black">{compliance?.issues?.length ?? 0}</span>
                                    <span className="text-[10px] text-indigo-300 uppercase font-bold tracking-wider">Criticità</span>
                                </div>
                            </div>

                            <button
                                onClick={() => setShowComplianceModal(true)}
                                className="w-full py-2.5 bg-white text-indigo-900 rounded-lg text-sm font-bold shadow-lg shadow-black/20 hover:bg-indigo-50 transition-all flex items-center justify-center gap-2"
                            >
                                Visualizza Dettagli
                                <Info size={14} />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Compliance Detail Modal */}
            {showComplianceModal && compliance && (
                <ComplianceDetailModal
                    data={compliance}
                    onClose={() => setShowComplianceModal(false)}
                />
            )}
        </div>
    );
}

function ComplianceDetailModal({ data, onClose }: { data: any, onClose: () => void }) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
            <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-scaleIn">
                <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                    <div>
                        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                            <CheckCircle className="text-indigo-600" size={20} />
                            Dettaglio Controlli Compliance
                        </h2>
                        <p className="text-sm text-gray-500">Periodo {data.period}</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-full transition-colors">
                        <X size={20} className="text-gray-500" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-8">
                    {/* Checks Grid */}
                    <section>
                        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4">Stato Regole Aziendali</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {data.checks?.map((check: any) => (
                                <div key={check.id} className="p-4 rounded-xl border border-gray-100 bg-gray-50/50 hover:border-indigo-100 transition-colors">
                                    <div className="flex justify-between items-start mb-2">
                                        <h4 className="font-bold text-gray-900">{check.name}</h4>
                                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${check.status === 'PASS' ? 'bg-emerald-100 text-emerald-700' :
                                            check.status === 'WARN' ? 'bg-amber-100 text-amber-700' :
                                                'bg-red-100 text-red-700'
                                            }`}>
                                            {check.status === 'PASS' ? 'OK' : check.status}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-600 mb-3">{check.description}</p>
                                    <div className="flex justify-between items-center pt-3 border-t border-gray-100">
                                        <span className="text-xs text-gray-400">Risultato:</span>
                                        <span className="text-sm font-bold text-indigo-600">{check.result_value}</span>
                                    </div>
                                    {check.details && check.details.length > 0 && (
                                        <ul className="mt-3 space-y-1">
                                            {check.details.map((d: string, idx: number) => (
                                                <li key={idx} className="text-[10px] text-orange-600 bg-orange-50 px-2 py-1 rounded flex items-center gap-1">
                                                    <AlertTriangle size={10} /> {d}
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* Critical Issues */}
                    <section>
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest">Segnalazioni per Dipendente</h3>
                            <span className="text-xs font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-full border border-red-100">
                                {data.issues?.length || 0} Anomalie
                            </span>
                        </div>

                        {data.issues?.length === 0 ? (
                            <div className="text-center py-10 bg-emerald-50 rounded-2xl border-2 border-dashed border-emerald-100 text-emerald-600 italic">
                                Nessuna anomalia rilevata per il personale nell'attuale monitoraggio.
                            </div>
                        ) : (
                            <div className="overflow-hidden border border-gray-200 rounded-xl shadow-sm">
                                <table className="w-full text-left">
                                    <thead className="bg-gray-50 border-b border-gray-200">
                                        <tr>
                                            <th className="px-4 py-3 text-xs font-bold text-gray-500 uppercase">Dipendente</th>
                                            <th className="px-4 py-3 text-xs font-bold text-gray-500 uppercase">Oggetto</th>
                                            <th className="px-4 py-3 text-xs font-bold text-gray-500 uppercase">Gravità</th>
                                            <th className="px-4 py-3 text-xs font-bold text-gray-500 uppercase">Dettaglio</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {data.issues.map((issue: any, idx: number) => (
                                            <tr key={idx} className="hover:bg-gray-50 transition-colors">
                                                <td className="px-4 py-3">
                                                    <span className="text-sm font-bold text-gray-900">{issue.employee_name}</span>
                                                </td>
                                                <td className="px-4 py-3">
                                                    <span className="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-1 rounded">
                                                        {issue.type}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3">
                                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${issue.severity === 'critical' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                                                        }`}>
                                                        {issue.severity.toUpperCase()}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 text-sm text-gray-600">
                                                    {issue.description}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>
                </div>

                <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end">
                    <Button variant="primary" onClick={onClose}>
                        Ho Capito
                    </Button>
                </div>
            </div>
        </div>
    );
}

function DashboardCard({ title, value, subtitle, icon, color }: any) {
    return (
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 flex items-start gap-4 hover:shadow-md transition-shadow">
            <div className={`p-3 rounded-xl shrink-0 ${color}`}>
                {icon}
            </div>
            <div>
                <p className="text-xs font-bold text-gray-400 uppercase tracking-wide mb-1">{title}</p>
                <h3 className="text-2xl font-black text-gray-900 leading-none mb-1">{value}</h3>
                <p className="text-[10px] text-gray-500 font-medium">{subtitle}</p>
            </div>
        </div>
    );
}

function ApprovalItem({ label, count, icon, href }: any) {
    return (
        <Link to={href} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors group">
            <div className="flex items-center gap-3">
                <div className="text-gray-400 group-hover:text-indigo-600 transition-colors">
                    {icon}
                </div>
                <span className="text-sm font-medium text-gray-700">{label}</span>
            </div>
            {count > 0 ? (
                <span className="bg-indigo-100 text-indigo-700 text-xs font-bold px-2 py-0.5 rounded-full">
                    {count}
                </span>
            ) : (
                <span className="text-gray-300 text-xs">0</span>
            )}
        </Link>
    );
}

export default HRConsolePage;
