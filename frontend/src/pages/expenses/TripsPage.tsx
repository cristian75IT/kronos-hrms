/**
 * KRONOS - Business Trips Page
 * Enterprise-grade travel management interface
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTrips } from '../../hooks/useApi';
import {
    Plus,
    MapPin,
    AlertCircle,
    Plane,
    ArrowRight,
    RefreshCw,
    Calendar,
    Briefcase,
    Search,
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

export function TripsPage() {
    const navigate = useNavigate();
    const [statusFilter, setStatusFilter] = useState<string>('');
    const { data: trips, isLoading, error, refetch } = useTrips(statusFilter || undefined);

    // Stats calculation
    const stats = {
        total: trips?.length || 0,
        pending: trips?.filter(t => ['submitted', 'pending'].includes(t.status)).length || 0,
        approved: trips?.filter(t => t.status === 'approved').length || 0,
        totalBudget: trips?.reduce((sum, t) => sum + (Number(t.estimated_budget) || 0), 0) || 0,
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center p-32 gap-6">
                <div className="relative">
                    <div className="w-20 h-20 border-4 border-slate-200 border-t-emerald-600 rounded-full animate-spin" />
                    <Plane className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-emerald-600" size={32} />
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
                    <p className="text-slate-500 mt-2">Impossibile recuperare le trasferte. Verifica la connessione.</p>
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
                            <Briefcase size={24} />
                        </div>
                        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Trasferte</h1>
                    </div>
                    <p className="text-slate-500 max-w-2xl">
                        Pianifica e gestisci le tue missioni aziendali. Tieni traccia di budget, destinazioni e rimborsi in un unico posto.
                    </p>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex items-center gap-4 px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl">
                        <div className="text-right">
                            <div className="text-[10px] uppercase tracking-wider font-bold text-slate-400">Budget Totale</div>
                            <div className="text-lg font-bold text-slate-900">€{stats.totalBudget.toLocaleString('it-IT', { minimumFractionDigits: 2 })}</div>
                        </div>
                        <div className="h-8 w-px bg-slate-200" />
                        <div className="text-right">
                            <div className="text-[10px] uppercase tracking-wider font-bold text-slate-400">Missioni Attive</div>
                            <div className="text-lg font-bold text-emerald-600">{stats.pending + stats.approved}</div>
                        </div>
                    </div>

                    <Link to="/trips/new" className="btn bg-slate-900 hover:bg-slate-800 text-white border-none rounded-xl px-6 shadow-lg shadow-slate-900/20">
                        <Plus size={18} className="mr-2" />
                        Nuova Missione
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
                    { id: 'completed', label: 'Completate', icon: Briefcase },
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
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider w-[250px]">Missione</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">Date & Dettagli</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">Stato</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Budget Stimato</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider w-[100px] text-right">Azioni</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {trips?.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="py-16 text-center">
                                        <div className="flex flex-col items-center justify-center">
                                            <Search size={48} className="text-slate-200 mb-4" />
                                            <h3 className="text-lg font-semibold text-slate-900">Nessun risultato</h3>
                                            <p className="text-slate-400 text-sm">Non ci sono trasferte che corrispondono ai filtri.</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                trips?.map((trip) => (
                                    <tr
                                        key={trip.id}
                                        onClick={() => navigate(`/trips/${trip.id}`)}
                                        className="group hover:bg-slate-50/80 transition-colors cursor-pointer"
                                    >
                                        <td className="py-4 px-6 align-top">
                                            <div className="flex items-start gap-3">
                                                <div className="mt-1 p-1.5 bg-emerald-50 text-emerald-600 rounded-lg shrink-0">
                                                    <MapPin size={16} />
                                                </div>
                                                <div>
                                                    <span className="font-bold text-slate-900 block group-hover:text-emerald-700 transition-colors">
                                                        {trip.destination}
                                                    </span>
                                                    <span className="text-xs text-slate-500 font-medium capitalize">
                                                        {trip.title}
                                                    </span>
                                                    <div className="text-xs text-slate-400 mt-1 uppercase tracking-wider">
                                                        {trip.destination_type?.replace('_', ' ') || 'N/A'}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>

                                        <td className="py-4 px-6 align-top">
                                            <div className="flex items-center gap-1.5 text-sm font-semibold text-slate-700 mb-1">
                                                <Calendar size={14} className="text-slate-400" />
                                                {safeFormat(trip.start_date, 'dd MMM')} - {safeFormat(trip.end_date, 'dd MMM yyyy')}
                                            </div>
                                            <div className="text-sm text-slate-500 line-clamp-1">
                                                {trip.purpose || <span className="italic opacity-50">Nessuna descrizione</span>}
                                            </div>
                                        </td>

                                        <td className="py-4 px-6 align-top">
                                            <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${getStatusBadgeClass(trip.status)}`}>
                                                {getStatusLabel(trip.status)}
                                            </div>
                                        </td>

                                        <td className="py-4 px-6 align-top text-right">
                                            <div className="font-bold text-slate-900">
                                                €{Number(trip.estimated_budget || 0).toLocaleString('it-IT', { minimumFractionDigits: 2 })}
                                            </div>
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

                {trips && trips.length > 0 && (
                    <div className="bg-slate-50 border-t border-slate-200 px-6 py-3 text-xs text-slate-500 flex justify-between items-center">
                        <span>Mostrati {trips.length} record</span>
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
        submitted: 'In Approvazione',
        pending: 'In Approvazione',
        approved: 'Approvata',
        rejected: 'Rifiutata',
        completed: 'Completata',
        cancelled: 'Annullata',
    };
    return labels[status.toLowerCase()] || status;
}

function getStatusBadgeClass(status: string): string {
    const classes: Record<string, string> = {
        draft: 'bg-slate-100 text-slate-600 border-slate-200',
        submitted: 'bg-amber-50 text-amber-700 border-amber-200',
        pending: 'bg-amber-50 text-amber-700 border-amber-200',
        approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        rejected: 'bg-red-50 text-red-700 border-red-200',
        completed: 'bg-blue-50 text-blue-700 border-blue-200',
        cancelled: 'bg-slate-100 text-slate-400 border-slate-200',
    };
    return classes[status.toLowerCase()] || 'bg-slate-100 text-slate-600 border-slate-200';
}

export default TripsPage;
