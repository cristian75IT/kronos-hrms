/**
 * KRONOS - Expense Report Detail Page
 * Enterprise-grade expense report view
 */
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useState } from 'react';
import {
    ArrowLeft,
    FileText,
    CheckCircle,
    XCircle,
    AlertCircle,
    Receipt,
    Edit,
    Trash2,
    Send,
    CreditCard,
    Plus,
    Loader
} from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { useReports } from '../../hooks/useApi';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { reportsService } from '../../services/expenses.service';

export function ExpenseDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const toast = useToast();
    const { isApprover } = useAuth();
    const { data: reports, isLoading, refetch } = useReports();
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [showRejectModal, setShowRejectModal] = useState(false);
    const [rejectReason, setRejectReason] = useState('');

    // Find specific report
    const report = reports?.find(r => r.id === id);

    const getStatusConfig = (status: string) => {
        const configs: Record<string, { color: string; icon: React.ReactNode; label: string; bg: string }> = {
            draft: {
                color: 'var(--color-text-muted)',
                icon: <FileText size={20} />,
                label: 'Bozza',
                bg: 'var(--color-bg-tertiary)'
            },
            submitted: {
                color: 'var(--color-warning)',
                icon: <Send size={20} />,
                label: 'In Approvazione',
                bg: 'var(--color-warning-bg)'
            },
            approved: {
                color: 'var(--color-success)',
                icon: <CheckCircle size={20} />,
                label: 'Approvata',
                bg: 'var(--color-success-bg)'
            },
            rejected: {
                color: 'var(--color-danger)',
                icon: <XCircle size={20} />,
                label: 'Rifiutata',
                bg: 'var(--color-danger-bg)'
            },
            paid: {
                color: 'var(--color-info)',
                icon: <CreditCard size={20} />,
                label: 'Pagata',
                bg: 'var(--color-info-bg)'
            }
        };
        return configs[status] || configs.draft;
    };

    // Action Handlers
    const handleSubmit = async () => {
        if (!id) return;
        setActionLoading('submit');
        try {
            await reportsService.submitReport(id);
            toast.success('Nota spese inviata per approvazione');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'invio');
        } finally {
            setActionLoading(null);
        }
    };

    const handleApprove = async () => {
        if (!id) return;
        setActionLoading('approve');
        try {
            await reportsService.approveReport(id, report?.total_amount);
            toast.success('Nota spese approvata');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'approvazione');
        } finally {
            setActionLoading(null);
        }
    };

    const handleReject = async () => {
        if (!id || !rejectReason.trim()) return;
        setActionLoading('reject');
        try {
            await reportsService.rejectReport(id, rejectReason);
            toast.success('Nota spese rifiutata');
            setShowRejectModal(false);
            setRejectReason('');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante il rifiuto');
        } finally {
            setActionLoading(null);
        }
    };

    const handleMarkPaid = async () => {
        if (!id) return;
        setActionLoading('paid');
        try {
            await reportsService.markPaid(id, 'Bonifico'); // Default payment ref for simplicity
            toast.success('Nota spese contrassegnata come pagata');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'operazione');
        } finally {
            setActionLoading(null);
        }
    };

    if (isLoading) {
        return (
            <div className="detail-page animate-fadeIn">
                <div className="detail-loading">
                    <Loader size={32} className="animate-spin" />
                    <p>Caricamento nota spese...</p>
                </div>
            </div>
        );
    }

    if (!report) {
        return (
            <div className="detail-page animate-fadeIn">
                <div className="detail-empty">
                    <AlertCircle size={48} />
                    <h2>Nota spesa non trovata</h2>
                    <p>La nota spese che stai cercando non esiste o è stata eliminata.</p>
                    <Link to="/expenses" className="btn btn-primary">
                        Torna alle Note Spese
                    </Link>
                </div>
            </div>
        );
    }

    const statusConfig = getStatusConfig(report.status);

    return (
        <div className="detail-page animate-fadeIn">
            {/* Header */}
            <header className="detail-header">
                <div className="detail-header-left">
                    <button onClick={() => navigate(-1)} className="btn btn-ghost btn-icon">
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <div className="detail-breadcrumb">
                            <Link to="/expenses">Note Spese</Link>
                            <span>/</span>
                            <span>{report.report_number}</span>
                        </div>
                        <h1 className="detail-title">{report.title}</h1>
                    </div>
                </div>
                <div className="detail-header-right">
                    <div
                        className="detail-status-badge"
                        style={{
                            background: statusConfig.bg,
                            color: statusConfig.color
                        }}
                    >
                        {statusConfig.icon}
                        <span>{statusConfig.label}</span>
                    </div>
                </div>
            </header>

            <div className="detail-content">
                {/* Main Column */}
                <div className="detail-main">
                    {/* Items Card */}
                    <div className="detail-card card animate-fadeInUp">
                        <div className="card-header-actions">
                            <h3 className="detail-section-title">
                                <Receipt size={18} />
                                Voci di Spesa
                            </h3>
                            {report.status === 'draft' && (
                                <button className="btn btn-primary btn-sm">
                                    <Plus size={16} />
                                    Aggiungi Voce
                                </button>
                            )}
                        </div>

                        {(!report.items || report.items.length === 0) ? (
                            <div className="empty-state">
                                <div className="empty-state-icon">
                                    <Receipt size={32} />
                                </div>
                                <h3 className="empty-state-title">Nessuna voce presente</h3>
                                <p className="empty-state-description">
                                    Aggiungi le voci di spesa per completare la nota.
                                </p>
                            </div>
                        ) : (
                            <div className="expense-items-list">
                                {report.items.map(item => (
                                    <div key={item.id} className="expense-item-row">
                                        <div className="item-date">
                                            {format(new Date(item.date), 'dd MMM', { locale: it })}
                                        </div>
                                        <div className="item-info">
                                            <div className="item-title">{item.description}</div>
                                            <div className="item-meta">
                                                {item.merchant_name && <span>{item.merchant_name}</span>}
                                                <span className="badge badge-sm">{item.expense_type_code}</span>
                                            </div>
                                        </div>
                                        <div className="item-amount">
                                            € {item.amount.toFixed(2)}
                                        </div>
                                        {report.status === 'draft' && (
                                            <button className="btn btn-ghost btn-sm btn-icon text-danger">
                                                <Trash2 size={16} />
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Notes */}
                    {report.employee_notes && (
                        <div className="detail-card card animate-fadeInUp">
                            <h3 className="detail-section-title">Note</h3>
                            <p className="detail-notes">{report.employee_notes}</p>
                        </div>
                    )}
                </div>

                {/* Sidebar */}
                <div className="detail-sidebar">
                    {/* Actions */}
                    <div className="card">
                        <h3 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>Azioni</h3>
                        <div className="detail-actions">
                            {report.status === 'draft' && (
                                <>
                                    <button
                                        className="btn btn-primary btn-lg"
                                        style={{ width: '100%' }}
                                        onClick={handleSubmit}
                                        disabled={actionLoading !== null}
                                    >
                                        {actionLoading === 'submit' ? <Loader size={18} className="animate-spin" /> : <Send size={18} />}
                                        Invia Richiesta
                                    </button>
                                    <Link to={`/expenses/${id}/edit`} className="btn btn-secondary" style={{ width: '100%' }}>
                                        <Edit size={18} />
                                        Modifica
                                    </Link>
                                    <button className="btn btn-ghost text-danger" style={{ width: '100%' }}>
                                        <Trash2 size={18} />
                                        Elimina
                                    </button>
                                </>
                            )}
                            {report.status === 'submitted' && isApprover && (
                                <>
                                    <button
                                        className="btn btn-success btn-lg"
                                        style={{ width: '100%' }}
                                        onClick={handleApprove}
                                        disabled={actionLoading !== null}
                                    >
                                        {actionLoading === 'approve' ? <Loader size={18} className="animate-spin" /> : <CheckCircle size={18} />}
                                        Approva
                                    </button>
                                    <button
                                        className="btn btn-danger"
                                        style={{ width: '100%' }}
                                        onClick={() => setShowRejectModal(true)}
                                        disabled={actionLoading !== null}
                                    >
                                        <XCircle size={18} />
                                        Rifiuta
                                    </button>
                                </>
                            )}
                            {report.status === 'approved' && ( // Assuming HR or Admin can mark as paid
                                <button
                                    className="btn btn-primary btn-lg"
                                    style={{ width: '100%' }}
                                    onClick={handleMarkPaid}
                                    disabled={actionLoading !== null}
                                >
                                    {actionLoading === 'paid' ? <Loader size={18} className="animate-spin" /> : <CreditCard size={18} />}
                                    Segna come Pagato
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Summary */}
                    <div className="card">
                        <h3 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>Riepilogo</h3>
                        <div className="summary-list">
                            <div className="summary-item">
                                <span className="summary-label">Totale</span>
                                <span className="summary-value font-bold text-lg">€ {report.total_amount.toFixed(2)}</span>
                            </div>
                            {report.approved_amount !== undefined && (
                                <div className="summary-item">
                                    <span className="summary-label">Approvato</span>
                                    <span className="summary-value text-success font-semibold">€ {report.approved_amount.toFixed(2)}</span>
                                </div>
                            )}
                            <div className="summary-item">
                                <span className="summary-label">Periodo</span>
                                <span className="summary-value text-sm text-right">
                                    {format(new Date(report.period_start), 'd MMM', { locale: it })} - {format(new Date(report.period_end), 'd MMM yyyy', { locale: it })}
                                </span>
                            </div>
                            <div className="summary-item">
                                <span className="summary-label">N. Voci</span>
                                <span className="summary-value">{report.items?.length || 0}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Reject Modal */}
            {showRejectModal && (
                <div className="modal-overlay" onClick={() => setShowRejectModal(false)}>
                    <div className="modal-container animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Rifiuta Nota Spese</h3>
                            <button className="btn btn-ghost btn-icon" onClick={() => setShowRejectModal(false)}>
                                <XCircle size={20} />
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label className="input-label input-label-required">Motivo del Rifiuto</label>
                                <textarea
                                    className="input"
                                    placeholder="Inserisci il motivo del rifiuto..."
                                    value={rejectReason}
                                    onChange={(e) => setRejectReason(e.target.value)}
                                    rows={4}
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-ghost" onClick={() => setShowRejectModal(false)}>
                                Annulla
                            </button>
                            <button
                                className="btn btn-danger"
                                onClick={handleReject}
                                disabled={!rejectReason.trim() || actionLoading === 'reject'}
                            >
                                {actionLoading === 'reject' ? <Loader size={16} className="animate-spin" /> : null}
                                Conferma Rifiuto
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <style>{`
                .detail-page {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-6);
                }

                .detail-loading,
                .detail-empty {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 400px;
                    gap: var(--space-4);
                    text-align: center;
                    color: var(--color-text-muted);
                }

                .detail-empty h2 {
                    color: var(--color-text-primary);
                }

                .detail-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    gap: var(--space-4);
                }

                .detail-header-left {
                    display: flex;
                    align-items: flex-start;
                    gap: var(--space-4);
                }

                .detail-breadcrumb {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    font-size: var(--font-size-sm);
                    color: var(--color-text-muted);
                    margin-bottom: var(--space-1);
                }

                .detail-breadcrumb a:hover {
                    color: var(--color-primary);
                }

                .detail-title {
                    font-size: var(--font-size-2xl);
                    font-weight: var(--font-weight-bold);
                }

                .detail-status-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--space-2);
                    padding: var(--space-2) var(--space-4);
                    border-radius: var(--radius-full);
                    font-weight: var(--font-weight-medium);
                    font-size: var(--font-size-sm);
                }

                .detail-content {
                    display: grid;
                    grid-template-columns: 1fr 320px;
                    gap: var(--space-6);
                }

                @media (max-width: 1024px) {
                    .detail-content {
                        grid-template-columns: 1fr;
                    }
                }

                .detail-card {
                    padding: var(--space-6);
                }

                .detail-section-title {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    font-size: var(--font-size-sm);
                    font-weight: var(--font-weight-semibold);
                    color: var(--color-text-secondary);
                    margin-bottom: var(--space-4);
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }

                .detail-notes {
                    color: var(--color-text-secondary);
                    line-height: var(--line-height-relaxed);
                }

                .card-header-actions {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--space-4);
                }

                .card-header-actions .detail-section-title {
                    margin-bottom: 0;
                }

                .empty-state {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: var(--space-8);
                    text-align: center;
                    color: var(--color-text-muted);
                    background: var(--color-bg-tertiary);
                    border-radius: var(--radius-lg);
                    border: 1px dashed var(--color-border);
                }

                .empty-state-icon {
                    width: 48px;
                    height: 48px;
                    background: var(--color-bg-secondary);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: var(--space-3);
                    color: var(--color-text-muted);
                }

                .expense-items-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-2);
                }

                .expense-item-row {
                    display: flex;
                    align-items: center;
                    gap: var(--space-4);
                    padding: var(--space-3);
                    background: var(--color-bg-tertiary);
                    border-radius: var(--radius-lg);
                    transition: all var(--transition-fast);
                }

                .expense-item-row:hover {
                    background: var(--color-bg-secondary);
                }

                .item-date {
                    font-size: var(--font-size-sm);
                    font-weight: var(--font-weight-medium);
                    color: var(--color-text-secondary);
                    min-width: 60px;
                    text-align: center;
                    line-height: 1.2;
                }

                .item-info {
                    flex: 1;
                    min-width: 0;
                }

                .item-title {
                    font-weight: var(--font-weight-medium);
                    color: var(--color-text-primary);
                    margin-bottom: 2px;
                }

                .item-meta {
                    display: flex;
                    gap: var(--space-2);
                    font-size: var(--font-size-xs);
                    color: var(--color-text-muted);
                }

                .item-amount {
                    font-weight: var(--font-weight-bold);
                    color: var(--color-text-primary);
                    font-size: var(--font-size-lg);
                }

                .detail-sidebar {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-4);
                }

                .detail-actions {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-3);
                }

                .summary-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-3);
                }

                .summary-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: var(--space-2) 0;
                    border-bottom: 1px solid var(--color-border-light);
                }

                .summary-item:last-child {
                    border-bottom: none;
                }

                .summary-label {
                    font-size: var(--font-size-sm);
                    color: var(--color-text-muted);
                }

                .summary-value {
                    font-size: var(--font-size-sm);
                    color: var(--color-text-primary);
                }
            `}</style>
        </div>
    );
}

export default ExpenseDetailPage;
