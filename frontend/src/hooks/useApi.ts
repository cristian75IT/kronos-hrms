/**
 * KRONOS - React Query Hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { leavesService } from '../services/leaves.service';
import { tripsService, reportsService } from '../services/expenses.service';
import { walletsService } from '../services/wallets.service';
import { userService } from '../services/userService';
import { configService } from '../services/config.service';
import { calendarService } from '../services/calendar.service';
import { useToast } from '../context/ToastContext';
import type {
    LeaveRequestCreate,
    LeaveRequestUpdate,
    BusinessTrip,
    ExpenseReport,
    ExpenseItem,
    UserWithProfile,
    TripWallet,
    TripWalletTransaction,
} from '../types';

// ═══════════════════════════════════════════════════════════════════
// Query Keys
// ═══════════════════════════════════════════════════════════════════

export const queryKeys = {
    // Leaves
    leaveRequests: ['leave-requests'] as const,
    leaveRequest: (id: string) => ['leave-requests', id] as const,
    pendingApprovals: ['leave-requests', 'pending'] as const,
    leaveBalance: (year?: number) => ['leave-balance', year] as const,
    balanceSummary: ['balance-summary'] as const,
    calendarEvents: (start: string, end: string) => ['calendar', start, end] as const,

    // Expenses
    trips: ['trips'] as const,
    trip: (id: string) => ['trips', id] as const,
    pendingTrips: ['trips', 'pending'] as const,
    tripAllowances: (tripId: string) => ['trips', tripId, 'allowances'] as const,

    reports: ['expense-reports'] as const,
    report: (id: string) => ['expense-reports', id] as const,
    pendingReports: ['expense-reports', 'pending'] as const,
    tripWallet: (tripId: string) => ['trip-wallet', tripId] as const,
    tripTransactions: (tripId: string) => ['trip-wallet', tripId, 'transactions'] as const,

    // Users
    users: ['users'] as const,
    user: (id: string) => ['users', id] as const,

    // Configs
    configs: ['configs'] as const,
    contractTypes: ['contract-types'] as const,
};

// ═══════════════════════════════════════════════════════════════════
// Leave Hooks
// ═══════════════════════════════════════════════════════════════════

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
        retry: 1, // Don't spam if it fails
    });
}

export function useCalendarEvents(startDate: string, endDate: string, includeTeam = false) {
    return useQuery({
        queryKey: queryKeys.calendarEvents(startDate, endDate),
        queryFn: () => leavesService.getCalendarEvents(startDate, endDate, includeTeam, true),
        enabled: !!startDate && !!endDate,
    });
}

export function useCalendarRange(startDate: string, endDate: string, locationId?: string) {
    return useQuery({
        queryKey: ['calendar-range', startDate, endDate, locationId],
        queryFn: () => calendarService.getCalendarRange({ start_date: startDate, end_date: endDate, location_id: locationId }),
        enabled: !!startDate && !!endDate,
    });
}

export function useCreateCalendarEvent() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: any) => calendarService.createEvent(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['calendar-range'] });
        },
    });
}

// User Calendars
export function useUserCalendars() {
    return useQuery({
        queryKey: ['user-calendars'],
        queryFn: () => calendarService.getUserCalendars(),
    });
}

export function useCreateUserCalendar() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: any) => calendarService.createUserCalendar(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['user-calendars'] });
        },
    });
}

export function useDeleteUserCalendar() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => calendarService.deleteUserCalendar(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['user-calendars'] });
            queryClient.invalidateQueries({ queryKey: ['calendar-range'] });
        },
    });
}

export function useShareUserCalendar() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ calendarId, data }: { calendarId: string, data: any }) =>
            calendarService.shareCalendar(calendarId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['user-calendars'] });
        },
    });
}

export function useUnshareUserCalendar() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ calendarId, sharedUserId }: { calendarId: string, sharedUserId: string }) =>
            calendarService.unshareCalendar(calendarId, sharedUserId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['user-calendars'] });
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
        mutationFn: async ({ id, approvalRequestId, notes }: { id: string; approvalRequestId?: string; notes?: string }) => {
            // Use centralized approvals service if approval_request_id is available
            if (approvalRequestId) {
                const { approvalsService } = await import('../services/approvals.service');
                return approvalsService.approveRequest(approvalRequestId, notes);
            }
            // Fallback to direct leaves service for legacy requests
            return leavesService.approveRequest(id, notes);
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
        mutationFn: async ({ id, approvalRequestId, reason }: { id: string; approvalRequestId?: string; reason: string }) => {
            // Use centralized approvals service if approval_request_id is available
            if (approvalRequestId) {
                const { approvalsService } = await import('../services/approvals.service');
                return approvalsService.rejectRequest(approvalRequestId, reason);
            }
            // Fallback to direct leaves service for legacy requests
            return leavesService.rejectRequest(id, reason);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.leaveRequests });
            queryClient.invalidateQueries({ queryKey: queryKeys.pendingApprovals });
            queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });  // For approvals page
        },
    });
}

// ═══════════════════════════════════════════════════════════════════
// Trip Hooks
// ═══════════════════════════════════════════════════════════════════

export function useTrips(status?: string, year?: number) {
    return useQuery({
        queryKey: [...queryKeys.trips, { status, year }],
        queryFn: () => tripsService.getMyTrips(status, year),
    });
}

export function useTrip(id: string) {
    return useQuery({
        queryKey: queryKeys.trip(id),
        queryFn: () => tripsService.getTrip(id),
        enabled: !!id,
    });
}

export function usePendingTrips() {
    return useQuery({
        queryKey: queryKeys.pendingTrips,
        queryFn: () => tripsService.getPendingTrips(),
    });
}

export function useTripAllowances(tripId: string) {
    return useQuery({
        queryKey: queryKeys.tripAllowances(tripId),
        queryFn: () => tripsService.getTripAllowances(tripId),
        enabled: !!tripId,
    });
}

export function useCreateTrip() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: Partial<BusinessTrip>) => tripsService.createTrip(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.trips });
            queryClient.invalidateQueries({ queryKey: queryKeys.pendingTrips });
        },
    });
}

export function useSubmitTrip() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: string) => tripsService.submitTrip(id),
        onSuccess: (_, id) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.trip(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.trips });
        },
    });
}

export function useUploadTripAttachment() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, file }: { id: string; file: File }) =>
            tripsService.uploadAttachment(id, file),
        onSuccess: (_, { id }) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.trip(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.trips });
        },
    });
}

export function useTripWallet(tripId: string) {
    return useQuery<TripWallet | null>({
        queryKey: queryKeys.tripWallet(tripId),
        queryFn: async () => {
            try {
                return await walletsService.getTripWallet(tripId);
            } catch (error: any) {
                // 404 means wallet doesn't exist yet - this is expected for unapproved trips
                if (error?.response?.status === 404) {
                    return null;
                }
                throw error;
            }
        },
        enabled: !!tripId,
        retry: false, // Don't retry on 404
    });
}

export function useTripTransactions(tripId: string) {
    return useQuery<TripWalletTransaction[]>({
        queryKey: queryKeys.tripTransactions(tripId),
        queryFn: async () => {
            try {
                return await walletsService.getTripTransactions(tripId);
            } catch (error: any) {
                // 404 means wallet doesn't exist yet
                if (error?.response?.status === 404) {
                    return [];
                }
                throw error;
            }
        },
        enabled: !!tripId,
        retry: false, // Don't retry on 404
    });
}

// ═══════════════════════════════════════════════════════════════════
// Expense Report Hooks
// ═══════════════════════════════════════════════════════════════════

export function useExpenseReports(status?: string) {
    return useQuery({
        queryKey: [...queryKeys.reports, { status }],
        queryFn: () => reportsService.getMyReports(status),
    });
}

export const useReports = useExpenseReports;
export const useReport = useExpenseReport;

export function useExpenseReport(id: string) {
    return useQuery({
        queryKey: queryKeys.report(id),
        queryFn: () => reportsService.getReport(id),
        enabled: !!id,
    });
}

export function usePendingReports() {
    return useQuery({
        queryKey: queryKeys.pendingReports,
        queryFn: () => reportsService.getPendingReports(),
    });
}

export function useCreateExpenseReport() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: Partial<ExpenseReport>) => reportsService.createReport(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.reports });
        },
    });
}

export function useAddExpenseItem() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ reportId, data }: { reportId: string; data: Partial<ExpenseItem> }) =>
            reportsService.addItem(reportId, data),
        onSuccess: (_, { reportId }) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.report(reportId) });
        },
    });
}

export function useSubmitExpenseReport() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: string) => reportsService.submitReport(id),
        onSuccess: (_, id) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.report(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.reports });
        },
    });
}

export function useUploadReportAttachment() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, file }: { id: string; file: File }) =>
            reportsService.uploadAttachment(id, file),
        onSuccess: (_, { id }) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.report(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.reports });
        },
    });
}

// ═══════════════════════════════════════════════════════════════════
// User Hooks
// ═══════════════════════════════════════════════════════════════════

export function useUsers() {
    return useQuery({
        queryKey: queryKeys.users,
        queryFn: () => userService.getUsers(),
    });
}

export function useUser(id: string) {
    return useQuery({
        queryKey: queryKeys.user(id),
        queryFn: () => userService.getUser(id),
        enabled: !!id,
    });
}

export function useCreateUser() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: Partial<UserWithProfile>) => userService.createUser(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.users });
        },
    });
}

export function useUpdateUser() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<UserWithProfile> }) =>
            userService.updateUser(id, data),
        onSuccess: (_, { id }) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.user(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.users });
        },
    });
}

export function useContractTypes() {
    return useQuery({
        queryKey: queryKeys.contractTypes,
        queryFn: () => userService.getContractTypes(),
    });
}

export function useCreateContractType() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: any) => userService.createContractType(data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.contractTypes }),
    });
}

export function useUpdateContractType() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: any }) => userService.updateContractType(id, data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.contractTypes }),
    });
}

export function useExpenseTypes(activeOnly = true) {
    return useQuery({
        queryKey: ['expense-types', activeOnly],
        queryFn: () => configService.getExpenseTypes(activeOnly),
    });
}

// ═══════════════════════════════════════════════════════════════════
// Config Hooks
// ═══════════════════════════════════════════════════════════════════

export function useConfigs() {
    return useQuery({
        queryKey: queryKeys.configs,
        queryFn: () => configService.getAllConfigs(),
    });
}

export function useUpdateConfig() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ key, value }: { key: string; value: any }) =>
            configService.updateConfig(key, value),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.configs });
        },
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

export function useClearCache() {
    return useMutation({
        mutationFn: () => configService.clearCache(),
    });
}
