/**
 * KRONOS - Leave Detail Actions Hook
 * 
 * Encapsulates all action logic for leave request detail page.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useToast } from '../../context/ToastContext';
import { leavesService } from '../../services/leaves.service';
import approvalsService from '../../services/approvals.service';
import { formatApiError } from '../../utils/errorUtils';
import { useApproveLeaveRequest, useRejectLeaveRequest, queryKeys } from './useLeaves';

interface UseLeaveDetailActionsProps {
    leaveId: string | undefined;
    approvalRequestId: string | undefined;
    onRefetch: () => void;
}

export function useLeaveDetailActions({ leaveId, approvalRequestId, onRefetch }: UseLeaveDetailActionsProps) {
    const navigate = useNavigate();
    const toast = useToast();
    const queryClient = useQueryClient();

    // Mutations
    const approveMutation = useApproveLeaveRequest();
    const rejectMutation = useRejectLeaveRequest();

    // Loading state
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    // Modal states
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

    // Action handlers
    const handleSubmit = async () => {
        if (!leaveId) return;
        setActionLoading('submit');
        try {
            await leavesService.submitRequest(leaveId);
            toast.success('Richiesta inviata con successo');
            onRefetch();
        } catch (error: unknown) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleCancel = async () => {
        if (!leaveId || !cancelReason.trim()) return;
        setActionLoading('cancel');
        try {
            await leavesService.cancelRequest(leaveId, cancelReason);
            toast.success('Richiesta annullata');
            setShowCancelModal(false);
            setCancelReason('');
            onRefetch();
        } catch (error: unknown) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const onRequestDelete = () => {
        if (!leaveId) return;
        setShowDeleteConfirm(true);
    };

    const confirmDelete = async () => {
        if (!leaveId) return;
        setActionLoading('delete');
        try {
            await leavesService.deleteRequest(leaveId);
            toast.success('Richiesta eliminata');
            navigate('/leaves');
            queryClient.invalidateQueries({ queryKey: queryKeys.leaveRequests });
        } catch (error: unknown) {
            toast.error(formatApiError(error));
            setActionLoading(null);
            setShowDeleteConfirm(false);
        }
    };

    const handleApprove = () => {
        if (!leaveId) return;
        setActionLoading('approve');
        approveMutation.mutate(
            { id: leaveId, approvalRequestId, notes: approverNotes },
            {
                onSuccess: () => {
                    toast.success('Richiesta approvata');
                    setShowApproveModal(false);
                    setApproverNotes('');
                    onRefetch();
                    setActionLoading(null);
                },
                onError: (error: unknown) => {
                    toast.error(formatApiError(error));
                    setActionLoading(null);
                }
            }
        );
    };

    const handleReject = () => {
        if (!leaveId || !rejectReason.trim()) return;
        setActionLoading('reject');
        rejectMutation.mutate(
            { id: leaveId, approvalRequestId, reason: rejectReason },
            {
                onSuccess: () => {
                    toast.success('Richiesta rifiutata');
                    setShowRejectModal(false);
                    setRejectReason('');
                    onRefetch();
                    setActionLoading(null);
                },
                onError: (error: unknown) => {
                    toast.error(formatApiError(error));
                    setActionLoading(null);
                }
            }
        );
    };

    const handleConditionalApprove = async () => {
        if (!leaveId || !conditionDetails.trim()) return;
        if (!approvalRequestId) {
            toast.error('Impossibile approvare: richiesta di approvazione non trovata');
            return;
        }
        setActionLoading('conditional');
        try {
            await approvalsService.approveRequestConditional(approvalRequestId, conditionType, conditionDetails);
            toast.success('Richiesta approvata con condizioni');
            setShowConditionalModal(false);
            setConditionDetails('');
            onRefetch();
        } catch (error: unknown) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleRevoke = async () => {
        if (!leaveId || !revokeReason.trim()) return;
        setActionLoading('revoke');
        try {
            await leavesService.revokeApproval(leaveId, revokeReason);
            toast.success('Approvazione revocata');
            setShowRevokeModal(false);
            setRevokeReason('');
            onRefetch();
        } catch (error: unknown) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleReopen = async () => {
        if (!leaveId) return;
        setActionLoading('reopen');
        try {
            await leavesService.reopenRequest(leaveId, reopenNotes || undefined);
            toast.success('Richiesta riaperta');
            setShowReopenModal(false);
            setReopenNotes('');
            onRefetch();
        } catch (error: unknown) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleRecall = async () => {
        if (!leaveId || !recallReason.trim() || !recallDate) return;
        setActionLoading('recall');
        try {
            await leavesService.recallRequest(leaveId, recallReason, recallDate);
            toast.success('Dipendente richiamato in servizio');
            setShowRecallModal(false);
            setRecallReason('');
            setRecallDate('');
            onRefetch();
        } catch (error: unknown) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    const handleConditionResponse = async (accept: boolean) => {
        if (!leaveId) return;
        setActionLoading(accept ? 'accept_condition' : 'reject_condition');
        try {
            await leavesService.acceptCondition(leaveId, accept);
            toast.success(accept ? 'Condizioni accettate' : 'Condizioni rifiutate');
            onRefetch();
        } catch (error: unknown) {
            toast.error(formatApiError(error));
        } finally {
            setActionLoading(null);
        }
    };

    return {
        // Loading
        actionLoading,

        // Actions
        handleSubmit,
        handleCancel,
        onRequestDelete,
        confirmDelete,
        handleApprove,
        handleReject,
        handleConditionalApprove,
        handleRevoke,
        handleReopen,
        handleRecall,
        handleConditionResponse,

        // Modal states and setters
        showDeleteConfirm,
        setShowDeleteConfirm,
        showRejectModal,
        setShowRejectModal,
        rejectReason,
        setRejectReason,
        showCancelModal,
        setShowCancelModal,
        cancelReason,
        setCancelReason,
        showConditionalModal,
        setShowConditionalModal,
        conditionType,
        setConditionType,
        conditionDetails,
        setConditionDetails,
        showApproveModal,
        setShowApproveModal,
        approverNotes,
        setApproverNotes,
        showRevokeModal,
        setShowRevokeModal,
        revokeReason,
        setRevokeReason,
        showReopenModal,
        setShowReopenModal,
        reopenNotes,
        setReopenNotes,
        showRecallModal,
        setShowRecallModal,
        recallReason,
        setRecallReason,
        recallDate,
        setRecallDate,
    };
}
