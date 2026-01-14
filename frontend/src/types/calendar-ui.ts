export interface CalendarFilters {
    showNationalHolidays: boolean;
    showLocalHolidays: boolean;
    showCompanyClosures: boolean;
    showTeamLeaves: boolean;
    hiddenCalendars: string[];
}

export type CalendarView = 'dayGridMonth' | 'timeGridWeek' | 'timeGridDay';
