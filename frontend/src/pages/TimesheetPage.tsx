import { useState, useEffect } from 'react';
import { format, subMonths, addMonths, parseISO, isWeekend } from 'date-fns';
import { it } from 'date-fns/locale';
import {
    ChevronLeft,
    ChevronRight,
    CheckCircle,
    AlertTriangle,
    Calendar as CalendarIcon,
    FileText,
    Clock,
    Briefcase
} from 'lucide-react';

import { timesheetService } from '../services/timesheet.service';
import type { MonthlyTimesheet } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import PageHeader from '../components/common/PageHeader';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ConfirmModal } from '../components/common/ConfirmModal';
// import { useAuth } from '../context/AuthContext'; 

// Helper for status color
const getStatusColor = (status: string) => {
    if (!status) return 'text-gray-500 bg-gray-50';
    const s = status.toLowerCase();
    if (s.includes('assente') || s.includes('malattia')) return 'text-red-700 bg-red-50';
    if (s.includes('ferie')) return 'text-yellow-700 bg-yellow-50';
    if (s.includes('festivo') || s.includes('weekend')) return 'text-gray-500 bg-gray-100';
    if (s.includes('trasferta')) return 'text-purple-700 bg-purple-50';
    if (s.includes('presente')) return 'text-green-700 bg-green-50';
    return 'text-gray-700 bg-gray-50';
};

export default function TimesheetPage() {
    const [viewDate, setViewDate] = useState(new Date()); // Represents the month we are viewing
    const [timesheet, setTimesheet] = useState<MonthlyTimesheet | null>(null);
    const [loading, setLoading] = useState(false);
    const [confirmModalOpen, setConfirmModalOpen] = useState(false);

    // const { user } = useAuth(); 

    useEffect(() => {
        loadTimesheet();
    }, [viewDate]);

    const loadTimesheet = async () => {
        setLoading(true);
        try {
            const y = viewDate.getFullYear();
            const m = viewDate.getMonth() + 1; // JS month is 0-indexed
            const data = await timesheetService.getMyTimesheet(y, m);
            setTimesheet(data);
        } catch (error) {
            console.error("Failed to load timesheet", error);
            setTimesheet(null);
        } finally {
            setLoading(false);
        }
    };

    const handlePreviousMonth = () => setViewDate(subMonths(viewDate, 1));
    const handleNextMonth = () => setViewDate(addMonths(viewDate, 1));

    const onConfirmTimesheet = async () => {
        if (!timesheet) return;
        try {
            await timesheetService.confirmMyTimesheet(timesheet.year, timesheet.month);
            setConfirmModalOpen(false);
            loadTimesheet();
        } catch (err) {
            console.error(err);
            alert("Errore durante la conferma. Riprova più tardi.");
        }
    };

    if (loading && !timesheet) {
        return (
            <div className="flex justify-center items-center h-screen">
                <LoadingSpinner />
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            <PageHeader
                title="Giornaliero Presenze"
                description="Visualizza e conferma le tue presenze mensili"
            />

            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row justify-between items-center bg-white p-4 rounded-lg shadow-sm border border-gray-200 gap-4">
                <div className="flex items-center space-x-4">
                    <button onClick={handlePreviousMonth} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                    <h2 className="text-xl font-semibold capitalize min-w-[200px] text-center">
                        {format(viewDate, 'MMMM yyyy', { locale: it })}
                    </h2>
                    <button onClick={handleNextMonth} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                        <ChevronRight className="w-5 h-5" />
                    </button>
                </div>

                <div className="flex items-center gap-4">
                    {timesheet?.status === 'CONFIRMED' || timesheet?.status === 'APPROVED' ? (
                        <div className="flex items-center space-x-2 px-4 py-2 bg-green-50 border border-green-200 text-green-700 rounded-lg">
                            <CheckCircle className="w-5 h-5" />
                            <div className="flex flex-col">
                                <span className="font-semibold text-sm">Confermato</span>
                                {timesheet.confirmed_at && (
                                    <span className="text-xs">il {format(parseISO(timesheet.confirmed_at), 'dd/MM/yyyy')}</span>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center gap-3">
                            {timesheet ? (
                                <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium border border-yellow-200">
                                    Bozza
                                </span>
                            ) : (
                                <span className="italic text-gray-500">Nessun dato</span>
                            )}

                            {timesheet?.can_confirm && (
                                <Button variant="primary" onClick={() => setConfirmModalOpen(true)}>
                                    Conferma Mese
                                </Button>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {!timesheet ? (
                <Card>
                    <div className="p-8 text-center text-gray-500">
                        Seleziona un mese per visualizzare il giornaliero.
                    </div>
                </Card>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Table */}
                    <Card className="lg:col-span-2">
                        <div className="p-4 border-b bg-gray-50/50 flex justify-between items-center">
                            <h3 className="font-semibold text-lg flex items-center text-gray-800">
                                <CalendarIcon className="w-5 h-5 mr-2 text-indigo-600" />
                                Dettaglio {format(viewDate, 'MMMM', { locale: it })}
                            </h3>
                            <span className="text-xs text-gray-500">
                                {timesheet.days.length} giorni
                            </span>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b">
                                    <tr>
                                        <th className="px-6 py-3 font-medium">Data</th>
                                        <th className="px-6 py-3 font-medium">Stato</th>
                                        <th className="px-6 py-3 font-medium text-center">Ore</th>
                                        <th className="px-6 py-3 font-medium">Note</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {timesheet.days.map((day, idx) => {
                                        const dateObj = parseISO(day.date);
                                        const isDayWeekend = isWeekend(dateObj);
                                        return (
                                            <tr key={idx} className={`hover:bg-gray-50 transition-colors ${isDayWeekend ? 'bg-gray-50/50' : ''}`}>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col">
                                                        <span className={`font-medium capitalize ${isDayWeekend ? 'text-red-500' : 'text-gray-900'}`}>
                                                            {format(dateObj, 'EEEE', { locale: it })}
                                                        </span>
                                                        <span className="text-gray-500 text-xs">{format(dateObj, 'dd MMM')}</span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-2.5 py-1 rounded-md text-xs font-semibold inline-flex items-center shadow-sm border border-transparent ${getStatusColor(day.status)}`}>
                                                        {day.status}
                                                    </span>
                                                    {day.leave_type && (
                                                        <div className="text-xs text-gray-500 mt-1 ml-1">
                                                            {day.leave_type}
                                                        </div>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 text-center">
                                                    {day.hours_worked > 0 ? (
                                                        <span className="font-semibold text-gray-900">{day.hours_worked}h</span>
                                                    ) : (
                                                        <span className="text-gray-300">-</span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 text-gray-500 italic truncate max-w-xs">
                                                    {day.notes || '-'}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </Card>

                    {/* Sidebar Summary */}
                    <div className="space-y-6">
                        <Card>
                            <div className="p-4 border-b bg-gray-50/50">
                                <h3 className="font-semibold flex items-center text-gray-800">
                                    <FileText className="w-4 h-4 mr-2 text-indigo-600" />
                                    Riepilogo Mese
                                </h3>
                            </div>
                            <div className="p-4 space-y-5">
                                <div className="flex justify-between items-center pb-2 border-b border-gray-100">
                                    <span className="text-gray-600 text-sm">Giorni Totali</span>
                                    <span className="font-semibold text-gray-900">{timesheet.summary?.total_days || 0}</span>
                                </div>

                                <div className="space-y-3">
                                    <div className="flex justify-between items-center text-sm">
                                        <span className="flex items-center text-green-700">
                                            <Briefcase className="w-4 h-4 mr-2" />
                                            Lavorati
                                        </span>
                                        <span className="font-bold text-green-700">{timesheet.summary?.days_worked || 0}</span>
                                    </div>
                                    <div className="flex justify-between items-center text-sm">
                                        <span className="flex items-center text-red-600">
                                            <AlertTriangle className="w-4 h-4 mr-2" />
                                            Assenze
                                        </span>
                                        <span className="font-bold text-red-600">{timesheet.summary?.days_absent || 0}</span>
                                    </div>
                                </div>

                                <div className="pt-3 border-t border-gray-100 space-y-2 text-sm bg-gray-50 p-3 rounded-md">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Ferie</span>
                                        <span className="font-medium">{timesheet.summary?.vacation_days || 0}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Malattia</span>
                                        <span className="font-medium">{timesheet.summary?.sickness_days || 0}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Permessi/Altro</span>
                                        <span className="font-medium">{timesheet.summary?.other_days || 0}</span>
                                    </div>
                                </div>

                                <div className="mt-4 pt-4 border-t border-gray-200">
                                    <div className="flex justify-between items-center">
                                        <span className="flex items-center text-gray-700 font-medium">
                                            <Clock className="w-4 h-4 mr-2 text-indigo-600" />
                                            Ore Totali
                                        </span>
                                        <span className="font-bold text-xl text-indigo-700">{timesheet.summary?.hours_worked || 0}h</span>
                                    </div>
                                </div>
                            </div>
                        </Card>

                        {timesheet.confirmation_deadline && (
                            <div className={`border rounded-lg p-4 text-sm shadow-sm ${timesheet.status === 'CONFIRMED'
                                ? 'bg-green-50 border-green-200 text-green-800'
                                : 'bg-blue-50 border-blue-200 text-blue-800'
                                }`}>
                                <p className="font-semibold mb-1 flex items-center">
                                    <CalendarIcon className="w-4 h-4 mr-2" />
                                    Scadenza Conferma
                                </p>
                                <p className="opacity-90">
                                    {timesheet.status === 'CONFIRMED'
                                        ? "Hai rispettato la scadenza."
                                        : (
                                            <>
                                                Conferma entro il <strong>{format(parseISO(timesheet.confirmation_deadline), 'dd MMMM yyyy', { locale: it })}</strong>.
                                            </>
                                        )
                                    }
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <ConfirmModal
                isOpen={confirmModalOpen}
                onClose={() => setConfirmModalOpen(false)}
                onConfirm={onConfirmTimesheet}
                title="Conferma Timesheet"
                message={`Stai confermando il timesheet di ${format(viewDate, 'MMMM yyyy', { locale: it })}. L'azione è irreversibile.`}
                confirmLabel="Conferma Definitivamente"
                variant="warning"
            />
        </div>
    );
}
