/**
 * KRONOS - Expense Reports Page
 * Enterprise expense management interface - Data Table View
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useStandaloneReports } from '../../hooks/domain/useExpenses';
import {
    Plus,
    AlertCircle,
    Receipt,
    ArrowRight,
    RefreshCw,
    Calendar,
    Search,
    Info,
    CheckCircle2,
    XCircle,
    Clock,
    FileText
} from 'lucide-react';
import { format, isValid } from 'date-fns';
import { it } from 'date-fns/locale';

// Safe date formatter helper
const safeFormat = (dateStr: string | undefined | null, formatStr: string) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    return isValid(date) ? format(date, formatStr, { locale: it }) : null;
};

export function ExpensesPage() {
    const navigate = useNavigate();
    const [statusFilter, setStatusFilter] = useState<string>('');
    const { data: reports, isLoading, error, refetch } = useStandaloneReports(statusFilter || undefined);

    // Stats calculation
    const stats = {
        total: reports?.length || 0,
        pending: reports?.filter(r => r.status === 'submitted').length || 0,
        paid: reports?.filter(r => r.status === 'paid').length || 0,
        totalAmount: reports?.reduce((sum, r) => sum + (Number(r.total_amount) || 0), 0) || 0,
        paidAmount: reports?.filter(r => r.status === 'paid').reduce((sum, r) => sum + (Number(r.approved_amount || r.total_amount) || 0), 0) || 0,
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center p-32 gap-6">
                <div className="relative">
                    <div className="w-20 h-20 border-4 border-slate-200 border-t-emerald-600 rounded-full animate-spin" />
                    <Receipt className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-emerald-600" size={32} />
                </div>
                <p className="text-sm font-bold uppercase tracking-widest text-slate-400 animate-pulse">Caricamento...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center p-12 gap-6 bg-red-50/50 border border-red-100 rounded-3xl text-center max-w-2xl mx-auto mt-12">
                <div className="p-4 bg-white rounded-2xl shadow-sm border border-red-100">
                    <AlertCircle size={48} className="text-red-500" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-slate-900">Errore di Connessione</h2>
                    <p className="text-slate-500 mt-2">Impossibile recuperare le note spese. Verifica la connessione.</p>
                </div>
                <button className="btn bg-white hover:bg-slate-50 text-slate-900 border border-slate-200 shadow-sm rounded-xl px-6" onClick={() => refetch()}>
                    <RefreshCw size={18} className="mr-2" /> Riprova
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-fadeIn max-w-[1600px] mx-auto pb-12">
            {/* Enterprise Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-slate-200">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-emerald-100 rounded-lg text-emerald-700">
                            <Receipt size={24} />
                        </div>
                        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Note Spese</h1>
                    </div>
                    <p className="text-slate-500 max-w-2xl">
                        Gestisci le tue richieste di rimborso spese. Monitora lo stato di approvazione e visualizza lo storico dei pagamenti con la massima trasparenza.
                    </p>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex items-center gap-4 px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl">
                        <div className="text-right">
                            <div className="text-[10px] uppercase tracking-wider font-bold text-slate-400">Totale Richiesto</div>
                            <div className="text-lg font-bold text-slate-900">€{stats.totalAmount.toLocaleString('it-IT', { minimumFractionDigits: 2 })}</div>
                        </div>
                        <div className="h-8 w-px bg-slate-200" />
                        <div className="text-right">
                            <div className="text-[10px] uppercase tracking-wider font-bold text-slate-400">Totale Rimborsato</div>
                            <div className="text-lg font-bold text-emerald-600">€{stats.paidAmount.toLocaleString('it-IT', { minimumFractionDigits: 2 })}</div>
                        </div>
                    </div>

                    <Link to="/expenses/new?standalone=true" className="btn bg-slate-900 hover:bg-slate-800 text-white border-none rounded-xl px-6 shadow-lg shadow-slate-900/20">
                        <Plus size={18} className="mr-2" />
                        Nuova Nota
                    </Link>
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
                {[
                    { id: '', label: 'Tutte', icon: FileText },
                    { id: 'submitted', label: 'In Approvazione', icon: Clock },
                    { id: 'approved', label: 'Approvate', icon: CheckCircle2 },
                    { id: 'rejected', label: 'Rifiutate', icon: XCircle },
                    { id: 'paid', label: 'Saldate', icon: Receipt },
                    { id: 'draft', label: 'Bozze', icon: FileText },
                ].map(filter => (
                    <button
                        key={filter.id}
                        onClick={() => setStatusFilter(filter.id)}
                        className={`
                            flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap
                            ${statusFilter === filter.id
                                ? 'bg-slate-900 text-white shadow-md'
                                : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200 hover:border-slate-300'}
                        `}
                    >
                        <filter.icon size={16} className={statusFilter === filter.id ? 'text-emerald-400' : 'text-slate-400'} />
                        {filter.label}
                    </button>
                ))}
            </div>

            {/* Data Table */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50 border-b border-slate-200">
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider w-[180px]">Referenza</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">Dettagli</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">Stato</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Importo</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Approvato</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider w-[100px] text-right">Azioni</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {reports?.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="py-16 text-center">
                                        <div className="flex flex-col items-center justify-center">
                                            <Search size={48} className="text-slate-200 mb-4" />
                                            <h3 className="text-lg font-semibold text-slate-900">Nessun risultato</h3>
                                            <p className="text-slate-400 text-sm">Non ci sono note spese che corrispondono ai filtri.</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                reports?.map((report) => (
                                    <tr
                                        key={report.id}
                                        onClick={() => navigate(`/expenses/${report.id}`)}
                                        className="group hover:bg-slate-50/80 transition-colors cursor-pointer"
                                    >
                                        <td className="py-4 px-6 align-top">
                                            <span className="font-mono text-xs font-medium text-slate-500 block mb-1">
                                                {report.report_number || 'ND'}
                                            </span>
                                            <div className="text-xs text-slate-400">
                                                {safeFormat(report.created_at, 'dd MMM yyyy')}
                                            </div>
                                        </td>

                                        <td className="py-4 px-6 align-top">
                                            <div className="font-bold text-slate-900 mb-1 group-hover:text-emerald-700 transition-colors">
                                                {report.title}
                                            </div>
                                            <div className="text-sm text-slate-500 line-clamp-1 mb-1">
                                                {report.employee_notes || <span className="italic opacity-50">Nessuna nota</span>}
                                            </div>
                                            <div className="flex items-center gap-1.5 text-xs text-slate-400">
                                                <Calendar size={12} />
                                                {safeFormat(report.period_start, 'dd MMM')} - {safeFormat(report.period_end, 'dd MMM yyyy')}
                                            </div>
                                        </td>

                                        <td className="py-4 px-6 align-top">
                                            <div className="flex items-center gap-2">
                                                <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${getStatusBadgeClass(report.status)}`}>
                                                    {getStatusLabel(report.status)}
                                                </div>
                                                {report.status === 'rejected' && report.approver_notes && (
                                                    <div className="tooltip tooltip-right" data-tip={report.approver_notes}>
                                                        <Info size={16} className="text-red-400 hover:text-red-600" />
                                                    </div>
                                                )}
                                            </div>
                                        </td>

                                        <td className="py-4 px-6 align-top text-right">
                                            <div className="font-bold text-slate-900">
                                                €{Number(report.total_amount).toLocaleString('it-IT', { minimumFractionDigits: 2 })}
                                            </div>
                                        </td>

                                        <td className="py-4 px-6 align-top text-right">
                                            {report.approved_amount !== undefined &&
                                                report.status !== 'draft' &&
                                                report.status !== 'submitted' ? (
                                                <div className={`font-bold ${Number(report.approved_amount) < Number(report.total_amount)
                                                    ? 'text-amber-600'
                                                    : 'text-emerald-600'
                                                    }`}>
                                                    €{Number(report.approved_amount).toLocaleString('it-IT', { minimumFractionDigits: 2 })}
                                                </div>
                                            ) : (
                                                <span className="text-slate-300 text-sm">-</span>
                                            )}
                                        </td>

                                        <td className="py-4 px-6 align-middle text-right">
                                            <button className="btn btn-ghost btn-sm btn-square text-slate-400 group-hover:text-emerald-600 hover:bg-emerald-50">
                                                <ArrowRight size={18} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {reports && reports.length > 0 && (
                    <div className="bg-slate-50 border-t border-slate-200 px-6 py-3 text-xs text-slate-500 flex justify-between items-center">
                        <span>Mostrati {reports.length} record</span>
                        <span>Dati aggiornati in tempo reale</span>
                    </div>
                )}
            </div>
        </div>
    );
}

function getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
        draft: 'Bozza',
        submitted: 'In Approvazione', // More enterprise friendly
        approved: 'Approvata',
        rejected: 'Rifiutata',
        paid: 'Saldata',
        cancelled: 'Annullata',
    };
    return labels[status.toLowerCase()] || status;
}

function getStatusBadgeClass(status: string): string {
    const classes: Record<string, string> = {
        draft: 'bg-slate-100 text-slate-600 border-slate-200',
        submitted: 'bg-amber-50 text-amber-700 border-amber-200',
        approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        rejected: 'bg-red-50 text-red-700 border-red-200',
        paid: 'bg-blue-50 text-blue-700 border-blue-200',
        cancelled: 'bg-slate-100 text-slate-400 border-slate-200',
    };
    return classes[status.toLowerCase()] || 'bg-slate-100 text-slate-600 border-slate-200';
}

export default ExpensesPage;
