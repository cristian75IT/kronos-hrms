
import { useState, useEffect } from 'react';
import { Download, Search, User, CheckCircle, XCircle, BarChart2, Calendar as CalendarIcon, Filter, Shield, FileText } from 'lucide-react';
import hrReportingService from '../../services/hrReporting.service';
import type { DailyAttendanceResponse, AggregateReportResponse } from '../../types';
import { useToast } from '../../context/ToastContext';
import { clsx } from 'clsx';
import { format, startOfMonth, endOfMonth } from 'date-fns';
import { it } from 'date-fns/locale';
import { EnterpriseKPICard } from '../../components/hr/EnterpriseKPICard';
import { Button } from '../../components/common';

type TabType = 'daily' | 'aggregate';

export function HRReportsPage() {
    const [activeTab, setActiveTab] = useState<TabType>('daily');

    // Daily View States
    const [date, setDate] = useState<string>(new Date().toISOString().split('T')[0]);
    const [dailyData, setDailyData] = useState<DailyAttendanceResponse | null>(null);

    // Aggregate View States
    const [startDate, setStartDate] = useState<string>(format(startOfMonth(new Date()), 'yyyy-MM-dd'));
    const [endDate, setEndDate] = useState<string>(format(endOfMonth(new Date()), 'yyyy-MM-dd'));
    const [aggregateData, setAggregateData] = useState<AggregateReportResponse | null>(null);

    // Common States
    const [department, setDepartment] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);
    const toast = useToast();

    const loadDailyData = async () => {
        setIsLoading(true);
        try {
            const result = await hrReportingService.getDailyAttendance(date, department || undefined);
            setDailyData(result);
        } catch (error) {
            console.error(error);
            toast.error('Errore caricamento report giornaliero');
        } finally {
            setIsLoading(false);
        }
    };

    const loadAggregateData = async () => {
        setIsLoading(true);
        try {
            const result = await hrReportingService.getAggregateAttendance({
                start_date: startDate,
                end_date: endDate,
                department: department || undefined
            });
            setAggregateData(result);
        } catch (error) {
            console.error(error);
            toast.error('Errore caricamento report aggregato');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'daily') {
            loadDailyData();
        } else {
            loadAggregateData();
        }
    }, [activeTab, date, startDate, endDate, department]);

    const handleExport = () => {
        toast.info('Esportazione in corso...');
        // Placeholder for export logic
    };

    return (
        <div className="space-y-6 animate-fadeIn pb-12">
            {/* Enterprise Header */}
            <div className="relative overflow-hidden rounded-2xl bg-white p-6 shadow-sm border border-gray-100">
                <div className="absolute -right-10 -top-10 opacity-5">
                    <BarChart2 size={200} className="text-indigo-600" />
                </div>
                <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl">
                                <FileText size={24} />
                            </div>
                            <div>
                                <h1 className="text-2xl font-black tracking-tight text-gray-900">Report HR</h1>
                                <p className="text-gray-500 text-sm font-medium">
                                    Monitoraggio e analisi presenze
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 mt-3 block">
                            <span className="text-[10px] font-bold bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full flex items-center gap-1 border border-indigo-200">
                                <Shield size={10} />
                                HR MANAGER
                            </span>
                            <span className="text-[10px] font-medium text-gray-400">
                                Dati aggiornati al {format(new Date(), "d MMM HH:mm", { locale: it })}
                            </span>
                        </div>
                    </div>

                    <div className="flex items-center bg-gray-50 p-1 rounded-xl border border-gray-200">
                        <button
                            onClick={() => setActiveTab('daily')}
                            className={clsx(
                                "flex items-center px-4 py-2 text-sm font-bold rounded-lg transition-all duration-200",
                                activeTab === 'daily'
                                    ? "bg-white text-indigo-600 shadow-sm ring-1 ring-gray-200"
                                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"
                            )}
                        >
                            <CalendarIcon className="w-4 h-4 mr-2" />
                            Giornaliero
                        </button>
                        <button
                            onClick={() => setActiveTab('aggregate')}
                            className={clsx(
                                "flex items-center px-4 py-2 text-sm font-bold rounded-lg transition-all duration-200",
                                activeTab === 'aggregate'
                                    ? "bg-white text-indigo-600 shadow-sm ring-1 ring-gray-200"
                                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"
                            )}
                        >
                            <BarChart2 className="w-4 h-4 mr-2" />
                            Aggregato
                        </button>
                    </div>
                </div>
            </div>

            {/* Filters Bar */}
            <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 flex flex-wrap items-end gap-4">
                <div className="flex-1 min-w-[200px]">
                    <label className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 flex items-center gap-1">
                        <Filter size={12} /> Dipartimento
                    </label>
                    <select
                        value={department}
                        onChange={(e) => setDepartment(e.target.value)}
                        className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:ring-2 focus:ring-indigo-100 focus:border-indigo-400 outline-none transition-all"
                    >
                        <option value="">Tutta l'azienda</option>
                        <option value="Sviluppo">Sviluppo</option>
                        <option value="HR">HR</option>
                        <option value="Marketing">Marketing</option>
                        <option value="Amministrazione">Amministrazione</option>
                    </select>
                </div>

                {activeTab === 'daily' ? (
                    <div className="flex-1 min-w-[200px]">
                        <label className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5">Data Riferimento</label>
                        <input
                            type="date"
                            value={date}
                            onChange={(e) => setDate(e.target.value)}
                            className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:ring-2 focus:ring-indigo-100 focus:border-indigo-400 outline-none transition-all"
                        />
                    </div>
                ) : (
                    <>
                        <div className="flex-1 min-w-[150px]">
                            <label className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5">Dal</label>
                            <input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:ring-2 focus:ring-indigo-100 focus:border-indigo-400 outline-none transition-all"
                            />
                        </div>
                        <div className="flex-1 min-w-[150px]">
                            <label className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5">Al</label>
                            <input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:ring-2 focus:ring-indigo-100 focus:border-indigo-400 outline-none transition-all"
                            />
                        </div>
                    </>
                )}

                <div className="flex items-center gap-2">
                    <Button
                        onClick={activeTab === 'daily' ? loadDailyData : loadAggregateData}
                        variant="secondary"
                        className="py-2.5"
                    >
                        <Search className="w-4 h-4 mr-2" />
                        Cerca
                    </Button>
                    <Button
                        onClick={handleExport}
                        variant="primary"
                        className="py-2.5 shadow-lg shadow-indigo-200/50"
                    >
                        <Download className="w-4 h-4 mr-2" />
                        Export
                    </Button>
                </div>
            </div>

            {/* Content for Daily View */}
            {activeTab === 'daily' && dailyData && (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <EnterpriseKPICard
                            title="Presenti Oggi"
                            value={dailyData.total_present}
                            subtitle="In sede o smart working"
                            icon={<CheckCircle />}
                            color="emerald"
                            trend={Math.round((dailyData.total_present / Math.max(dailyData.total_employees, 1)) * 100)}
                            trendLabel="tasso presenza"
                        />
                        <EnterpriseKPICard
                            title="Assenti / Ferie"
                            value={dailyData.total_absent}
                            subtitle="Ferie, malattia, permessi"
                            icon={<XCircle />}
                            color="rose"
                            trend={null}
                        />
                        <EnterpriseKPICard
                            title="Totale Organico"
                            value={dailyData.items.length}
                            subtitle="Dipendenti attivi"
                            icon={<User />}
                            color="blue"
                            badge="LIVE"
                            trend={null}
                        />
                    </div>

                    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden ring-1 ring-gray-100">
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-100">
                                <thead className="bg-gray-50/50">
                                    <tr>
                                        <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Dipendente</th>
                                        <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Stato</th>
                                        <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Ore Lavorate</th>
                                        <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Note</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-50">
                                    {isLoading && !dailyData ? (
                                        <tr><td colSpan={4} className="px-6 py-12 text-center text-sm text-gray-500">Caricamento presenze...</td></tr>
                                    ) : (
                                        dailyData.items.map((item) => (
                                            <tr key={item.user_id} className="hover:bg-gray-50/80 transition-colors group">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="flex items-center">
                                                        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-indigo-100 to-white border border-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm shadow-sm group-hover:scale-110 transition-transform">
                                                            {(item.full_name || '??').split(' ').map(n => n[0]).join('').slice(0, 2)}
                                                        </div>
                                                        <div className="ml-4">
                                                            <div className="text-sm font-bold text-gray-900">{item.full_name || 'Sconosciuto'}</div>
                                                            <div className="text-xs text-gray-500 font-medium">{item.department || 'N/A'}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={clsx(
                                                        "px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full border shadow-sm",
                                                        item.status.includes('Presente')
                                                            ? "bg-emerald-50 text-emerald-700 border-emerald-100"
                                                            : item.status.includes('Malattia')
                                                                ? "bg-rose-50 text-rose-700 border-rose-100"
                                                                : "bg-amber-50 text-amber-700 border-amber-100"
                                                    )}>
                                                        {item.status}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-700">
                                                    {item.hours_worked > 0 ? `${item.hours_worked}h` : '-'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 italic">
                                                    {item.leave_request_id && (
                                                        <span className="flex items-center gap-1 text-xs not-italic bg-gray-100 px-2 py-1 rounded text-gray-600">
                                                            <FileText size={10} />
                                                            {item.leave_type || 'Assenza'}
                                                        </span>
                                                    )}
                                                    {item.notes && <span className="text-xs ml-2">{item.notes}</span>}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}

            {/* Content for Aggregate View */}
            {activeTab === 'aggregate' && aggregateData && (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden ring-1 ring-gray-100">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-100">
                            <thead className="bg-gray-50/50">
                                <tr>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Dipendente</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-400 uppercase tracking-wider">Presenze</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-rose-500 bg-rose-50/30 uppercase tracking-wider border-b-2 border-rose-100">Ferie (gg)</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-blue-500 bg-blue-50/30 uppercase tracking-wider border-b-2 border-blue-100">Festività (gg)</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-orange-500 bg-orange-50/30 uppercase tracking-wider border-b-2 border-orange-100">ROL (ore)</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-yellow-600 bg-yellow-50/30 uppercase tracking-wider border-b-2 border-yellow-100">Permessi (ore)</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-400 uppercase tracking-wider">Malattia</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-400 uppercase tracking-wider">Altro</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-50">
                                {isLoading && !aggregateData ? (
                                    <tr><td colSpan={8} className="px-6 py-12 text-center text-sm text-gray-500">Caricamento statistiche...</td></tr>
                                ) : (
                                    aggregateData.items.map((item) => (
                                        <tr key={item.user_id} className="hover:bg-gray-50/80 transition-colors group">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center">
                                                    <div className="h-9 w-9 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 font-bold text-xs shadow-sm border border-gray-200">
                                                        {(item.full_name || '??').split(' ').map(n => n[0]).join('').slice(0, 2)}
                                                    </div>
                                                    <div className="ml-3">
                                                        <div className="text-sm font-bold text-gray-900 group-hover:text-indigo-600 transition-colors">{item.full_name || 'Sconosciuto'}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-gray-50 border border-gray-200">
                                                    <span className="text-sm font-bold text-indigo-700">{item.worked_days}</span>
                                                    <span className="text-[10px] text-gray-400 font-medium">/ {item.total_days}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                                {item.vacation_days > 0 ? (
                                                    <span className="text-sm font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-100">{item.vacation_days}</span>
                                                ) : <span className="text-gray-300">-</span>}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium text-blue-600">
                                                {item.holiday_days > 0 ? item.holiday_days : <span className="text-gray-300 font-normal">-</span>}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium text-orange-600">
                                                {item.rol_hours > 0 ? item.rol_hours : <span className="text-gray-300 font-normal">-</span>}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium text-yellow-600">
                                                {item.permit_hours > 0 ? item.permit_hours : <span className="text-gray-300 font-normal">-</span>}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-600">
                                                {item.sick_days > 0 ? (
                                                    <span className="text-xs font-bold bg-gray-100 px-2 py-0.5 rounded">{item.sick_days}</span>
                                                ) : <span className="text-gray-300">-</span>}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">
                                                {item.other_absences > 0 ? item.other_absences : <span className="text-gray-300">-</span>}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

export default HRReportsPage;
