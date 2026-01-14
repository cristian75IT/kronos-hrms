/**
 * KRONOS - System Calendars Hook
 *
 * Manages data fetching and mutations for holidays, closures, and exceptions.
 */
import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '../../context/ToastContext';
import { calendarService } from '../../services/calendar.service';
import type { Holiday, WorkingDayException } from '../../services/calendar.service';

// Query keys
export const systemCalendarKeys = {
    all: ['system-calendars'] as const,
    holidays: (year: number) => [...systemCalendarKeys.all, 'holidays', year] as const,
    closures: (year: number) => [...systemCalendarKeys.all, 'closures', year] as const,
    exceptions: (year: number) => [...systemCalendarKeys.all, 'exceptions', year] as const,
};

// Form types
export interface HolidayForm {
    date: string;
    name: string;
    scope: 'national' | 'regional' | 'local' | 'company';
}

export interface ClosureForm {
    name: string;
    description: string;
    start_date: string;
    end_date: string;
    closure_type: 'total' | 'partial';
    is_paid: boolean;
    consumes_leave_balance: boolean;
}

export interface ExceptionForm {
    date: string;
    exception_type: 'working' | 'non_working';
    reason: string;
}

export function useSystemCalendars(year: number) {
    const toast = useToast();
    const queryClient = useQueryClient();

    // Data queries
    const holidaysQuery = useQuery({
        queryKey: systemCalendarKeys.holidays(year),
        queryFn: () => calendarService.getHolidays({ year }),
        staleTime: 5 * 60 * 1000,
    });

    const closuresQuery = useQuery({
        queryKey: systemCalendarKeys.closures(year),
        queryFn: () => calendarService.getClosures({ year }),
        staleTime: 5 * 60 * 1000,
    });

    const exceptionsQuery = useQuery({
        queryKey: systemCalendarKeys.exceptions(year),
        queryFn: () => calendarService.getWorkingDayExceptions(year),
        staleTime: 5 * 60 * 1000,
    });

    // Derived data
    const holidays = holidaysQuery.data || [];
    const closures = closuresQuery.data || [];
    const exceptions = (exceptionsQuery.data || []).filter((e: WorkingDayException) => e.exception_type === 'working');
    const isLoading = holidaysQuery.isLoading || closuresQuery.isLoading || exceptionsQuery.isLoading;

    // Invalidate all data
    const invalidateAll = useCallback(() => {
        queryClient.invalidateQueries({ queryKey: systemCalendarKeys.holidays(year) });
        queryClient.invalidateQueries({ queryKey: systemCalendarKeys.closures(year) });
        queryClient.invalidateQueries({ queryKey: systemCalendarKeys.exceptions(year) });
    }, [queryClient, year]);

    // Holiday mutations
    const createHolidayMutation = useMutation({
        mutationFn: (data: HolidayForm) => calendarService.createHoliday({ ...data, year }),
        onSuccess: () => {
            toast.success('Festività aggiunta');
            invalidateAll();
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore');
        },
    });

    const updateHolidayMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<HolidayForm> }) =>
            calendarService.updateHoliday(id, data),
        onSuccess: () => {
            toast.success('Festività aggiornata');
            invalidateAll();
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore');
        },
    });

    const deleteHolidayMutation = useMutation({
        mutationFn: (id: string) => calendarService.deleteHoliday(id),
        onSuccess: () => {
            toast.success('Festività eliminata');
            invalidateAll();
        },
        onError: () => toast.error('Errore'),
    });

    const confirmHolidayMutation = useMutation({
        mutationFn: (id: string) => calendarService.updateHoliday(id, { is_confirmed: true }),
        onSuccess: () => {
            toast.success('Festività confermata');
            invalidateAll();
        },
        onError: () => toast.error('Errore nella conferma'),
    });

    const generateHolidaysMutation = useMutation({
        mutationFn: () => calendarService.generateHolidaysForYear(year),
        onSuccess: (created: Holiday[]) => {
            toast.success(`${created.length} festività nazionali ${year} generate con successo`);
            invalidateAll();
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore nella generazione');
        },
    });

    const copyHolidaysMutation = useMutation({
        mutationFn: () => calendarService.copyHolidaysFromYear(year - 1, year),
        onSuccess: (copied: number) => {
            toast.success(`${copied} festività copiate dal ${year - 1}`);
            invalidateAll();
        },
        onError: () => toast.error('Errore nella copia'),
    });

    // Closure mutations
    const createClosureMutation = useMutation({
        mutationFn: (data: ClosureForm) => calendarService.createClosure({ ...data, year }),
        onSuccess: () => {
            toast.success('Chiusura pianificata');
            invalidateAll();
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore');
        },
    });

    const updateClosureMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: ClosureForm }) =>
            calendarService.updateClosure(id, data),
        onSuccess: () => {
            toast.success('Chiusura aggiornata');
            invalidateAll();
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore');
        },
    });

    const deleteClosureMutation = useMutation({
        mutationFn: (id: string) => calendarService.deleteClosure(id),
        onSuccess: () => {
            toast.success('Chiusura eliminata');
            invalidateAll();
        },
        onError: () => toast.error('Errore'),
    });

    // Exception mutations
    const createExceptionMutation = useMutation({
        mutationFn: (data: ExceptionForm) => calendarService.createWorkingDayException({ ...data, year }),
        onSuccess: () => {
            toast.success('Eccezione salvata');
            invalidateAll();
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore');
        },
    });

    const deleteExceptionMutation = useMutation({
        mutationFn: (id: string) => calendarService.deleteWorkingDayException(id),
        onSuccess: () => {
            toast.success('Eccezione eliminata');
            invalidateAll();
        },
        onError: () => toast.error('Errore'),
    });

    return {
        // Data
        holidays,
        closures,
        exceptions,
        isLoading,

        // Holiday actions
        createHoliday: createHolidayMutation.mutate,
        updateHoliday: updateHolidayMutation.mutate,
        deleteHoliday: deleteHolidayMutation.mutate,
        confirmHoliday: confirmHolidayMutation.mutate,
        generateHolidays: generateHolidaysMutation.mutate,
        copyHolidays: copyHolidaysMutation.mutate,

        // Closure actions
        createClosure: createClosureMutation.mutate,
        updateClosure: updateClosureMutation.mutate,
        deleteClosure: deleteClosureMutation.mutate,

        // Exception actions
        createException: createExceptionMutation.mutate,
        deleteException: deleteExceptionMutation.mutate,

        // Mutation states
        isGenerating: generateHolidaysMutation.isPending || copyHolidaysMutation.isPending,
        isSavingHoliday: createHolidayMutation.isPending || updateHolidayMutation.isPending,
        isSavingClosure: createClosureMutation.isPending || updateClosureMutation.isPending,
        isSavingException: createExceptionMutation.isPending,
    };
}

// Hook for subscription URLs
export function useSubscriptionUrls(year: number) {
    const [urls, setUrls] = useState<{
        holidays: { url: string; description: string };
        closures: { url: string; description: string };
        combined: { url: string; description: string };
    } | null>(null);
    const toast = useToast();

    const fetchUrls = useCallback(async () => {
        if (urls) return urls;
        try {
            const data = await calendarService.getSubscriptionUrls(year);
            setUrls(data);
            return data;
        } catch (error) {
            console.error('Failed to load subscription urls', error);
            toast.error('Impossibile caricare gli URL di sincronizzazione');
            return null;
        }
    }, [year, urls, toast]);

    return { urls, fetchUrls };
}
