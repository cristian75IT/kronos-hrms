/**
 * KRONOS - Calendar Page
 * Dedicated calendar view for leaves, holidays, and company closures
 */
import { useState, useMemo, useRef } from 'react';
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
    Settings,
    X,
    Lock,
    Clock,
    Tag,
    Users,
} from 'lucide-react';
import { format, startOfMonth, endOfMonth, addMonths, subMonths } from 'date-fns';
import {
    useCalendarRange,
    useCreateCalendarEvent,
    useUserCalendars,
    useCreateUserCalendar,
    useDeleteUserCalendar,
    useUsers,
    useShareUserCalendar,
    useUnshareUserCalendar
} from '../hooks/useApi';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common';
import { useToast } from '../context/ToastContext';
import type { UserWithProfile } from '../types';

interface CalendarFilters {
    showNationalHolidays: boolean;
    showLocalHolidays: boolean;
    showCompanyClosures: boolean;
    showTeamLeaves: boolean;
    hiddenCalendars: string[];
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
        hiddenCalendars: [],
    });
    const [isEventModalOpen, setIsEventModalOpen] = useState(false);
    const [isCalendarModalOpen, setIsCalendarModalOpen] = useState(false);
    const [selectedDate, setSelectedDate] = useState<string | null>(null);
    const toast = useToast();
    const createEvent = useCreateCalendarEvent();
    const { data: userCalendarsData } = useUserCalendars();
    const userCalendars = useMemo(() => Array.isArray(userCalendarsData) ? userCalendarsData : [], [userCalendarsData]);
    const createUserCalendar = useCreateUserCalendar();
    const deleteUserCalendar = useDeleteUserCalendar();
    const { data: users } = useUsers();
    const shareCalendarMut = useShareUserCalendar();
    const unshareCalendarMut = useUnshareUserCalendar();
    const [sharingCalendarId, setSharingCalendarId] = useState<string | null>(null);
    useAuth();

    const startDate = format(startOfMonth(subMonths(currentDate, 1)), 'yyyy-MM-dd');
    const endDate = format(endOfMonth(addMonths(currentDate, 2)), 'yyyy-MM-dd');

    const { data: calendarData } = useCalendarRange(startDate, endDate);

    // Build calendar events based on filters
    const events = useMemo(() => {
        if (!calendarData || !calendarData.days) return [];

        const result: any[] = [];

        calendarData.days.forEach(day => {
            day.items.forEach(item => {
                const isHoliday = item.item_type === 'holiday';
                const isClosure = item.item_type === 'closure';
                const isLeave = item.item_type === 'leave';
                const isEvent = item.item_type === 'event';

                // Skip if filtered out
                if (isHoliday) {
                    const isNational = (item.metadata as any)?.scope === 'national';
                    if (isNational && !filters.showNationalHolidays) return;
                    if (!isNational && !filters.showLocalHolidays) return;
                }
                if (isClosure && !filters.showCompanyClosures) return;
                if (isLeave && !filters.showTeamLeaves) return;
                if (isEvent) {
                    const calendarId = (item.metadata as any)?.calendar_id;
                    if (calendarId && filters.hiddenCalendars.includes(calendarId)) return;
                }

                // Map to FullCalendar format if not already added (some items might span multiple days)
                // However, the backend returns items per day. FullCalendar handles start/end.
                // To avoid duplicates in display, we only add if it's the start date OR if it's a single day item
                if (item.start_date !== day.date && item.item_type !== 'holiday') return;

                let title = item.title;
                let classNames: string[] = [];
                let color = item.color;

                if (isHoliday) {
                    title = `🏛️ ${item.title}`;
                    const isNational = (item.metadata as any)?.scope === 'national';
                    classNames = ['holiday-event', isNational ? 'national' : 'local',
                        isNational
                            ? '!bg-red-100 !text-red-900 !border-red-200 !font-medium'
                            : '!bg-orange-100 !text-orange-900 !border-orange-200 !font-medium'
                    ];
                } else if (isClosure) {
                    title = `🏢 ${item.title}`;
                    classNames = ['closure-event', '!bg-purple-100 !text-purple-900 !border-purple-200 !font-medium'];
                } else if (isLeave) {
                    title = `${item.title}`; // Title already has name and "Assente" in backend if leave
                    classNames = ['team-leave-event', '!bg-blue-100 !text-blue-900 !border-blue-200 !font-medium', 'border'];
                } else if (isEvent) {
                    const calendarId = (item.metadata as any)?.calendar_id;
                    const customCal = userCalendars.find(c => c.id === calendarId);

                    title = `📅 ${item.title}`;
                    color = customCal?.color || item.color;
                    classNames = ['personal-event', '!font-medium', 'shadow-sm'];
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
                    extendedProps: { ...item.metadata, type: item.item_type },
                });
            });
        });

        return result;
    }, [calendarData, filters]);

    const handleViewChange = (view: CalendarView) => {
        setCurrentView(view);
        calendarRef.current?.getApi().changeView(view);
    };

    const toggleFilter = (key: keyof CalendarFilters) => {
        setFilters(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const toggleCalendarVisibility = (calendarId: string) => {
        setFilters(prev => ({
            ...prev,
            hiddenCalendars: prev.hiddenCalendars.includes(calendarId)
                ? prev.hiddenCalendars.filter(id => id !== calendarId)
                : [...prev.hiddenCalendars, calendarId]
        }));
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
                        Calendario
                    </h1>
                    <p className="text-sm text-gray-500">Gestisci i tuoi impegni e visualizza le assenze del team</p>
                </div>
                <div className="flex items-center gap-3">
                    <Button
                        variant="outline"
                        icon={<Settings size={18} />}
                        onClick={() => setIsCalendarModalOpen(true)}
                    >
                        I miei Calendari
                    </Button>
                    <Button
                        variant="primary"
                        icon={<Plus size={18} />}
                        onClick={() => {
                            setSelectedDate(format(new Date(), 'yyyy-MM-dd'));
                            setIsEventModalOpen(true);
                        }}
                    >
                        Nuovo Impegno
                    </Button>
                </div>
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

                                <div className="p-4 border-b border-gray-100">
                                    <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
                                        <Users size={14} />
                                        Team
                                    </div>
                                    <label className="flex items-center gap-3 cursor-pointer group">
                                        <input
                                            type="checkbox"
                                            checked={filters.showTeamLeaves}
                                            onChange={() => toggleFilter('showTeamLeaves')}
                                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                        />
                                        <span className="w-3 h-3 rounded bg-blue-500" />
                                        <span className="text-sm text-gray-700 group-hover:text-gray-900">Assenze Colleghi</span>
                                    </label>
                                </div>

                                <div className="p-4">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                            <Lock size={14} />
                                            I miei Calendari
                                        </div>
                                        <button
                                            onClick={() => setIsCalendarModalOpen(true)}
                                            className="text-indigo-600 hover:text-indigo-700 text-[10px] font-bold uppercase"
                                        >
                                            Gestisci
                                        </button>
                                    </div>
                                    <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                                        {userCalendars.map(cal => (
                                            <label key={cal.id} className="flex items-center gap-3 cursor-pointer group">
                                                <input
                                                    type="checkbox"
                                                    checked={!filters.hiddenCalendars.includes(cal.id)}
                                                    onChange={() => toggleCalendarVisibility(cal.id)}
                                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                                />
                                                <span className="w-3 h-3 rounded shadow-sm" style={{ backgroundColor: cal.color }} />
                                                <span className="text-sm text-gray-700 group-hover:text-gray-900 flex-1 truncate">{cal.name}</span>
                                            </label>
                                        ))}
                                        {(!userCalendars || userCalendars.length === 0) && (
                                            <p className="text-xs text-gray-400 italic">Nessun calendario personalizzato</p>
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
                            <span className="text-gray-600">Assenze Colleghi</span>
                        </div>
                    )}
                    {userCalendars.map(cal => !filters.hiddenCalendars.includes(cal.id) && (
                        <div key={cal.id} className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded shadow-sm" style={{ backgroundColor: cal.color }} />
                            <span className="text-gray-600">{cal.name}</span>
                        </div>
                    ))}
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
                            setSelectedDate(info.dateStr);
                            setIsEventModalOpen(true);
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
            </div >

            {/* Event Modal */}
            {isEventModalOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-scaleIn">
                        <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-indigo-50">
                            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                                <Plus className="text-indigo-600" size={20} />
                                Nuovo Impegno
                            </h3>
                            <button onClick={() => setIsEventModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={async (e) => {
                            e.preventDefault();
                            const formData = new FormData(e.currentTarget);
                            const data = {
                                title: formData.get('title') as string,
                                start_date: formData.get('start_date') as string,
                                end_date: formData.get('end_date') as string,
                                event_type: formData.get('category') as string || 'General',
                                color: formData.get('color') as string || '#4F46E5',
                                calendar_id: formData.get('calendar_id') as string || undefined,
                                visibility: 'private',
                                is_all_day: true
                            };

                            try {
                                await createEvent.mutateAsync(data);
                                toast.success('Impegno creato correttamente');
                                setIsEventModalOpen(false);
                            } catch (err) {
                                toast.error('Errore durante la creazione');
                            }
                        }} className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Titolo</label>
                                <input
                                    name="title"
                                    required
                                    className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                                    placeholder="Es: Riunione con cliente..."
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                                        <Clock size={14} /> Inizio
                                    </label>
                                    <input
                                        type="date"
                                        name="start_date"
                                        defaultValue={selectedDate || format(new Date(), 'yyyy-MM-dd')}
                                        required
                                        className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                                        <Clock size={14} /> Fine
                                    </label>
                                    <input
                                        type="date"
                                        name="end_date"
                                        defaultValue={selectedDate || format(new Date(), 'yyyy-MM-dd')}
                                        required
                                        className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                                    <Tag size={14} /> Calendario
                                </label>
                                <select
                                    name="calendar_id"
                                    className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                                >
                                    <option value="">Nessuno (Generale)</option>
                                    {userCalendars.map(cal => (
                                        <option key={cal.id} value={cal.id}>{cal.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Colore</label>
                                <div className="flex gap-3">
                                    {['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#EC4899', '#8B5CF6'].map(color => (
                                        <label key={color} className="relative cursor-pointer group">
                                            <input type="radio" name="color" value={color} className="sr-only" defaultChecked={color === '#4F46E5'} />
                                            <div className="w-8 h-8 rounded-full shadow-sm group-hover:scale-110 transition-transform ring-offset-2 peer-checked:ring-2 ring-transparent" style={{ backgroundColor: color }} />
                                        </label>
                                    ))}
                                </div>
                            </div>

                            <div className="pt-4 flex gap-3">
                                <Button
                                    type="button"
                                    variant="outline"
                                    className="flex-1"
                                    onClick={() => setIsEventModalOpen(false)}
                                >
                                    Annulla
                                </Button>
                                <Button
                                    type="submit"
                                    variant="primary"
                                    className="flex-1"
                                    isLoading={createEvent.isPending}
                                >
                                    Crea Impegno
                                </Button>
                            </div>

                            <p className="text-[10px] text-center text-gray-400 mt-2 flex items-center justify-center gap-1">
                                <Lock size={10} /> Questo impegno sarà visibile solo a te
                            </p>
                        </form>
                    </div>
                </div>
            )}

            {/* Calendar Management Modal */}
            {isCalendarModalOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-scaleIn">
                        <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-indigo-50">
                            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                                <Settings className="text-indigo-600" size={20} />
                                Gestione Calendari
                            </h3>
                            <button onClick={() => setIsCalendarModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="p-6 space-y-6">
                            {/* Create New Calendar Form */}
                            <form
                                onSubmit={async (e) => {
                                    e.preventDefault();
                                    const formData = new FormData(e.currentTarget);
                                    try {
                                        await createUserCalendar.mutateAsync({
                                            name: formData.get('name') as string,
                                            color: formData.get('color') as string || '#4F46E5'
                                        });
                                        toast.success('Calendario creato');
                                        (e.target as HTMLFormElement).reset();
                                    } catch (err) {
                                        toast.error('Errore durante la creazione');
                                    }
                                }}
                                className="bg-gray-50 p-4 rounded-xl border border-gray-100"
                            >
                                <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                                    <Plus size={14} className="text-indigo-600" />
                                    Crea Nuovo Calendario
                                </h4>
                                <div className="flex gap-3">
                                    <input
                                        name="name"
                                        required
                                        placeholder="Nome calendario (es. Meeting, Sport...)"
                                        className="flex-1 px-3 py-2 text-sm rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    />
                                    <input
                                        type="color"
                                        name="color"
                                        defaultValue="#4F46E5"
                                        className="w-10 h-9 rounded-lg border border-gray-200 cursor-pointer"
                                    />
                                    <Button type="submit" variant="primary" size="sm" isLoading={createUserCalendar.isPending}>
                                        Aggiungi
                                    </Button>
                                </div>
                            </form>

                            {/* Existing Calendars List */}
                            <div className="space-y-3">
                                <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                                    <Tag size={14} className="text-indigo-600" />
                                    I tuoi Calendari
                                </h4>
                                <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                                    {userCalendars.map(cal => (
                                        <div key={cal.id} className="space-y-2">
                                            <div className="flex items-center justify-between p-3 rounded-xl border border-gray-100 hover:bg-gray-50 transition-colors">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-4 h-4 rounded shadow-sm" style={{ backgroundColor: cal.color }} />
                                                    <div className="flex flex-col">
                                                        <span className="text-sm font-medium text-gray-700">{cal.name}</span>
                                                        {!cal.is_owner && (
                                                            <span className="text-[10px] text-gray-400">Condiviso con te</span>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    {cal.is_owner && (
                                                        <>
                                                            <button
                                                                onClick={() => setSharingCalendarId(sharingCalendarId === cal.id ? null : cal.id)}
                                                                className={`p-1.5 rounded-lg transition-colors ${sharingCalendarId === cal.id ? 'bg-indigo-50 text-indigo-600' : 'text-gray-400 hover:bg-gray-100 hover:text-indigo-600'}`}
                                                                title="Condividi"
                                                            >
                                                                <Users size={16} />
                                                            </button>
                                                            <button
                                                                onClick={async () => {
                                                                    if (confirm(`Sei sicuro di voler eliminare il calendario "${cal.name}"? Gli impegni associati perderanno il colore personalizzato.`)) {
                                                                        try {
                                                                            await deleteUserCalendar.mutateAsync(cal.id);
                                                                            toast.success('Calendario eliminato');
                                                                        } catch (err) {
                                                                            toast.error('Errore durante l\'eliminazione');
                                                                        }
                                                                    }
                                                                }}
                                                                className="text-gray-400 hover:text-red-600 transition-colors p-1.5 hover:bg-red-50 rounded-lg"
                                                            >
                                                                <X size={16} />
                                                            </button>
                                                        </>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Sharing Section */}
                                            {sharingCalendarId === cal.id && cal.is_owner && (
                                                <div className="ml-7 p-3 bg-gray-50 rounded-xl border border-gray-200 space-y-3 animate-in fade-in slide-in-from-top-2">
                                                    <div className="flex items-center justify-between">
                                                        <h5 className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Gestisci Accessi</h5>
                                                        <button onClick={() => setSharingCalendarId(null)} className="text-gray-400 hover:text-gray-600">
                                                            <X size={12} />
                                                        </button>
                                                    </div>

                                                    {/* List of current shares */}
                                                    <div className="space-y-2">
                                                        {cal.shared_with?.map(share => {
                                                            const sharedUser = users?.find((u: UserWithProfile) => u.id === share.shared_with_user_id);
                                                            return (
                                                                <div key={share.id} className="flex items-center justify-between text-sm bg-white p-2 rounded-lg border border-gray-100">
                                                                    <div className="flex items-center gap-2">
                                                                        <div className="w-6 h-6 rounded-full bg-indigo-100 flex items-center justify-center text-[10px] font-bold text-indigo-600">
                                                                            {sharedUser?.first_name?.[0].toUpperCase()}{sharedUser?.last_name?.[0].toUpperCase()}
                                                                        </div>
                                                                        <span className="text-gray-600">{sharedUser?.first_name} {sharedUser?.last_name}</span>
                                                                    </div>
                                                                    <button
                                                                        onClick={() => unshareCalendarMut.mutate({ calendarId: cal.id, sharedUserId: share.shared_with_user_id })}
                                                                        className="text-red-400 hover:text-red-600 p-1"
                                                                    >
                                                                        <X size={14} />
                                                                    </button>
                                                                </div>
                                                            );
                                                        })}
                                                        {(!cal.shared_with || cal.shared_with.length === 0) && (
                                                            <p className="text-[11px] text-gray-400 italic">Nessuna condivisione attiva</p>
                                                        )}
                                                    </div>

                                                    {/* Add share form */}
                                                    <div className="pt-2 border-t border-gray-200">
                                                        <select
                                                            className="w-full text-xs px-2 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none bg-white font-medium"
                                                            onChange={(e) => {
                                                                if (e.target.value) {
                                                                    shareCalendarMut.mutate({
                                                                        calendarId: cal.id,
                                                                        data: { shared_with_user_id: e.target.value }
                                                                    });
                                                                    e.target.value = "";
                                                                }
                                                            }}
                                                        >
                                                            <option value="">Aggiungi collega...</option>
                                                            {users?.filter((u: UserWithProfile) => u.id !== cal.user_id && !cal.shared_with?.some(s => s.shared_with_user_id === u.id)).map((u: UserWithProfile) => (
                                                                <option key={u.id} value={u.id}>
                                                                    {u.first_name} {u.last_name}
                                                                </option>
                                                            ))}
                                                        </select>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                    {(!userCalendars || userCalendars.length === 0) && (
                                        <div className="text-center py-8 text-gray-400">
                                            <CalendarIcon size={32} className="mx-auto mb-2 opacity-20" />
                                            <p className="text-sm">Non hai ancora creato calendari personalizzati</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-end">
                            <Button onClick={() => setIsCalendarModalOpen(false)} variant="outline">
                                Chiudi
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div >
    );
}

export default CalendarPage;
