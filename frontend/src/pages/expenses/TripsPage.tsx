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
    FileText,
    AlertCircle,
    Plane,
    ArrowRight,
    RefreshCw
} from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

export function TripsPage() {
    const navigate = useNavigate();
    const [statusFilter, setStatusFilter] = useState<string>('');
    const { data: trips, isLoading, error, refetch } = useTrips(statusFilter || undefined);

    // Stats calculation
    const stats = {
        total: trips?.length || 0,
        pending: trips?.filter(t => t.status === 'submitted').length || 0,
        approved: trips?.filter(t => t.status === 'approved').length || 0,
        totalBudget: trips?.reduce((sum, t) => sum + (Number(t.estimated_budget) || 0), 0) || 0,
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center p-32 gap-6">
                <div className="relative">
                    <div className="w-20 h-20 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
                    <Plane className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-cyan-500" size={32} />
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
                    <p className="text-sm text-gray-500 mt-1">Pianifica, traccia e rendiconta le tue missioni di lavoro.</p>
                </div>

                <div className="flex flex-wrap gap-3 items-center">
                    <div className="flex items-center gap-2 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-200">
                        <span className="text-sm font-semibold text-gray-600">Budget Totale:</span>
                        <span className="text-sm font-bold text-gray-900">€{stats.totalBudget.toLocaleString('it-IT', { minimumFractionDigits: 2 })}</span>
                    </div>

                    <Link to="/trips/new" className="btn btn-primary btn-sm h-10 px-4 rounded-lg font-medium shadow-none">
                        <Plus size={16} className="mr-2" />
                        Nuova Missione
                    </Link>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-white border border-gray-200 rounded-lg">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Missioni Totali</div>
                    <div className="text-2xl font-bold text-gray-900 mt-1">{stats.total}</div>
                </div>
                <div className="p-4 bg-white border border-gray-200 rounded-lg">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Pendenti</div>
                    <div className="text-2xl font-bold text-amber-600 mt-1">{stats.pending}</div>
                </div>
                <div className="p-4 bg-white border border-gray-200 rounded-lg">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Approvate</div>
                    <div className="text-2xl font-bold text-emerald-600 mt-1">{stats.approved}</div>
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
                                ? 'bg-gray-900 text-white border-gray-900'
                                : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
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
                    <div className="col-span-full flex flex-col items-center justify-center p-16 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                        <Plane size={48} className="text-gray-300 mb-4" />
                        <h3 className="text-lg font-semibold text-gray-900">Nessuna Missione</h3>
                        <p className="text-sm text-gray-500 mt-1">Non ci sono trasferte registrate per questo filtro.</p>
                        <Link to="/trips/new" className="mt-6 btn btn-outline btn-sm">
                            Pianifica la Prima
                        </Link>
                    </div>
                ) : (
                    trips?.map((trip) => (
                        <div
                            key={trip.id}
                            onClick={() => navigate(`/trips/${trip.id}`)}
                            className="group flex flex-col bg-white rounded-lg border border-gray-200 hover:border-cyan-500/50 hover:shadow-sm transition-all cursor-pointer p-5"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className="space-y-1">
                                    <div className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusBadgeClass(trip.status)}`}>
                                        {getStatusLabel(trip.status)}
                                    </div>
                                    <h3 className="text-lg font-bold text-gray-900 line-clamp-1 group-hover:text-cyan-700 transition-colors flex items-center gap-2">
                                        <MapPin size={16} className="text-cyan-500" />
                                        {trip.destination}
                                    </h3>
                                </div>
                            </div>

                            <p className="text-sm text-gray-500 line-clamp-2 mb-4 flex-1">
                                {trip.purpose || 'Nessuna descrizione'}
                            </p>

                            <div className="grid grid-cols-2 gap-4 mb-4">
                                <div className="p-3 bg-gray-50 rounded-lg">
                                    <span className="text-[0.65rem] font-bold text-gray-400 uppercase tracking-wider block mb-1">Periodo</span>
                                    <div className="text-sm font-semibold text-gray-900">
                                        {format(new Date(trip.start_date), 'dd MMM', { locale: it })} - {format(new Date(trip.end_date), 'dd MMM', { locale: it })}
                                    </div>
                                </div>
                                <div className="p-3 bg-gray-50 rounded-lg">
                                    <span className="text-[0.65rem] font-bold text-gray-400 uppercase tracking-wider block mb-1">Budget</span>
                                    <div className="text-sm font-semibold text-gray-900">
                                        €{Number(trip.estimated_budget || 0).toLocaleString('it-IT', { minimumFractionDigits: 2 })}
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center justify-between text-xs text-gray-400 pt-4 border-t border-gray-100 mt-auto">
                                <div className="flex items-center gap-1.5">
                                    <FileText size={14} />
                                    Trasferta
                                </div>
                                <div className="flex items-center gap-1 text-cyan-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                                    Dettagli <ArrowRight size={14} />
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
        approved: 'Approvata',
        rejected: 'Rifiutata',
        completed: 'Completata',
        cancelled: 'Annullata',
    };
    return labels[status] || status;
}

function getStatusBadgeClass(status: string): string {
    const classes: Record<string, string> = {
        draft: 'bg-gray-100 text-gray-600',
        submitted: 'bg-amber-50 text-amber-700 border border-amber-100',
        approved: 'bg-emerald-50 text-emerald-700 border border-emerald-100',
        rejected: 'bg-red-50 text-red-700 border border-red-100',
        completed: 'bg-cyan-50 text-cyan-700 border border-cyan-100',
        cancelled: 'bg-gray-100 text-gray-500',
    };
    return classes[status] || 'bg-gray-100 text-gray-600';
}

export default TripsPage;
