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
    X
} from 'lucide-react';
import notificationService from '../../services/notification.service';
import type { EmailLog, EmailEvent } from '../../services/notification.service';
import { useToast } from '../../context/ToastContext';

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

    const getEventBadge = (event: string) => {
        const styles: Record<string, { bg: string; text: string }> = {
            'delivered': { bg: '#ecfdf5', text: '#059669' },
            'opened': { bg: '#eff6ff', text: '#2563eb' },
            'clicked': { bg: '#faf5ff', text: '#7c3aed' },
            'sent': { bg: '#f0fdf4', text: '#16a34a' },
            'bounced': { bg: '#fef2f2', text: '#dc2626' },
            'hardBounce': { bg: '#fef2f2', text: '#dc2626' },
            'softBounce': { bg: '#fffbeb', text: '#d97706' },
            'spam': { bg: '#fef2f2', text: '#dc2626' },
            'unsubscribed': { bg: '#f3f4f6', text: '#6b7280' },
            'blocked': { bg: '#fef2f2', text: '#dc2626' },
            'deferred': { bg: '#fffbeb', text: '#d97706' },
        };
        const style = styles[event] || { bg: '#f3f4f6', text: '#374151' };
        return {
            backgroundColor: style.bg,
            color: style.text,
            padding: '2px 8px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 500,
            textTransform: 'uppercase' as const,
        };
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'sent':
            case 'delivered':
                return <CheckCircle size={18} className="text-green-500" />;
            case 'failed':
            case 'bounced':
                return <XCircle size={18} className="text-red-500" />;
            case 'pending':
            case 'queued':
                return <Clock size={18} className="text-amber-500" />;
            default:
                return <AlertTriangle size={18} className="text-gray-500" />;
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('it-IT', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatEventDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('it-IT', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    return (
        <div className="email-logs-page">
            <div className="page-header">
                <div className="header-title">
                    <Mail size={24} />
                    <h1>Log Email</h1>
                </div>
                <button className="refresh-btn" onClick={fetchLogs} disabled={loading}>
                    <RefreshCw size={18} className={loading ? 'spinning' : ''} />
                    Aggiorna
                </button>
            </div>

            {stats && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-icon bg-blue-50">
                            <Mail size={24} className="text-blue-500" />
                        </div>
                        <div className="stat-content">
                            <span className="stat-label">Totale (7gg)</span>
                            <span className="stat-value">{stats.total}</span>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon bg-green-50">
                            <CheckCircle size={24} className="text-green-500" />
                        </div>
                        <div className="stat-content">
                            <span className="stat-label">Inviate</span>
                            <span className="stat-value text-green-600">{stats.sent}</span>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon bg-red-50">
                            <XCircle size={24} className="text-red-500" />
                        </div>
                        <div className="stat-content">
                            <span className="stat-label">Fallite</span>
                            <span className="stat-value text-red-600">{stats.failed}</span>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon bg-amber-50">
                            <Clock size={24} className="text-amber-500" />
                        </div>
                        <div className="stat-content">
                            <span className="stat-label">In Coda</span>
                            <span className="stat-value text-amber-600">{stats.pending}</span>
                        </div>
                    </div>
                </div>
            )}

            <div className="content-card">
                <div className="filters-bar">
                    <div className="search-filter">
                        <Search size={18} className="search-icon" />
                        <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="status-select"
                        >
                            <option value="">Tutti gli stati</option>
                            <option value="sent">Inviate</option>
                            <option value="failed">Fallite</option>
                            <option value="pending">In Coda</option>
                        </select>
                    </div>
                </div>

                <div className="table-container">
                    <table className="logs-table">
                        <thead>
                            <tr>
                                <th>Stato</th>
                                <th>Destinatario</th>
                                <th>Template</th>
                                <th>Oggetto</th>
                                <th>Data</th>
                                <th>Azioni</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="empty-state">
                                        Nessun log trovato
                                    </td>
                                </tr>
                            ) : (
                                logs.map(log => (
                                    <tr key={log.id}>
                                        <td className="status-cell">
                                            <div className="status-badge">
                                                {getStatusIcon(log.status)}
                                                <span>{log.status.toUpperCase()}</span>
                                            </div>
                                        </td>
                                        <td>
                                            <div className="recipient-cell">
                                                <span className="email">{log.to_email}</span>
                                                {log.to_name && <span className="name">{log.to_name}</span>}
                                            </div>
                                        </td>
                                        <td>
                                            <span className="template-badge">{log.template_code}</span>
                                        </td>
                                        <td>
                                            <div className="subject-cell">
                                                <span>{log.subject || '-'}</span>
                                                {log.error_message && (
                                                    <span className="error-text" title={log.error_message}>
                                                        {log.error_message}
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td>{formatDate(log.created_at)}</td>
                                        <td>
                                            <div className="action-buttons">
                                                {log.status === 'sent' && (
                                                    <button
                                                        className="events-btn"
                                                        onClick={() => handleViewEvents(log)}
                                                        title="Visualizza eventi Brevo"
                                                    >
                                                        <Activity size={16} />
                                                    </button>
                                                )}
                                                {log.status === 'failed' && (
                                                    <button
                                                        className="retry-btn"
                                                        onClick={() => handleRetry(log.id)}
                                                        disabled={retrying === log.id}
                                                        title="Riprova invio"
                                                    >
                                                        <RotateCw size={16} className={retrying === log.id ? 'spinning' : ''} />
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="pagination">
                    <button
                        disabled={page === 1}
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        className="page-btn"
                    >
                        Precedente
                    </button>
                    <span className="page-info">Pagina {page}</span>
                    <button
                        disabled={logs.length < pageSize}
                        onClick={() => setPage(p => p + 1)}
                        className="page-btn"
                    >
                        Successiva
                    </button>
                </div>
            </div>

            {/* Events Modal */}
            {eventsModalOpen && (
                <div className="modal-overlay" onClick={() => setEventsModalOpen(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Eventi Brevo</h2>
                            <button className="modal-close" onClick={() => setEventsModalOpen(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="modal-body">
                            {selectedLog && (
                                <div className="modal-info">
                                    <div className="info-header">
                                        <div>
                                            <p><strong>Destinatario:</strong> {selectedLog.to_email}</p>
                                            <p><strong>Template:</strong> {selectedLog.template_code}</p>
                                            {selectedLog.message_id && (
                                                <p><strong>Message ID:</strong> <code>{selectedLog.message_id}</code></p>
                                            )}
                                        </div>
                                        <button
                                            className="search-permissive-btn"
                                            onClick={() => handleViewEvents(selectedLog, true)}
                                            disabled={eventsLoading}
                                            title="Cerca tutti gli eventi per questo destinatario (senza ID messaggio)"
                                        >
                                            <Search size={16} />
                                            Ricerca Estesa
                                        </button>
                                    </div>
                                </div>
                            )}
                            {eventsLoading ? (
                                <div className="loading-state">
                                    <RefreshCw size={24} className="spinning" />
                                    <span>Caricamento eventi...</span>
                                </div>
                            ) : events.length === 0 ? (
                                <div className="empty-events" style={{ textAlign: 'center' }}>
                                    <AlertTriangle size={24} />
                                    <p>Nessun evento diretto trovato per questo ID messaggio.</p>
                                    <button
                                        className="search-permissive-btn mt-4"
                                        onClick={() => handleViewEvents(selectedLog!, true)}
                                        style={{ margin: '16px auto' }}
                                    >
                                        <Search size={16} />
                                        Prova Ricerca Estesa
                                    </button>
                                </div>
                            ) : (
                                <div className="events-list">
                                    {events.map((event, idx) => (
                                        <div key={idx} className="event-item">
                                            <div className="event-badge">
                                                <span style={getEventBadge(event.event)}>{event.event}</span>
                                            </div>
                                            <div className="event-details">
                                                <span className="event-date">{formatEventDate(event.date)}</span>
                                                {event.subject && <span className="event-subject">{event.subject}</span>}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            <style>{`
                .email-logs-page {
                    padding: 24px;
                    max-width: 1200px;
                    margin: 0 auto;
                }

                .page-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 24px;
                }

                .header-title {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }

                .header-title h1 {
                    font-size: 24px;
                    font-weight: 600;
                    margin: 0;
                    color: #111827;
                }

                .refresh-btn {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 8px 16px;
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    color: #374151;
                    transition: all 0.2s;
                }

                .refresh-btn:hover {
                    background: #f9fafb;
                    border-color: #d1d5db;
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 16px;
                    margin-bottom: 24px;
                }

                .stat-card {
                    background: white;
                    padding: 16px;
                    border-radius: 12px;
                    border: 1px solid #e5e7eb;
                    display: flex;
                    align-items: center;
                    gap: 16px;
                }

                .stat-icon {
                    width: 48px;
                    height: 48px;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .stat-content {
                    display: flex;
                    flex-direction: column;
                }

                .stat-label {
                    font-size: 13px;
                    color: #6b7280;
                }

                .stat-value {
                    font-size: 24px;
                    font-weight: 600;
                    color: #111827;
                }

                .content-card {
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 12px;
                    overflow: hidden;
                }

                .filters-bar {
                    padding: 16px;
                    border-bottom: 1px solid #e5e7eb;
                }

                .search-filter {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    max-width: 300px;
                }

                .status-select {
                    padding: 8px 12px;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    width: 100%;
                    font-size: 14px;
                }

                .table-container {
                    overflow-x: auto;
                }

                .logs-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 14px;
                }

                .logs-table th {
                    text-align: left;
                    padding: 12px 16px;
                    background: #f9fafb;
                    color: #374151;
                    font-weight: 500;
                    border-bottom: 1px solid #e5e7eb;
                }

                .logs-table td {
                    padding: 12px 16px;
                    border-bottom: 1px solid #e5e7eb;
                    color: #374151;
                }

                .status-badge {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-weight: 500;
                    font-size: 13px;
                }

                .recipient-cell {
                    display: flex;
                    flex-direction: column;
                }

                .recipient-cell .name {
                    font-size: 12px;
                    color: #6b7280;
                }

                .template-badge {
                    padding: 2px 8px;
                    background: #eff6ff;
                    color: #1d4ed8;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                }

                .subject-cell {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }

                .error-text {
                    font-size: 12px;
                    color: #ef4444;
                }

                .retry-btn {
                    padding: 6px;
                    border: 1px solid #e5e7eb;
                    background: white;
                    border-radius: 4px;
                    cursor: pointer;
                    color: #374151;
                    transition: all 0.2s;
                }

                .retry-btn:hover {
                    background: #f3f4f6;
                    color: #111827;
                }

                .pagination {
                    padding: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 16px;
                    border-top: 1px solid #e5e7eb;
                }

                .page-btn {
                    padding: 6px 12px;
                    border: 1px solid #d1d5db;
                    background: white;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                }

                .page-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .text-green-500 { color: #10b981; }
                .text-green-600 { color: #059669; }
                .text-red-500 { color: #ef4444; }
                .text-red-600 { color: #dc2626; }
                .text-amber-500 { color: #f59e0b; }
                .text-amber-600 { color: #d97706; }
                .text-blue-500 { color: #3b82f6; }
                .text-gray-500 { color: #6b7280; }
                
                .bg-green-50 { background: #ecfdf5; }
                .bg-red-50 { background: #fef2f2; }
                .bg-amber-50 { background: #fffbeb; }
                .bg-blue-50 { background: #eff6ff; }

                .action-buttons {
                    display: flex;
                    gap: 8px;
                }

                .events-btn {
                    padding: 6px;
                    border: 1px solid #e5e7eb;
                    background: white;
                    border-radius: 4px;
                    cursor: pointer;
                    color: #3b82f6;
                    transition: all 0.2s;
                }

                .events-btn:hover {
                    background: #eff6ff;
                    border-color: #3b82f6;
                }

                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }

                .modal-content {
                    background: white;
                    border-radius: 12px;
                    width: 90%;
                    max-width: 600px;
                    max-height: 80vh;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                }

                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px 20px;
                    border-bottom: 1px solid #e5e7eb;
                }

                .modal-header h2 {
                    font-size: 18px;
                    font-weight: 600;
                    margin: 0;
                }

                .modal-close {
                    padding: 4px;
                    border: none;
                    background: transparent;
                    cursor: pointer;
                    color: #6b7280;
                    border-radius: 4px;
                }

                .modal-close:hover {
                    background: #f3f4f6;
                    color: #111827;
                }

                .modal-body {
                    padding: 20px;
                    overflow-y: auto;
                }

                .modal-info {
                    background: #f9fafb;
                    padding: 12px;
                    border-radius: 8px;
                    margin-bottom: 16px;
                }

                .modal-info p {
                    margin: 4px 0;
                    font-size: 14px;
                }

                .modal-info code {
                    font-size: 12px;
                    background: #e5e7eb;
                    padding: 2px 6px;
                    border-radius: 4px;
                }

                .info-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    gap: 16px;
                }

                .search-permissive-btn {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 8px 12px;
                    background: #eff6ff;
                    border: 1px solid #bfdbfe;
                    border-radius: 6px;
                    color: #1d4ed8;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                    white-space: nowrap;
                }

                .search-permissive-btn:hover {
                    background: #dbeafe;
                    border-color: #3b82f6;
                }

                .search-permissive-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .mt-4 {
                    margin-top: 16px;
                }

                .loading-state,
                .empty-events {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 8px;
                    padding: 32px;
                    color: #6b7280;
                }

                .events-list {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }

                .event-item {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px;
                    background: #f9fafb;
                    border-radius: 8px;
                    border: 1px solid #e5e7eb;
                }

                .event-badge {
                    flex-shrink: 0;
                }

                .event-details {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }

                .event-date {
                    font-size: 14px;
                    font-weight: 500;
                    color: #111827;
                }

                .event-subject {
                    font-size: 13px;
                    color: #6b7280;
                }

                .spinning {
                    animation: spin 1s linear infinite;
                }

                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
};
