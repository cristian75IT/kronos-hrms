/**
 * KRONOS - Trip Detail Page
 * Enterprise-grade business trip detail view
 */
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import {
    ArrowLeft,
    MapPin,
    Calendar,
    Clock,
    FileText,
    CheckCircle,
    XCircle,
    AlertCircle,
    Download,
    Edit,
    Send,
    Plane,
    Building,
    Globe,
    DollarSign,
    Receipt,
    Plus,
    Loader,
    Trash2,
    Ban
} from 'lucide-react';
import { format, differenceInDays, isValid } from 'date-fns';
import { it } from 'date-fns/locale';
import { useTrip } from '../../hooks/useApi';
import { useAuth, useIsApprover, useIsAdmin, useIsHR } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { tripsService } from '../../services/expenses.service';
// walletsService removed

// Safe date formatter helper
const safeFormat = (dateStr: string | undefined | null, formatStr: string) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    return isValid(date) ? format(date, formatStr, { locale: it }) : null;
};

export function TripDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const toast = useToast();
    const { user } = useAuth();
    const isApprover = useIsApprover();
    const isAdmin = useIsAdmin();
    const isHR = useIsHR();
    const { data: trip, isLoading, refetch } = useTrip(id || '');

    const [activeTab, setActiveTab] = useState<'details' | 'expenses' | 'allowances'>('details');
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [showRejectModal, setShowRejectModal] = useState(false);
    const [rejectReason, setRejectReason] = useState('');
    const [showCancelModal, setShowCancelModal] = useState(false);
    const [cancelReason, setCancelReason] = useState('');
    const [showDeleteModal, setShowDeleteModal] = useState(false);

    // Wallet hooks removed

    // Check ownership
    const isOwner = user?.id === trip?.user_id || user?.keycloak_id === trip?.user_id;
    const status = trip?.status?.toLowerCase() || 'draft';

    // Action handlers
    const handleSubmit = async () => {
        if (!id) return;
        setActionLoading('submit');
        try {
            await tripsService.submitTrip(id);
            toast.success('Trasferta inviata per approvazione');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'invio');
        } finally {
            setActionLoading(null);
        }
    };

    const handleComplete = async () => {
        if (!id) return;
        setActionLoading('complete');
        try {
            await tripsService.completeTrip(id);
            toast.success('Trasferta completata');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante il completamento');
        } finally {
            setActionLoading(null);
        }
    };

    const handleApprove = async () => {
        if (!id) return;
        setActionLoading('approve');
        try {
            await tripsService.approveTrip(id);
            toast.success('Trasferta approvata');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'approvazione');
        } finally {
            setActionLoading(null);
        }
    };

    const handleReject = async () => {
        if (!id || !rejectReason.trim()) return;
        setActionLoading('reject');
        try {
            await tripsService.rejectTrip(id, rejectReason);
            toast.success('Trasferta rifiutata');
            setShowRejectModal(false);
            setRejectReason('');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante il rifiuto');
        } finally {
            setActionLoading(null);
        }
    };

    const handleCancel = async () => {
        if (!id || !cancelReason.trim()) return;
        setActionLoading('cancel');
        try {
            await tripsService.cancelTrip(id, cancelReason);
            toast.success('Richiesta annullata');
            setShowCancelModal(false);
            setCancelReason('');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'annullamento');
        } finally {
            setActionLoading(null);
        }
    };

    const handleDelete = async () => {
        if (!id) return;
        setActionLoading('delete');
        try {
            await tripsService.deleteTrip(id);
            toast.success('Trasferta eliminata');
            navigate('/trips');
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'eliminazione');
        } finally {
            setActionLoading(null);
        }
    };

    // handleInitializeWallet removed

    if (isLoading) {
        return (
            <div className="detail-page animate-fadeIn">
                <div className="detail-loading">
                    <div className="spinner-lg" />
                    <p>Caricamento trasferta...</p>
                </div>
            </div>
        );
    }

    if (!trip) {
        return (
            <div className="detail-page animate-fadeIn">
                <div className="detail-empty">
                    <AlertCircle size={48} />
                    <h2>Trasferta non trovata</h2>
                    <p>La trasferta che stai cercando non esiste o è stata eliminata.</p>
                    <Link to="/trips" className="btn btn-primary">
                        Torna alle Trasferte
                    </Link>
                </div>
            </div>
        );
    }

    const getStatusConfig = (status: string) => {
        const s = status?.toLowerCase();
        const configs: Record<string, { className: string; icon: React.ReactNode; label: string }> = {
            draft: {
                className: 'bg-slate-100 text-slate-600 border-slate-200',
                icon: <FileText size={16} />,
                label: 'Bozza'
            },
            pending: {
                className: 'bg-amber-50 text-amber-700 border-amber-200',
                icon: <Clock size={16} />,
                label: 'In Approvazione'
            },
            submitted: {
                className: 'bg-amber-50 text-amber-700 border-amber-200',
                icon: <Clock size={16} />,
                label: 'In Approvazione'
            },
            approved: {
                className: 'bg-emerald-50 text-emerald-700 border-emerald-200',
                icon: <CheckCircle size={16} />,
                label: 'Approvata'
            },
            rejected: {
                className: 'bg-red-50 text-red-700 border-red-200',
                icon: <XCircle size={16} />,
                label: 'Rifiutata'
            },
            completed: {
                className: 'bg-blue-50 text-blue-700 border-blue-200',
                icon: <CheckCircle size={16} />,
                label: 'Completata'
            },
            cancelled: {
                className: 'bg-slate-100 text-slate-500 border-slate-200',
                icon: <XCircle size={16} />,
                label: 'Annullata'
            },
        };
        return configs[s] || configs.draft;
    };

    const getDestinationIcon = (type: string) => {
        switch (type) {
            case 'national': return <Building size={20} />;
            case 'eu': return <Globe size={20} />;
            case 'extra_eu': return <Plane size={20} />;
            default: return <MapPin size={20} />;
        }
    };

    const getDestinationLabel = (type: string) => {
        switch (type) {
            case 'national': return 'Italia';
            case 'eu': return 'Europa';
            case 'extra_eu': return 'Extra UE';
            default: return type;
        }
    };

    const statusConfig = getStatusConfig(trip.status);

    // Calculate trip days safely
    let tripDays = '-';
    if (trip.start_date && trip.end_date) {
        const start = new Date(trip.start_date);
        const end = new Date(trip.end_date);
        if (isValid(start) && isValid(end)) {
            tripDays = (differenceInDays(end, start) + 1).toString();
        }
    }

    return (
        <div className="max-w-7xl mx-auto space-y-6 pb-8 animate-fadeIn px-4 sm:px-6 lg:px-8 pt-6">
            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start gap-4">
                <div className="flex items-start gap-4">
                    <button
                        onClick={() => navigate(-1)}
                        className="p-2 rounded-full hover:bg-gray-100 transition-colors text-gray-500 hover:text-gray-900"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <div className="flex items-center gap-2 text-sm text-slate-500 mb-1">
                            <Link to="/trips" className="hover:text-emerald-600 transition-colors">Trasferte</Link>
                            <span>/</span>
                            <span>Dettaglio</span>
                        </div>
                        <h1 className="text-2xl font-bold text-slate-900">{trip.title || trip.destination}</h1>
                    </div>
                </div>
                <div>
                    <div className={`px-4 py-2 rounded-full border flex items-center gap-2 text-sm font-semibold ${statusConfig.className}`}>
                        {statusConfig.icon}
                        <span>{statusConfig.label}</span>
                    </div>
                </div>
            </header>

            {/* Hero Card */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm flex flex-col md:flex-row justify-between items-center gap-6">
                <div className="flex items-center gap-6 w-full md:w-auto">
                    <div className="w-14 h-14 flex items-center justify-center bg-emerald-50 text-emerald-600 rounded-xl shrink-0 border border-emerald-100">
                        {getDestinationIcon(trip.destination_type)}
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-gray-900 mb-1">{trip.destination}</h2>
                        <span className="text-sm text-gray-500">{getDestinationLabel(trip.destination_type)}</span>
                    </div>

                    <div className="h-10 w-px bg-gray-200 mx-2 hidden md:block"></div>

                    <div className="flex gap-6 hidden md:flex">
                        <div className="flex items-center gap-2 text-emerald-600">
                            <Calendar size={18} />
                            <div className="flex flex-col">
                                <span className="text-lg font-bold text-slate-900 leading-none">{tripDays}</span>
                                <span className="text-xs text-slate-500 font-medium uppercase tracking-wide">giorni</span>
                            </div>
                        </div>
                        {trip.estimated_budget && (
                            <div className="flex items-center gap-2 text-emerald-600">
                                <DollarSign size={18} />
                                <div className="flex flex-col">
                                    <span className="text-lg font-bold text-slate-900 leading-none">€{Number(trip.estimated_budget).toFixed(0)}</span>
                                    <span className="text-xs text-slate-500 font-medium uppercase tracking-wide">budget</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-6 pt-4 border-t border-gray-100 w-full md:w-auto md:border-0 justify-center">
                    <div className="flex flex-col gap-1 items-center md:items-start">
                        <span className="text-xs text-gray-400 font-medium uppercase tracking-wide">Partenza</span>
                        <span className="font-semibold text-gray-900">
                            {safeFormat(trip.start_date, 'd MMM yyyy') || '-'}
                        </span>
                    </div>
                    <div className="text-xl text-emerald-500">→</div>
                    <div className="flex flex-col gap-1 items-center md:items-end">
                        <span className="text-xs text-gray-400 font-medium uppercase tracking-wide">Ritorno</span>
                        <span className="font-semibold text-gray-900">
                            {safeFormat(trip.end_date, 'd MMM yyyy') || '-'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-8 items-start">
                {/* Left Column - Main Info */}
                <div>
                    {/* Tabs */}
                    <div className="flex p-1 space-x-1 bg-slate-100/80 rounded-xl mb-6 border border-slate-200">
                        <button
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${activeTab === 'details'
                                ? 'bg-white text-slate-900 shadow-sm ring-1 ring-black/5'
                                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50'
                                }`}
                            onClick={() => setActiveTab('details')}
                        >
                            <FileText size={16} />
                            Dettagli
                        </button>
                        <button
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${activeTab === 'expenses'
                                ? 'bg-white text-slate-900 shadow-sm ring-1 ring-black/5'
                                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50'
                                }`}
                            onClick={() => setActiveTab('expenses')}
                        >
                            <Receipt size={16} />
                            Spese
                        </button>
                        <button
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${activeTab === 'allowances'
                                ? 'bg-white text-slate-900 shadow-sm ring-1 ring-black/5'
                                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50'
                                }`}
                            onClick={() => setActiveTab('allowances')}
                        >
                            <DollarSign size={16} />
                            Diarie
                        </button>
                        {/* Wallet Tab removed */}
                    </div>

                    {activeTab === 'details' && (
                        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm animate-fadeInUp">
                            {/* Purpose */}
                            {trip.purpose && (
                                <div className="p-6 border-b border-gray-100">
                                    <h3 className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">
                                        <FileText size={18} />
                                        Scopo della Trasferta
                                    </h3>
                                    <p className="text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-lg border border-gray-100 text-sm">
                                        {trip.purpose}
                                    </p>
                                </div>
                            )}

                            {/* Project Info */}
                            {(trip.project_code || trip.client_name) && (
                                <div className="p-6 border-b border-gray-100">
                                    <h3 className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">
                                        <Building size={18} />
                                        Informazioni Progetto
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {trip.project_code && (
                                            <div className="flex flex-col gap-1">
                                                <span className="text-xs text-gray-500 uppercase font-medium">Codice Progetto</span>
                                                <span className="font-medium text-gray-900">{trip.project_code}</span>
                                            </div>
                                        )}
                                        {trip.client_name && (
                                            <div className="flex flex-col gap-1">
                                                <span className="text-xs text-gray-500 uppercase font-medium">Cliente</span>
                                                <span className="font-medium text-gray-900">{trip.client_name}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Attachment */}
                            {trip.attachment_path && (
                                <div className="p-6">
                                    <h3 className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">
                                        <FileText size={18} />
                                        Allegati
                                    </h3>
                                    <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                                        <Download size={16} />
                                        Scarica Documento
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'expenses' && (
                        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm animate-fadeInUp min-h-[300px] flex items-center justify-center text-center">
                            <div className="max-w-xs">
                                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center text-gray-400 mx-auto mb-4">
                                    <Receipt size={32} />
                                </div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">Nessuna spesa registrata</h3>
                                <p className="text-gray-500 text-sm mb-6">
                                    Le spese per questa trasferta appariranno qui una volta aggiunte alla nota spese.
                                </p>
                                <Link to={`/expenses/new?trip_id=${id}`} className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-medium transition-colors">
                                    <Plus size={18} />
                                    Crea Nota Spese
                                </Link>
                            </div>
                        </div>
                    )}

                    {activeTab === 'allowances' && (
                        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm animate-fadeInUp min-h-[300px] flex items-center justify-center text-center">
                            <div className="max-w-xs">
                                <div className="w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center text-emerald-500 mx-auto mb-4">
                                    <DollarSign size={32} />
                                </div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">Diarie non calcolate</h3>
                                <p className="text-gray-500 text-sm">
                                    Le diarie verranno calcolate automaticamente al completamento della trasferta.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Wallet Tab Content Removed */}
                </div>

                {/* Right Column - Actions & Summary */}
                <div className="space-y-6">
                    {/* Actions Card */}
                    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                        <div className="p-4 bg-gray-50 border-b border-gray-200">
                            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide">Azioni</h3>
                        </div>

                        {/* Employee Actions Section */}
                        {(isOwner || status === 'draft') && (
                            <div className="p-4 border-b border-gray-100">
                                <div className="flex items-center gap-2 mb-3">
                                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Dipendente</h4>
                                </div>
                                <div className="space-y-2">
                                    {status === 'draft' && (
                                        <>
                                            <button
                                                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                                onClick={handleSubmit}
                                                disabled={actionLoading !== null}
                                            >
                                                {actionLoading === 'submit' ? <Loader size={18} className="animate-spin" /> : <Send size={18} />}
                                                Invia per Approvazione
                                            </button>
                                            <Link to={`/trips/${id}/edit`} className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-medium transition-colors">
                                                <Edit size={18} />
                                                Modifica
                                            </Link>
                                            <button
                                                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-red-600 hover:bg-red-50 border border-red-200 rounded-lg font-medium transition-colors disabled:opacity-50"
                                                onClick={() => setShowDeleteModal(true)}
                                                disabled={actionLoading !== null}
                                            >
                                                <Trash2 size={18} />
                                                Elimina Bozza
                                            </button>
                                        </>
                                    )}
                                    {(status === 'submitted' || status === 'pending') && isOwner && (
                                        <button
                                            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white border border-red-200 text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors disabled:opacity-50"
                                            onClick={() => setShowCancelModal(true)}
                                            disabled={actionLoading !== null}
                                        >
                                            <XCircle size={18} />
                                            Annulla Richiesta
                                        </button>
                                    )}
                                    {status === 'approved' && isOwner && (
                                        <>
                                            <Link to={`/expenses/new?trip_id=${id}`} className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors">
                                                <Receipt size={18} />
                                                Crea Nota Spese
                                            </Link>
                                            <button
                                                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-medium transition-colors disabled:opacity-50"
                                                onClick={handleComplete}
                                                disabled={actionLoading !== null}
                                            >
                                                {actionLoading === 'complete' ? <Loader size={18} className="animate-spin" /> : <CheckCircle size={18} />}
                                                Completa Trasferta
                                            </button>
                                            <button
                                                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white border border-red-200 text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors disabled:opacity-50"
                                                onClick={() => setShowCancelModal(true)}
                                                disabled={actionLoading !== null}
                                            >
                                                <Ban size={18} />
                                                Annulla Trasferta
                                            </button>
                                        </>
                                    )}
                                    {(status === 'completed' || status === 'rejected' || status === 'cancelled') && (
                                        <p className="text-center text-sm text-gray-400 italic py-2">
                                            Nessuna azione disponibile
                                        </p>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Approver Actions Section */}
                        {isApprover && (!isOwner || isAdmin || isHR) && status !== 'draft' && status !== 'completed' && (
                            <div className="p-4">
                                <div className="flex items-center gap-2 mb-3">
                                    <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Approvatore</h4>
                                </div>
                                <div className="space-y-2">
                                    {(status === 'submitted' || status === 'pending') && (
                                        <>
                                            <button
                                                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                                onClick={handleApprove}
                                                disabled={actionLoading !== null}
                                            >
                                                {actionLoading === 'approve' ? <Loader size={18} className="animate-spin" /> : <CheckCircle size={18} />}
                                                Approva
                                            </button>
                                            <button
                                                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                                onClick={() => setShowRejectModal(true)}
                                                disabled={actionLoading !== null}
                                            >
                                                <XCircle size={18} />
                                                Rifiuta
                                            </button>
                                        </>
                                    )}
                                    {status === 'approved' && (
                                        <button
                                            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                            onClick={() => setShowCancelModal(true)}
                                            disabled={actionLoading !== null}
                                        >
                                            <Ban size={18} />
                                            Revoca Approvazione
                                        </button>
                                    )}
                                    {(status === 'rejected' || status === 'cancelled') && (
                                        <p className="text-center text-sm text-gray-400 italic py-2">
                                            Trasferta già processata
                                        </p>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* No Actions Available */}
                        {!isOwner && !isApprover && status !== 'draft' && (
                            <div className="p-4">
                                <p className="text-center text-sm text-gray-400 italic">
                                    Nessuna azione disponibile per questa trasferta.
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Summary Card */}
                    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide mb-4">Riepilogo</h3>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="text-sm text-gray-500">Destinazione</span>
                                <span className="text-sm font-medium text-gray-900">{trip.destination}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="text-sm text-gray-500">Tipo</span>
                                <span className="text-sm font-medium text-gray-900">{getDestinationLabel(trip.destination_type)}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="text-sm text-gray-500">Durata</span>
                                <span className="text-sm font-bold text-gray-900">{tripDays} giorni</span>
                            </div>
                            {trip.estimated_budget && (
                                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                    <span className="text-sm text-gray-500">Budget</span>
                                    <span className="text-sm font-bold text-gray-900">€{Number(trip.estimated_budget).toFixed(2)}</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Reject Modal */}
            {
                showRejectModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowRejectModal(false)}>
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                            <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                                <h3 className="font-bold text-gray-900">Rifiuta Trasferta</h3>
                                <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowRejectModal(false)}>
                                    <XCircle size={20} />
                                </button>
                            </div>
                            <div className="p-6">
                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-700">Motivo del Rifiuto <span className="text-red-500">*</span></label>
                                    <textarea
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm min-h-[100px] resize-y"
                                        placeholder="Inserisci il motivo del rifiuto..."
                                        value={rejectReason}
                                        onChange={(e) => setRejectReason(e.target.value)}
                                        rows={4}
                                    />
                                </div>
                            </div>
                            <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                                <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowRejectModal(false)}>
                                    Annulla
                                </button>
                                <button
                                    className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                    onClick={handleReject}
                                    disabled={!rejectReason.trim() || actionLoading === 'reject'}
                                >
                                    {actionLoading === 'reject' ? <Loader size={16} className="animate-spin" /> : null}
                                    Conferma Rifiuto
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }
            {/* Cancel Modal */}
            {
                showCancelModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn">
                        <div className="bg-white rounded-xl shadow-xl w-full max-w-md animate-scaleIn overflow-hidden" onClick={e => e.stopPropagation()}>
                            <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50">
                                <h3 className="font-bold text-gray-900">Annulla Trasferta</h3>
                                <button className="text-gray-400 hover:text-gray-600" onClick={() => setShowCancelModal(false)}>
                                    <XCircle size={20} />
                                </button>
                            </div>
                            <div className="p-6">
                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-700">Motivo dell'Annullamento <span className="text-red-500">*</span></label>
                                    <textarea
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 min-h-[100px]"
                                        placeholder="Inserisci il motivo..."
                                        value={cancelReason}
                                        onChange={(e) => setCancelReason(e.target.value)}
                                    />
                                </div>
                            </div>
                            <div className="flex justify-end gap-3 p-4 bg-gray-50/50 border-t border-gray-100">
                                <button className="btn btn-ghost text-gray-600 hover:bg-white border border-transparent hover:border-gray-200" onClick={() => setShowCancelModal(false)}>
                                    Annulla
                                </button>
                                <button
                                    className="btn bg-red-600 hover:bg-red-700 text-white shadow-sm flex items-center gap-2"
                                    onClick={handleCancel}
                                    disabled={!cancelReason.trim() || actionLoading === 'cancel'}
                                >
                                    {actionLoading === 'cancel' ? <Loader size={16} className="animate-spin" /> : null}
                                    Conferma
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Delete Modal */}
            {
                showDeleteModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn">
                        <div className="bg-white rounded-xl shadow-xl w-full max-w-md animate-scaleIn overflow-hidden" onClick={e => e.stopPropagation()}>
                            <div className="p-6 text-center">
                                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                                    <Trash2 className="h-6 w-6 text-red-600" />
                                </div>
                                <h3 className="text-lg font-bold text-gray-900 mb-2">Elimina Trasferta</h3>
                                <p className="text-sm text-gray-500 mb-6">Sei sicuro di voler eliminare questa trasferta? L'azione è irreversibile.</p>
                                <div className="flex justify-center gap-3">
                                    <button className="btn btn-ghost" onClick={() => setShowDeleteModal(false)}>Annulla</button>
                                    <button
                                        className="btn bg-red-600 hover:bg-red-700 text-white"
                                        onClick={handleDelete}
                                        disabled={actionLoading === 'delete'}
                                    >
                                        {actionLoading === 'delete' ? <Loader size={16} className="animate-spin mr-2" /> : null}
                                        Elimina
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )
            }
        </div>
    );
}

export default TripDetailPage;
