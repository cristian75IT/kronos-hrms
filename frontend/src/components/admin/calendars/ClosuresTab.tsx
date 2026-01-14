/**
 * KRONOS - Closures Tab Component
 * 
 * Displays company closures list with actions.
 */
import {
    Building,
    Plus,
    Edit,
    Trash2,
    Check,
    Briefcase,
    Calendar,
    Sparkles,
    Info,
    ArrowUpRight,
} from 'lucide-react';
import { format, parseISO, differenceInDays } from 'date-fns';
import { it } from 'date-fns/locale';
import type { Closure } from '../../../services/calendar.service';

interface ClosuresTabProps {
    closures: Closure[];
    onAdd: () => void;
    onEdit: (closure: Closure) => void;
    onDelete: (id: string) => void;
}

export function ClosuresTab({ closures, onAdd, onEdit, onDelete }: ClosuresTabProps) {
    return (
        <div className="space-y-6">
            {/* Toolbar */}
            <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
                <p className="text-sm font-medium text-gray-500 flex items-center gap-2">
                    <Info size={16} className="text-indigo-400" />
                    Gestisci ponti e festività aziendali obbligatorie per tutti o parte dei dipendenti.
                </p>
                <button
                    onClick={onAdd}
                    className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-indigo-100"
                >
                    <Plus size={18} />
                    Pianifica Chiusura
                </button>
            </div>

            {/* Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {closures.map(closure => {
                    const daysCount = differenceInDays(parseISO(closure.end_date), parseISO(closure.start_date)) + 1;
                    return (
                        <div
                            key={closure.id}
                            className="bg-white border border-gray-200 rounded-3xl overflow-hidden shadow-sm hover:shadow-xl transition-all group"
                        >
                            <div className="p-6">
                                <div className="flex items-start justify-between mb-6">
                                    <div className="flex items-center gap-4">
                                        <div
                                            className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-inner ${closure.closure_type === 'total'
                                                ? 'bg-purple-100 text-purple-600'
                                                : 'bg-violet-100 text-violet-600'
                                                }`}
                                        >
                                            <Briefcase size={24} />
                                        </div>
                                        <div>
                                            <h4 className="text-lg font-bold text-gray-900">{closure.name}</h4>
                                            <p className="text-sm text-gray-500">
                                                {closure.closure_type === 'total'
                                                    ? 'Sospensione Totale Attività'
                                                    : 'Sospensione Parziale'}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-1 opacity-10 md:opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            onClick={() => onEdit(closure)}
                                            className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
                                        >
                                            <Edit size={20} />
                                        </button>
                                        <button
                                            onClick={() => onDelete(closure.id)}
                                            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                                        >
                                            <Trash2 size={20} />
                                        </button>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4 mb-6">
                                    <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100">
                                        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Periodo</p>
                                        <div className="flex items-center gap-2">
                                            <Calendar size={14} className="text-gray-400" />
                                            <span className="text-sm font-bold text-gray-900">
                                                {format(parseISO(closure.start_date), 'd MMM') ===
                                                    format(parseISO(closure.end_date), 'd MMM')
                                                    ? format(parseISO(closure.start_date), 'd MMMM', { locale: it })
                                                    : `${format(parseISO(closure.start_date), 'd MMM')} - ${format(
                                                        parseISO(closure.end_date),
                                                        'd MMM'
                                                    )}`}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100">
                                        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Durata</p>
                                        <div className="flex items-center gap-2">
                                            <Sparkles size={14} className="text-indigo-400" />
                                            <span className="text-sm font-bold text-gray-900">
                                                {daysCount} {daysCount === 1 ? 'giorno' : 'giorni'}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex flex-wrap gap-2">
                                    {closure.is_paid && (
                                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 text-xs font-bold ring-1 ring-inset ring-emerald-100">
                                            <Check size={12} /> Azienda
                                        </span>
                                    )}
                                    {closure.consumes_leave_balance && (
                                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-50 text-amber-700 text-xs font-bold ring-1 ring-inset ring-amber-100">
                                            <ArrowUpRight size={12} /> Scala Ferie
                                        </span>
                                    )}
                                    <div className="flex-1" />
                                    {closure.description && (
                                        <div className="text-xs text-gray-400 pt-2">{closure.description}</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}

                {closures.length === 0 && (
                    <div className="col-span-full py-20 text-center bg-white border border-gray-100 rounded-3xl">
                        <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Building size={32} className="text-gray-300" />
                        </div>
                        <h3 className="text-lg font-bold text-gray-900">Nessuna chiusura pianificata</h3>
                        <p className="text-sm text-gray-500 max-w-xs mx-auto mt-1">
                            Organizza ferie collettive o chiusure per manutenzione per l'intero staff.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
