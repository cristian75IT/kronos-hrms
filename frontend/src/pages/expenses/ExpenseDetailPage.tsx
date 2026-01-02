/**
 * KRONOS - Expense Report Detail Page
 * Enterprise-grade expense report view
 */
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useState } from 'react';
import {
    ArrowLeft,
    FileText,
    CheckCircle,
    XCircle,
    AlertCircle,
    Receipt,
    Edit,
    Trash2,
    Send,
    CreditCard,
    Plus,
    Loader,
    Ban
} from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { useExpenseReport } from '../../hooks/useApi';
import { useAuth, useIsApprover, useIsAdmin, useIsHR } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { reportsService } from '../../services/expenses.service';

export function ExpenseDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const toast = useToast();
    const { user } = useAuth();
    const isApprover = useIsApprover();
    const isAdmin = useIsAdmin();
    const isHR = useIsHR();
    const { data: report, isLoading, refetch } = useExpenseReport(id || '');
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [showRejectModal, setShowRejectModal] = useState(false);
    const [rejectReason, setRejectReason] = useState('');
    const [showCancelModal, setShowCancelModal] = useState(false);
    const [cancelReason, setCancelReason] = useState('');
    const [showDeleteModal, setShowDeleteModal] = useState(false);

    // Check ownership
    const isOwner = user?.id === report?.user_id || user?.keycloak_id === report?.user_id;
    const reportStatus = report?.status?.toLowerCase() || 'draft';

    const getStatusConfig = (status: string) => {
        const s = status?.toLowerCase();
        const configs: Record<string, { className: string; icon: React.ReactNode; label: string }> = {
            draft: {
                className: 'bg-gray-100 text-gray-600 border-gray-200',
                icon: <FileText size={18} />,
                label: 'Bozza'
            },
            submitted: {
                className: 'bg-yellow-50 text-yellow-700 border-yellow-200',
                icon: <Send size={18} />,
                label: 'In Approvazione'
            },
            approved: {
                className: 'bg-green-50 text-green-700 border-green-200',
                icon: <CheckCircle size={18} />,
                label: 'Approvata'
            },
            rejected: {
                className: 'bg-red-50 text-red-700 border-red-200',
                icon: <XCircle size={18} />,
                label: 'Rifiutata'
            },
            paid: {
                className: 'bg-blue-50 text-blue-700 border-blue-200',
                icon: <CreditCard size={18} />,
                label: 'Pagata'
            },
            cancelled: {
                className: 'bg-gray-100 text-gray-500 border-gray-200',
                icon: <XCircle size={18} />,
                label: 'Annullata'
            }
        };
        return configs[s] || configs.draft;
    };

    // Action Handlers
    const handleSubmit = async () => {
        if (!id) return;
        setActionLoading('submit');
        try {
            await reportsService.submitReport(id);
            toast.success('Nota spese inviata per approvazione');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'invio');
        } finally {
            setActionLoading(null);
        }
    };

    const handleApprove = async () => {
        if (!id) return;
        setActionLoading('approve');
        try {
            await reportsService.approveReport(id, report?.total_amount);
            toast.success('Nota spese approvata');
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
            await reportsService.rejectReport(id, rejectReason);
            toast.success('Nota spese rifiutata');
            setShowRejectModal(false);
            setRejectReason('');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante il rifiuto');
        } finally {
            setActionLoading(null);
        }
    };

    const handleMarkPaid = async () => {
        if (!id) return;
        setActionLoading('paid');
        try {
            await reportsService.markPaid(id, 'Bonifico'); // Default payment ref for simplicity
            toast.success('Nota spese contrassegnata come pagata');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'operazione');
        } finally {
            setActionLoading(null);
        }
    };

    const handleDelete = async () => {
        if (!id) return;
        setActionLoading('delete');
        try {
            await reportsService.deleteReport(id);
            toast.success('Nota spese eliminata');
            navigate('/expenses');
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'eliminazione');
        } finally {
            setActionLoading(null);
        }
    };

    const handleCancel = async () => {
        if (!id || !cancelReason.trim()) return;
        setActionLoading('cancel');
        try {
            await reportsService.cancelReport(id, cancelReason);
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

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="flex flex-col items-center gap-4 text-gray-500">
                    <Loader size={32} className="animate-spin text-indigo-600" />
                    <p>Caricamento nota spese...</p>
                </div>
            </div>
        );
    }

    if (!report) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-8">
                <div className="bg-gray-100 p-4 rounded-full mb-4">
                    <AlertCircle size={48} className="text-gray-400" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Nota spesa non trovata</h2>
                <p className="text-gray-500 mb-6 max-w-md">La nota spese che stai cercando non esiste o è stata eliminata. Controlla l'URL o torna all'elenco.</p>
                <Link to="/expenses" className="btn btn-primary">
                    Torna alle Note Spese
                </Link>
            </div>
        );
    }

    const statusConfig = getStatusConfig(report.status);

    return (
        <div className="space-y-8 animate-fadeIn pb-12">
            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate(-1)} className="btn btn-ghost p-2 rounded-full hover:bg-gray-100">
                        <ArrowLeft size={20} className="text-gray-500" />
                    </button>
                    <div>
                        <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                            <Link to="/expenses" className="hover:text-primary transition-colors">Note Spese</Link>
                            <span>/</span>
                            <span>{report.report_number}</span>
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900">{report.title}</h1>
                    </div>
                </div>
                <div>
                    <div className={`px-4 py-2 rounded-full border flex items-center gap-2 text-sm font-medium ${statusConfig.className}`}>
                        {statusConfig.icon}
                        <span>{statusConfig.label}</span>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-8 items-start">
                {/* Main Column */}
                <div className="space-y-6">
                    {/* Items Card */}
                    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                        <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-100">
                            <div className="flex items-center gap-2 text-gray-900 font-semibold">
                                <Receipt size={18} className="text-indigo-600" />
                                <h3>Voci di Spesa</h3>
                            </div>
                            {report.status === 'draft' && (
                                <button className="btn btn-primary btn-sm flex items-center gap-2">
                                    <Plus size={16} />
                                    Aggiungi Voce
                                </button>
                            )}
                        </div>

                        {(!report.items || report.items.length === 0) ? (
                            <div className="flex flex-col items-center justify-center py-12 text-center bg-gray-50 rounded-lg border border-dashed border-gray-300">
                                <div className="bg-white p-3 rounded-full shadow-sm mb-3">
                                    <Receipt size={24} className="text-gray-400" />
                                </div>
                                <h3 className="text-gray-900 font-medium mb-1">Nessuna voce presente</h3>
                                <p className="text-sm text-gray-500">
                                    Aggiungi le voci di spesa per completare la nota.
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {report.items.map(item => (
                                    <div key={item.id} className="flex flex-col sm:flex-row sm:items-center p-4 rounded-lg bg-white border border-gray-200 hover:border-indigo-300 hover:shadow-sm transition-all gap-4">
                                        <div className="flex flex-col items-center justify-center min-w-[60px] p-2 bg-gray-50 rounded-lg border border-gray-100">
                                            <span className="text-xs text-gray-500 uppercase font-semibold">{format(new Date(item.date), 'MMM', { locale: it })}</span>
                                            <span className="text-xl font-bold text-gray-900">{format(new Date(item.date), 'dd', { locale: it })}</span>
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium text-gray-900 truncate mb-1">{item.description}</div>
                                            <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                                                {item.merchant_name && (
                                                    <span className="flex items-center gap-1">
                                                        <span>{item.merchant_name}</span>
                                                        <span className="w-1 h-1 rounded-full bg-gray-300"></span>
                                                    </span>
                                                )}
                                                <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200 font-medium">{item.expense_type_code}</span>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-4 justify-between sm:justify-end w-full sm:w-auto mt-2 sm:mt-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-gray-100">
                                            <div className="font-bold text-lg text-gray-900">
                                                € {Number(item.amount || 0).toFixed(2)}
                                            </div>
                                            {report.status === 'draft' && (
                                                <button className="btn btn-ghost p-2 text-red-500 hover:bg-red-50 hover:text-red-700 rounded-lg">
                                                    <Trash2 size={18} />
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Notes */}
                    {report.employee_notes && (
                        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4 border-b border-gray-100 pb-2">Note</h3>
                            <p className="text-gray-700 leading-relaxed text-sm bg-yellow-50/50 p-4 rounded-lg border border-yellow-100">{report.employee_notes}</p>
                        </div>
                    )}
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* Actions */}
                    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Azioni</h3>
                        <div className="space-y-3">
                            {reportStatus === 'draft' && isOwner && (
                                <>
                                    <button
                                        className="btn btn-primary w-full flex justify-center items-center gap-2 py-2.5"
                                        onClick={handleSubmit}
                                        disabled={actionLoading !== null}
                                    >
                                        {actionLoading === 'submit' ? <Loader size={18} className="animate-spin" /> : <Send size={18} />}
                                        Invia Richiesta
                                    </button>
                                    <Link to={`/expenses/${id}/edit`} className="btn btn-white border border-gray-300 text-gray-700 hover:bg-gray-50 w-full flex justify-center items-center gap-2 py-2.5">
                                        <Edit size={18} />
                                        Modifica
                                    </Link>
                                    <button
                                        className="btn btn-white border border-red-200 text-red-600 hover:bg-red-50 w-full flex justify-center items-center gap-2 py-2.5"
                                        onClick={() => setShowDeleteModal(true)}
                                        disabled={actionLoading !== null}
                                    >
                                        <Trash2 size={18} />
                                        Elimina
                                    </button>
                                </>
                            )}
                            {reportStatus === 'submitted' && isOwner && (
                                <button
                                    className="btn btn-white border border-red-200 text-red-600 hover:bg-red-50 w-full flex justify-center items-center gap-2 py-2.5"
                                    onClick={() => setShowCancelModal(true)}
                                    disabled={actionLoading !== null}
                                >
                                    <Ban size={18} />
                                    Annulla Richiesta
                                </button>
                            )}
                            {reportStatus !== 'draft' && reportStatus !== 'paid' && isApprover && (!isOwner || isAdmin || isHR) && (
                                <>
                                    <button
                                        className="btn bg-emerald-600 hover:bg-emerald-700 text-white w-full flex justify-center items-center gap-2 py-2.5 shadow-sm"
                                        onClick={handleApprove}
                                        disabled={actionLoading !== null || reportStatus === 'approved'}
                                    >
                                        {actionLoading === 'approve' ? <Loader size={18} className="animate-spin" /> : <CheckCircle size={18} />}
                                        Approva
                                    </button>
                                    <button
                                        className="btn bg-white border border-red-200 text-red-600 hover:bg-red-50 w-full flex justify-center items-center gap-2 py-2.5"
                                        onClick={() => setShowRejectModal(true)}
                                        disabled={actionLoading !== null || reportStatus === 'rejected'}
                                    >
                                        <XCircle size={18} />
                                        Rifiuta
                                    </button>
                                </>
                            )}
                            {reportStatus === 'approved' && (
                                <>
                                    {isApprover && (
                                        <button
                                            className="btn btn-primary w-full flex justify-center items-center gap-2 py-2.5"
                                            onClick={handleMarkPaid}
                                            disabled={actionLoading !== null}
                                        >
                                            {actionLoading === 'paid' ? <Loader size={18} className="animate-spin" /> : <CreditCard size={18} />}
                                            Segna come Pagato
                                        </button>
                                    )}
                                    {isOwner && (
                                        <button
                                            className="btn btn-white border border-red-200 text-red-600 hover:bg-red-50 w-full flex justify-center items-center gap-2 py-2.5"
                                            onClick={() => setShowCancelModal(true)}
                                            disabled={actionLoading !== null}
                                        >
                                            <Ban size={18} />
                                            Annulla Nota Spese
                                        </button>
                                    )}
                                </>
                            )}
                        </div>
                    </div>

                    {/* Summary */}
                    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Riepilogo</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="text-sm text-gray-500">Totale</span>
                                <span className="font-bold text-xl text-gray-900">€ {Number(report.total_amount || 0).toFixed(2)}</span>
                            </div>
                            {report.approved_amount !== undefined && (
                                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                    <span className="text-sm text-gray-500">Approvato</span>
                                    <span className="font-bold text-lg text-emerald-600">€ {Number(report.approved_amount || 0).toFixed(2)}</span>
                                </div>
                            )}
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="text-sm text-gray-500">Periodo</span>
                                <span className="text-sm font-medium text-gray-900 text-right">
                                    {format(new Date(report.period_start), 'd MMM', { locale: it })} - {format(new Date(report.period_end), 'd MMM yyyy', { locale: it })}
                                </span>
                            </div>
                            <div className="flex justify-between items-center py-2">
                                <span className="text-sm text-gray-500">N. Voci</span>
                                <span className="text-sm font-medium text-gray-900">{report.items?.length || 0}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Reject Modal */}
            {showRejectModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md animate-scaleIn overflow-hidden" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50">
                            <h3 className="font-bold text-gray-900">Rifiuta Nota Spese</h3>
                            <button className="text-gray-400 hover:text-gray-600" onClick={() => setShowRejectModal(false)}>
                                <XCircle size={20} />
                            </button>
                        </div>
                        <div className="p-6">
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Motivo del Rifiuto <span className="text-red-500">*</span></label>
                                <textarea
                                    className="w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 min-h-[100px]"
                                    placeholder="Inserisci il motivo del rifiuto..."
                                    value={rejectReason}
                                    onChange={(e) => setRejectReason(e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 p-4 bg-gray-50/50 border-t border-gray-100">
                            <button className="btn btn-ghost text-gray-600 hover:bg-white border border-transparent hover:border-gray-200" onClick={() => setShowRejectModal(false)}>
                                Annulla
                            </button>
                            <button
                                className="btn bg-red-600 hover:bg-red-700 text-white shadow-sm flex items-center gap-2"
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
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md animate-scaleIn overflow-hidden" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50">
                            <h3 className="font-bold text-gray-900">Annulla Richiesta</h3>
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
            )}

            {/* Delete Modal */}
            {showDeleteModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md animate-scaleIn overflow-hidden" onClick={e => e.stopPropagation()}>
                        <div className="p-6 text-center">
                            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                                <Trash2 className="h-6 w-6 text-red-600" />
                            </div>
                            <h3 className="text-lg font-bold text-gray-900 mb-2">Elimina Nota Spese</h3>
                            <p className="text-sm text-gray-500 mb-6">Sei sicuro di voler eliminare questa nota spese? L'azione è irreversibile.</p>
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
            )}
        </div>
    );
}


export default ExpenseDetailPage;
