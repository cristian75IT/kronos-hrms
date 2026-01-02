import React, { useState, useEffect } from 'react';
import {
    Activity,
    Eye,
    Search,
    Terminal,
    ShieldAlert,
    Info,
    Clock,
    ChevronLeft,
    ChevronRight,
    X
} from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { auditService } from '../../services/audit.service';
import type { AuditLogListItem, AuditLogDetails, DataTableRequest } from '../../types';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common';

export function AuditLogPage() {
    const toast = useToast();
    const [isLoading, setIsLoading] = useState(false);
    const [logs, setLogs] = useState<AuditLogListItem[]>([]);
    const [totalRecords, setTotalRecords] = useState(0);
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize] = useState(15);
    const [searchValue, setSearchValue] = useState('');
    const [selectedLog, setSelectedLog] = useState<AuditLogDetails | null>(null);
    const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
    const [isLoadingDetails, setIsLoadingDetails] = useState(false);

    const loadLogs = async () => {
        setIsLoading(true);
        try {
            const request: DataTableRequest = {
                draw: 1,
                start: (currentPage - 1) * pageSize,
                length: pageSize,
                search_value: searchValue
            };
            const response = await auditService.getLogsDataTable(request);
            setLogs(response.data);
            setTotalRecords(response.recordsFiltered);
        } catch (error) {
            console.error(error);
            toast.error('Errore nel caricamento degli audit log');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadLogs();
    }, [currentPage, pageSize]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setCurrentPage(1);
        loadLogs();
    };

    const handleViewDetails = async (id: string) => {
        setIsLoadingDetails(true);
        setIsDetailModalOpen(true);
        try {
            const details = await auditService.getLogDetails(id);
            setSelectedLog(details);
        } catch (error) {
            console.error(error);
            toast.error('Errore nel caricamento dei dettagli');
            setIsDetailModalOpen(false);
        } finally {
            setIsLoadingDetails(false);
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'SUCCESS':
                return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Successo</span>;
            case 'FAILURE':
                return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">Fallito</span>;
            case 'ERROR':
                return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Errore</span>;
            default:
                return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{status}</span>;
        }
    };

    const totalPages = Math.ceil(totalRecords / pageSize);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Terminal className="text-indigo-600" size={28} />
                        Audit Log
                    </h1>
                    <p className="text-sm text-gray-500">Registro delle attività di sistema e modifiche dati</p>
                </div>
                <div className="flex items-center gap-3">
                    <form onSubmit={handleSearch} className="relative">
                        <input
                            type="text"
                            placeholder="Cerca per email, azione..."
                            value={searchValue}
                            onChange={(e) => setSearchValue(e.target.value)}
                            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 w-64 text-sm"
                        />
                        <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
                    </form>
                    <Button variant="secondary" onClick={loadLogs} disabled={isLoading}>
                        <Activity size={18} className={isLoading ? 'animate-spin' : ''} />
                    </Button>
                </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50 uppercase text-[10px] font-bold tracking-wider text-gray-500">
                            <tr>
                                <th className="px-6 py-4 text-left">Data e Ora</th>
                                <th className="px-6 py-4 text-left">Utente</th>
                                <th className="px-6 py-4 text-left">Servizio</th>
                                <th className="px-6 py-4 text-left">Azione</th>
                                <th className="px-6 py-4 text-left">Risorsa</th>
                                <th className="px-6 py-4 text-left">Stato</th>
                                <th className="px-6 py-4 text-right">Azioni</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 bg-white">
                            {isLoading && logs.length === 0 ? (
                                Array.from({ length: 5 }).map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        <td colSpan={7} className="px-6 py-4 bg-gray-50/50"></td>
                                    </tr>
                                ))
                            ) : logs.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500 italic">
                                        Nessun log trovato.
                                    </td>
                                </tr>
                            ) : (
                                logs.map((log: AuditLogListItem) => (
                                    <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-600 font-mono">
                                            {format(new Date(log.created_at), 'dd/MM/yyyy HH:mm:ss', { locale: it })}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                                            {log.user_email || <span className="text-gray-400 italic">Sistema</span>}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="text-[11px] px-2 py-0.5 rounded bg-gray-100 text-gray-600 font-bold">
                                                {log.service_name}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                            {log.action}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                                            {log.resource_type} {log.resource_id && <span className="text-gray-300 ml-1">#{log.resource_id.substring(0, 8)}</span>}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {getStatusBadge(log.status)}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={() => handleViewDetails(log.id)}
                                                className="text-indigo-600 hover:text-indigo-900 p-1 rounded-md hover:bg-indigo-50 transition-colors"
                                                title="Visualizza dettagli"
                                            >
                                                <Eye size={18} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalRecords > 0 && (
                    <div className="bg-gray-50 px-6 py-3 border-t border-gray-200 flex items-center justify-between">
                        <div className="text-xs text-gray-500">
                            Mostrando <strong>{((currentPage - 1) * pageSize) + 1}</strong>-<strong>{Math.min(currentPage * pageSize, totalRecords)}</strong> di <strong>{totalRecords}</strong> log
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                disabled={currentPage === 1 || isLoading}
                                className="p-1 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <ChevronLeft size={18} />
                            </button>
                            {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
                                let pageNum = currentPage;
                                if (totalPages <= 5) pageNum = i + 1;
                                else if (currentPage <= 3) pageNum = i + 1;
                                else if (currentPage > totalPages - 2) pageNum = totalPages - 4 + i;
                                else pageNum = currentPage - 2 + i;

                                return (
                                    <button
                                        key={pageNum}
                                        onClick={() => setCurrentPage(pageNum)}
                                        className={`w-8 h-8 text-xs font-medium rounded-md transition-colors ${currentPage === pageNum ? 'bg-indigo-600 text-white border border-indigo-600' : 'border border-gray-300 bg-white text-gray-600 hover:bg-gray-50'}`}
                                    >
                                        {pageNum}
                                    </button>
                                );
                            })}
                            <button
                                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                disabled={currentPage === totalPages || isLoading}
                                className="p-1 rounded-md border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <ChevronRight size={18} />
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Detail Modal */}
            {isDetailModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden animate-scaleIn">
                        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
                            <h3 className="font-bold text-gray-900 flex items-center gap-2">
                                <Info className="text-indigo-600" size={20} />
                                Dettaglio Audit Log
                            </h3>
                            <button onClick={() => setIsDetailModalOpen(false)} className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="p-6 max-h-[70vh] overflow-y-auto">
                            {isLoadingDetails ? (
                                <div className="flex flex-col items-center justify-center py-12 gap-3">
                                    <Activity className="animate-spin text-indigo-600" size={32} />
                                    <span className="text-sm text-gray-500 font-medium italic">Recupero dati estesi...</span>
                                </div>
                            ) : selectedLog ? (
                                <div className="space-y-6">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                                            <p className="text-[10px] font-bold text-gray-400 uppercase mb-1 flex items-center gap-1">
                                                <Clock size={12} /> Timestamp
                                            </p>
                                            <p className="text-sm font-mono text-gray-900">
                                                {format(new Date(selectedLog.created_at), 'dd MMMM yyyy, HH:mm:ss', { locale: it })}
                                            </p>
                                        </div>
                                        <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                                            <p className="text-[10px] font-bold text-gray-400 uppercase mb-1 flex items-center gap-1">
                                                Id Log
                                            </p>
                                            <p className="text-[11px] font-mono text-gray-500 break-all">{selectedLog.id}</p>
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <div className="flex items-start gap-4">
                                            <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600 h-9 w-9 flex items-center justify-center shrink-0">
                                                <Terminal size={18} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-bold text-gray-900">{selectedLog.action}</p>
                                                <p className="text-xs text-gray-500 font-medium">
                                                    Su risorsa <span className="text-indigo-600">{selectedLog.resource_type}</span> {selectedLog.resource_id && `(ID: ${selectedLog.resource_id})`}
                                                </p>
                                            </div>
                                            <div className="shrink-0">{getStatusBadge(selectedLog.status)}</div>
                                        </div>

                                        {selectedLog.description && (
                                            <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100 text-sm text-blue-900 italic">
                                                {selectedLog.description}
                                            </div>
                                        )}
                                    </div>

                                    <div className="border-t border-gray-100 pt-6 grid grid-cols-2 gap-y-4">
                                        <div>
                                            <p className="text-[10px] font-bold text-gray-400 uppercase">Endpoint</p>
                                            <p className="text-xs font-mono text-gray-700">{selectedLog.http_method || 'N/D'} {selectedLog.endpoint || 'N/D'}</p>
                                        </div>
                                        <div>
                                            <p className="text-[10px] font-bold text-gray-400 uppercase">IP Address</p>
                                            <p className="text-xs font-mono text-gray-700">{selectedLog.ip_address || 'Locale'}</p>
                                        </div>
                                        <div className="col-span-2">
                                            <p className="text-[10px] font-bold text-gray-400 uppercase">Servizio Origine</p>
                                            <p className="text-xs font-medium text-gray-900">{selectedLog.service_name}</p>
                                        </div>
                                    </div>

                                    {(selectedLog.request_data || selectedLog.response_data) && (
                                        <div className="space-y-4 border-t border-gray-100 pt-6">
                                            <p className="text-xs font-bold text-gray-900 uppercase tracking-wide">Dati Tecnici (JSON)</p>
                                            {selectedLog.request_data && (
                                                <div className="space-y-1">
                                                    <p className="text-[10px] text-gray-400 font-bold uppercase ml-1">Request Body</p>
                                                    <pre className="bg-gray-900 text-gray-300 p-4 rounded-xl text-[10px] overflow-x-auto max-h-40 font-mono">
                                                        {JSON.stringify(selectedLog.request_data, null, 2)}
                                                    </pre>
                                                </div>
                                            )}
                                            {selectedLog.error_message && (
                                                <div className="bg-red-50 p-4 rounded-xl border border-red-100 flex items-start gap-3">
                                                    <ShieldAlert className="text-red-600 shrink-0" size={18} />
                                                    <div className="space-y-1 min-w-0">
                                                        <p className="text-xs font-bold text-red-900 uppercase">Dettaglio Errore</p>
                                                        <p className="text-xs text-red-700 font-mono break-all">{selectedLog.error_message}</p>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-gray-400 italic">Dati non disponibili</div>
                            )}
                        </div>

                        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end">
                            <Button variant="secondary" onClick={() => setIsDetailModalOpen(false)}>
                                Chiudi
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AuditLogPage;
