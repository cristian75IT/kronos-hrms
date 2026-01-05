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
    Briefcase
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
                    <div className="w-20 h-20 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
                    <Plane className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-emerald-500" size={32} />
                </div>
                <p className="text-sm font-black uppercase tracking-[0.2em] text-base-content/30 animate-pulse">Sincronizzazione Missioni...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center p-12 gap-6 bg-error/5 border border-error/10 rounded-[3rem] text-center">
                <div className="p-4 bg-error/10 rounded-2xl">
                    <AlertCircle size={48} className="text-error" />
                </div>
                <div>
                    <h2 className="text-2xl font-black">Errore di Connessione</h2>
                    <p className="text-base-content/50 max-w-md mx-auto">Impossibile recuperare i dati delle trasferte.</p>
                </div>
                <button className="btn btn-primary rounded-2xl px-8" onClick={() => refetch()}>
                    <RefreshCw size={18} /> Riprova
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fadeIn max-w-[1400px] mx-auto pb-8">
            {/* Enterprise Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Trasferte Aziendali</h1>
                    <p className="text-sm text-slate-500 mt-1">Pianifica, traccia e rendiconta le tue missioni di lavoro.</p>
                </div>

                <div className="flex flex-wrap gap-3 items-center">
                    <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
                        <span className="text-sm font-semibold text-slate-600">Budget Totale:</span>
                        <span className="text-sm font-bold text-emerald-700">€{stats.totalBudget.toLocaleString('it-IT', { minimumFractionDigits: 2 })}</span>
                    </div>

                    <Link to="/trips/new" className="btn btn-primary btn-sm h-10 px-4 rounded-lg font-medium shadow-none bg-slate-900 hover:bg-slate-800 text-white border-none">
                        <Plus size={16} className="mr-2" />
                        Nuova Missione
                    </Link>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-sm">
                    <div className="flex items-center justify-between">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Missioni Totali</div>
                        <Briefcase size={16} className="text-slate-400" />
                    </div>
                    <div className="text-2xl font-bold text-slate-900 mt-2">{stats.total}</div>
                </div>
                <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-sm">
                    <div className="flex items-center justify-between">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">In Approvazione</div>
                        <AlertCircle size={16} className="text-amber-400" />
                    </div>
                    <div className="text-2xl font-bold text-amber-600 mt-2">{stats.pending}</div>
                </div>
                <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-sm">
                    <div className="flex items-center justify-between">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Approvate</div>
                        <Plane size={16} className="text-emerald-400" />
                    </div>
                    <div className="text-2xl font-bold text-emerald-600 mt-2">{stats.approved}</div>
                </div>
            </div>

            {/* Filter Toolbar */}
            <div className="flex items-center justify-between py-2 overflow-x-auto">
                <div className="flex gap-2">
                    {['', 'draft', 'submitted', 'approved', 'completed'].map(status => (
                        <button
                            key={status}
                            onClick={() => setStatusFilter(status)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${statusFilter === status
                                ? 'bg-slate-900 text-white border-slate-900'
                                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                                }`}
                        >
                            {status === '' ? 'Tutte' : getStatusLabel(status)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Trips Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {trips?.length === 0 ? (
                    <div className="col-span-full flex flex-col items-center justify-center p-16 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                        <Plane size={48} className="text-slate-300 mb-4" />
                        <h3 className="text-lg font-semibold text-slate-900">Nessuna Missione</h3>
                        <p className="text-sm text-slate-500 mt-1">Non ci sono trasferte registrate per questo filtro.</p>
                        <Link to="/trips/new" className="mt-6 btn btn-outline btn-sm">
                            Pianifica la Prima
                        </Link>
                    </div>
                ) : (
                    trips?.map((trip) => (
                        <div
                            key={trip.id}
                            onClick={() => navigate(`/trips/${trip.id}`)}
                            className="group flex flex-col bg-white rounded-lg border border-slate-200 hover:border-emerald-500/50 hover:shadow-md transition-all cursor-pointer p-0 overflow-hidden"
                        >
                            <div className="p-5 flex-1">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="space-y-1 w-full">
                                        <div className="flex justify-between w-full mb-2">
                                            <div className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${getStatusBadgeClass(trip.status)}`}>
                                                {getStatusLabel(trip.status)}
                                            </div>
                                            <span className="text-xs text-slate-400 font-medium">
                                                {safeFormat(trip.created_at, 'dd MMM yyyy')}
                                            </span>
                                        </div>
                                        <h3 className="text-lg font-bold text-slate-900 line-clamp-1 group-hover:text-emerald-700 transition-colors flex items-center gap-2">
                                            <MapPin size={18} className="text-emerald-500 flex-shrink-0" />
                                            {trip.destination}
                                        </h3>
                                        <p className="text-sm text-slate-500 line-clamp-2 min-h-[40px]">
                                            {trip.purpose || 'Nessuna descrizione'}
                                        </p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4 mt-4">
                                    <div className="p-3 bg-slate-50 rounded-lg">
                                        <div className="flex items-center gap-1.5 mb-1 text-slate-400">
                                            <Calendar size={12} />
                                            <span className="text-[0.65rem] font-bold uppercase tracking-wider">Date</span>
                                        </div>
                                        <div className="text-sm font-semibold text-slate-900">
                                            {safeFormat(trip.start_date, 'dd MMM') && safeFormat(trip.end_date, 'dd MMM')
                                                ? `${safeFormat(trip.start_date, 'dd MMM')} - ${safeFormat(trip.end_date, 'dd MMM')}`
                                                : 'Date non disponibili'}
                                        </div>
                                    </div>
                                    <div className="p-3 bg-slate-50 rounded-lg">
                                        <div className="flex items-center gap-1.5 mb-1 text-slate-400">
                                            <Briefcase size={12} />
                                            <span className="text-[0.65rem] font-bold uppercase tracking-wider">Budget</span>
                                        </div>
                                        <div className="text-sm font-semibold text-emerald-700">
                                            €{Number(trip.estimated_budget || 0).toLocaleString('it-IT', { minimumFractionDigits: 2 })}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                                <span className="text-xs font-medium text-slate-500 capitalize">{trip.destination_type?.replace('_', ' ') || 'N/A'}</span>
                                <div className="flex items-center gap-1 text-emerald-600 font-medium text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                                    Vedi Dettagli <ArrowRight size={12} />
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

function getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
        draft: 'Bozza',
        submitted: 'Pendente',
        pending: 'Pendente',
        approved: 'Approvata',
        rejected: 'Rifiutata',
        completed: 'Completata',
        cancelled: 'Annullata',
    };
    return labels[status] || status;
}

function getStatusBadgeClass(status: string): string {
    const classes: Record<string, string> = {
        draft: 'bg-slate-100 text-slate-600',
        submitted: 'bg-amber-50 text-amber-700 border border-amber-100',
        pending: 'bg-amber-50 text-amber-700 border border-amber-100',
        approved: 'bg-emerald-50 text-emerald-700 border border-emerald-100',
        rejected: 'bg-red-50 text-red-700 border border-red-100',
        completed: 'bg-blue-50 text-blue-700 border border-blue-100',
        cancelled: 'bg-slate-100 text-slate-500',
    };
    return classes[status] || 'bg-slate-100 text-slate-600';
}

export default TripsPage;
