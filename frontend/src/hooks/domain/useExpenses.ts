import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tripsService, reportsService } from '../../services/expenses.service';
import { queryKeys } from './queryKeys';
import type { BusinessTrip, ExpenseReport, ExpenseItem } from '../../types';

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

// ═══════════════════════════════════════════════════════════════════
// Expense Report Hooks
// ═══════════════════════════════════════════════════════════════════

export function useExpenseReports(status?: string) {
    return useQuery({
        queryKey: [...queryKeys.reports, { status }],
        queryFn: () => reportsService.getMyReports(status),
    });
}

export function useStandaloneReports(status?: string) {
    return useQuery({
        queryKey: ['standaloneReports', { status }],
        queryFn: () => reportsService.getStandaloneReports(status),
    });
}

export function useExpenseReport(id: string) {
    return useQuery({
        queryKey: queryKeys.report(id),
        queryFn: () => reportsService.getReport(id),
        enabled: !!id,
    });
}
// Aliases for backward compatibility in imports if needed, 
// though we will use specific names in aggregator
export const useReports = useExpenseReports;
export const useReport = useExpenseReport;

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
