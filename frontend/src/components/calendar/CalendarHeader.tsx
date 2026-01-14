import { Calendar as CalendarIcon, Filter, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { Button } from '../common';
import type { CalendarView } from '../../types/calendar-ui';

interface CalendarHeaderProps {
    currentDate: Date;
    onPrev: () => void;
    onNext: () => void;
    onToday: () => void;
    currentView: CalendarView;
    onChangeView: (view: CalendarView) => void;
    onExportIcs: () => void;
    onToggleMobileSidebar: () => void;
}

export function CalendarHeader({
    currentDate,
    onPrev,
    onNext,
    onToday,
    currentView,
    onChangeView,
    onExportIcs,
    onToggleMobileSidebar
}: CalendarHeaderProps) {
    return (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                    <CalendarIcon className="text-indigo-600" />
                    Calendario Aziendale
                </h1>
                <p className="text-slate-500 mt-1">
                    Gestisci presenze, ferie ed eventi
                </p>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-2 sm:pb-0">
                <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-lg p-1 mr-2 shadow-sm">
                    <button
                        onClick={onPrev}
                        className="p-1.5 hover:bg-slate-100 rounded-md text-slate-600 transition-colors"
                    >
                        <ChevronLeft size={18} />
                    </button>
                    <button
                        onClick={onToday}
                        className="px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-100 rounded-md transition-colors"
                    >
                        {format(currentDate, 'MMMM yyyy', { locale: it }).toUpperCase()}
                    </button>
                    <button
                        onClick={onNext}
                        className="p-1.5 hover:bg-slate-100 rounded-md text-slate-600 transition-colors"
                    >
                        <ChevronRight size={18} />
                    </button>
                </div>

                <div className="flex gap-2">
                    <div className="flex bg-slate-100 rounded-lg p-1">
                        <button
                            onClick={() => onChangeView('dayGridMonth')}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${currentView === 'dayGridMonth'
                                ? 'bg-white text-indigo-600 shadow-sm'
                                : 'text-slate-500 hover:text-slate-700'
                                }`}
                        >
                            Mese
                        </button>
                        <button
                            onClick={() => onChangeView('timeGridWeek')}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${currentView === 'timeGridWeek'
                                ? 'bg-white text-indigo-600 shadow-sm'
                                : 'text-slate-500 hover:text-slate-700'
                                }`}
                        >
                            Settimana
                        </button>
                        <button
                            onClick={() => onChangeView('timeGridDay')}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${currentView === 'timeGridDay'
                                ? 'bg-white text-indigo-600 shadow-sm'
                                : 'text-slate-500 hover:text-slate-700'
                                }`}
                        >
                            Giorno
                        </button>
                    </div>

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onExportIcs}
                        title="Esporta Calendario (iCal)"
                        className="hidden sm:flex"
                    >
                        <Download size={16} />
                    </Button>

                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={onToggleMobileSidebar}
                        className="lg:hidden"
                    >
                        <Filter size={16} />
                    </Button>
                </div>
            </div>
        </div>
    );
}
