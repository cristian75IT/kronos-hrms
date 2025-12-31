/**
 * KRONOS - Leave Request Detail Page
 * Enterprise-grade detail view with timeline and actions
 */
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import {
    ArrowLeft,
    Calendar,
    Clock,
    FileText,
    CheckCircle,
    XCircle,
    AlertCircle,
    Download,
    MessageSquare,
    History,
    Edit,
    Trash2,
    Send,
    Loader,
} from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { useLeaveRequests } from '../../hooks/useApi';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { leavesService } from '../../services/leaves.service';

export function LeaveDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const toast = useToast();
    const { isApprover } = useAuth();
    const { data: leaves, isLoading, refetch } = useLeaveRequests(new Date().getFullYear());
    const [activeTab, setActiveTab] = useState<'details' | 'history'>('details');
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [showRejectModal, setShowRejectModal] = useState(false);
    const [rejectReason, setRejectReason] = useState('');
    const [showCancelModal, setShowCancelModal] = useState(false);
    const [cancelReason, setCancelReason] = useState('');

    // Find the specific leave request
    const leave = leaves?.find(l => l.id === id);

    // Action handlers
    const handleSubmit = async () => {
        if (!id) return;
        setActionLoading('submit');
        try {
            await leavesService.submitRequest(id);
            toast.success('Richiesta inviata con successo');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'invio della richiesta');
        } finally {
            setActionLoading(null);
        }
    };

    const handleCancel = async () => {
        if (!id || !cancelReason.trim()) return;
        setActionLoading('cancel');
        try {
            await leavesService.cancelRequest(id, cancelReason);
            toast.success('Richiesta annullata');
            setShowCancelModal(false);
            setCancelReason('');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'annullamento');
        } finally {
            setActionLoading(null);
        }
    };

    const handleDelete = async () => {
        if (!id) return;
        if (!confirm('Sei sicuro di voler eliminare questa richiesta?')) return;
        setActionLoading('delete');
        try {
            await leavesService.deleteRequest(id);
            toast.success('Richiesta eliminata');
            navigate('/leaves');
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'eliminazione');
        } finally {
            setActionLoading(null);
        }
    };

    const handleApprove = async () => {
        if (!id) return;
        setActionLoading('approve');
        try {
            await leavesService.approveRequest(id);
            toast.success('Richiesta approvata');
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
            await leavesService.rejectRequest(id, rejectReason);
            toast.success('Richiesta rifiutata');
            setShowRejectModal(false);
            setRejectReason('');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante il rifiuto');
        } finally {
            setActionLoading(null);
        }
    };

    if (isLoading) {
        return (
            <div className="detail-page animate-fadeIn">
                <div className="detail-loading">
                    <div className="spinner-lg" />
                    <p>Caricamento richiesta...</p>
                </div>
            </div>
        );
    }

    if (!leave) {
        return (
            <div className="detail-page animate-fadeIn">
                <div className="detail-empty">
                    <AlertCircle size={48} />
                    <h2>Richiesta non trovata</h2>
                    <p>La richiesta che stai cercando non esiste o è stata eliminata.</p>
                    <Link to="/leaves" className="btn btn-primary">
                        Torna alle Ferie
                    </Link>
                </div>
            </div>
        );
    }

    const getStatusConfig = (status: string) => {
        const configs: Record<string, { color: string; icon: React.ReactNode; label: string; bg: string }> = {
            pending: {
                color: 'var(--color-warning)',
                icon: <Clock size={20} />,
                label: 'In Attesa',
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
            draft: {
                color: 'var(--color-text-muted)',
                icon: <FileText size={20} />,
                label: 'Bozza',
                bg: 'var(--color-bg-tertiary)'
            },
            cancelled: {
                color: 'var(--color-text-muted)',
                icon: <XCircle size={20} />,
                label: 'Annullata',
                bg: 'var(--color-bg-tertiary)'
            },
        };
        return configs[status] || configs.pending;
    };

    const statusConfig = getStatusConfig(leave.status);

    const leaveTypeNames: Record<string, string> = {
        FER: 'Ferie',
        ROL: 'Riduzione Orario Lavoro',
        PAR: 'Ex-Festività / Altri',
        MAL: 'Malattia',
        MAT: 'Maternità/Paternità',
        LUT: 'Lutto',
        STU: 'Studio',
        DON: 'Donazione Sangue',
        L104: 'Legge 104',
        SW: 'Smart Working',
        NRT: 'Non Retribuito',
    };

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
                            <Link to="/leaves">Ferie</Link>
                            <span>/</span>
                            <span>Dettaglio Richiesta</span>
                        </div>
                        <h1 className="detail-title">
                            {leaveTypeNames[leave.leave_type_code] || leave.leave_type_code}
                        </h1>
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

            {/* Main Content */}
            <div className="detail-content">
                {/* Left Column - Main Info */}
                <div className="detail-main">
                    {/* Tabs */}
                    <div className="detail-tabs">
                        <button
                            className={`detail-tab ${activeTab === 'details' ? 'active' : ''}`}
                            onClick={() => setActiveTab('details')}
                        >
                            <FileText size={16} />
                            Dettagli
                        </button>
                        <button
                            className={`detail-tab ${activeTab === 'history' ? 'active' : ''}`}
                            onClick={() => setActiveTab('history')}
                        >
                            <History size={16} />
                            Cronologia
                        </button>
                    </div>

                    {activeTab === 'details' && (
                        <div className="detail-card card animate-fadeInUp">
                            {/* Period Info */}
                            <div className="detail-section">
                                <h3 className="detail-section-title">
                                    <Calendar size={18} />
                                    Periodo Richiesto
                                </h3>
                                <div className="detail-period">
                                    <div className="period-dates">
                                        <div className="period-date">
                                            <span className="period-label">Dal</span>
                                            <span className="period-value">
                                                {format(new Date(leave.start_date), 'EEEE d MMMM yyyy', { locale: it })}
                                            </span>
                                            {leave.start_half_day && (
                                                <span className="badge badge-info">Solo pomeriggio</span>
                                            )}
                                        </div>
                                        <div className="period-divider">
                                            <div className="period-line" />
                                            <span className="period-days">{leave.days_requested} giorni</span>
                                            <div className="period-line" />
                                        </div>
                                        <div className="period-date">
                                            <span className="period-label">Al</span>
                                            <span className="period-value">
                                                {format(new Date(leave.end_date), 'EEEE d MMMM yyyy', { locale: it })}
                                            </span>
                                            {leave.end_half_day && (
                                                <span className="badge badge-info">Solo mattina</span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Notes */}
                            {leave.employee_notes && (
                                <div className="detail-section">
                                    <h3 className="detail-section-title">
                                        <MessageSquare size={18} />
                                        Note del Dipendente
                                    </h3>
                                    <p className="detail-notes">{leave.employee_notes}</p>
                                </div>
                            )}

                            {/* Approver Notes */}
                            {leave.approver_notes && (
                                <div className="detail-section">
                                    <h3 className="detail-section-title">
                                        <MessageSquare size={18} />
                                        Note dell'Approvatore
                                    </h3>
                                    <p className="detail-notes">{leave.approver_notes}</p>
                                </div>
                            )}

                            {/* Attachment - future feature */}
                            {(leave as any).attachment_path && (
                                <div className="detail-section">
                                    <h3 className="detail-section-title">
                                        <FileText size={18} />
                                        Allegato
                                    </h3>
                                    <button className="btn btn-secondary">
                                        <Download size={16} />
                                        Scarica Allegato
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'history' && (
                        <div className="detail-card card animate-fadeInUp">
                            <div className="timeline">
                                <div className="timeline-item">
                                    <div className="timeline-dot" style={{ background: 'var(--color-primary)' }} />
                                    <div className="timeline-content">
                                        <div className="timeline-title">Richiesta Creata</div>
                                        <div className="timeline-date">
                                            {format(new Date(leave.created_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                                        </div>
                                    </div>
                                </div>
                                {leave.status !== 'draft' && (
                                    <div className="timeline-item">
                                        <div className="timeline-dot" style={{ background: 'var(--color-info)' }} />
                                        <div className="timeline-content">
                                            <div className="timeline-title">Richiesta Inviata</div>
                                            <div className="timeline-date">
                                                {format(new Date(leave.created_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                                            </div>
                                        </div>
                                    </div>
                                )}
                                {leave.status === 'approved' && leave.approved_at && (
                                    <div className="timeline-item">
                                        <div className="timeline-dot" style={{ background: 'var(--color-success)' }} />
                                        <div className="timeline-content">
                                            <div className="timeline-title">Richiesta Approvata</div>
                                            <div className="timeline-date">
                                                {format(new Date(leave.approved_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                                            </div>
                                        </div>
                                    </div>
                                )}
                                {leave.status === 'rejected' && (
                                    <div className="timeline-item">
                                        <div className="timeline-dot" style={{ background: 'var(--color-danger)' }} />
                                        <div className="timeline-content">
                                            <div className="timeline-title">Richiesta Rifiutata</div>
                                            <div className="timeline-date">
                                                {format(new Date(leave.updated_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Column - Actions & Summary */}
                <div className="detail-sidebar">
                    {/* Actions Card */}
                    <div className="card">
                        <h3 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>Azioni</h3>
                        <div className="detail-actions">
                            {leave.status === 'draft' && (
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
                                    <Link
                                        to={`/leaves/${id}/edit`}
                                        className="btn btn-secondary"
                                        style={{ width: '100%' }}
                                    >
                                        <Edit size={18} />
                                        Modifica
                                    </Link>
                                    <button
                                        className="btn btn-ghost text-danger"
                                        style={{ width: '100%' }}
                                        onClick={handleDelete}
                                        disabled={actionLoading !== null}
                                    >
                                        {actionLoading === 'delete' ? <Loader size={18} className="animate-spin" /> : <Trash2 size={18} />}
                                        Elimina
                                    </button>
                                </>
                            )}
                            {leave.status === 'pending' && !isApprover && (
                                <button
                                    className="btn btn-danger"
                                    style={{ width: '100%' }}
                                    onClick={() => setShowCancelModal(true)}
                                    disabled={actionLoading !== null}
                                >
                                    <XCircle size={18} />
                                    Annulla Richiesta
                                </button>
                            )}
                            {leave.status === 'pending' && isApprover && (
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
                            {(leave.status === 'approved' || leave.status === 'rejected' || leave.status === 'cancelled') && (
                                <p className="text-muted text-sm" style={{ textAlign: 'center' }}>
                                    Nessuna azione disponibile per questa richiesta.
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Summary Card */}
                    <div className="card">
                        <h3 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>Riepilogo</h3>
                        <div className="summary-list">
                            <div className="summary-item">
                                <span className="summary-label">Tipo</span>
                                <span className="summary-value">{leaveTypeNames[leave.leave_type_code] || leave.leave_type_code}</span>
                            </div>
                            <div className="summary-item">
                                <span className="summary-label">Giorni</span>
                                <span className="summary-value font-semibold">{leave.days_requested}</span>
                            </div>
                            <div className="summary-item">
                                <span className="summary-label">Creata il</span>
                                <span className="summary-value">
                                    {format(new Date(leave.created_at), 'd MMM yyyy', { locale: it })}
                                </span>
                            </div>
                            {leave.approved_at && (
                                <div className="summary-item">
                                    <span className="summary-label">Approvata il</span>
                                    <span className="summary-value">
                                        {format(new Date(leave.approved_at), 'd MMM yyyy', { locale: it })}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Reject Modal */}
            {showRejectModal && (
                <div className="modal-overlay" onClick={() => setShowRejectModal(false)}>
                    <div className="modal-container animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Rifiuta Richiesta</h3>
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

            {/* Cancel Modal */}
            {showCancelModal && (
                <div className="modal-overlay" onClick={() => setShowCancelModal(false)}>
                    <div className="modal-container animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Annulla Richiesta</h3>
                            <button className="btn btn-ghost btn-icon" onClick={() => setShowCancelModal(false)}>
                                <XCircle size={20} />
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label className="input-label input-label-required">Motivo dell'Annullamento</label>
                                <textarea
                                    className="input"
                                    placeholder="Inserisci il motivo dell'annullamento..."
                                    value={cancelReason}
                                    onChange={(e) => setCancelReason(e.target.value)}
                                    rows={4}
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-ghost" onClick={() => setShowCancelModal(false)}>
                                Indietro
                            </button>
                            <button
                                className="btn btn-danger"
                                onClick={handleCancel}
                                disabled={!cancelReason.trim() || actionLoading === 'cancel'}
                            >
                                {actionLoading === 'cancel' ? <Loader size={16} className="animate-spin" /> : null}
                                Conferma Annullamento
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

        .detail-tabs {
          display: flex;
          gap: var(--space-1);
          margin-bottom: var(--space-4);
          padding: var(--space-1);
          background: var(--color-bg-tertiary);
          border-radius: var(--radius-lg);
        }

        .detail-tab {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-2);
          padding: var(--space-2) var(--space-4);
          background: transparent;
          border: none;
          border-radius: var(--radius-md);
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-medium);
          color: var(--color-text-muted);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .detail-tab:hover {
          color: var(--color-text-primary);
        }

        .detail-tab.active {
          background: var(--color-bg-primary);
          color: var(--color-primary);
          box-shadow: var(--shadow-sm);
        }

        .detail-card {
          padding: var(--space-6);
        }

        .detail-section {
          padding: var(--space-4) 0;
          border-bottom: 1px solid var(--color-border-light);
        }

        .detail-section:last-child {
          border-bottom: none;
          padding-bottom: 0;
        }

        .detail-section:first-child {
          padding-top: 0;
        }

        .detail-section-title {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-semibold);
          color: var(--color-text-secondary);
          margin-bottom: var(--space-3);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .detail-period {
          background: var(--color-bg-secondary);
          border-radius: var(--radius-lg);
          padding: var(--space-4);
        }

        .period-dates {
          display: flex;
          flex-direction: column;
          gap: var(--space-3);
        }

        .period-date {
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
        }

        .period-label {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .period-value {
          font-size: var(--font-size-lg);
          font-weight: var(--font-weight-semibold);
          color: var(--color-text-primary);
          text-transform: capitalize;
        }

        .period-divider {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-2) 0;
        }

        .period-line {
          flex: 1;
          height: 1px;
          background: var(--color-border);
        }

        .period-days {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-semibold);
          color: var(--color-primary);
          padding: var(--space-1) var(--space-3);
          background: rgba(var(--color-primary-rgb), 0.1);
          border-radius: var(--radius-full);
        }

        .detail-notes {
          color: var(--color-text-secondary);
          line-height: var(--line-height-relaxed);
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

        .timeline {
          position: relative;
          padding-left: var(--space-6);
        }

        .timeline::before {
          content: '';
          position: absolute;
          left: 6px;
          top: 8px;
          bottom: 8px;
          width: 2px;
          background: var(--color-border);
        }

        .timeline-item {
          position: relative;
          padding-bottom: var(--space-6);
        }

        .timeline-item:last-child {
          padding-bottom: 0;
        }

        .timeline-dot {
          position: absolute;
          left: calc(-1 * var(--space-6) + 2px);
          top: 4px;
          width: 12px;
          height: 12px;
          border-radius: var(--radius-full);
          border: 2px solid var(--color-bg-primary);
        }

        .timeline-content {
          padding-left: var(--space-2);
        }

        .timeline-title {
          font-weight: var(--font-weight-medium);
          color: var(--color-text-primary);
          margin-bottom: var(--space-1);
        }

        .timeline-date {
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
        }
      `}</style>
        </div>
    );
}

export default LeaveDetailPage;
