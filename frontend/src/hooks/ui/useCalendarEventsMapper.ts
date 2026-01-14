import { useMemo } from 'react';
import type { CalendarRangeView, UserCalendar } from '../../services/calendar.service';
import type { CalendarFilters } from '../../types/calendar-ui';

export function useCalendarEventsMapper(
    calendarData: CalendarRangeView | undefined,
    filters: CalendarFilters,
    userCalendars: UserCalendar[]
) {
    return useMemo(() => {
        if (!calendarData || !calendarData.days) return [];

        const result: any[] = [];

        calendarData.days.forEach(day => {
            day.items.forEach(item => {
                const isHoliday = item.item_type === 'holiday';
                const isClosure = item.item_type === 'closure';
                const isLeave = item.item_type === 'leave';
                const eventTypes = ['event', 'meeting', 'task', 'reminder', 'personal', 'deadline', 'other', 'generic'];
                const isEvent = eventTypes.includes(item.item_type);

                // Skip if filtered out
                if (isHoliday) {
                    const isNational = (item.metadata as any)?.scope === 'national';
                    const filterKey = isNational ? 'showNationalHolidays' : 'showLocalHolidays';
                    if (!filters[filterKey]) return;
                }
                if (isClosure && !filters.showCompanyClosures) return;
                if (isLeave && !filters.showTeamLeaves) return;
                if (isEvent) {
                    const calendarId = (item.metadata as any)?.calendar_id;
                    if (calendarId && filters.hiddenCalendars.includes(calendarId)) return;
                }

                // Map to FullCalendar format if not already added
                if (item.start_date !== day.date && item.item_type !== 'holiday') return;

                let title = item.title;
                let classNames: string[] = [];
                let color = item.color;
                const status = (item.metadata as any)?.status;

                if (isHoliday) {
                    title = `🏛️ ${item.title}`;
                    const isNational = (item.metadata as any)?.scope === 'national';
                    classNames = ['holiday-event', isNational ? 'national' : 'local', 'cursor-default',
                        isNational
                            ? '!bg-rose-50 !text-rose-700 !border-rose-100 !font-medium rounded-lg'
                            : '!bg-orange-50 !text-orange-700 !border-orange-100 !font-medium rounded-lg'
                    ];
                } else if (isClosure) {
                    title = `🏢 ${item.title}`;
                    classNames = ['closure-event', 'cursor-default', '!bg-slate-100 !text-slate-800 !border-slate-200 !font-medium rounded-lg'];
                } else if (isLeave) {
                    title = `${item.title}`;
                    if (status === 'approved' || status === 'approved_conditional') {
                        color = '#10B981';
                        classNames = ['team-leave-event', 'cursor-default', '!bg-emerald-50 !text-emerald-700 !border-emerald-200 !font-medium rounded-lg border-l-4 !border-l-emerald-500'];
                    } else if (status === 'pending') {
                        color = '#F59E0B';
                        classNames = ['team-leave-event', 'cursor-default', '!bg-amber-50 !text-amber-700 !border-amber-200 !font-medium rounded-lg border-l-4 !border-l-amber-400'];
                    } else {
                        classNames = ['team-leave-event', 'cursor-default', '!bg-blue-50 !text-blue-700 !border-blue-200 !font-medium rounded-lg border-l-4 !border-l-blue-400'];
                    }
                } else if (isEvent) {
                    const calendarId = (item.metadata as any)?.calendar_id;
                    const customCal = userCalendars.find(c => c.id === calendarId);

                    const eventTypeIcons: Record<string, string> = {
                        meeting: '📅', task: '✅', reminder: '🔔', personal: '👤',
                        deadline: '⏰', other: '📌', event: '📅', generic: '📅'
                    };
                    const icon = eventTypeIcons[item.item_type] || '📅';
                    title = `${icon} ${item.title}`;
                    color = customCal?.color || item.color;
                    classNames = ['personal-event', '!font-medium', 'shadow-sm', 'rounded-lg'];
                }

                result.push({
                    id: item.id,
                    title: title,
                    start: item.start_date,
                    end: item.end_date,
                    allDay: true,
                    backgroundColor: color,
                    borderColor: color,
                    classNames: classNames,
                    extendedProps: { ...item.metadata, type: item.item_type, raw: item },
                });
            });
        });

        return result;
    }, [calendarData, filters, userCalendars]);
}
