/**
 * KRONOS - Leave Detail Modals Component
 * 
 * Contains all modals used in the leave detail page.
 */
import { Loader, CheckCircle, XCircle, AlertCircle, Phone, History } from 'lucide-react';
import { ConfirmModal } from '../common';

interface LeaveDetailModalsProps {
    // Delete Modal
    showDeleteConfirm: boolean;
    setShowDeleteConfirm: (show: boolean) => void;
    confirmDelete: () => void;

    // Cancel Modal
    showCancelModal: boolean;
    setShowCancelModal: (show: boolean) => void;
    cancelReason: string;
    setCancelReason: (reason: string) => void;
    handleCancel: () => void;

    // Approve Modal
    showApproveModal: boolean;
    setShowApproveModal: (show: boolean) => void;
    approverNotes: string;
    setApproverNotes: (notes: string) => void;
    handleApprove: () => void;

    // Reject Modal
    showRejectModal: boolean;
    setShowRejectModal: (show: boolean) => void;
    rejectReason: string;
    setRejectReason: (reason: string) => void;
    handleReject: () => void;

    // Conditional Approve Modal
    showConditionalModal: boolean;
    setShowConditionalModal: (show: boolean) => void;
    conditionType: string;
    setConditionType: (type: string) => void;
    conditionDetails: string;
    setConditionDetails: (details: string) => void;
    handleConditionalApprove: () => void;

    // Revoke Modal
    showRevokeModal: boolean;
    setShowRevokeModal: (show: boolean) => void;
    revokeReason: string;
    setRevokeReason: (reason: string) => void;
    handleRevoke: () => void;

    // Reopen Modal
    showReopenModal: boolean;
    setShowReopenModal: (show: boolean) => void;
    reopenNotes: string;
    setReopenNotes: (notes: string) => void;
    handleReopen: () => void;

    // Recall Modal
    showRecallModal: boolean;
    setShowRecallModal: (show: boolean) => void;
    recallReason: string;
    setRecallReason: (reason: string) => void;
    recallDate: string;
    setRecallDate: (date: string) => void;
    handleRecall: () => void;

    // Loading state
    actionLoading: string | null;
}

export function LeaveDetailModals({
    showDeleteConfirm,
    setShowDeleteConfirm,
    confirmDelete,
    showCancelModal,
    setShowCancelModal,
    cancelReason,
    setCancelReason,
    handleCancel,
    showApproveModal,
    setShowApproveModal,
    approverNotes,
    setApproverNotes,
    handleApprove,
    showRejectModal,
    setShowRejectModal,
    rejectReason,
    setRejectReason,
    handleReject,
    showConditionalModal,
    setShowConditionalModal,
    conditionType,
    setConditionType,
    conditionDetails,
    setConditionDetails,
    handleConditionalApprove,
    showRevokeModal,
    setShowRevokeModal,
    revokeReason,
    setRevokeReason,
    handleRevoke,
    showReopenModal,
    setShowReopenModal,
    reopenNotes,
    setReopenNotes,
    handleReopen,
    showRecallModal,
    setShowRecallModal,
    recallReason,
    setRecallReason,
    recallDate,
    setRecallDate,
    handleRecall,
    actionLoading,
}: LeaveDetailModalsProps) {
    return (
        <>
            {/* Delete Confirm Modal */}
            <ConfirmModal
                isOpen={showDeleteConfirm}
                onClose={() => setShowDeleteConfirm(false)}
                onConfirm={confirmDelete}
                title="Elimina Bozza"
                message="Sei sicuro di voler eliminare questa bozza? L'azione è irreversibile."
                confirmLabel="Elimina"
                variant="danger"
            />

            {/* Cancel Modal */}
            {showCancelModal && (
                <ModalWrapper onClose={() => setShowCancelModal(false)}>
                    <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                        <h3 className="font-bold text-gray-900">Annulla Richiesta</h3>
                        <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowCancelModal(false)}>
                            <XCircle size={20} />
                        </button>
                    </div>
                    <div className="p-6">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Motivo annullamento *</label>
                            <textarea
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm min-h-[100px] resize-y"
                                placeholder="Es: Ho modificato i piani per le ferie..."
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
                            {actionLoading === 'cancel' ? <Loader size={16} className="animate-spin" /> : <XCircle size={16} />}
                            Annulla Richiesta
                        </button>
                    </div>
                </ModalWrapper>
            )}

            {/* Approve Modal */}
            {showApproveModal && (
                <ModalWrapper onClose={() => setShowApproveModal(false)}>
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
                </ModalWrapper>
            )}

            {/* Reject Modal */}
            {showRejectModal && (
                <ModalWrapper onClose={() => setShowRejectModal(false)}>
                    <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                        <h3 className="font-bold text-gray-900">Rifiuta Richiesta</h3>
                        <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowRejectModal(false)}>
                            <XCircle size={20} />
                        </button>
                    </div>
                    <div className="p-6">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Motivazione del rifiuto *</label>
                            <textarea
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm min-h-[100px] resize-y"
                                placeholder="Es: Le date richieste non sono disponibili..."
                                value={rejectReason}
                                onChange={(e) => setRejectReason(e.target.value)}
                                rows={4}
                            />
                            <p className="text-xs text-gray-500">La motivazione verrà comunicata al dipendente.</p>
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
                            {actionLoading === 'reject' ? <Loader size={16} className="animate-spin" /> : <XCircle size={16} />}
                            Conferma Rifiuto
                        </button>
                    </div>
                </ModalWrapper>
            )}

            {/* Conditional Approve Modal */}
            {showConditionalModal && (
                <ModalWrapper onClose={() => setShowConditionalModal(false)}>
                    <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-amber-50">
                        <h3 className="font-bold text-gray-900">Approva con Condizioni</h3>
                        <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowConditionalModal(false)}>
                            <XCircle size={20} />
                        </button>
                    </div>
                    <div className="p-6 space-y-4">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Tipo di condizione</label>
                            <select
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm"
                                value={conditionType}
                                onChange={(e) => setConditionType(e.target.value)}
                            >
                                <option value="ric">Riserva di Richiamo</option>
                                <option value="rep">Reperibilità</option>
                                <option value="par">Approvazione Parziale</option>
                                <option value="mod">Modifica Date</option>
                                <option value="alt">Altra Condizione</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Dettagli condizione *</label>
                            <textarea
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 sm:text-sm min-h-[100px] resize-y"
                                placeholder="Es: La richiesta è approvata, ma potrebbe essere necessario un richiamo in caso di emergenze operative..."
                                value={conditionDetails}
                                onChange={(e) => setConditionDetails(e.target.value)}
                                rows={4}
                            />
                        </div>
                        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                            <strong>Nota:</strong> Il dipendente dovrà accettare le condizioni prima che la richiesta sia definitivamente approvata.
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
                </ModalWrapper>
            )}

            {/* Revoke Modal */}
            {showRevokeModal && (
                <ModalWrapper onClose={() => setShowRevokeModal(false)}>
                    <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-orange-50">
                        <h3 className="font-bold text-gray-900">Revoca Approvazione</h3>
                        <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowRevokeModal(false)}>
                            <XCircle size={20} />
                        </button>
                    </div>
                    <div className="p-6">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Motivazione della revoca *</label>
                            <textarea
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-orange-500 focus:ring-orange-500 sm:text-sm min-h-[100px] resize-y"
                                placeholder="Es: Necessità operative non previste..."
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
                            {actionLoading === 'revoke' ? <Loader size={16} className="animate-spin" /> : <XCircle size={16} />}
                            Conferma Revoca
                        </button>
                    </div>
                </ModalWrapper>
            )}

            {/* Reopen Modal */}
            {showReopenModal && (
                <ModalWrapper onClose={() => setShowReopenModal(false)}>
                    <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-blue-50">
                        <h3 className="font-bold text-gray-900">Riapri Richiesta</h3>
                        <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowReopenModal(false)}>
                            <XCircle size={20} />
                        </button>
                    </div>
                    <div className="p-6">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Note (opzionale)</label>
                            <textarea
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm min-h-[100px] resize-y"
                                placeholder="Es: La richiesta viene riaperta per..."
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
                </ModalWrapper>
            )}

            {/* Recall Modal */}
            {showRecallModal && (
                <ModalWrapper onClose={() => setShowRecallModal(false)}>
                    <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-red-50">
                        <h3 className="font-bold text-gray-900">Richiama in Servizio</h3>
                        <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowRecallModal(false)}>
                            <XCircle size={20} />
                        </button>
                    </div>
                    <div className="p-6 space-y-4">
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Data di rientro *</label>
                            <input
                                type="date"
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm"
                                value={recallDate}
                                onChange={(e) => setRecallDate(e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Motivazione del richiamo *</label>
                            <textarea
                                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm min-h-[100px] resize-y"
                                placeholder="Es: Esigenze operative urgenti..."
                                value={recallReason}
                                onChange={(e) => setRecallReason(e.target.value)}
                                rows={4}
                            />
                        </div>
                        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
                            <strong>Attenzione:</strong> Questa azione notificherà il dipendente e modificherà la data di fine del permesso.
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
                </ModalWrapper>
            )}
        </>
    );
}

// Helper component for modal wrapper
function ModalWrapper({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scaleIn"
                onClick={e => e.stopPropagation()}
            >
                {children}
            </div>
        </div>
    );
}
