import React, { useEffect, useState } from 'react';
import {
    Mail,
    RefreshCw,
    CheckCircle,
    XCircle,
    Clock,
    AlertTriangle,
    Search,
    RotateCw,
    Activity,
    X,
    Filter
} from 'lucide-react';
import notificationService from '../../services/notification.service';
import type { EmailLog, EmailEvent } from '../../services/notification.service';
import { useToast } from '../../context/ToastContext';
import { PageHeader } from '../../components/common/PageHeader';
import { Button } from '../../components/common';
import { clsx } from 'clsx';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

export const EmailLogsPage: React.FC = () => {
    const [logs, setLogs] = useState<EmailLog[]>([]);
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [retrying, setRetrying] = useState<string | null>(null);
    const [filterStatus, setFilterStatus] = useState<string>('');
    const [page, setPage] = useState(1);
    const [pageSize] = useState(50);
    const [eventsModalOpen, setEventsModalOpen] = useState(false);
    const [eventsLoading, setEventsLoading] = useState(false);
    const [selectedLog, setSelectedLog] = useState<EmailLog | null>(null);
    const [events, setEvents] = useState<EmailEvent[]>([]);
    const toast = useToast();

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const data = await notificationService.getEmailLogs({
                limit: pageSize,
                offset: (page - 1) * pageSize,
                status: filterStatus || undefined
            });
            setLogs(data);
        } catch (error) {
            console.error(error);
            toast.error('Errore nel caricamento dei log email');
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const data = await notificationService.getEmailStats(7);
            setStats(data);
        } catch (error) {
            console.error(error);
        }
    };

    useEffect(() => {
        fetchLogs();
        fetchStats();
    }, [page, filterStatus]);

    const handleRetry = async (id: string) => {
        setRetrying(id);
        try {
            const updatedLog = await notificationService.retryEmail(id);
            toast.success('Email reinviata con successo');
            // Update local state
            setLogs(logs.map(log => log.id === id ? updatedLog : log));
            fetchStats();
        } catch (error) {
            console.error(error);
            toast.error('Errore durante il reinvio dell\'email');
        } finally {
            setRetrying(null);
        }
    };

    const handleViewEvents = async (log: EmailLog, permissive: boolean = false) => {
        setSelectedLog(log);
        setEventsModalOpen(true);
        setEventsLoading(true);
        if (permissive) {
            setEvents([]); // Clear previous specific results
        }
        try {
            const data = await notificationService.getEmailEvents(log.id, permissive);
            setEvents(data);
            if (permissive && data.length > 0) {
                toast.success('Ricerca estesa completata');
            }
        } catch (error) {
            console.error(error);
            toast.error('Errore nel caricamento degli eventi Brevo');
            setEvents([]);
        } finally {
            setEventsLoading(false);
        }
    };

    const getEventBadgeClass = (event: string) => {
        const styles: Record<string, string> = {
            'delivered': 'bg-green-50 text-green-700 border-green-200',
            'opened': 'bg-blue-50 text-blue-700 border-blue-200',
            'clicked': 'bg-purple-50 text-purple-700 border-purple-200',
            'sent': 'bg-green-50 text-green-600 border-green-200',
            'bounced': 'bg-red-50 text-red-700 border-red-200',
            'hardBounce': 'bg-red-50 text-red-700 border-red-200',
            'softBounce': 'bg-amber-50 text-amber-700 border-amber-200',
            'spam': 'bg-red-50 text-red-700 border-red-200',
            'unsubscribed': 'bg-gray-100 text-gray-600 border-gray-200',
            'blocked': 'bg-red-50 text-red-700 border-red-200',
            'deferred': 'bg-amber-50 text-amber-700 border-amber-200',
        };
        return styles[event] || 'bg-gray-50 text-gray-700 border-gray-200';
    };



    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'sent':
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Inviata</span>;
            case 'delivered':
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Consegnata</span>;
            case 'failed':
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Fallita</span>;
            case 'bounced':
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Bounce</span>;
            case 'pending':
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">In Coda</span>;
            default:
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{status}</span>;
        }
    };

    const formatDate = (dateString: string) => {
        return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: it });
    };

    const formatEventDate = (dateString: string) => {
        return format(new Date(dateString), 'dd MMM HH:mm:ss', { locale: it });
    };

    return (
        <div className="space-y-6 animate-fadeIn pb-12">
            <PageHeader
                title="Log Email"
                description="Monitoraggio invio email transazionali e stato consegne (SMTP/API)"
                actions={
                    <Button variant="secondary" onClick={fetchLogs} disabled={loading} icon={<RefreshCw size={18} className={loading ? 'animate-spin' : ''} />}>
                        Aggiorna
                    </Button>
                }
            />

            {stats && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                        <div className="p-3 bg-blue-50 rounded-xl text-blue-600">
                            <Mail size={24} />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">Totale (7gg)</p>
                            <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
                        </div>
                    </div>
                    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                        <div className="p-3 bg-green-50 rounded-xl text-green-600">
                            <CheckCircle size={24} />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">Inviate</p>
                            <p className="text-2xl font-bold text-green-600">{stats.sent}</p>
                        </div>
                    </div>
                    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                        <div className="p-3 bg-red-50 rounded-xl text-red-600">
                            <XCircle size={24} />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">Fallite</p>
                            <p className="text-2xl font-bold text-red-600">{stats.failed}</p>
                        </div>
                    </div>
                    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                        <div className="p-3 bg-amber-50 rounded-xl text-amber-600">
                            <Clock size={24} />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">In Coda</p>
                            <p className="text-2xl font-bold text-amber-600">{stats.pending}</p>
                        </div>
                    </div>
                </div>
            )}

            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                {/* Filters */}
                <div className="p-4 border-b border-slate-200 flex items-center gap-4 bg-slate-50/50">
                    <div className="relative max-w-xs w-full">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Filter size={18} className="text-slate-400" />
                        </div>
                        <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg leading-5 bg-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition duration-150 ease-in-out"
                        >
                            <option value="">Tutti gli stati</option>
                            <option value="sent">Inviate</option>
                            <option value="failed">Fallite</option>
                            <option value="pending">In Coda</option>
                        </select>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200">
                        <thead className="bg-slate-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Stato</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Destinatario</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Template</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Oggetto / Errore</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Data</th>
                                <th className="px-6 py-3 text-right text-xs font-bold text-slate-500 uppercase tracking-wider">Azioni</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-slate-200">
                            {logs.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500 italic">
                                        Nessun log trovato con i filtri correnti.
                                    </td>
                                </tr>
                            ) : (
                                logs.map(log => (
                                    <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {getStatusBadge(log.status)}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <span className="text-sm font-medium text-slate-900">{log.to_email}</span>
                                                {log.to_name && <span className="text-xs text-slate-500">{log.to_name}</span>}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100 font-mono">
                                                {log.template_code}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1 max-w-sm">
                                                <span className="text-sm text-slate-700 truncate block" title={log.subject || ''}>{log.subject || '-'}</span>
                                                {log.error_message && (
                                                    <span className="text-xs text-red-600 bg-red-50 p-1 rounded border border-red-100 flex items-center gap-1" title={log.error_message}>
                                                        <AlertTriangle size={12} />
                                                        <span className="truncate block max-w-[200px]">{log.error_message}</span>
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 font-mono">
                                            {formatDate(log.created_at)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <div className="flex justify-end gap-2">
                                                {log.status === 'sent' && (
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleViewEvents(log)}
                                                        title="Visualizza eventi Provider"
                                                        className="text-indigo-600 hover:bg-indigo-50"
                                                    >
                                                        <Activity size={16} />
                                                    </Button>
                                                )}
                                                {log.status === 'failed' && (
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleRetry(log.id)}
                                                        disabled={retrying === log.id}
                                                        title="Riprova invio"
                                                        className={clsx("text-slate-600 hover:bg-slate-100", retrying === log.id && "animate-spin")}
                                                    >
                                                        <RotateCw size={16} />
                                                    </Button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                <div className="bg-slate-50 px-4 py-3 border-t border-slate-200 flex items-center justify-between sm:px-6">
                    <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                        <div>
                            <p className="text-sm text-slate-500">
                                Pagina <span className="font-medium">{page}</span>
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                            >
                                Precedente
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage(p => p + 1)}
                                disabled={logs.length < pageSize}
                            >
                                Successiva
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Events Modal */}
            {eventsModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn" onClick={() => setEventsModalOpen(false)}>
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden animate-scaleIn" onClick={(e) => e.stopPropagation()}>
                        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                            <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
                                <Activity className="text-indigo-600" size={20} />
                                Tracking Eventi Email
                            </h3>
                            <button onClick={() => setEventsModalOpen(false)} className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200 transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="p-6 overflow-y-auto">
                            {selectedLog && (
                                <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 mb-6">
                                    <div className="flex justify-between items-start gap-4">
                                        <div className="space-y-1 text-sm">
                                            <p className="flex items-center gap-2">
                                                <span className="font-bold text-slate-500 w-24">Destinatario:</span>
                                                <span className="font-mono text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">{selectedLog.to_email}</span>
                                            </p>
                                            <p className="flex items-center gap-2">
                                                <span className="font-bold text-slate-500 w-24">Template:</span>
                                                <span className="font-mono text-indigo-600">{selectedLog.template_code}</span>
                                            </p>
                                            {selectedLog.message_id && (
                                                <p className="flex items-center gap-2">
                                                    <span className="font-bold text-slate-500 w-24">Message ID:</span>
                                                    <span className="font-mono text-slate-500 text-xs break-all">{selectedLog.message_id}</span>
                                                </p>
                                            )}
                                        </div>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleViewEvents(selectedLog, true)}
                                            disabled={eventsLoading}
                                            icon={<Search size={14} />}
                                            className="whitespace-nowrap"
                                        >
                                            Deep Search
                                        </Button>
                                    </div>
                                </div>
                            )}

                            {eventsLoading ? (
                                <div className="flex flex-col items-center justify-center py-12 gap-3 text-slate-500">
                                    <RefreshCw size={32} className="animate-spin text-indigo-500" />
                                    <span className="text-sm font-medium">Sincronizzazione eventi con provider...</span>
                                </div>
                            ) : events.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 gap-3 text-slate-400 border-2 border-dashed border-slate-200 rounded-xl">
                                    <AlertTriangle size={32} />
                                    <p className="text-sm font-medium">Nessun evento tracciato trovato.</p>
                                    <p className="text-xs max-w-xs text-center">Potrebbe essere necessario attendere qualche minuto dopo l'invio per la propagazione degli eventi.</p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    <div className="flex items-center gap-2 mb-2">
                                        <div className="h-px bg-slate-200 flex-1"></div>
                                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Timeline Eventi</span>
                                        <div className="h-px bg-slate-200 flex-1"></div>
                                    </div>
                                    {events.map((event, idx) => (
                                        <div key={idx} className="flex gap-4 group">
                                            <div className="flex flex-col items-center">
                                                <div className="w-2 h-2 rounded-full bg-slate-300 group-first:bg-indigo-500 mt-2"></div>
                                                <div className="w-0.5 flex-1 bg-slate-100 group-last:hidden h-full"></div>
                                            </div>
                                            <div className="flex-1 bg-white border border-slate-200 rounded-lg p-3 hover:shadow-sm transition-shadow">
                                                <div className="flex justify-between items-start mb-1">
                                                    <span className={clsx("text-xs font-bold px-2 py-0.5 rounded border uppercase tracking-wide", getEventBadgeClass(event.event))}>
                                                        {event.event}
                                                    </span>
                                                    <span className="text-xs text-slate-400 font-mono">{formatEventDate(event.date)}</span>
                                                </div>
                                                {event.subject && <p className="text-sm text-slate-600 mt-2">{event.subject}</p>}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default EmailLogsPage;
