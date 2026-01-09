/**
 * KRONOS - Calendar Page
 * Dedicated calendar view for leaves, holidays, and company closures
 */
import { useState, useMemo, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import {
    Plus,
    Calendar as CalendarIcon,
    ChevronDown,
    Settings,
    X,
    Lock,
    Clock,
    Tag,
    Users,
    Edit3,
} from 'lucide-react';
import { format, startOfMonth, endOfMonth, addMonths, subMonths } from 'date-fns';
import {
    useCalendarRange,
    useUserCalendars,
    useCreateUserCalendar,
    useDeleteUserCalendar,
    useUpdateUserCalendar,
    useShareUserCalendar,
    useUnshareUserCalendar
} from '../hooks/domain/useCalendar';
import { useUsers } from '../hooks/domain/useUsers';
import { useAuth } from '../context/AuthContext';
import { Button, PageHeader } from '../components/common';
import { NewEventModal, EventDetailModal } from '../components/calendar';
import { calendarService } from '../services/calendar.service';
import { useToast } from '../context/ToastContext';

interface CalendarFilters {
    showNationalHolidays: boolean;
    showLocalHolidays: boolean;
    showCompanyClosures: boolean;
    showTeamLeaves: boolean;
    hiddenCalendars: string[];
}

type CalendarView = 'dayGridMonth' | 'timeGridWeek' | 'timeGridDay';

interface FilterToggleProps {
    label: string;
    color: string;
    checked: boolean;
    onChange: () => void;
}

function FilterToggle({ label, color, checked, onChange }: FilterToggleProps) {
    return (
        <label className="flex items-center gap-3 cursor-pointer group p-1.5 rounded-lg hover:bg-slate-50 transition-colors">
            <div className="relative flex items-center">
                <input
                    type="checkbox"
                    checked={checked}
                    onChange={onChange}
                    className="rounded border-slate-300 text-indigo-600 focus:ring-0 w-4 h-4 cursor-pointer"
                />
            </div>
            <span className={`w-2.5 h-2.5 rounded-full shadow-sm bg-${color}`} />
            <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900 transition-colors">{label}</span>
        </label>
    );
}

export function CalendarPage() {
    const calendarRef = useRef<FullCalendar>(null);
    const lastClickRef = useRef<{ id: string, time: number } | null>(null); // For double click detection
    const [currentDate, setCurrentDate] = useState(new Date());
    const [currentView, setCurrentView] = useState<CalendarView>('dayGridMonth');
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
    const queryClient = useQueryClient();
    const { data: userCalendarsData } = useUserCalendars();
    const userCalendars = useMemo(() => Array.isArray(userCalendarsData) ? userCalendarsData : [], [userCalendarsData]);
    const createUserCalendar = useCreateUserCalendar();
    const deleteUserCalendar = useDeleteUserCalendar();
    const updateUserCalendar = useUpdateUserCalendar();
    const { data: users, isLoading: usersLoading } = useUsers();
    const shareCalendarMut = useShareUserCalendar();
    const unshareCalendarMut = useUnshareUserCalendar();
    const [sharingCalendarId, setSharingCalendarId] = useState<string | null>(null);
    const [editingCalendarId, setEditingCalendarId] = useState<string | null>(null);
    const [selectedEvent, setSelectedEvent] = useState<any | null>(null);
    const [isEditModeInitial, setIsEditModeInitial] = useState(false);
    const { user } = useAuth();

    const startDate = format(startOfMonth(subMonths(currentDate, 1)), 'yyyy-MM-dd');
    const endDate = format(endOfMonth(addMonths(currentDate, 2)), 'yyyy-MM-dd');

    const { data: calendarData } = useCalendarRange(startDate, endDate);

    /**
     * Trasforma i dati provenienti dal servizio calendar in eventi compatibili con FullCalendar.
     * Applica i filtri di visualizzazione definiti dall'utente.
     */
    const events = useMemo(() => {
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
                    // Enterprise Color Mapping
                    if (status === 'approved' || status === 'approved_conditional') {
                        color = '#10B981'; // Emerald 500
                        classNames = ['team-leave-event', 'cursor-default', '!bg-emerald-50 !text-emerald-700 !border-emerald-200 !font-medium rounded-lg border-l-4 !border-l-emerald-500'];
                    } else if (status === 'pending') {
                        color = '#F59E0B'; // Amber 500
                        classNames = ['team-leave-event', 'cursor-default', '!bg-amber-50 !text-amber-700 !border-amber-200 !font-medium rounded-lg border-l-4 !border-l-amber-400'];
                    } else {
                        classNames = ['team-leave-event', 'cursor-default', '!bg-blue-50 !text-blue-700 !border-blue-200 !font-medium rounded-lg border-l-4 !border-l-blue-400'];
                    }
                } else if (isEvent) {
                    const calendarId = (item.metadata as any)?.calendar_id;
                    const customCal = userCalendars.find(c => c.id === calendarId);

                    const eventTypeIcons: Record<string, string> = {
                        meeting: '📅',
                        task: '✅',
                        reminder: '🔔',
                        personal: '👤',
                        deadline: '⏰',
                        other: '📌',
                        event: '📅',
                        generic: '📅'
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
                    extendedProps: { ...item.metadata, type: item.item_type },
                });
            });
        });

        return result;
    }, [calendarData, filters, userCalendars]);

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

    // Calculate "Who is Away Today"
    const todayStr = format(new Date(), 'yyyy-MM-dd');
    const awayToday = useMemo(() => {
        if (!calendarData || !calendarData.days) return [];
        const todayData = calendarData.days.find(d => d.date === todayStr);
        if (!todayData) return [];
        return todayData.items.filter(item => item.item_type === 'leave');
    }, [calendarData, todayStr]);

    return (
        <div className="flex flex-col h-[calc(100vh-120px)] animate-fadeIn">
            {/**
             * Intestazione della pagina con controlli di navigazione dei mesi 
             * e pulsante per la creazione di nuovi eventi.
             */}
            {/* Enterprise Page Header */}
            {/* Enterprise Page Header */}
            <PageHeader
                title="Calendario Aziendale"
                description={`Visualizza e gestisci impegni, scadenze e assenze. ${awayToday.length} assenze oggi.`}
                breadcrumbs={[
                    { label: 'Dashboard', path: '/' },
                    { label: 'Calendario' }
                ]}
                actions={
                    <div className="flex flex-col md:flex-row items-center gap-4">
                        {/* View Toggles */}
                        <div className="flex items-center gap-2 bg-slate-50 p-1 rounded-xl border border-slate-200">
                            {(['dayGridMonth', 'timeGridWeek', 'timeGridDay'] as CalendarView[]).map(view => (
                                <button
                                    key={view}
                                    className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${currentView === view
                                        ? 'bg-white text-indigo-600 shadow-sm border border-slate-200'
                                        : 'text-slate-500 hover:text-slate-900'
                                        }`}
                                    onClick={() => handleViewChange(view)}
                                >
                                    {viewLabels[view]}
                                </button>
                            ))}
                        </div>

                        <Button
                            variant="primary"
                            icon={<Plus size={18} />}
                            className="!rounded-xl shadow-md shadow-indigo-100"
                            onClick={() => {
                                setSelectedDate(format(new Date(), 'yyyy-MM-dd'));
                                setIsEventModalOpen(true);
                            }}
                        >
                            Nuovo Evento
                        </Button>
                    </div>
                }
            />

            <div className="flex flex-1 gap-6 overflow-hidden">
                {/** 
                 * Sidebar sinistra: include mini-riepilogo assenze odierne,
                 * filtri di visualizzazione e gestione dei calendari personali.
                 */}
                <aside className="w-72 flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar hidden lg:flex">
                    {/* Navigation / Today Card */}
                    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                                <Clock size={16} className="text-indigo-500" />
                                Oggi
                            </h3>
                            <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
                                {format(new Date(), 'EE dd')}
                            </span>
                        </div>
                        <div className="space-y-3">
                            {awayToday.length > 0 ? (
                                awayToday.slice(0, 3).map((leave, idx) => (
                                    <div key={idx} className="flex items-center gap-3 group">
                                        <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-600 border border-white shadow-sm ring-2 ring-slate-50">
                                            {leave.title.charAt(0)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-semibold text-slate-800 truncate">{leave.title}</p>
                                            <p className="text-[10px] text-slate-500">{(leave.metadata as any)?.leave_type_code || 'FERIE'}</p>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <p className="text-xs text-slate-400 italic">Nessun assente oggi</p>
                            )}
                            {awayToday.length > 3 && (
                                <button className="text-[10px] font-bold text-indigo-500 hover:text-indigo-600 w-full text-center py-1">
                                    + altri {awayToday.length - 3}
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Filters Sidebar Section */}
                    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                            <Settings size={14} /> Filtri Visualizzazione
                        </h3>
                        <div className="space-y-4">
                            <div>
                                <p className="text-[10px] font-bold text-slate-400 mb-2 uppercase">Pubblici</p>
                                <div className="space-y-2">
                                    <FilterToggle
                                        label="Festività Nazionali"
                                        color="rose-500"
                                        checked={filters.showNationalHolidays}
                                        onChange={() => toggleFilter('showNationalHolidays')}
                                    />
                                    <FilterToggle
                                        label="Chiusure Aziendali"
                                        color="slate-700"
                                        checked={filters.showCompanyClosures}
                                        onChange={() => toggleFilter('showCompanyClosures')}
                                    />
                                </div>
                            </div>
                            <div>
                                <p className="text-[10px] font-bold text-slate-400 mb-2 uppercase">Team</p>
                                <div className="space-y-2">
                                    <FilterToggle
                                        label="Assenze Team"
                                        color="emerald-500"
                                        checked={filters.showTeamLeaves}
                                        onChange={() => toggleFilter('showTeamLeaves')}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* My Calendars Sidebar Section */}
                    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex-1">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                <Lock size={14} /> I miei Calendari
                            </h3>
                            <button
                                onClick={() => setIsCalendarModalOpen(true)}
                                className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-indigo-600 transition-colors"
                                title="Gestione Calendari"
                            >
                                <Settings size={14} />
                            </button>
                        </div>
                        <div className="space-y-2 max-h-60 overflow-y-auto pr-1 custom-scrollbar">
                            {userCalendars.map(cal => (
                                <label key={cal.id} className="flex items-center gap-3 cursor-pointer group p-1.5 rounded-lg hover:bg-slate-50 transition-colors">
                                    <div className="relative flex items-center">
                                        <input
                                            type="checkbox"
                                            checked={!filters.hiddenCalendars.includes(cal.id)}
                                            onChange={() => toggleCalendarVisibility(cal.id)}
                                            className="rounded border-slate-300 text-indigo-600 focus:ring-0 w-4 h-4 cursor-pointer"
                                        />
                                    </div>
                                    <span className="w-2.5 h-2.5 rounded-full shadow-sm" style={{ backgroundColor: cal.color }} />
                                    <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900 flex-1 truncate">{cal.name}</span>
                                    {!cal.is_owner && (
                                        <span title="Condiviso con te">
                                            <Users size={12} className="text-slate-400" />
                                        </span>
                                    )}
                                </label>
                            ))}
                            {userCalendars.length === 0 && (
                                <p className="text-xs text-slate-400 italic">Nessun calendario</p>
                            )}
                        </div>
                    </div>
                </aside>

                {/* Main Calendar Content */}
                <main className="flex-1 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
                    {/* Internal FC Header Replacement */}
                    <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50/50">
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => calendarRef.current?.getApi().prev()}
                                className="p-2 hover:bg-white hover:shadow-sm rounded-xl border border-transparent hover:border-slate-200 transition-all text-slate-600"
                            >
                                <ChevronDown size={18} className="rotate-90" />
                            </button>
                            <button
                                onClick={() => calendarRef.current?.getApi().today()}
                                className="px-3 py-1.5 text-xs font-bold text-slate-700 hover:text-indigo-600 transition-colors border border-slate-200 bg-white rounded-lg shadow-sm"
                            >
                                Oggi
                            </button>
                            <button
                                onClick={() => calendarRef.current?.getApi().next()}
                                className="p-2 hover:bg-white hover:shadow-sm rounded-xl border border-transparent hover:border-slate-200 transition-all text-slate-600"
                            >
                                <ChevronDown size={18} className="-rotate-90" />
                            </button>
                        </div>
                        <h2 className="text-lg font-bold text-slate-800 tracking-tight">
                            {format(currentDate, 'MMMM yyyy')}
                        </h2>
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-3 px-3 py-1.5 bg-white rounded-lg border border-slate-200 shadow-sm text-[10px] font-bold text-slate-400">
                                <div className="flex items-center gap-1">
                                    <span className="w-2 h-2 rounded bg-emerald-500" />
                                    <span>APPROVED</span>
                                </div>
                                <div className="flex items-center gap-1">
                                    <span className="w-2 h-2 rounded bg-amber-500" />
                                    <span>PENDING</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 p-4 overflow-y-auto custom-scrollbar fc-enterprise-theme">
                        <FullCalendar
                            ref={calendarRef}
                            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                            initialView={currentView}
                            locale="it"
                            headerToolbar={false}
                            events={events}
                            eventClick={async (info) => {
                                const eventType = info.event.extendedProps?.type;
                                const personalEventTypes = ['event', 'meeting', 'task', 'reminder', 'personal', 'deadline', 'other', 'generic'];

                                // Only open detail modal for user events, explicitly excluding leaves/holidays
                                if (personalEventTypes.includes(eventType)) {
                                    const now = new Date().getTime();
                                    const last = lastClickRef.current;
                                    const isDoubleClick = last && last.id === info.event.id && (now - last.time) < 500;
                                    lastClickRef.current = { id: info.event.id, time: now };

                                    try {
                                        const eventData = await calendarService.getEvent(info.event.id);
                                        setIsEditModeInitial(!!isDoubleClick);
                                        setSelectedEvent(eventData);
                                    } catch (err) {
                                        console.error('Error fetching event:', err);
                                    }
                                }
                            }}
                            dateClick={(info) => {
                                setSelectedDate(info.dateStr);
                                setIsEventModalOpen(true);
                            }}
                            datesSet={(dateInfo) => {
                                setCurrentDate(dateInfo.view.currentStart);
                            }}
                            height="100%"
                            dayMaxEvents={4}
                            weekends={true}
                            firstDay={1}
                            slotMinTime="08:00:00"
                            slotMaxTime="20:00:00"
                            allDaySlot={true}
                            nowIndicator={true}
                        />
                    </div>
                </main>
            </div>

            {/* Event Modal */}
            <NewEventModal
                isOpen={isEventModalOpen}
                onClose={() => setIsEventModalOpen(false)}
                onEventCreated={() => {
                    queryClient.invalidateQueries({ queryKey: ['calendar-range'] });
                    toast.success('Impegno creato correttamente');
                }}
                selectedDate={selectedDate}
                userCalendars={userCalendars}
            />

            {/* Event Detail Modal */}
            <EventDetailModal
                isOpen={!!selectedEvent}
                onClose={() => {
                    setSelectedEvent(null);
                    setIsEditModeInitial(false);
                }}
                event={selectedEvent}
                onEventUpdated={() => {
                    queryClient.invalidateQueries({ queryKey: ['calendar-range'] });
                    setSelectedEvent(null);
                    setIsEditModeInitial(false);
                }}
                onEventDeleted={() => {
                    queryClient.invalidateQueries({ queryKey: ['calendar-range'] });
                    setSelectedEvent(null);
                    setIsEditModeInitial(false);
                }}
                userCalendars={userCalendars}
                currentUserId={user?.id}
                initialIsEditing={isEditModeInitial}
            />

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
                                            {editingCalendarId === cal.id ? (
                                                /* Inline Edit Mode */
                                                <form
                                                    onSubmit={async (e) => {
                                                        e.preventDefault();
                                                        const formData = new FormData(e.currentTarget);
                                                        try {
                                                            await updateUserCalendar.mutateAsync({
                                                                id: cal.id,
                                                                data: {
                                                                    name: formData.get('name') as string,
                                                                    color: formData.get('color') as string
                                                                }
                                                            });
                                                            toast.success('Calendario aggiornato');
                                                            setEditingCalendarId(null);
                                                        } catch (err) {
                                                            toast.error('Errore durante l\'aggiornamento');
                                                        }
                                                    }}
                                                    className="flex items-center gap-3 p-3 rounded-xl border border-indigo-200 bg-indigo-50"
                                                >
                                                    <input
                                                        type="color"
                                                        name="color"
                                                        defaultValue={cal.color}
                                                        className="w-8 h-8 rounded cursor-pointer border-none"
                                                    />
                                                    <input
                                                        type="text"
                                                        name="name"
                                                        defaultValue={cal.name}
                                                        required
                                                        className="flex-1 px-2 py-1 text-sm rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                                                    />
                                                    <Button type="submit" variant="primary" size="sm" isLoading={updateUserCalendar.isPending}>
                                                        Salva
                                                    </Button>
                                                    <button
                                                        type="button"
                                                        onClick={() => setEditingCalendarId(null)}
                                                        className="text-gray-400 hover:text-gray-600 p-1"
                                                    >
                                                        <X size={16} />
                                                    </button>
                                                </form>
                                            ) : (
                                                /* View Mode */
                                                <div className="flex items-center justify-between p-3 rounded-xl border border-gray-100 hover:bg-gray-50 transition-colors">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-4 h-4 rounded shadow-sm" style={{ backgroundColor: cal.color }} />
                                                        <div className="flex flex-col">
                                                            <span className="text-sm font-medium text-gray-700">{cal.name}</span>
                                                            {!cal.is_owner && (() => {
                                                                if (cal.type === 'SYSTEM') {
                                                                    return <span className="text-[10px] text-gray-400">Calendario di Sistema</span>;
                                                                }
                                                                if (cal.type === 'LOCATION') {
                                                                    return <span className="text-[10px] text-gray-400">Calendario Sede</span>;
                                                                }
                                                                const ownerId = cal.user_id || cal.owner_id;
                                                                const owner = (users || []).find((u: any) => u.id === ownerId);
                                                                const ownerName = owner?.full_name || `${owner?.first_name || ''} ${owner?.last_name || ''}`.trim() || 'un collega';
                                                                return (
                                                                    <span className="text-[10px] text-gray-400">
                                                                        Condiviso da {ownerName}
                                                                    </span>
                                                                );
                                                            })()}
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-1">
                                                        {cal.is_owner && (
                                                            <>
                                                                <button
                                                                    onClick={() => setEditingCalendarId(cal.id)}
                                                                    className="p-1.5 rounded-lg transition-colors text-gray-400 hover:bg-gray-100 hover:text-amber-600"
                                                                    title="Modifica"
                                                                >
                                                                    <Edit3 size={16} />
                                                                </button>
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
                                            )}

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
                                                        {((cal as any).shares || cal.shared_with || []).map((share: any) => {
                                                            const shareUserId = share.user_id || share.shared_with_user_id;
                                                            const sharedUser = users?.find((u: any) => u.id === shareUserId);
                                                            const userName = sharedUser ? `${sharedUser.first_name || ''} ${sharedUser.last_name || ''}`.trim() : 'Utente';
                                                            const initials = userName.split(' ').map((n: string) => n[0]?.toUpperCase() || '').join('').slice(0, 2);
                                                            return (
                                                                <div key={share.id} className="flex items-center justify-between text-sm bg-white p-2 rounded-lg border border-gray-100">
                                                                    <div className="flex items-center gap-2">
                                                                        <div className="w-6 h-6 rounded-full bg-indigo-100 flex items-center justify-center text-[10px] font-bold text-indigo-600">
                                                                            {initials}
                                                                        </div>
                                                                        <span className="text-gray-600">{userName}</span>
                                                                    </div>
                                                                    <button
                                                                        onClick={() => unshareCalendarMut.mutate({ calendarId: cal.id, sharedUserId: shareUserId })}
                                                                        className="text-red-400 hover:text-red-600 p-1"
                                                                    >
                                                                        <X size={14} />
                                                                    </button>
                                                                </div>
                                                            );
                                                        })}
                                                        {(!((cal as any).shares || cal.shared_with) || ((cal as any).shares || cal.shared_with || []).length === 0) && (
                                                            <p className="text-[11px] text-gray-400 italic">Nessuna condivisione attiva</p>
                                                        )}
                                                    </div>

                                                    {/* Add share form */}
                                                    <div className="pt-2 border-t border-gray-200">
                                                        <select
                                                            className="w-full text-xs px-2 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none bg-white font-medium"
                                                            disabled={usersLoading}
                                                            onChange={(e) => {
                                                                if (e.target.value) {
                                                                    shareCalendarMut.mutate({
                                                                        calendarId: cal.id,
                                                                        data: { user_id: e.target.value, permission: 'READ' }
                                                                    });
                                                                    e.target.value = "";
                                                                }
                                                            }}
                                                        >
                                                            <option value="">{usersLoading ? 'Caricamento colleghi...' : 'Aggiungi collega...'}</option>
                                                            {(users || [])
                                                                .filter((u: any) => {
                                                                    // Exclude current user (calendar owner)
                                                                    const ownerId = cal.user_id || cal.owner_id || user?.id;
                                                                    if (u.id === ownerId) return false;
                                                                    // Exclude already shared users - use 'shares' and 's.user_id'
                                                                    const shares = (cal as any).shares || cal.shared_with || [];
                                                                    if (shares.some((s: any) => s.user_id === u.id || s.shared_with_user_id === u.id)) return false;
                                                                    return true;
                                                                })
                                                                .map((u: any) => (
                                                                    <option key={u.id} value={u.id}>
                                                                        {`${u.first_name || ''} ${u.last_name || ''}`.trim() || u.email}
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
            <style>{`
                .fc-enterprise-theme .fc {
                    --fc-border-color: #f1f5f9;
                    --fc-today-bg-color: #f8faff;
                    --fc-page-bg-color: #ffffff;
                    font-family: inherit;
                }
                .fc-enterprise-theme .fc-theme-standard td, 
                .fc-enterprise-theme .fc-theme-standard th {
                    border: 1px solid #f1f5f9;
                }
                .fc-enterprise-theme .fc-col-header-cell {
                    background: #f8faff;
                    padding: 12px 0;
                    font-size: 0.75rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: #64748b;
                    border-bottom: 2px solid #e2e8f0 !important;
                }
                .fc-enterprise-theme .fc-daygrid-day-number {
                    font-size: 0.875rem;
                    font-weight: 600;
                    color: #334155;
                    padding: 8px !important;
                }
                .fc-enterprise-theme .fc-daygrid-day.fc-day-today {
                    background-color: #f0f7ff !important;
                }
                .fc-enterprise-theme .fc-event {
                    border-radius: 8px !important;
                    padding: 4px 8px !important;
                    margin: 1px 4px !important;
                    border: none !important;
                    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                .fc-enterprise-theme .fc-event:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                    filter: brightness(0.95);
                }
                .fc-enterprise-theme .fc-daygrid-more-link {
                    font-size: 0.75rem;
                    font-weight: 700;
                    color: #6366f1;
                    padding: 2px 6px;
                }
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #e2e8f0;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #cbd5e1;
                }
            `}</style>
        </div>
    );
}

export default CalendarPage;
