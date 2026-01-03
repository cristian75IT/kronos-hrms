import { useState, useEffect } from 'react';
import { Download, Search, User, CheckCircle, XCircle, BarChart2, Calendar as CalendarIcon } from 'lucide-react';
import hrReportingService from '../../services/hrReporting.service';
import type { DailyAttendanceResponse, AggregateReportResponse } from '../../types';
import { useToast } from '../../context/ToastContext';
import { clsx } from 'clsx';
import { format, startOfMonth, endOfMonth } from 'date-fns';

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
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Report Risorse Umane</h1>
                    <p className="text-sm text-gray-500">Monitoraggio presenze, assenze e statistiche aggregate</p>
                </div>

                <div className="flex items-center space-x-3 bg-white p-1 rounded-lg border border-gray-200">
                    <button
                        onClick={() => setActiveTab('daily')}
                        className={clsx(
                            "flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors",
                            activeTab === 'daily' ? "bg-indigo-50 text-indigo-700 shadow-sm" : "text-gray-500 hover:text-gray-700"
                        )}
                    >
                        <CalendarIcon className="w-4 h-4 mr-2" />
                        Giornaliero
                    </button>
                    <button
                        onClick={() => setActiveTab('aggregate')}
                        className={clsx(
                            "flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors",
                            activeTab === 'aggregate' ? "bg-indigo-50 text-indigo-700 shadow-sm" : "text-gray-500 hover:text-gray-700"
                        )}
                    >
                        <BarChart2 className="w-4 h-4 mr-2" />
                        Aggregato
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-wrap items-center gap-4">
                <div className="flex flex-col">
                    <label className="text-xs font-semibold text-gray-500 mb-1">Dipartimento</label>
                    <select
                        value={department}
                        onChange={(e) => setDepartment(e.target.value)}
                        className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                    >
                        <option value="">Tutti i dipartimenti</option>
                        <option value="Sviluppo">Sviluppo</option>
                        <option value="HR">HR</option>
                        <option value="Marketing">Marketing</option>
                        <option value="Amministrazione">Amministrazione</option>
                    </select>
                </div>

                {activeTab === 'daily' ? (
                    <div className="flex flex-col">
                        <label className="text-xs font-semibold text-gray-500 mb-1">Data</label>
                        <input
                            type="date"
                            value={date}
                            onChange={(e) => setDate(e.target.value)}
                            className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                        />
                    </div>
                ) : (
                    <>
                        <div className="flex flex-col">
                            <label className="text-xs font-semibold text-gray-500 mb-1">Dal</label>
                            <input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                            />
                        </div>
                        <div className="flex flex-col">
                            <label className="text-xs font-semibold text-gray-500 mb-1">Al</label>
                            <input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                            />
                        </div>
                    </>
                )}

                <div className="flex-1"></div>

                <div className="flex items-center gap-2 self-end">
                    <button
                        onClick={activeTab === 'daily' ? loadDailyData : loadAggregateData}
                        className="p-2.5 bg-gray-50 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
                        title="Aggiorna"
                    >
                        <Search className="w-5 h-5" />
                    </button>
                    <button
                        onClick={handleExport}
                        className="flex items-center px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm"
                    >
                        <Download className="w-4 h-4 mr-2" />
                        Esporta CSV
                    </button>
                </div>
            </div>

            {/* Content for Daily View */}
            {activeTab === 'daily' && dailyData && (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <StatsCard
                            title="Presenti"
                            value={dailyData.total_present}
                            icon={<CheckCircle className="w-6 h-6 text-green-600" />}
                            bgColor="bg-green-50"
                        />
                        <StatsCard
                            title="Assenti / Ferie"
                            value={dailyData.total_absent}
                            icon={<XCircle className="w-6 h-6 text-red-600" />}
                            bgColor="bg-red-50"
                        />
                        <StatsCard
                            title="Totale Dipendenti"
                            value={dailyData.items.length}
                            icon={<User className="w-6 h-6 text-blue-600" />}
                            bgColor="bg-blue-50"
                        />
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Dipendente</th>
                                        <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Stato</th>
                                        <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Ore Lavorate</th>
                                        <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Note</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {isLoading && !dailyData ? (
                                        <tr><td colSpan={4} className="px-6 py-10 text-center text-sm text-gray-500">Caricamento...</td></tr>
                                    ) : (
                                        dailyData.items.map((item) => (
                                            <tr key={item.user_id} className="hover:bg-gray-50 transition-colors">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="flex items-center">
                                                        <div className="h-9 w-9 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm">
                                                            {item.full_name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                                                        </div>
                                                        <div className="ml-3">
                                                            <div className="text-sm font-semibold text-gray-900">{item.full_name}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={clsx(
                                                        "px-2.5 py-1 inline-flex text-xs leading-5 font-bold rounded-full",
                                                        item.status.includes('Presente') ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                                                    )}>
                                                        {item.status}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{item.hours_worked}h</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 italic">
                                                    {item.leave_request_id ? "Assenza approvata" : ""}
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
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Dipendente</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">Presenze (Lavorati/Lavorativi)</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider text-red-600">Ferie (gg)</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider text-blue-600">Festività (gg)</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider text-orange-600">ROL (ore)</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider text-yellow-600">Permessi (ore)</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">Malattia</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">Altro</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {isLoading && !aggregateData ? (
                                    <tr><td colSpan={7} className="px-6 py-10 text-center text-sm text-gray-500">Caricamento statistiche...</td></tr>
                                ) : (
                                    aggregateData.items.map((item) => (
                                        <tr key={item.user_id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="text-sm font-semibold text-gray-900">{item.full_name}</div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                                <span className="text-sm font-bold text-indigo-700">{item.worked_days}</span>
                                                <span className="text-xs text-gray-400"> / {item.total_days}</span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium text-red-600">{item.vacation_days}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium text-blue-600">{item.holiday_days}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium text-orange-600">{item.rol_hours}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium text-yellow-600">{item.permit_hours}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-600">{item.sick_days}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">{item.other_absences}</td>
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


interface StatsCardProps {
    title: string;
    value: number | string;
    icon: React.ReactNode;
    bgColor: string;
}

function StatsCard({ title, value, icon, bgColor }: StatsCardProps) {
    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all hover:scale-[1.02] hover:shadow-md">
            <div className="flex items-center">
                <div className={clsx("p-3 rounded-xl", bgColor)}>
                    {icon}
                </div>
                <div className="ml-4">
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-widest leading-none mb-1">{title}</p>
                    <p className="text-2xl font-black text-gray-900 leading-none">{value}</p>
                </div>
            </div>
        </div>
    );
}

export default HRReportsPage;
