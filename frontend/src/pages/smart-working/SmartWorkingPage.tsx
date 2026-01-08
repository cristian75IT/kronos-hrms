import { useState, useEffect } from 'react';
import {
    Calendar as CalendarIcon,
    FileText,
    List,
    Loader2
} from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { useAuth } from '../../context/AuthContext';
import { smartWorkingService } from '../../services/smartWorking.service';
import type { SWAgreement, SWRequest } from '../../services/smartWorking.service';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { format } from 'date-fns';
import { AttendanceWidget } from '../../components/smart-working/AttendanceWidget';
import { AgreementRequestModal } from '../../components/smart-working/AgreementRequestModal';
import { RequestCalendar } from '../../components/smart-working/RequestCalendar';

export const SmartWorkingPage = () => {
    const toast = useToast();
    const { user } = useAuth();
    const [agreements, setAgreements] = useState<SWAgreement[]>([]);
    const [requests, setRequests] = useState<SWRequest[]>([]);
    const [loading, setLoading] = useState(true);

    // Tabs: overview (Calendar), list (Table), requests (Agreements)
    const [activeTab, setActiveTab] = useState<'calendar' | 'list' | 'agreements'>('calendar');
    const [isAgreementModalOpen, setIsAgreementModalOpen] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [userAgreements, userRequests] = await Promise.all([
                smartWorkingService.getMyAgreements(),
                smartWorkingService.getMyRequests()
            ]);
            setAgreements(userAgreements);
            setRequests(userRequests);
        } catch (error) {
            console.error('Error fetching SW data:', error);
            toast.error('Errore nel caricamento dei dati Smart Working');
        } finally {
            setLoading(false);
        }
    };

    const activeAgreement = agreements.find(a => a.status === 'ACTIVE');

    // Find today's request for the widget
    const todayStr = format(new Date(), 'yyyy-MM-dd');
    const todayRequest = requests.find(r => r.date === todayStr);

    // Helpers
    const formatDate = (d: string) => new Date(d).toLocaleDateString('it-IT');

    const getStatusBadge = (status: string) => {
        const map: Record<string, string> = {
            PENDING: 'bg-amber-50 text-amber-700 border-amber-200',
            APPROVED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
            REJECTED: 'bg-red-50 text-red-700 border-red-200',
            CANCELLED: 'bg-gray-100 text-gray-700 border-gray-200',
            ACTIVE: 'bg-emerald-50 text-emerald-700 border-emerald-200',
            TERMINATED: 'bg-red-50 text-red-700 border-red-200',
            EXPIRED: 'bg-gray-100 text-gray-700 border-gray-200',
        };
        return map[status] || 'bg-gray-100 text-gray-700 border-gray-200';
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <span className="ml-2 text-slate-500">Caricamento...</span>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 mb-1">Lavoro Agile</h1>
                    <p className="text-sm text-gray-500">Gestione presenze e accordi di Smart Working</p>
                </div>
                {/* RBAC: Only HR/Admin can create agreements */}
                {user?.is_hr && (
                    <div className="flex gap-3">
                        <Button
                            variant="secondary"
                            onClick={() => setIsAgreementModalOpen(true)}
                            icon={<FileText size={18} />}
                        >
                            Nuovo Accordo
                        </Button>
                    </div>
                )}
            </div>

            {/* Overview Stats & Widget */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <Card className="p-4 border-l-4 border-l-primary">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-primary/10 rounded-full text-primary">
                            <FileText size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500 font-medium">Stato Accordo</p>
                            <h3 className="text-lg font-bold text-slate-900">
                                {activeAgreement ? 'Attivo' : 'Nessun Accordo'}
                            </h3>
                            {activeAgreement && (
                                <p className="text-xs text-slate-500">
                                    Scade il {formatDate(activeAgreement.end_date || '')}
                                </p>
                            )}
                        </div>
                    </div>
                </Card>

                <Card className="p-4 border-l-4 border-l-blue-500">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-blue-500/10 rounded-full text-blue-600">
                            <CalendarIcon size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500 font-medium">Giorni Residui</p>
                            <h3 className="text-lg font-bold text-slate-900">
                                {activeAgreement?.allowed_days_per_week || 0} / {activeAgreement?.allowed_days_per_week || 0}
                            </h3>
                            <p className="text-xs text-slate-500">Disponibili questa settimana</p>
                        </div>
                    </div>
                </Card>

                {/* Helper Wrapper for Conditional Render logic if needed, but Widget handles it */}
                <AttendanceWidget
                    todayRequest={todayRequest}
                    onStatusChange={fetchData}
                />
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-200 mb-6">
                <button
                    className={`px-4 py-2 font-medium text-sm transition-colors flex items-center gap-2 ${activeTab === 'calendar' ? 'text-primary border-b-2 border-primary' : 'text-slate-500 hover:text-slate-700'}`}
                    onClick={() => setActiveTab('calendar')}
                >
                    <CalendarIcon size={16} /> Calendario
                </button>
                <button
                    className={`px-4 py-2 font-medium text-sm transition-colors flex items-center gap-2 ${activeTab === 'list' ? 'text-primary border-b-2 border-primary' : 'text-slate-500 hover:text-slate-700'}`}
                    onClick={() => setActiveTab('list')}
                >
                    <List size={16} /> Lista Richieste
                </button>
                <button
                    className={`px-4 py-2 font-medium text-sm transition-colors flex items-center gap-2 ${activeTab === 'agreements' ? 'text-primary border-b-2 border-primary' : 'text-slate-500 hover:text-slate-700'}`}
                    onClick={() => setActiveTab('agreements')}
                >
                    <FileText size={16} /> Storico Accordi
                </button>
            </div>

            {/* Content */}
            <div className="animate-fadeIn">
                {activeTab === 'calendar' && (
                    <RequestCalendar
                        requests={requests}
                        activeAgreement={activeAgreement}
                        onRefresh={fetchData}
                    />
                )}

                {activeTab === 'list' && (
                    <Card>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                                    <tr>
                                        <th className="px-4 py-3">Data</th>
                                        <th className="px-4 py-3">Stato</th>
                                        <th className="px-4 py-3">Check-in</th>
                                        <th className="px-4 py-3">Check-out</th>
                                        <th className="px-4 py-3">Note</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {requests.length === 0 ? (
                                        <tr>
                                            <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                                                Nessuna richiesta trovata.
                                            </td>
                                        </tr>
                                    ) : (
                                        requests.map((req) => (
                                            <tr key={req.id} className="hover:bg-slate-50/50">
                                                <td className="px-4 py-3 font-medium text-slate-900">
                                                    {formatDate(req.date)}
                                                </td>
                                                <td className="px-4 py-3">
                                                    <span className={`px-2.5 py-0.5 rounded text-xs font-medium border uppercase tracking-wide ${getStatusBadge(req.status)}`}>
                                                        {req.status}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 text-slate-500">
                                                    {req.attendance?.check_in
                                                        ? new Date(req.attendance.check_in).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
                                                        : '-'}
                                                </td>
                                                <td className="px-4 py-3 text-slate-500">
                                                    {req.attendance?.check_out
                                                        ? new Date(req.attendance.check_out).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
                                                        : '-'}
                                                </td>
                                                <td className="px-4 py-3 text-slate-500">{req.notes || '-'}</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </Card>
                )}

                {activeTab === 'agreements' && (
                    <Card>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                                    <tr>
                                        <th className="px-4 py-3">Validità</th>
                                        <th className="px-4 py-3">Giorni/Settimana</th>
                                        <th className="px-4 py-3">Stato</th>
                                        <th className="px-4 py-3">Note</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {agreements.length === 0 ? (
                                        <tr>
                                            <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                                                Nessun accordo trovato.
                                            </td>
                                        </tr>
                                    ) : (
                                        agreements.map((agm) => (
                                            <tr key={agm.id} className="hover:bg-slate-50/50">
                                                <td className="px-4 py-3 font-medium text-slate-900">
                                                    {formatDate(agm.start_date)} - {agm.end_date ? formatDate(agm.end_date) : 'Indefinito'}
                                                </td>
                                                <td className="px-4 py-3">
                                                    {agm.allowed_days_per_week}
                                                </td>
                                                <td className="px-4 py-3">
                                                    <span className={`px-2.5 py-0.5 rounded text-xs font-medium border uppercase tracking-wide ${getStatusBadge(agm.status)}`}>
                                                        {agm.status}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 text-slate-500">{agm.notes || '-'}</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </Card>
                )}
            </div>

            <AgreementRequestModal
                isOpen={isAgreementModalOpen}
                onClose={() => setIsAgreementModalOpen(false)}
                onSuccess={fetchData}
            />
        </div>
    );
};
