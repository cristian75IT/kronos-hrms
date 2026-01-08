import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { leavesService } from '../../services/leaves.service';
import { useToast } from '../../context/ToastContext';
import { queryKeys } from './queryKeys';
export { queryKeys };
import type { LeaveRequestCreate, LeaveRequestUpdate } from '../../types';

export function useLeaveRequests(year?: number, status?: string) {
    return useQuery({
        queryKey: [...queryKeys.leaveRequests, { year, status }],
        queryFn: () => leavesService.getMyRequests(year, status),
    });
}

export function useLeaveRequest(id: string) {
    return useQuery({
        queryKey: queryKeys.leaveRequest(id),
        queryFn: () => leavesService.getRequest(id),
        enabled: !!id,
    });
}

export function usePendingApprovals() {
    return useQuery({
        queryKey: queryKeys.pendingApprovals,
        queryFn: () => leavesService.getPendingApprovals(),
    });
}

export function useApprovalHistory(params?: { status?: string; year?: number; limit?: number }) {
    return useQuery({
        queryKey: ['approvalHistory', params],
        queryFn: () => leavesService.getApprovalHistory(params),
    });
}

export function useLeaveBalance(year?: number, userId?: string) {
    return useQuery({
        queryKey: [...queryKeys.leaveBalance(year), userId],
        queryFn: () => leavesService.getMyBalance(year, userId),
    });
}

export function useBalanceSummary(userId?: string) {
    const toast = useToast();
    return useQuery({
        queryKey: [...queryKeys.balanceSummary, userId],
        queryFn: async () => {
            try {
                return await leavesService.getBalanceSummary(userId);
            } catch (error: any) {
                toast.error(
                    'Errore durante il recupero del saldo ferie. Per favore, ricarica la pagina.'
                );
                throw error;
            }
        },
        retry: 1,
    });
}

export function useRecalculateAccruals() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (year?: number) => leavesService.recalculateAccruals(year),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['leave-balance'] });
            queryClient.invalidateQueries({ queryKey: queryKeys.balanceSummary });
        },
    });
}

// Mutations
export function useCreateLeaveRequest() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: LeaveRequestCreate) => leavesService.createRequest(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.leaveRequests });
            queryClient.invalidateQueries({ queryKey: queryKeys.balanceSummary });
        },
    });
}

export function useUpdateLeaveRequest() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: LeaveRequestUpdate }) =>
            leavesService.updateRequest(id, data),
        onSuccess: (_, { id }) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.leaveRequest(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.leaveRequests });
            queryClient.invalidateQueries({ queryKey: queryKeys.balanceSummary });
        },
    });
}

export function useSubmitLeaveRequest() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: string) => leavesService.submitRequest(id),
        onSuccess: (_, id) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.leaveRequest(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.leaveRequests });
            queryClient.invalidateQueries({ queryKey: queryKeys.balanceSummary });
        },
    });
}

export function useApproveLeaveRequest() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ approvalRequestId, notes }: { id?: string; approvalRequestId?: string; notes?: string }) => {
            if (!approvalRequestId) {
                throw new Error('Impossibile approvare: richiesta di approvazione non trovata. Contattare l\'amministratore.');
            }
            const { approvalsService } = await import('../../services/approvals.service');
            return approvalsService.approveRequest(approvalRequestId, notes);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.leaveRequests });
            queryClient.invalidateQueries({ queryKey: queryKeys.pendingApprovals });
            queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });  // For approvals page
        },
    });
}

export function useRejectLeaveRequest() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ approvalRequestId, reason }: { id?: string; approvalRequestId?: string; reason: string }) => {
            if (!approvalRequestId) {
                throw new Error('Impossibile rifiutare: richiesta di approvazione non trovata. Contattare l\'amministratore.');
            }
            const { approvalsService } = await import('../../services/approvals.service');
            return approvalsService.rejectRequest(approvalRequestId, reason);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.leaveRequests });
            queryClient.invalidateQueries({ queryKey: queryKeys.pendingApprovals });
            queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });  // For approvals page
        },
    });
}
