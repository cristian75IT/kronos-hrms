import { useParams, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import {
    ArrowLeft,
    Calendar,
    Clock,
    FileText,
    CheckCircle,
    XCircle,
    AlertCircle,
    Download,
    MessageSquare,
    History,
    Edit,
    Trash2,
    Send,
    Loader,
} from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import {
    useLeaveRequests,
    useApproveLeaveRequest,
    useRejectLeaveRequest,
    queryKeys
} from '../../hooks/useApi';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { leavesService } from '../../services/leaves.service';
import { formatApiError } from '../../utils/errorUtils';
import { useQueryClient } from '@tanstack/react-query';

export function LeaveDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const toast = useToast();
    const queryClient = useQueryClient();

    const { isApprover } = useAuth();
    const { data: leaves, isLoading, refetch } = useLeaveRequests(new Date().getFullYear());

    // Mutations
    const approveMutation = useApproveLeaveRequest();
    const rejectMutation = useRejectLeaveRequest();

    const [activeTab, setActiveTab] = useState<'details' | 'history'>('details');
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [showRejectModal, setShowRejectModal] = useState(false);
    const [rejectReason, setRejectReason] = useState('');
    const [showCancelModal, setShowCancelModal] = useState(false);
    const [cancelReason, setCancelReason] = useState('');

    // Find the specific leave request
    const leave = leaves?.find(l => l.id === id);

    // Action handlers
    const handleSubmit = async () => {
        if (!id) return;
        setActionLoading('submit');
        try {
            await leavesService.submitRequest(id);
            toast.success('Richiesta inviata con successo');
            refetch();
        } catch (error: any) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleCancel = async () => {
        if (!id || !cancelReason.trim()) return;
        setActionLoading('cancel');
        try {
            await leavesService.cancelRequest(id, cancelReason);
            toast.success('Richiesta annullata');
            setShowCancelModal(false);
            setCancelReason('');
            refetch();
        } catch (error: any) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleDelete = async () => {
        if (!id) return;
        if (!confirm('Sei sicuro di voler eliminare questa richiesta?')) return;
        setActionLoading('delete');
        try {
            await leavesService.deleteRequest(id);
            toast.success('Richiesta eliminata');
            // Invalidate cache before navigating
            await queryClient.invalidateQueries({ queryKey: queryKeys.leaveRequests });
            navigate('/leaves');
        } catch (error: any) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleApprove = () => {
        if (!id) return;
        setActionLoading('approve');
        approveMutation.mutate(
            { id, notes: '' },
            {
                onSuccess: () => {
                    toast.success('Richiesta approvata');
                    refetch(); // Update local list
                    setActionLoading(null);
                },
                onError: (error: any) => {
                    toast.error(formatApiError(error));
                    setActionLoading(null);
                }
            }
        );
    };

    const handleReject = () => {
        if (!id || !rejectReason.trim()) return;
        setActionLoading('reject');
        rejectMutation.mutate(
            { id, reason: rejectReason },
            {
                onSuccess: () => {
                    toast.success('Richiesta rifiutata');
                    setShowRejectModal(false);
                    setRejectReason('');
                    refetch(); // Update local list
                    setActionLoading(null);
                },
                onError: (error: any) => {
                    toast.error(formatApiError(error));
                    setActionLoading(null);
                }
            }
        );
    };

    if (isLoading) {
        return (
            <div className="detail-page animate-fadeIn">
                <div className="detail-loading">
                    <div className="spinner-lg" />
                    <p>Caricamento richiesta...</p>
                </div>
            </div>
        );
    }

    if (!leave) {
        return (
            <div className="detail-page animate-fadeIn">
                <div className="detail-empty">
                    <AlertCircle size={48} />
                    <h2>Richiesta non trovata</h2>
                    <p>La richiesta che stai cercando non esiste o è stata eliminata.</p>
                    <Link to="/leaves" className="btn btn-primary">
                        Torna alle Ferie
                    </Link>
                </div>
            </div>
        );
    }

    const getStatusConfig = (status: string) => {
        const configs: Record<string, { className: string; icon: React.ReactNode; label: string }> = {
            pending: {
                className: 'bg-amber-50 text-amber-700 border-amber-200',
                icon: <Clock size={16} />,
                label: 'In Attesa'
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
            draft: {
                className: 'bg-gray-100 text-gray-600 border-gray-200',
                icon: <FileText size={16} />,
                label: 'Bozza'
            },
            cancelled: {
                className: 'bg-gray-100 text-gray-500 border-gray-200',
                icon: <XCircle size={16} />,
                label: 'Annullata'
            },
        };
        return configs[status] || configs.pending;
    };

    const statusConfig = getStatusConfig(leave.status);

    const leaveTypeNames: Record<string, string> = {
        FER: 'Ferie',
        ROL: 'Riduzione Orario Lavoro',
        PAR: 'Ex-Festività / Altri',
        MAL: 'Malattia',
        MAT: 'Maternità/Paternità',
        LUT: 'Lutto',
        STU: 'Studio',
        DON: 'Donazione Sangue',
        L104: 'Legge 104',
        SW: 'Smart Working',
        NRT: 'Non Retribuito',
    };

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
                        <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                            <Link to="/leaves" className="hover:text-indigo-600 transition-colors">Ferie</Link>
                            <span>/</span>
                            <span>Dettaglio Richiesta</span>
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            {leaveTypeNames[leave.leave_type_code] || leave.leave_type_code}
                        </h1>
                    </div>
                </div>
                <div>
                    <div className={`px-4 py-2 rounded-full border flex items-center gap-2 text-sm font-semibold ${statusConfig.className}`}>
                        {statusConfig.icon}
                        <span>{statusConfig.label}</span>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-8 items-start">
                {/* Left Column - Main Info */}
                <div>
                    {/* Tabs */}
                    <div className="flex p-1 space-x-1 bg-gray-100/80 rounded-xl mb-6 border border-gray-200">
                        <button
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${activeTab === 'details'
                                    ? 'bg-white text-gray-900 shadow-sm ring-1 ring-black/5'
                                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200/50'
                                }`}
                            onClick={() => setActiveTab('details')}
                        >
                            <FileText size={16} />
                            Dettagli
                        </button>
                        <button
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${activeTab === 'history'
                                    ? 'bg-white text-gray-900 shadow-sm ring-1 ring-black/5'
                                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200/50'
                                }`}
                            onClick={() => setActiveTab('history')}
                        >
                            <History size={16} />
                            Cronologia
                        </button>
                    </div>

                    {activeTab === 'details' && (
                        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm animate-fadeInUp">
                            {/* Period Info */}
                            <div className="p-6 border-b border-gray-100">
                                <h3 className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider mb-6">
                                    <Calendar size={18} />
                                    Periodo Richiesto
                                </h3>
                                <div className="bg-gray-50/50 rounded-xl p-6 border border-gray-100">
                                    <div className="flex flex-col gap-6">

                                        {/* Start Date */}
                                        <div>
                                            <div className="text-xs uppercase font-semibold text-gray-400 mb-1 tracking-wide">Dal</div>
                                            <div className="flex flex-wrap items-center gap-3">
                                                <span className="text-lg font-semibold text-gray-900 capitalize">
                                                    {format(new Date(leave.start_date), 'EEEE d MMMM yyyy', { locale: it })}
                                                </span>
                                                {leave.start_half_day && (
                                                    <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                                                        Solo pomeriggio
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Days connector */}
                                        <div className="flex items-center gap-4">
                                            <div className="h-px bg-gray-200 flex-1"></div>
                                            <span className="px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-sm font-bold border border-indigo-100">
                                                {leave.days_requested} giorni
                                            </span>
                                            <div className="h-px bg-gray-200 flex-1"></div>
                                        </div>

                                        {/* End Date */}
                                        <div>
                                            <div className="text-xs uppercase font-semibold text-gray-400 mb-1 tracking-wide">Al</div>
                                            <div className="flex flex-wrap items-center gap-3">
                                                <span className="text-lg font-semibold text-gray-900 capitalize">
                                                    {format(new Date(leave.end_date), 'EEEE d MMMM yyyy', { locale: it })}
                                                </span>
                                                {leave.end_half_day && (
                                                    <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                                                        Solo mattina
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                    </div>
                                </div>
                            </div>

                            {/* Notes */}
                            {leave.employee_notes && (
                                <div className="p-6 border-b border-gray-100">
                                    <h3 className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">
                                        <MessageSquare size={18} />
                                        Note del Dipendente
                                    </h3>
                                    <p className="text-gray-700 bg-yellow-50/50 p-4 rounded-lg border border-yellow-100 text-sm leading-relaxed">
                                        {leave.employee_notes}
                                    </p>
                                </div>
                            )}

                            {/* Approver Notes */}
                            {leave.approver_notes && (
                                <div className="p-6 border-b border-gray-100">
                                    <h3 className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">
                                        <MessageSquare size={18} />
                                        Note dell'Approvatore
                                    </h3>
                                    <p className="text-gray-700 bg-gray-50 p-4 rounded-lg border border-gray-100 text-sm leading-relaxed">
                                        {leave.approver_notes}
                                    </p>
                                </div>
                            )}

                            {/* Attachment - future feature */}
                            {(leave as any).attachment_path && (
                                <div className="p-6">
                                    <h3 className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">
                                        <FileText size={18} />
                                        Allegato
                                    </h3>
                                    <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                                        <Download size={16} />
                                        Scarica Allegato
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'history' && (
                        <div className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm animate-fadeInUp">
                            <div className="relative border-l-2 border-gray-100 ml-3 space-y-8">
                                <div className="relative pl-8">
                                    <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 border-white bg-indigo-500 shadow-sm" />
                                    <div className="font-semibold text-gray-900">Richiesta Creata</div>
                                    <div className="text-sm text-gray-500 mt-1">
                                        {format(new Date(leave.created_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                                    </div>
                                </div>
                                {leave.status !== 'draft' && (
                                    <div className="relative pl-8">
                                        <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 border-white bg-blue-500 shadow-sm" />
                                        <div className="font-semibold text-gray-900">Richiesta Inviata</div>
                                        <div className="text-sm text-gray-500 mt-1">
                                            {format(new Date(leave.created_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                                        </div>
                                    </div>
                                )}
                                {leave.status === 'approved' && leave.approved_at && (
                                    <div className="relative pl-8">
                                        <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 border-white bg-emerald-500 shadow-sm" />
                                        <div className="font-semibold text-gray-900">Richiesta Approvata</div>
                                        <div className="text-sm text-gray-500 mt-1">
                                            {format(new Date(leave.approved_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                                        </div>
                                    </div>
                                )}
                                {leave.status === 'rejected' && (
                                    <div className="relative pl-8">
                                        <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 border-white bg-red-500 shadow-sm" />
                                        <div className="font-semibold text-gray-900">Richiesta Rifiutata</div>
                                        <div className="text-sm text-gray-500 mt-1">
                                            {format(new Date(leave.updated_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Column - Actions & Summary */}
                <div className="space-y-6">
                    {/* Actions Card */}
                    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide mb-4">Azioni</h3>
                        <div className="space-y-3">
                            {leave.status === 'draft' && (
                                <>
                                    <button
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                        onClick={handleSubmit}
                                        disabled={actionLoading !== null}
                                    >
                                        {actionLoading === 'submit' ? <Loader size={18} className="animate-spin" /> : <Send size={18} />}
                                        Invia Richiesta
                                    </button>
                                    <Link
                                        to={`/leaves/${id}/edit`}
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-medium transition-colors"
                                    >
                                        <Edit size={18} />
                                        Modifica
                                    </Link>
                                    <button
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors disabled:opacity-50"
                                        onClick={handleDelete}
                                        disabled={actionLoading !== null}
                                    >
                                        {actionLoading === 'delete' ? <Loader size={18} className="animate-spin" /> : <Trash2 size={18} />}
                                        Elimina
                                    </button>
                                </>
                            )}
                            {leave.status === 'pending' && !isApprover && (
                                <button
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-white border border-red-200 text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors disabled:opacity-50"
                                    onClick={() => setShowCancelModal(true)}
                                    disabled={actionLoading !== null}
                                >
                                    <XCircle size={18} />
                                    Annulla Richiesta
                                </button>
                            )}
                            {leave.status === 'pending' && isApprover && (
                                <>
                                    <button
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                        onClick={handleApprove}
                                        disabled={actionLoading !== null}
                                    >
                                        {actionLoading === 'approve' ? <Loader size={18} className="animate-spin" /> : <CheckCircle size={18} />}
                                        Approva
                                    </button>
                                    <button
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                        onClick={() => setShowRejectModal(true)}
                                        disabled={actionLoading !== null}
                                    >
                                        <XCircle size={18} />
                                        Rifiuta
                                    </button>
                                </>
                            )}
                            {(leave.status === 'approved' || leave.status === 'rejected' || leave.status === 'cancelled') && (
                                <p className="text-center text-sm text-gray-500 italic">
                                    Nessuna azione disponibile per questa richiesta.
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Summary Card */}
                    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide mb-4">Riepilogo</h3>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="text-sm text-gray-500">Tipo</span>
                                <span className="text-sm font-medium text-gray-900">{leaveTypeNames[leave.leave_type_code] || leave.leave_type_code}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="text-sm text-gray-500">Giorni</span>
                                <span className="text-sm font-bold text-gray-900">{leave.days_requested}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="text-sm text-gray-500">Creata il</span>
                                <span className="text-sm font-medium text-gray-900">
                                    {format(new Date(leave.created_at), 'd MMM yyyy', { locale: it })}
                                </span>
                            </div>
                            {leave.approved_at && (
                                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                    <span className="text-sm text-gray-500">Approvata il</span>
                                    <span className="text-sm font-medium text-gray-900">
                                        {format(new Date(leave.approved_at), 'd MMM yyyy', { locale: it })}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Reject Modal */}
            {showRejectModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowRejectModal(false)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                            <h3 className="font-bold text-gray-900">Rifiuta Richiesta</h3>
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
            )}

            {/* Cancel Modal */}
            {showCancelModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowCancelModal(false)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                            <h3 className="font-bold text-gray-900">Annulla Richiesta</h3>
                            <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowCancelModal(false)}>
                                <XCircle size={20} />
                            </button>
                        </div>
                        <div className="p-6">
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Motivo dell'Annullamento <span className="text-red-500">*</span></label>
                                <textarea
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm min-h-[100px] resize-y"
                                    placeholder="Inserisci il motivo dell'annullamento..."
                                    value={cancelReason}
                                    onChange={(e) => setCancelReason(e.target.value)}
                                    rows={4}
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                            <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowCancelModal(false)}>
                                Indietro
                            </button>
                            <button
                                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                onClick={handleCancel}
                                disabled={!cancelReason.trim() || actionLoading === 'cancel'}
                            >
                                {actionLoading === 'cancel' ? <Loader size={16} className="animate-spin" /> : null}
                                Conferma Annullamento
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default LeaveDetailPage;
