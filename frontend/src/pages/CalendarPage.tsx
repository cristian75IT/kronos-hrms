/**
 * KRONOS - Calendar Page
 * Dedicated calendar view for leaves, holidays, and company closures
 */
import { useState, useMemo, useRef } from 'react';
import { Link } from 'react-router-dom';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import {
    Plus,
    Calendar as CalendarIcon,
    ChevronDown,
    Building,
    Flag,
    Users,
    Settings,
    X,
} from 'lucide-react';
import { useCalendarEvents } from '../hooks/useApi';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common';
import { format, startOfMonth, endOfMonth, addMonths, subMonths } from 'date-fns';
import type { CalendarEvent } from '../types';

interface CalendarFilters {
    showNationalHolidays: boolean;
    showLocalHolidays: boolean;
    showCompanyClosures: boolean;
    showTeamLeaves: boolean;
    teamScope: 'department' | 'company';
}

type CalendarView = 'dayGridMonth' | 'timeGridWeek' | 'timeGridDay';

export function CalendarPage() {
    const calendarRef = useRef<FullCalendar>(null);
    const [currentDate, setCurrentDate] = useState(new Date());
    const [currentView, setCurrentView] = useState<CalendarView>('dayGridMonth');
    const [filtersOpen, setFiltersOpen] = useState(false);
    const [filters, setFilters] = useState<CalendarFilters>({
        showNationalHolidays: true,
        showLocalHolidays: true,
        showCompanyClosures: true,
        showTeamLeaves: true,
        teamScope: 'company',
    });
    useAuth();

    const startDate = format(startOfMonth(subMonths(currentDate, 1)), 'yyyy-MM-dd');
    const endDate = format(endOfMonth(addMonths(currentDate, 2)), 'yyyy-MM-dd');

    const { data: calendarData } = useCalendarEvents(startDate, endDate, filters.showTeamLeaves);

    // Build calendar events based on filters
    const events = useMemo(() => {
        if (!calendarData) return [];

        const result: any[] = [];

        // Leave events (own)
        const leaveEvents = (calendarData.events || []).map(event => {
            const status = event.extendedProps?.status || 'default';
            let statusColorClass = '!bg-blue-600 !text-white !font-medium';

            if (status === 'approved') statusColorClass = '!bg-emerald-600 !text-white !font-medium';
            else if (status === 'pending') statusColorClass = '!bg-amber-400 !text-amber-900 !font-medium';
            else if (status === 'rejected') statusColorClass = '!bg-red-600 !text-white !font-medium';

            return {
                ...event,
                allDay: true,
                classNames: [statusColorClass, 'leave-event', 'shadow-sm', 'border-0'],
            };
        });
        result.push(...leaveEvents);

        // National & Local Holidays
        if (filters.showNationalHolidays || filters.showLocalHolidays) {
            const holidays = (calendarData.holidays || []).filter(h => {
                const isNational = h.extendedProps?.is_national;
                if (isNational && filters.showNationalHolidays) return true;
                if (!isNational && filters.showLocalHolidays) return true;
                return false;
            }).map(holiday => {
                const isNational = holiday.extendedProps?.is_national;
                return {
                    id: holiday.id,
                    title: `🏛️ ${holiday.title}`,
                    start: holiday.start,
                    end: holiday.end,
                    allDay: true,
                    // Use standard display instead of background to ensure title is shown
                    classNames: ['holiday-event', isNational ? 'national' : 'local',
                        isNational
                            ? '!bg-red-100 !text-red-900 !border-red-200 !font-medium'
                            : '!bg-orange-100 !text-orange-900 !border-orange-200 !font-medium'
                    ],
                    extendedProps: { ...holiday.extendedProps, type: 'holiday' },
                };
            });
            result.push(...holidays);
        }

        // Company Closures
        if (filters.showCompanyClosures) {
            const closures = (calendarData.closures || []).map((closure) => ({
                id: closure.id,
                title: `🏢 ${closure.title}`,
                start: closure.start,
                end: closure.end,
                allDay: true,
                // Use standard display to ensure title is shown
                classNames: ['closure-event', closure.extendedProps?.closure_type || 'total', closure.extendedProps?.closure_type === 'total'
                    ? '!bg-purple-100 !text-purple-900 !border-purple-200 !font-medium'
                    : '!bg-purple-50 !text-purple-800 !border-purple-200 !font-medium'],
                extendedProps: { ...closure.extendedProps, type: 'closure' },
            }));
            result.push(...closures);
        }

        // Team leaves (if showing)
        if (filters.showTeamLeaves && (calendarData as any).teamEvents) {
            const teamEvents = ((calendarData as any).teamEvents || []).map((event: CalendarEvent) => {
                const status = event.extendedProps?.status || 'default';
                // Using lighter backgrounds with dark text for team events to differentiate from own leaves
                let statusColorClass = '!bg-blue-100 !text-blue-900 !border-blue-200 !font-medium';

                if (status === 'approved') statusColorClass = '!bg-emerald-100 !text-emerald-900 !border-emerald-200 !font-medium';
                else if (status === 'pending') statusColorClass = '!bg-amber-100 !text-amber-900 !border-amber-200 !font-medium';

                return {
                    ...event,
                    title: `${event.userName || 'Collega'} - Assente`,
                    classNames: ['team-leave-event', statusColorClass, 'border'],
                };
            });
            result.push(...teamEvents);
        }

        return result;
    }, [calendarData, filters]);

    const handleViewChange = (view: CalendarView) => {
        setCurrentView(view);
        calendarRef.current?.getApi().changeView(view);
    };

    const toggleFilter = (key: keyof CalendarFilters) => {
        if (key === 'teamScope') return;
        setFilters(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const viewLabels: Record<CalendarView, string> = {
        'dayGridMonth': 'Mese',
        'timeGridWeek': 'Settimana',
        'timeGridDay': 'Giorno',
    };

    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 mb-1 flex items-center gap-2">
                        <CalendarIcon className="text-indigo-600" size={24} />
                        Calendario Aziendale
                    </h1>
                    <p className="text-sm text-gray-500">Visualizza ferie, festività e chiusure aziendali</p>
                </div>
                <Button
                    as={Link}
                    to="/leaves/new"
                    variant="primary"
                    icon={<Plus size={18} />}
                    className="shrink-0"
                >
                    Nuova Richiesta
                </Button>
            </div>

            {/* Calendar Section */}
            <div className="bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-xl overflow-hidden shadow-sm">
                {/* Toolbar */}
                <div className="flex flex-col md:flex-row justify-between items-center p-4 gap-4 border-b border-[var(--color-border)] bg-[var(--color-bg-tertiary)]">
                    <div className="flex items-center gap-2 text-[var(--color-text-primary)] font-bold text-lg">
                        <CalendarIcon size={20} className="text-[var(--color-primary)]" />
                        <h2>Calendario</h2>
                    </div>

                    <div className="flex bg-[var(--color-bg-primary)] rounded-lg p-1 border border-[var(--color-border)] shadow-sm">
                        {(['dayGridMonth', 'timeGridWeek', 'timeGridDay'] as CalendarView[]).map(view => (
                            <button
                                key={view}
                                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${currentView === view
                                    ? 'bg-indigo-600 text-white shadow-sm'
                                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
                                    }`}
                                onClick={() => handleViewChange(view)}
                            >
                                {viewLabels[view]}
                            </button>
                        ))}
                    </div>

                    <div className="relative">
                        <button
                            className={`flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border transition-colors ${filtersOpen
                                ? 'bg-[var(--color-bg-active)] text-[var(--color-text-primary)] border-[var(--color-border-strong)]'
                                : 'bg-[var(--color-bg-primary)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:bg-[var(--color-bg-hover)]'
                                }`}
                            onClick={() => setFiltersOpen(!filtersOpen)}
                        >
                            <Settings size={16} />
                            Visualizza
                            <ChevronDown size={14} className={`transition-transform duration-200 ${filtersOpen ? 'rotate-180' : ''}`} />
                        </button>

                        {filtersOpen && (
                            <div className="absolute right-0 top-full mt-2 w-72 bg-[var(--color-bg-elevated)] border border-[var(--color-border)] rounded-xl shadow-xl z-50 animate-fadeInUp overflow-hidden">
                                <div className="flex justify-between items-center p-3 border-b border-[var(--color-border-light)] bg-[var(--color-bg-tertiary)]">
                                    <h4 className="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wide">Elementi Visibili</h4>
                                    <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setFiltersOpen(false)}>
                                        <X size={14} />
                                    </button>
                                </div>

                                <div className="p-4 border-b border-gray-100">
                                    <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
                                        <Flag size={14} />
                                        Festività
                                    </div>
                                    <div className="space-y-2">
                                        <label className="flex items-center gap-3 cursor-pointer group">
                                            <input
                                                type="checkbox"
                                                checked={filters.showNationalHolidays}
                                                onChange={() => toggleFilter('showNationalHolidays')}
                                                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                            />
                                            <span className="w-3 h-3 rounded bg-red-500" />
                                            <span className="text-sm text-gray-700 group-hover:text-gray-900">Festività Nazionali</span>
                                        </label>
                                        <label className="flex items-center gap-3 cursor-pointer group">
                                            <input
                                                type="checkbox"
                                                checked={filters.showLocalHolidays}
                                                onChange={() => toggleFilter('showLocalHolidays')}
                                                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                            />
                                            <span className="w-3 h-3 rounded bg-orange-500" />
                                            <span className="text-sm text-gray-700 group-hover:text-gray-900">Festività Locali</span>
                                        </label>
                                    </div>
                                </div>

                                <div className="p-4 border-b border-gray-100">
                                    <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
                                        <Building size={14} />
                                        Azienda
                                    </div>
                                    <label className="flex items-center gap-3 cursor-pointer group">
                                        <input
                                            type="checkbox"
                                            checked={filters.showCompanyClosures}
                                            onChange={() => toggleFilter('showCompanyClosures')}
                                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                        />
                                        <span className="w-3 h-3 rounded bg-purple-600" />
                                        <span className="text-sm text-gray-700 group-hover:text-gray-900">Chiusure Aziendali</span>
                                    </label>
                                </div>

                                <div className="p-4">
                                    <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
                                        <Users size={14} />
                                        Colleghi
                                    </div>
                                    <div className="space-y-3">
                                        <label className="flex items-center gap-3 cursor-pointer group">
                                            <input
                                                type="checkbox"
                                                checked={filters.showTeamLeaves}
                                                onChange={() => toggleFilter('showTeamLeaves')}
                                                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                            />
                                            <span className="w-3 h-3 rounded bg-blue-500" />
                                            <span className="text-sm text-gray-700 group-hover:text-gray-900">Mostra Ferie Colleghi</span>
                                        </label>
                                        {filters.showTeamLeaves && (
                                            <div className="pl-7 space-y-2">
                                                <label className="flex items-center gap-2 cursor-pointer">
                                                    <input
                                                        type="radio"
                                                        name="teamScope"
                                                        checked={filters.teamScope === 'department'}
                                                        onChange={() => setFilters(prev => ({ ...prev, teamScope: 'department' }))}
                                                        className="border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                                    />
                                                    <span className="text-xs text-gray-600">Solo Dipartimento</span>
                                                </label>
                                                <label className="flex items-center gap-2 cursor-pointer">
                                                    <input
                                                        type="radio"
                                                        name="teamScope"
                                                        checked={filters.teamScope === 'company'}
                                                        onChange={() => setFilters(prev => ({ ...prev, teamScope: 'company' }))}
                                                        className="border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                                    />
                                                    <span className="text-xs text-gray-600">Tutta l'Azienda</span>
                                                </label>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Legend */}
                <div className="flex flex-wrap gap-4 p-3 bg-[var(--color-bg-secondary)] border-b border-[var(--color-border-light)] text-xs">
                    <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded bg-emerald-500" />
                        <span className="text-gray-600">Approvate</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded bg-amber-500" />
                        <span className="text-gray-600">In Attesa</span>
                    </div>
                    {filters.showNationalHolidays && (
                        <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded bg-red-500" />
                            <span className="text-gray-600">Festività</span>
                        </div>
                    )}
                    {filters.showCompanyClosures && (
                        <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded bg-purple-600" />
                            <span className="text-gray-600">Chiusure</span>
                        </div>
                    )}
                    {filters.showTeamLeaves && (
                        <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded bg-blue-500" />
                            <span className="text-gray-600">Colleghi</span>
                        </div>
                    )}
                </div>

                {/* Calendar */}
                <div className="p-4">
                    <FullCalendar
                        ref={calendarRef}
                        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                        initialView={currentView}
                        locale="it"
                        headerToolbar={{
                            left: 'prev,next today',
                            center: 'title',
                            right: '',
                        }}
                        events={events}
                        eventClick={(info) => {
                            const eventType = info.event.extendedProps?.type;
                            if (eventType !== 'holiday' && eventType !== 'closure') {
                                window.location.href = `/leaves/${info.event.id}`;
                            }
                        }}
                        dateClick={(info) => {
                            window.location.href = `/leaves/new?date=${info.dateStr}`;
                        }}
                        datesSet={(dateInfo) => {
                            setCurrentDate(dateInfo.view.currentStart);
                        }}
                        height="auto"
                        dayMaxEvents={3}
                        weekends={true}
                        firstDay={1}
                        buttonText={{
                            today: 'Oggi',
                            month: 'Mese',
                            week: 'Settimana',
                            day: 'Giorno',
                        }}
                        slotMinTime="08:00:00"
                        slotMaxTime="20:00:00"
                        allDaySlot={true}
                        nowIndicator={true}
                    />
                </div>
            </div>
        </div>
    );
}

export default CalendarPage;
