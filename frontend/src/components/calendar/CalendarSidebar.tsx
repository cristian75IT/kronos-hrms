import { format } from 'date-fns';
import { Clock, Settings, Lock, Users } from 'lucide-react';
import type { CalendarFilters } from '../../types/calendar-ui';
import type { UserCalendar, CalendarRangeView } from '../../services/calendar.service';
import { useMemo } from 'react';

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
            {/* Note: Colors like bg-rose-500 must be safelisted or used as standard styles. 
                Assuming Tailwind JIT is watching this file. */}
            <span className={`w-2.5 h-2.5 rounded-full shadow-sm bg-${color}`} />
            <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900 transition-colors">{label}</span>
        </label>
    );
}

interface CalendarSidebarProps {
    filters: CalendarFilters;
    onToggleFilter: (key: keyof CalendarFilters) => void;
    onToggleCalendarVisibility: (id: string) => void;
    userCalendars: UserCalendar[];
    onOpenCalendarModal: () => void;
    calendarData: CalendarRangeView | undefined;
}

export function CalendarSidebar({
    filters,
    onToggleFilter,
    onToggleCalendarVisibility,
    userCalendars,
    onOpenCalendarModal,
    calendarData,
}: CalendarSidebarProps) {
    // Calculate "Who is Away Today"
    const todayStr = format(new Date(), 'yyyy-MM-dd');
    const awayToday = useMemo(() => {
        if (!calendarData || !calendarData.days) return [];
        const todayData = calendarData.days.find(d => d.date === todayStr);
        if (!todayData) return [];
        return todayData.items.filter(item => item.item_type === 'leave');
    }, [calendarData, todayStr]);

    return (
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
                                onChange={() => onToggleFilter('showNationalHolidays')}
                            />
                            <FilterToggle
                                label="Chiusure Aziendali"
                                color="slate-700"
                                checked={filters.showCompanyClosures}
                                onChange={() => onToggleFilter('showCompanyClosures')}
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
                                onChange={() => onToggleFilter('showTeamLeaves')}
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
                        onClick={onOpenCalendarModal}
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
                                    onChange={() => onToggleCalendarVisibility(cal.id)}
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
    );
}
