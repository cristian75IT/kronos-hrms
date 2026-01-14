import { useState, useRef } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
// import listPlugin from '@fullcalendar/list'; // Plugin not installed
import itLocale from '@fullcalendar/core/locales/it';
import { format, startOfMonth, endOfMonth, addMonths, subMonths } from 'date-fns';
import { useCalendarRange, useUserCalendars } from '../hooks/domain/useCalendar';
import { calendarService } from '../services/calendar.service';
import type { UserCalendar, CalendarEvent } from '../services/calendar.service';
import type { CalendarFilters, CalendarView } from '../types/calendar-ui';
import { useCalendarEventsMapper } from '../hooks/ui/useCalendarEventsMapper';
import { CalendarHeader } from '../components/calendar/CalendarHeader';
import { CalendarSidebar } from '../components/calendar/CalendarSidebar';
import { CalendarManagementModal } from '../components/calendar/CalendarManagementModal';
import { NewEventModal } from '../components/calendar/NewEventModal';
import { EventDetailModal } from '../components/calendar/EventDetailModal';
import { useAuth } from '../context/AuthContext';

export default function CalendarPage() {
    // --- State ---
    const { user } = useAuth();
    const [currentDate, setCurrentDate] = useState(new Date());
    const [currentView, setCurrentView] = useState<CalendarView>('dayGridMonth');
    const calendarRef = useRef<FullCalendar>(null);
    const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

    // Filters
    const [filters, setFilters] = useState<CalendarFilters>({
        showNationalHolidays: true,
        showLocalHolidays: true,
        showCompanyClosures: true,
        showTeamLeaves: true,
        hiddenCalendars: []
    });

    // Modals
    const [isCalendarModalOpen, setIsCalendarModalOpen] = useState(false);
    const [isNewEventModalOpen, setIsNewEventModalOpen] = useState(false);
    const [isEventDetailModalOpen, setIsEventDetailModalOpen] = useState(false);

    // Selection State
    const [selectedDateInfo, setSelectedDateInfo] = useState<{ start: Date; end: Date; allDay: boolean } | null>(null);
    const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

    // --- Data Fetching ---
    // Initialize fetch range with a buffer around current date
    const [fetchRange, setFetchRange] = useState({
        start: format(subMonths(startOfMonth(new Date()), 1), 'yyyy-MM-dd'),
        end: format(addMonths(endOfMonth(new Date()), 1), 'yyyy-MM-dd')
    });

    const { data: calendarData, refetch } = useCalendarRange(fetchRange.start, fetchRange.end);
    const { data: userCalendarsData } = useUserCalendars();
    const userCalendars = (userCalendarsData || []) as UserCalendar[];

    // --- Derived Data ---
    const events = useCalendarEventsMapper(calendarData, filters, userCalendars);

    // --- Handlers ---
    const updateCurrentDate = () => {
        const api = calendarRef.current?.getApi();
        if (api) {
            setCurrentDate(api.getDate());
        }
    };

    const handleDatesSet = (arg: any) => {
        const viewStart = arg.view.activeStart;
        const viewEnd = arg.view.activeEnd;
        // Add 1 month buffer for smoother navigation cache
        const startStr = format(subMonths(viewStart, 1), 'yyyy-MM-dd');
        const endStr = format(addMonths(viewEnd, 1), 'yyyy-MM-dd');

        if (startStr !== fetchRange.start || endStr !== fetchRange.end) {
            setFetchRange({ start: startStr, end: endStr });
        }
        updateCurrentDate();
    };

    const handleDateSelect = (selectInfo: any) => {
        setSelectedDateInfo({
            start: selectInfo.start,
            end: selectInfo.end,
            allDay: selectInfo.allDay
        });
        setIsNewEventModalOpen(true);
    };

    const handleEventClick = (clickInfo: any) => {
        const type = clickInfo.event.extendedProps.type;

        // Types that can be opened in detail view
        const interactiveTypes = ['event', 'meeting', 'task', 'reminder', 'personal', 'deadline', 'other', 'generic'];

        if (interactiveTypes.includes(type)) {
            const raw = clickInfo.event.extendedProps.raw;
            const metadata = clickInfo.event.extendedProps;

            if (raw) {
                // Reconstruct CalendarEvent
                const recEvent: any = {
                    id: raw.id,
                    title: raw.title,
                    start_date: raw.start_date,
                    end_date: raw.end_date,
                    start_time: metadata.start_time,
                    end_time: metadata.end_time,
                    is_all_day: metadata.is_all_day ?? true,
                    event_type: metadata.event_type || type,
                    calendar_id: metadata.calendar_id,
                    description: metadata.description,
                    location: metadata.location,
                    is_virtual: metadata.is_virtual,
                    meeting_url: metadata.meeting_url,
                    visibility: metadata.visibility,
                    color: raw.color || metadata.color,
                    alert_before_minutes: metadata.alert_before_minutes,
                    created_by: metadata.created_by,
                    user_id: metadata.user_id,
                    recurrence_rule: metadata.recurrence_rule,
                    is_recurring: metadata.is_recurring,
                    participants: metadata.participants
                };

                setSelectedEvent(recEvent);
                setIsEventDetailModalOpen(true);
            }
        }
    };

    const handleFilterToggle = (key: keyof CalendarFilters) => {
        setFilters(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const handleCalendarVisibilityToggle = (id: string) => {
        setFilters(prev => {
            if (prev.hiddenCalendars.includes(id)) {
                return { ...prev, hiddenCalendars: prev.hiddenCalendars.filter(cid => cid !== id) };
            } else {
                return { ...prev, hiddenCalendars: [...prev.hiddenCalendars, id] };
            }
        });
    };

    const renderEventContent = (eventInfo: any) => {
        return (
            <div className="flex items-center w-full overflow-hidden">
                <div className="text-xs truncate font-medium px-1 w-full">
                    {eventInfo.event.title}
                </div>
            </div>
        );
    };

    return (
        <div className="p-4 lg:p-8 max-w-[1600px] mx-auto h-screen flex flex-col">
            <CalendarHeader
                currentDate={currentDate}
                currentView={currentView}
                onPrev={() => { calendarRef.current?.getApi().prev(); updateCurrentDate(); }}
                onNext={() => { calendarRef.current?.getApi().next(); updateCurrentDate(); }}
                onToday={() => { calendarRef.current?.getApi().today(); updateCurrentDate(); }}
                onChangeView={(view) => { calendarRef.current?.getApi().changeView(view); setCurrentView(view); }}
                onExportIcs={() => calendarService.downloadCombinedIcs(currentDate.getFullYear())}
                onToggleMobileSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
            />

            <div className="flex flex-1 gap-6 min-h-0">
                <CalendarSidebar
                    filters={filters}
                    onToggleFilter={handleFilterToggle}
                    onToggleCalendarVisibility={handleCalendarVisibilityToggle}
                    userCalendars={userCalendars}
                    onOpenCalendarModal={() => setIsCalendarModalOpen(true)}
                    calendarData={calendarData}
                />

                {/* Main Calendar Area */}
                <main className="flex-1 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex flex-col relative z-0">
                    <FullCalendar
                        ref={calendarRef}
                        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                        initialView="dayGridMonth"
                        headerToolbar={false}
                        locale={itLocale}
                        events={events}
                        editable={true}
                        selectable={true}
                        selectMirror={true}
                        dayMaxEvents={3}
                        weekNumbers={true}
                        nowIndicator={true}
                        height="100%"
                        datesSet={handleDatesSet}
                        select={handleDateSelect}
                        eventClick={handleEventClick}
                        eventContent={renderEventContent}
                        slotMinTime="07:00:00"
                        slotMaxTime="21:00:00"
                        allDaySlot={true}
                        allDayText="Tutto il giorno"
                    />
                </main>
            </div>

            {/* Modals */}
            <CalendarManagementModal
                isOpen={isCalendarModalOpen}
                onClose={() => setIsCalendarModalOpen(false)}
            />

            <NewEventModal
                isOpen={isNewEventModalOpen}
                onClose={() => setIsNewEventModalOpen(false)}
                selectedDate={selectedDateInfo ? format(selectedDateInfo.start, 'yyyy-MM-dd') : null}
                userCalendars={userCalendars}
                onEventCreated={() => { refetch(); }}
            />

            {selectedEvent && (
                <EventDetailModal
                    isOpen={isEventDetailModalOpen}
                    onClose={() => { setIsEventDetailModalOpen(false); setSelectedEvent(null); }}
                    event={selectedEvent}
                    userCalendars={userCalendars}
                    currentUserId={user?.id}
                    onEventUpdated={() => { refetch(); }}
                    onEventDeleted={() => { refetch(); }}
                />
            )}
        </div>
    );
}
