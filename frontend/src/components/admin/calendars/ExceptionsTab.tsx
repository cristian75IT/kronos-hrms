/**
 * KRONOS - Exceptions Tab Component
 * 
 * Displays working day exceptions list.
 */
import { Plus, Trash2, AlertCircle } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { it } from 'date-fns/locale';
import type { WorkingDayException } from '../../../services/calendar.service';

interface ExceptionsTabProps {
    exceptions: WorkingDayException[];
    onAdd: () => void;
    onDelete: (id: string) => void;
}

export function ExceptionsTab({ exceptions, onAdd, onDelete }: ExceptionsTabProps) {
    return (
        <div className="space-y-6">
            {/* Toolbar */}
            <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
                <p className="text-sm font-medium text-gray-500 flex items-center gap-2">
                    <AlertCircle size={16} className="text-amber-500" />
                    Gestione giorni lavorativi straordinari (es. recuperi, aperture straordinarie). Per chiusure e ponti,
                    utilizza la scheda Chiusure.
                </p>
                <button
                    onClick={onAdd}
                    className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-indigo-100"
                >
                    <Plus size={18} />
                    Aggiungi Eccezione
                </button>
            </div>

            {/* Table */}
            <div className="bg-white border border-gray-200 rounded-3xl overflow-hidden shadow-sm">
                <table className="w-full border-collapse">
                    <thead>
                        <tr className="bg-gray-50/50 border-b border-gray-100">
                            <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">
                                Data
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">
                                Motivazione
                            </th>
                            <th className="px-6 py-4 text-right text-xs font-bold text-gray-400 uppercase tracking-widest">
                                Azioni
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {exceptions.map(exception => (
                            <tr key={exception.id} className="hover:bg-gray-50/50 transition-colors">
                                <td className="px-6 py-4">
                                    <span className="font-bold text-gray-900">
                                        {format(parseISO(exception.date), 'EEEE d MMMM', { locale: it })}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-sm text-gray-500 font-medium">{exception.reason || '-'}</span>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => onDelete(exception.id)}
                                        className="p-2 text-gray-300 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </td>
                            </tr>
                        ))}

                        {exceptions.length === 0 && (
                            <tr>
                                <td colSpan={3} className="py-20 text-center">
                                    <AlertCircle size={40} className="mx-auto text-gray-200 mb-3" />
                                    <p className="text-sm font-bold text-gray-400">Nessuna eccezione pianificata</p>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
