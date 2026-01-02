import { useParams, Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
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
    Ban,
    Sunrise,
    Building,
    Phone,
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
import { ConfirmModal } from '../../components/common';
import { leavesService } from '../../services/leaves.service';
import { formatApiError } from '../../utils/errorUtils';
import { useQueryClient } from '@tanstack/react-query';

interface ExcludedDay {
    date: string;
    reason: 'weekend' | 'holiday' | 'closure';
    name: string;
}

function ExcludedDaysSection({ startDate, endDate }: { startDate: string; endDate: string }) {
    const [excludedDays, setExcludedDays] = useState<ExcludedDay[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        const fetchExcludedDays = async () => {
            try {
                setLoading(true);
                const response = await leavesService.getExcludedDays(startDate, endDate);
                setExcludedDays(response.excluded_days);
            } catch (err) {
                console.error('Failed to load excluded days:', err);
                setError(true);
            } finally {
                setLoading(false);
            }
        };
        fetchExcludedDays();
    }, [startDate, endDate]);

    if (loading) {
        return (
            <div className="mt-6 pt-6 border-t border-gray-100">
                <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Loader size={14} className="animate-spin" />
                    Caricamento giorni esclusi...
                </div>
            </div>
        );
    }

    if (error || excludedDays.length === 0) {
        return null;
    }

    const getReasonIcon = (reason: string) => {
        switch (reason) {
            case 'weekend':
                return <Ban size={14} className="text-gray-400" />;
            case 'holiday':
                return <Sunrise size={14} className="text-amber-500" />;
            case 'closure':
                return <Building size={14} className="text-blue-500" />;
            default:
                return <Ban size={14} className="text-gray-400" />;
        }
    };

    const getReasonLabel = (reason: string) => {
        switch (reason) {
            case 'weekend':
                return 'Weekend';
            case 'holiday':
                return 'Festività';
            case 'closure':
                return 'Chiusura';
            default:
                return reason;
        }
    };

    return (
        <div className="mt-6 pt-6 border-t border-gray-100">
            <h4 className="text-xs uppercase font-semibold text-gray-400 mb-3 tracking-wide flex items-center gap-2">
                <Ban size={14} />
                Giorni non conteggiati ({excludedDays.length})
            </h4>
            <div className="space-y-2">
                {excludedDays.map((day, index) => (
                    <div
                        key={index}
                        className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg text-sm"
                    >
                        <div className="flex items-center gap-3">
                            {getReasonIcon(day.reason)}
                            <span className="text-gray-700 capitalize">
                                {format(new Date(day.date), 'EEEE d MMM', { locale: it })}
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-gray-500">{day.name}</span>
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${day.reason === 'weekend' ? 'bg-gray-200 text-gray-600' :
                                day.reason === 'holiday' ? 'bg-amber-100 text-amber-700' :
                                    'bg-blue-100 text-blue-700'
                                }`}>
                                {getReasonLabel(day.reason)}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

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
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [showRejectModal, setShowRejectModal] = useState(false);
    const [rejectReason, setRejectReason] = useState('');
    const [showCancelModal, setShowCancelModal] = useState(false);
    const [cancelReason, setCancelReason] = useState('');
    const [showConditionalModal, setShowConditionalModal] = useState(false);
    const [conditionType, setConditionType] = useState<string>('ric');
    const [conditionDetails, setConditionDetails] = useState('');
    const [showApproveModal, setShowApproveModal] = useState(false);
    const [approverNotes, setApproverNotes] = useState('');
    const [showRevokeModal, setShowRevokeModal] = useState(false);
    const [revokeReason, setRevokeReason] = useState('');
    const [showReopenModal, setShowReopenModal] = useState(false);
    const [reopenNotes, setReopenNotes] = useState('');
    const [showRecallModal, setShowRecallModal] = useState(false);
    const [recallReason, setRecallReason] = useState('');
    const [recallDate, setRecallDate] = useState('');


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

    const onRequestDelete = () => {
        if (!id) return;
        setShowDeleteConfirm(true);
    };

    const confirmDelete = async () => {
        if (!id) return;
        setActionLoading('delete');
        try {
            await leavesService.deleteRequest(id);
            toast.success('Richiesta eliminata');
            // Invalidate cache before navigating
            await queryClient.invalidateQueries({ queryKey: queryKeys.leaveRequests });
            navigate('/leaves');
        } catch (error: any) {
            toast.error(formatApiError(error));
            setActionLoading(null);
            setShowDeleteConfirm(false);
        }
        // Note: No finally block resetting loading/modal here on success because we navigate away (component unmounts)
        // Adding it might cause "update on unmounted component" warning
    };

    const handleApprove = () => {
        if (!id) return;
        setActionLoading('approve');
        approveMutation.mutate(
            { id, notes: approverNotes },
            {
                onSuccess: () => {
                    toast.success('Richiesta approvata');
                    setShowApproveModal(false);
                    setApproverNotes('');
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

    const handleConditionalApprove = async () => {
        if (!id || !conditionDetails.trim()) return;
        setActionLoading('conditional');
        try {
            await leavesService.approveConditional(id, conditionType, conditionDetails);
            toast.success('Richiesta approvata con condizioni');
            setShowConditionalModal(false);
            setConditionDetails('');
            refetch();
        } catch (error: any) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleRevoke = async () => {
        if (!id || !revokeReason.trim()) return;
        setActionLoading('revoke');
        try {
            await leavesService.revokeApproval(id, revokeReason);
            toast.success('Approvazione revocata');
            setShowRevokeModal(false);
            setRevokeReason('');
            refetch();
        } catch (error: any) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleReopen = async () => {
        if (!id) return;
        setActionLoading('reopen');
        try {
            await leavesService.reopenRequest(id, reopenNotes || undefined);
            toast.success('Richiesta riaperta');
            setShowReopenModal(false);
            setReopenNotes('');
            refetch();
        } catch (error: any) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleRecall = async () => {
        if (!id || !recallReason.trim() || !recallDate) return;
        setActionLoading('recall');
        try {
            await leavesService.recallRequest(id, recallReason, recallDate);
            toast.success('Dipendente richiamato in servizio');
            setShowRecallModal(false);
            setRecallReason('');
            setRecallDate('');
            refetch();
        } catch (error: any) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleConditionResponse = async (accept: boolean) => {
        if (!id) return;
        setActionLoading(accept ? 'accept_condition' : 'reject_condition');
        try {
            await leavesService.acceptCondition(id, accept);
            toast.success(accept ? 'Condizioni accettate' : 'Condizioni rifiutate');
            // Check if we need to close any modal - currently prompt is direct.
            refetch();
        } catch (error: any) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
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

                                {/* Excluded Days Section */}
                                <ExcludedDaysSection startDate={leave.start_date} endDate={leave.end_date} />
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

                            {/* Condition Details - Must be visible to user */}
                            {(leave as any).has_conditions && (leave as any).condition_details && (
                                <div className="p-6 border-b border-gray-100">
                                    <h3 className="flex items-center gap-2 text-sm font-bold text-amber-500 uppercase tracking-wider mb-4">
                                        <AlertCircle size={18} />
                                        Condizioni di Approvazione
                                    </h3>
                                    <div className="bg-amber-50 p-4 rounded-lg border border-amber-100 text-sm leading-relaxed">
                                        <div className="flex items-center gap-2 mb-2 font-semibold text-amber-800">
                                            <span className="uppercase">{(leave as any).condition_type}</span>
                                            {leave.status === 'approved' && (leave as any).condition_accepted && (
                                                <span className="bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded text-xs flex items-center gap-1">
                                                    <CheckCircle size={10} /> Accettata
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-gray-700">{(leave as any).condition_details}</p>
                                    </div>
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
                                        onClick={onRequestDelete}
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
                                        onClick={() => setShowApproveModal(true)}
                                        disabled={actionLoading !== null}

                                    >
                                        <CheckCircle size={18} />
                                        Approva
                                    </button>

                                    <button
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                        onClick={() => setShowConditionalModal(true)}
                                        disabled={actionLoading !== null}
                                    >
                                        <AlertCircle size={18} />
                                        Approva con Condizioni
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

                            {/* Revoke approved request (approver only, before start date) */}
                            {(leave.status === 'approved' || leave.status === 'approved_conditional') && isApprover && (
                                <>
                                    <button
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                        onClick={() => setShowRevokeModal(true)}
                                        disabled={actionLoading !== null}
                                    >
                                        <Ban size={18} />
                                        Revoca Approvazione
                                    </button>
                                    <button
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                        onClick={() => setShowRecallModal(true)}
                                        disabled={actionLoading !== null}
                                    >
                                        <Phone size={18} />
                                        Richiama in Servizio
                                    </button>
                                </>
                            )}

                            {/* Reopen rejected/cancelled request (approver only, before start date) */}
                            {(leave.status === 'rejected' || leave.status === 'cancelled') && isApprover && (
                                <button
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                    onClick={() => setShowReopenModal(true)}
                                    disabled={actionLoading !== null}
                                >
                                    <History size={18} />
                                    Riapri Richiesta
                                </button>
                            )}

                            {/* No actions for non-approvers on processed requests */}
                            {(leave.status === 'approved' || leave.status === 'rejected' || leave.status === 'cancelled') && !isApprover && (
                                <p className="text-center text-sm text-gray-500 italic">
                                    Nessuna azione disponibile per questa richiesta.
                                </p>
                            )}

                            {/* Employee Condition Acceptance */}
                            {leave.status === 'approved_conditional' && !isApprover && (
                                <>
                                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 mb-2">
                                        <strong>Attenzione:</strong> Questa richiesta è stata approvata con condizioni. Accetta per confermare o rifiuta per annullare.
                                    </div>
                                    <button
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                        onClick={() => handleConditionResponse(true)}
                                        disabled={actionLoading !== null}
                                    >
                                        {actionLoading === 'accept_condition' ? <Loader size={18} className="animate-spin" /> : <CheckCircle size={18} />}
                                        Accetta Condizioni
                                    </button>
                                    <button
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                        onClick={() => handleConditionResponse(false)}
                                        disabled={actionLoading !== null}
                                    >
                                        {actionLoading === 'reject_condition' ? <Loader size={18} className="animate-spin" /> : <XCircle size={18} />}
                                        Rifiuta Condizioni
                                    </button>
                                </>
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

            {/* Approve Modal */}
            {showApproveModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowApproveModal(false)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-emerald-50">
                            <h3 className="font-bold text-gray-900">Approva Richiesta</h3>
                            <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowApproveModal(false)}>
                                <XCircle size={20} />
                            </button>
                        </div>
                        <div className="p-6">
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Note (opzionale)</label>
                                <textarea
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 sm:text-sm min-h-[100px] resize-y"
                                    placeholder="Aggiungi eventuali note per il dipendente..."
                                    value={approverNotes}
                                    onChange={(e) => setApproverNotes(e.target.value)}
                                    rows={4}
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                            <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowApproveModal(false)}>
                                Annulla
                            </button>
                            <button
                                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                onClick={handleApprove}
                                disabled={actionLoading === 'approve'}
                            >
                                {actionLoading === 'approve' ? <Loader size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                                Conferma Approvazione
                            </button>
                        </div>
                    </div>
                </div>
            )}


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

            {/* Conditional Approval Modal */}
            {showConditionalModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowConditionalModal(false)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-amber-50">
                            <h3 className="font-bold text-gray-900">Approva con Condizioni</h3>
                            <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowConditionalModal(false)}>
                                <XCircle size={20} />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Tipo di Condizione <span className="text-red-500">*</span></label>
                                <select
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm"
                                    value={conditionType}
                                    onChange={(e) => setConditionType(e.target.value)}
                                >
                                    <option value="ric">🔔 Riserva di Richiamo (Salvo Necessità Aziendali)</option>
                                    <option value="rep">📞 Reperibilità Richiesta</option>
                                    <option value="par">📅 Approvazione Parziale</option>
                                    <option value="mod">✏️ Modifica Date Richiesta</option>
                                    <option value="alt">📋 Altra Condizione</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Dettagli Condizione <span className="text-red-500">*</span></label>
                                <textarea
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm min-h-[120px] resize-y"
                                    placeholder="Descrivi i dettagli della condizione. Es: 'Approvato salvo esigenze operative aziendali. In caso di necessità, sarà richiesto il rientro anticipato.'"
                                    value={conditionDetails}
                                    onChange={(e) => setConditionDetails(e.target.value)}
                                    rows={5}
                                />
                            </div>
                            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
                                <strong>Nota:</strong> Il dipendente dovrà accettare le condizioni prima che la richiesta diventi definitiva.
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                            <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowConditionalModal(false)}>
                                Annulla
                            </button>
                            <button
                                className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                onClick={handleConditionalApprove}
                                disabled={!conditionDetails.trim() || actionLoading === 'conditional'}
                            >
                                {actionLoading === 'conditional' ? <Loader size={16} className="animate-spin" /> : <AlertCircle size={16} />}
                                Approva con Condizioni
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

            {/* Revoke Modal */}
            {showRevokeModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowRevokeModal(false)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-orange-50">
                            <h3 className="font-bold text-gray-900">Revoca Approvazione</h3>
                            <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowRevokeModal(false)}>
                                <XCircle size={20} />
                            </button>
                        </div>
                        <div className="p-6">
                            <div className="mb-4 p-3 bg-orange-50 border border-orange-200 rounded-lg text-sm text-orange-800">
                                <strong>Attenzione:</strong> Revocare un'approvazione riporterà la richiesta a stato "rifiutato" e ripristinerà il saldo ferie del dipendente.
                            </div>
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Motivo della Revoca <span className="text-red-500">*</span></label>
                                <textarea
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-orange-500 focus:ring-orange-500 sm:text-sm min-h-[100px] resize-y"
                                    placeholder="Inserisci il motivo della revoca..."
                                    value={revokeReason}
                                    onChange={(e) => setRevokeReason(e.target.value)}
                                    rows={4}
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                            <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowRevokeModal(false)}>
                                Annulla
                            </button>
                            <button
                                className="flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                onClick={handleRevoke}
                                disabled={!revokeReason.trim() || actionLoading === 'revoke'}
                            >
                                {actionLoading === 'revoke' ? <Loader size={16} className="animate-spin" /> : <Ban size={16} />}
                                Conferma Revoca
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Reopen Modal */}
            {showReopenModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowReopenModal(false)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-blue-50">
                            <h3 className="font-bold text-gray-900">Riapri Richiesta</h3>
                            <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowReopenModal(false)}>
                                <XCircle size={20} />
                            </button>
                        </div>
                        <div className="p-6">
                            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                                <strong>Info:</strong> La richiesta verrà riportata allo stato "in attesa" per una nuova valutazione.
                            </div>
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Note (opzionale)</label>
                                <textarea
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm min-h-[100px] resize-y"
                                    placeholder="Aggiungi eventuali note..."
                                    value={reopenNotes}
                                    onChange={(e) => setReopenNotes(e.target.value)}
                                    rows={4}
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                            <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowReopenModal(false)}>
                                Annulla
                            </button>
                            <button
                                className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                onClick={handleReopen}
                                disabled={actionLoading === 'reopen'}
                            >
                                {actionLoading === 'reopen' ? <Loader size={16} className="animate-spin" /> : <History size={16} />}
                                Riapri Richiesta
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Recall Modal (Richiamo in Servizio) */}
            {showRecallModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowRecallModal(false)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-red-50">
                            <h3 className="font-bold text-gray-900">Richiamo in Servizio</h3>
                            <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowRecallModal(false)}>
                                <XCircle size={20} />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                                <strong>Art. 2109 c.c. e CCNL:</strong> Il richiamo in servizio durante le ferie è consentito solo per inderogabili esigenze aziendali.
                                Il dipendente ha diritto a:
                                <ul className="list-disc list-inside mt-1">
                                    <li>Riprogrammare i giorni non goduti</li>
                                    <li>Rimborso spese documentate (viaggio, soggiorno)</li>
                                    <li>Eventuali compensazioni previste dal CCNL</li>
                                </ul>
                            </div>
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Data Rientro in Servizio <span className="text-red-500">*</span></label>
                                <input
                                    type="date"
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm"
                                    value={recallDate}
                                    onChange={(e) => setRecallDate(e.target.value)}
                                    min={leave?.start_date}
                                    max={leave?.end_date}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Motivazione Urgenza Aziendale <span className="text-red-500">*</span></label>
                                <textarea
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm min-h-[100px] resize-y"
                                    placeholder="Descrivi la criticità aziendale che giustifica il richiamo..."
                                    value={recallReason}
                                    onChange={(e) => setRecallReason(e.target.value)}
                                    rows={4}
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                            <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowRecallModal(false)}>
                                Annulla
                            </button>
                            <button
                                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                onClick={handleRecall}
                                disabled={!recallReason.trim() || !recallDate || actionLoading === 'recall'}
                            >
                                {actionLoading === 'recall' ? <Loader size={16} className="animate-spin" /> : <Phone size={16} />}
                                Conferma Richiamo
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <ConfirmModal
                isOpen={showDeleteConfirm}
                onClose={() => setShowDeleteConfirm(false)}
                onConfirm={confirmDelete}
                title="Elimina Richiesta"
                message="Sei sicuro di voler eliminare definitivamente questa richiesta? L'azione è irreversibile."
                variant="danger"
                confirmLabel="Elimina"
            />
        </div>
    );
}

export default LeaveDetailPage;
