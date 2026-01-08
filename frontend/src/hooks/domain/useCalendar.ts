import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { calendarService } from '../../services/calendar.service';
import { leavesService } from '../../services/leaves.service';
import { queryKeys } from './queryKeys';

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

export function useUpdateCalendarEvent() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: any }) => calendarService.updateEvent(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['calendar-range'] });
        },
    });
}

export function useDeleteCalendarEvent() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => calendarService.deleteEvent(id),
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

export function useUpdateUserCalendar() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: any }) => calendarService.updateUserCalendar(id, data),
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
