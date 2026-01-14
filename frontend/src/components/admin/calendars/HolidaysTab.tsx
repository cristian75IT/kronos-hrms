/**
 * KRONOS - Holidays Tab Component
 * 
 * Displays holidays list/grid with filters and actions.
 */
import { useState } from 'react';
import {
    Flag,
    MapPin,
    Plus,
    Edit,
    Trash2,
    Check,
    Loader,
    Copy,
    Sparkles,
    Calendar,
    Globe,
    Info,
    ArrowUpRight,
    LayoutGrid,
    List,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { it } from 'date-fns/locale';
import type { Holiday } from '../../../services/calendar.service';

type HolidayFilter = 'all' | 'national' | 'local';
type ViewMode = 'list' | 'grid';

interface HolidaysTabProps {
    holidays: Holiday[];
    year: number;
    onAdd: () => void;
    onEdit: (holiday: Holiday) => void;
    onDelete: (id: string) => void;
    onConfirm: (id: string) => void;
    onGenerate: () => void;
    onCopy: () => void;
    isGenerating: boolean;
}

export function HolidaysTab({
    holidays,
    year,
    onAdd,
    onEdit,
    onDelete,
    onConfirm,
    onGenerate,
    onCopy,
    isGenerating,
}: HolidaysTabProps) {
    const [filter, setFilter] = useState<HolidayFilter>('all');
    const [viewMode, setViewMode] = useState<ViewMode>('list');

    const filteredHolidays = holidays
        .filter(h => {
            if (filter === 'all') return true;
            if (filter === 'national') return h.scope === 'national';
            if (filter === 'local') return h.scope !== 'national';
            return true;
        })
        .sort((a, b) => a.date.localeCompare(b.date));

    return (
        <div className="space-y-6">
            {/* Actions Toolbar */}
            <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0 scrollbar-hide">
                    {(['all', 'national', 'local'] as HolidayFilter[]).map(f => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-4 py-2 text-sm font-medium rounded-xl transition-all whitespace-nowrap ${filter === f
                                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200'
                                : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                                }`}
                        >
                            {f === 'all' && 'Tutti i giorni'}
                            {f === 'national' && 'Istituzionali'}
                            {f === 'local' && 'Territoriali'}
                        </button>
                    ))}

                    {/* View Mode Toggle */}
                    <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-xl ml-2">
                        <button
                            onClick={() => setViewMode('list')}
                            className={`p-1.5 rounded-lg transition-all ${viewMode === 'list' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            <List size={16} />
                        </button>
                        <button
                            onClick={() => setViewMode('grid')}
                            className={`p-1.5 rounded-lg transition-all ${viewMode === 'grid' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            <LayoutGrid size={16} />
                        </button>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={onCopy}
                        className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-50 font-medium text-sm rounded-xl transition-all"
                    >
                        <Copy size={16} />
                        Copia da {year - 1}
                    </button>
                    <button
                        onClick={onGenerate}
                        disabled={isGenerating}
                        className="flex items-center gap-2 px-4 py-2 text-indigo-600 hover:bg-indigo-50 font-medium text-sm rounded-xl transition-all"
                    >
                        {isGenerating ? <Loader size={16} className="animate-spin" /> : <Sparkles size={16} />}
                        Auto-Genera
                    </button>
                    <div className="w-px h-6 bg-gray-200 mx-1 hidden md:block" />
                    <button
                        onClick={onAdd}
                        className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-indigo-100"
                    >
                        <Plus size={18} />
                        Aggiungi
                    </button>
                </div>
            </div>

            {/* Content */}
            {viewMode === 'list' ? (
                <HolidayListView
                    holidays={filteredHolidays}
                    year={year}
                    onEdit={onEdit}
                    onDelete={onDelete}
                    onConfirm={onConfirm}
                />
            ) : (
                <HolidayGridView
                    holidays={filteredHolidays}
                    year={year}
                    onEdit={onEdit}
                />
            )}
        </div>
    );
}

function HolidayListView({
    holidays,
    year,
    onEdit,
    onDelete,
    onConfirm,
}: {
    holidays: Holiday[];
    year: number;
    onEdit: (holiday: Holiday) => void;
    onDelete: (id: string) => void;
    onConfirm: (id: string) => void;
}) {
    if (holidays.length === 0) {
        return (
            <div className="py-20 text-center bg-white border border-gray-100 rounded-3xl">
                <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Calendar size={32} className="text-gray-300" />
                </div>
                <h3 className="text-lg font-bold text-gray-900">Nessuna festività trovata</h3>
                <p className="text-sm text-gray-500 max-w-xs mx-auto mt-1">
                    Non ci sono festività che corrispondono ai filtri selezionati per il {year}.
                </p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {holidays.map(holiday => (
                <div
                    key={holiday.id}
                    className={`bg-white border rounded-2xl p-5 transition-all hover:shadow-lg group relative ${!holiday.is_confirmed ? 'border-amber-200 bg-amber-50/10' : 'border-gray-200'
                        }`}
                >
                    <div className="flex items-start justify-between mb-4">
                        <div
                            className={`p-3 rounded-2xl ${holiday.scope === 'national'
                                ? 'bg-red-50 text-red-600'
                                : 'bg-orange-50 text-orange-600'
                                }`}
                        >
                            {holiday.scope === 'national' ? <Globe size={20} /> : <MapPin size={20} />}
                        </div>
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            {!holiday.is_confirmed && (
                                <button
                                    onClick={() => onConfirm(holiday.id)}
                                    className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-xl transition-all"
                                    title="Conferma"
                                >
                                    <Check size={18} />
                                </button>
                            )}
                            <button
                                onClick={() => onEdit(holiday)}
                                className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
                            >
                                <Edit size={18} />
                            </button>
                            <button
                                onClick={() => onDelete(holiday.id)}
                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                            >
                                <Trash2 size={18} />
                            </button>
                        </div>
                    </div>

                    <div className="mb-1">
                        <h4 className="font-bold text-gray-900 line-clamp-1">{holiday.name}</h4>
                        <p className="text-sm font-medium text-gray-500 uppercase tracking-tighter mt-0.5">
                            {format(parseISO(holiday.date), 'EEEE d MMMM', { locale: it })}
                        </p>
                    </div>

                    <div className="flex items-center gap-2 mt-4">
                        {holiday.scope === 'national' ? (
                            <span className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider bg-red-100 text-red-700 rounded-lg">
                                Istituzionale
                            </span>
                        ) : (
                            <span className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider bg-orange-100 text-orange-700 rounded-lg">
                                Territoriale
                            </span>
                        )}

                        {!holiday.is_confirmed && (
                            <div className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-700 rounded-lg animate-pulse">
                                <Info size={10} />
                                Pending
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}

function HolidayGridView({
    holidays,
    year,
    onEdit,
}: {
    holidays: Holiday[];
    year: number;
    onEdit: (holiday: Holiday) => void;
}) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {Array.from({ length: 12 }).map((_, i) => {
                const monthHolidays = holidays.filter(h => parseISO(h.date).getMonth() === i);
                if (monthHolidays.length === 0) return null;
                return (
                    <div key={i} className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
                        <div className="bg-gray-50 px-4 py-3 border-b border-gray-100">
                            <h5 className="font-bold text-gray-900 capitalize">
                                {format(new Date(year, i, 1), 'MMMM', { locale: it })}
                            </h5>
                        </div>
                        <div className="p-2 space-y-1">
                            {monthHolidays.map(h => (
                                <div
                                    key={h.id}
                                    onClick={() => onEdit(h)}
                                    className="flex items-center gap-3 p-2 hover:bg-indigo-50 rounded-xl cursor-pointer transition-all group"
                                >
                                    <div
                                        className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${h.scope === 'national' ? 'bg-red-100 text-red-600' : 'bg-orange-100 text-orange-600'
                                            }`}
                                    >
                                        {format(parseISO(h.date), 'dd')}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm font-semibold text-gray-900 truncate">{h.name}</div>
                                        <div className="text-[10px] text-gray-500 uppercase font-bold tracking-tight">
                                            {h.scope === 'national' ? 'Naz' : 'Loc'}
                                        </div>
                                    </div>
                                    <ArrowUpRight size={14} className="text-gray-300 group-hover:text-indigo-500" />
                                </div>
                            ))}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

// Re-export for component index
export { Flag, MapPin };
