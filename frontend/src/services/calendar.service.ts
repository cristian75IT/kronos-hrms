/**
 * KRONOS - Calendar Service Client
 * 
 * Frontend service for interacting with the Calendar microservice.
 * Manages holidays, closures, events, and working day calculations.
 */
import api from './api';

const CALENDAR_BASE = '/api/v1';

// ═══════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════

export interface Holiday {
    id: string;
    name: string;
    description?: string;
    date: string;
    year: number;
    scope: 'national' | 'regional' | 'local' | 'company';
    location_id?: string;
    region_code?: string;
    is_recurring: boolean;
    recurrence_rule?: string;
    is_confirmed: boolean;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface HolidayCreate {
    name: string;
    description?: string;
    date: string;
    year: number;
    scope?: 'national' | 'regional' | 'local' | 'company';
    location_id?: string;
    region_code?: string;
    is_recurring?: boolean;
    recurrence_rule?: string;
}

export interface HolidayUpdate {
    name?: string;
    description?: string;
    date?: string;
    scope?: string;
    location_id?: string;
    region_code?: string;
    is_recurring?: boolean;
    recurrence_rule?: string;
    is_confirmed?: boolean;
    is_active?: boolean;
}

export interface Closure {
    id: string;
    name: string;
    description?: string;
    start_date: string;
    end_date: string;
    year: number;
    closure_type: 'total' | 'partial';
    affected_departments?: string[];
    affected_locations?: string[];
    is_paid: boolean;
    consumes_leave_balance: boolean;
    leave_type_code?: string;
    is_active: boolean;
    created_by?: string;
    created_at: string;
    updated_at: string;
}

export interface ClosureCreate {
    name: string;
    description?: string;
    start_date: string;
    end_date: string;
    year: number;
    closure_type?: 'total' | 'partial';
    affected_departments?: string[];
    affected_locations?: string[];
    is_paid?: boolean;
    consumes_leave_balance?: boolean;
    leave_type_code?: string;
}

export interface ClosureUpdate {
    name?: string;
    description?: string;
    start_date?: string;
    end_date?: string;
    closure_type?: string;
    affected_departments?: string[];
    affected_locations?: string[];
    is_paid?: boolean;
    consumes_leave_balance?: boolean;
    leave_type_code?: string;
    is_active?: boolean;
}

export interface CalendarEvent {
    id: string;
    title: string;
    description?: string;
    start_date: string;
    end_date: string;
    start_time?: string;
    end_time?: string;
    is_all_day: boolean;
    event_type: string;
    user_id?: string;
    visibility: 'private' | 'team' | 'public';
    location?: string;
    is_virtual: boolean;
    meeting_url?: string;
    is_recurring: boolean;
    recurrence_rule?: string;
    color: string;
    status: string;
    calendar_id?: string;
    participants: EventParticipant[];
    created_at: string;
    updated_at: string;
}

export interface EventParticipant {
    id: string;
    user_id: string;
    response_status: 'pending' | 'accepted' | 'declined' | 'tentative';
    is_organizer: boolean;
    is_optional: boolean;
    responded_at?: string;
}

export interface CalendarDayItem {
    id: string;
    title: string;
    item_type: 'holiday' | 'closure' | 'event' | 'leave' | 'trip';
    start_date: string;
    end_date: string;
    color: string;
    metadata?: Record<string, unknown>;
}

export interface CalendarDayView {
    date: string;
    is_working_day: boolean;
    is_holiday: boolean;
    items: CalendarDayItem[];
}

export interface UserCalendar {
    id: string;
    user_id: string; // Mapped from owner_id
    owner_id?: string; // Original backend field
    name: string;
    description?: string;
    color: string;
    is_active: boolean;
    is_public?: boolean;
    type?: 'PERSONAL' | 'TEAM' | 'LOCATION' | 'SYSTEM';
    created_at: string;
    updated_at: string;
    shared_with?: CalendarShare[];
    is_owner: boolean;
}

export interface CalendarShare {
    id: string;
    shared_with_user_id: string;
    can_edit: boolean;
    created_at: string;
}

export interface CalendarShareCreate {
    shared_with_user_id: string;
    can_edit?: boolean;
}

export interface UserCalendarCreate {
    name: string;
    description?: string;
    color?: string;
}

export interface UserCalendarUpdate {
    name?: string;
    description?: string;
    color?: string;
    is_active?: boolean;
}

export interface CalendarRangeView {
    start_date: string;
    end_date: string;
    days: CalendarDayView[];
    working_days_count: number;
}

export interface WorkingDaysRequest {
    start_date: string;
    end_date: string;
    location_id?: string;
    exclude_closures?: boolean;
    exclude_holidays?: boolean;
}

export interface WorkingDaysResponse {
    start_date: string;
    end_date: string;
    total_calendar_days: number;
    working_days: number;
    holidays: string[];
    closure_days: string[];
    weekend_days: string[];
}

export interface WorkingDayException {
    id: string;
    date: string;
    year: number;
    exception_type: 'working' | 'non_working';
    reason?: string;
    location_id?: string;
    department_code?: string;
    created_at: string;
}

export interface WorkingDayExceptionCreate {
    date: string;
    year: number;
    exception_type: 'working' | 'non_working';
    reason?: string;
    location_id?: string;
    department_code?: string;
}



// ═══════════════════════════════════════════════════════════
// HOLIDAYS API
// ═══════════════════════════════════════════════════════════

export const calendarService = {
    // Holidays (Unified Calendar)
    getHolidays: async (params?: {
        year?: number;
        start_date?: string;
        end_date?: string;
    }): Promise<Holiday[]> => {
        // Use new list endpoint
        const response = await api.get(`/calendar/holidays-list`, { params });
        return response.data;
    },

    getHoliday: async (id: string): Promise<Holiday> => {
        // TODO: This might need admin endpoint if managing items directly
        // For now stubbed or legacy
        const response = await api.get(`/calendar/holidays/${id}`);
        return response.data;
    },

    createHoliday: async (_data: HolidayCreate): Promise<Holiday> => {
        // Requires Admin profile management usually. 
        // We map this to creating a holiday in a default profile? 
        // Or fail. 
        throw new Error("Use Admin Profile Management to create holidays");
    },

    updateHoliday: async (_id: string, _data: HolidayUpdate): Promise<Holiday> => {
        throw new Error("Use Admin Profile Management to update holidays");
    },

    deleteHoliday: async (_id: string): Promise<void> => {
        throw new Error("Use Admin Profile Management to delete holidays");
    },

    // Closures
    getClosures: async (params?: {
        year?: number;
        location_id?: string;
    }): Promise<Closure[]> => {
        const response = await api.get(`/calendar/closures-list`, { params });
        return response.data;
    },

    getClosure: async (id: string): Promise<Closure> => {
        const response = await api.get(`/closures/${id}`);
        return response.data;
    },

    createClosure: async (data: ClosureCreate): Promise<Closure> => {
        const response = await api.post(`/closures`, data);
        return response.data;
    },

    updateClosure: async (id: string, data: ClosureUpdate): Promise<Closure> => {
        const response = await api.put(`/closures/${id}`, data);
        return response.data;
    },

    deleteClosure: async (id: string): Promise<void> => {
        await api.delete(`/closures/${id}`);
    },

    // Events
    getEvents: async (params?: {
        start_date?: string;
        end_date?: string;
        event_type?: string;
        include_public?: boolean;
    }): Promise<CalendarEvent[]> => {
        const response = await api.get(`/calendar/events`, { params });
        return response.data;
    },

    getEvent: async (id: string): Promise<CalendarEvent> => {
        const response = await api.get(`/calendar/events/${id}`);
        return response.data;
    },

    createEvent: async (data: {
        title: string;
        description?: string;
        start_date: string;
        end_date: string;
        start_time?: string;
        end_time?: string;
        is_all_day?: boolean;
        event_type?: string;
        visibility?: string;
        location?: string;
        is_virtual?: boolean;
        meeting_url?: string;
        color?: string;
        calendar_id?: string;
        participant_ids?: string[];
    }): Promise<CalendarEvent> => {
        const response = await api.post(`/calendar/events`, data);
        return response.data;
    },

    updateEvent: async (id: string, data: Partial<CalendarEvent>): Promise<CalendarEvent> => {
        const response = await api.put(`/calendar/events/${id}`, data);
        return response.data;
    },

    deleteEvent: async (id: string): Promise<void> => {
        await api.delete(`/calendar/events/${id}`);
    },

    respondToEvent: async (id: string, response: 'accepted' | 'declined' | 'tentative'): Promise<void> => {
        await api.post(`/events/${id}/respond`, null, {
            params: { response }
        });
    },

    // Calendar Views
    getCalendarRange: async (params: {
        start_date: string;
        end_date: string;
        location_id?: string;
    }): Promise<CalendarRangeView> => {
        const response = await api.get(`/calendar/range`, { params });
        return response.data;
    },

    getCalendarDate: async (date: string, location_id?: string): Promise<CalendarDayView> => {
        const response = await api.get(`/calendar/date/${date}`, {
            params: location_id ? { location_id } : undefined
        });
        return response.data;
    },

    calculateWorkingDays: async (request: WorkingDaysRequest): Promise<WorkingDaysResponse> => {
        const response = await api.post(`/calendar/working-days`, request);
        return response.data;
    },

    isWorkingDay: async (date: string, location_id?: string): Promise<{ date: string; is_working_day: boolean }> => {
        const response = await api.get(`/calendar/working-days/check/${date}`, {
            params: location_id ? { location_id } : undefined
        });
        return response.data;
    },

    // Working Day Exceptions
    getWorkingDayExceptions: async (year: number, location_id?: string): Promise<WorkingDayException[]> => {
        const response = await api.get(`/calendar/exceptions`, {
            params: { year, location_id }
        });
        return response.data;
    },

    createWorkingDayException: async (data: WorkingDayExceptionCreate): Promise<WorkingDayException> => {
        const response = await api.post(`/calendar/exceptions`, data);
        return response.data;
    },

    deleteWorkingDayException: async (id: string): Promise<void> => {
        await api.delete(`/calendar/exceptions/${id}`);
    },

    // User Calendars (Unified)
    getUserCalendars: async (): Promise<UserCalendar[]> => {
        const response = await api.get(`/calendar/calendars`);
        // Map backend 'owner_id' to frontend 'user_id' for compatibility
        return response.data.map((c: any) => ({
            ...c,
            user_id: c.owner_id,
            // ensure color is present
            color: c.color || '#4F46E5'
        }));
    },

    createUserCalendar: async (data: UserCalendarCreate): Promise<UserCalendar> => {
        const response = await api.post(`/calendar/calendars`, {
            ...data,
            type: 'PERSONAL'
        });
        const c = response.data;
        return { ...c, user_id: c.owner_id };
    },

    updateUserCalendar: async (id: string, data: UserCalendarUpdate): Promise<UserCalendar> => {
        const response = await api.put(`/calendar/calendars/${id}`, data);
        const c = response.data;
        return { ...c, user_id: c.owner_id };
    },

    deleteUserCalendar: async (id: string): Promise<void> => {
        await api.delete(`/calendar/calendars/${id}`);
    },

    shareCalendar: async (calendarId: string, data: CalendarShareCreate): Promise<CalendarShare> => {
        const response = await api.post(`/calendar/calendars/${calendarId}/share`, data);
        return response.data;
    },

    unshareCalendar: async (calendarId: string, sharedUserId: string): Promise<void> => {
        await api.delete(`/calendar/calendars/${calendarId}/share/${sharedUserId}`);
    },


    // Utility: Generate holidays for a year (calls backend if available)
    generateHolidaysForYear: async (year: number): Promise<Holiday[]> => {
        // Italian national holidays - generate on the fly
        const italianHolidays = [
            { date: `${year}-01-01`, name: "Capodanno" },
            { date: `${year}-01-06`, name: "Epifania" },
            { date: `${year}-04-25`, name: "Festa della Liberazione" },
            { date: `${year}-05-01`, name: "Festa del Lavoro" },
            { date: `${year}-06-02`, name: "Festa della Repubblica" },
            { date: `${year}-08-15`, name: "Ferragosto" },
            { date: `${year}-11-01`, name: "Ognissanti" },
            { date: `${year}-12-08`, name: "Immacolata Concezione" },
            { date: `${year}-12-25`, name: "Natale" },
            { date: `${year}-12-26`, name: "Santo Stefano" },
        ];

        // Add Easter holidays (simplified - would need proper calculation)
        // These are approximate dates for demo

        const created: Holiday[] = [];
        for (const h of italianHolidays) {
            try {
                const holiday = await calendarService.createHoliday({
                    name: h.name,
                    date: h.date,
                    year,
                    scope: 'national',
                });
                created.push(holiday);
            } catch {
                // Holiday may already exist
            }
        }

        return created;
    },

    // Utility: Copy holidays from previous year
    copyHolidaysFromYear: async (fromYear: number, toYear: number): Promise<number> => {
        const previousHolidays = await calendarService.getHolidays({ year: fromYear });
        let copied = 0;

        for (const holiday of previousHolidays) {
            try {
                const newDate = holiday.date.replace(`${fromYear}`, `${toYear}`);
                await calendarService.createHoliday({
                    name: holiday.name,
                    description: holiday.description,
                    date: newDate,
                    year: toYear,
                    scope: holiday.scope,
                    location_id: holiday.location_id,
                    region_code: holiday.region_code,
                    is_recurring: holiday.is_recurring,
                    recurrence_rule: holiday.recurrence_rule,
                });
                copied++;
            } catch {
                // Holiday may already exist
            }
        }

        return copied;
    },

    // ═══════════════════════════════════════════════════════════
    // iCal Export
    // ═══════════════════════════════════════════════════════════

    /**
     * Get URL for downloading holidays as ICS file
     */
    getHolidaysIcsUrl: (year: number, scope?: string): string => {
        let url = `${CALENDAR_BASE}/export/holidays.ics?year=${year}`;
        if (scope) url += `&scope=${scope}`;
        return url;
    },

    /**
     * Get URL for downloading closures as ICS file
     */
    getClosuresIcsUrl: (year: number): string => {
        return `${CALENDAR_BASE}/export/closures.ics?year=${year}`;
    },

    /**
     * Get URL for downloading combined calendar as ICS file
     */
    getCombinedIcsUrl: (year: number, includeHolidays = true, includeClosures = true): string => {
        return `${CALENDAR_BASE}/export/combined.ics?year=${year}&include_holidays=${includeHolidays}&include_closures=${includeClosures}`;
    },

    /**
     * Get URL for downloading personal events as ICS file
     */
    getMyEventsIcsUrl: (year?: number): string => {
        const yearParam = year ? `?year=${year}` : '';
        return `${CALENDAR_BASE}/export/my-events.ics${yearParam}`;
    },

    /**
     * Get subscription URLs and instructions for external calendar apps
     */
    getSubscriptionUrls: async (year: number): Promise<{
        holidays: { url: string; description: string; refresh_interval: string };
        closures: { url: string; description: string; refresh_interval: string };
        combined: { url: string; description: string; refresh_interval: string };
        instructions: {
            google_calendar: string;
            outlook: string;
            apple_calendar: string;
        };
    }> => {
        const response = await api.get(`/export/subscription-url`, {
            params: { year }
        });
        return response.data;
    },

    /**
     * Trigger download of an ICS file
     */
    downloadIcs: (url: string, filename: string): void => {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    /**
     * Download holidays ICS file
     */
    downloadHolidaysIcs: (year: number, scope?: string): void => {
        const url = calendarService.getHolidaysIcsUrl(year, scope);
        calendarService.downloadIcs(url, `kronos_holidays_${year}.ics`);
    },

    /**
     * Download closures ICS file
     */
    downloadClosuresIcs: (year: number): void => {
        const url = calendarService.getClosuresIcsUrl(year);
        calendarService.downloadIcs(url, `kronos_closures_${year}.ics`);
    },

    /**
     * Download combined calendar ICS file
     */
    downloadCombinedIcs: (year: number): void => {
        const url = calendarService.getCombinedIcsUrl(year);
        calendarService.downloadIcs(url, `kronos_calendar_${year}.ics`);
    },
};

export default calendarService;
