/**
 * KRONOS - Trip Detail Page
 * Enterprise-grade business trip detail view
 */
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import {
    ArrowLeft,
    MapPin,
    Calendar,
    Clock,
    FileText,
    CheckCircle,
    XCircle,
    AlertCircle,
    Download,
    Edit,
    Send,
    Plane,
    Building,
    Globe,
    DollarSign,
    Receipt,
    Plus,
    Loader,
} from 'lucide-react';
import { format, differenceInDays } from 'date-fns';
import { it } from 'date-fns/locale';
import { useTrips } from '../../hooks/useApi';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { tripsService } from '../../services/expenses.service';

export function TripDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const toast = useToast();
    const { isApprover } = useAuth();
    const { data: trips, isLoading, refetch } = useTrips();
    const [activeTab, setActiveTab] = useState<'details' | 'expenses' | 'allowances'>('details');
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [showRejectModal, setShowRejectModal] = useState(false);
    const [rejectReason, setRejectReason] = useState('');

    // Find the specific trip
    const trip = trips?.find(t => t.id === id);

    // Action handlers
    const handleSubmit = async () => {
        if (!id) return;
        setActionLoading('submit');
        try {
            await tripsService.submitTrip(id);
            toast.success('Trasferta inviata per approvazione');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'invio');
        } finally {
            setActionLoading(null);
        }
    };

    const handleComplete = async () => {
        if (!id) return;
        setActionLoading('complete');
        try {
            await tripsService.completeTrip(id);
            toast.success('Trasferta completata');
            refetch();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante il completamento');
        } finally {
            setActionLoading(null);
        }
    };

    const handleApprove = async () => {
        if (!id) return;
        setActionLoading('approve');
        try {
            await tripsService.approveTrip(id);
            toast.success('Trasferta approvata');
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
            await tripsService.rejectTrip(id, rejectReason);
            toast.success('Trasferta rifiutata');
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
                    <p>Caricamento trasferta...</p>
                </div>
            </div>
        );
    }

    if (!trip) {
        return (
            <div className="detail-page animate-fadeIn">
                <div className="detail-empty">
                    <AlertCircle size={48} />
                    <h2>Trasferta non trovata</h2>
                    <p>La trasferta che stai cercando non esiste o è stata eliminata.</p>
                    <Link to="/trips" className="btn btn-primary">
                        Torna alle Trasferte
                    </Link>
                </div>
            </div>
        );
    }

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
                icon: <Clock size={20} />,
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
            completed: {
                color: 'var(--color-info)',
                icon: <CheckCircle size={20} />,
                label: 'Completata',
                bg: 'var(--color-info-bg)'
            },
            cancelled: {
                color: 'var(--color-text-muted)',
                icon: <XCircle size={20} />,
                label: 'Annullata',
                bg: 'var(--color-bg-tertiary)'
            },
        };
        return configs[status] || configs.draft;
    };

    const getDestinationIcon = (type: string) => {
        switch (type) {
            case 'national': return <Building size={20} />;
            case 'eu': return <Globe size={20} />;
            case 'extra_eu': return <Plane size={20} />;
            default: return <MapPin size={20} />;
        }
    };

    const getDestinationLabel = (type: string) => {
        switch (type) {
            case 'national': return 'Italia';
            case 'eu': return 'Europa';
            case 'extra_eu': return 'Extra UE';
            default: return type;
        }
    };

    const statusConfig = getStatusConfig(trip.status);
    const tripDays = differenceInDays(new Date(trip.end_date), new Date(trip.start_date)) + 1;

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
                            <Link to="/trips">Trasferte</Link>
                            <span>/</span>
                            <span>Dettaglio</span>
                        </div>
                        <h1 className="detail-title">{trip.title || trip.destination}</h1>
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

            {/* Hero Card */}
            <div className="trip-hero glass-card">
                <div className="trip-hero-content">
                    <div className="trip-hero-destination">
                        <div className="destination-icon">
                            {getDestinationIcon(trip.destination_type)}
                        </div>
                        <div>
                            <h2>{trip.destination}</h2>
                            <span className="destination-type">{getDestinationLabel(trip.destination_type)}</span>
                        </div>
                    </div>
                    <div className="trip-hero-stats">
                        <div className="hero-stat">
                            <Calendar size={18} />
                            <div>
                                <span className="hero-stat-value">{tripDays}</span>
                                <span className="hero-stat-label">giorni</span>
                            </div>
                        </div>
                        {trip.estimated_budget && (
                            <div className="hero-stat">
                                <DollarSign size={18} />
                                <div>
                                    <span className="hero-stat-value">€{Number(trip.estimated_budget).toFixed(0)}</span>
                                    <span className="hero-stat-label">budget</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
                <div className="trip-hero-dates">
                    <div className="hero-date">
                        <span className="hero-date-label">Partenza</span>
                        <span className="hero-date-value">
                            {format(new Date(trip.start_date), 'd MMM yyyy', { locale: it })}
                        </span>
                    </div>
                    <div className="hero-date-arrow">→</div>
                    <div className="hero-date">
                        <span className="hero-date-label">Ritorno</span>
                        <span className="hero-date-value">
                            {format(new Date(trip.end_date), 'd MMM yyyy', { locale: it })}
                        </span>
                    </div>
                </div>
            </div>

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
                            className={`detail-tab ${activeTab === 'expenses' ? 'active' : ''}`}
                            onClick={() => setActiveTab('expenses')}
                        >
                            <Receipt size={16} />
                            Spese
                        </button>
                        <button
                            className={`detail-tab ${activeTab === 'allowances' ? 'active' : ''}`}
                            onClick={() => setActiveTab('allowances')}
                        >
                            <DollarSign size={16} />
                            Diarie
                        </button>
                    </div>

                    {activeTab === 'details' && (
                        <div className="detail-card card animate-fadeInUp">
                            {/* Purpose */}
                            {trip.purpose && (
                                <div className="detail-section">
                                    <h3 className="detail-section-title">
                                        <FileText size={18} />
                                        Scopo della Trasferta
                                    </h3>
                                    <p className="detail-notes">{trip.purpose}</p>
                                </div>
                            )}

                            {/* Project Info */}
                            {(trip.project_code || trip.client_name) && (
                                <div className="detail-section">
                                    <h3 className="detail-section-title">
                                        <Building size={18} />
                                        Informazioni Progetto
                                    </h3>
                                    <div className="info-grid">
                                        {trip.project_code && (
                                            <div className="info-item">
                                                <span className="info-label">Codice Progetto</span>
                                                <span className="info-value">{trip.project_code}</span>
                                            </div>
                                        )}
                                        {trip.client_name && (
                                            <div className="info-item">
                                                <span className="info-label">Cliente</span>
                                                <span className="info-value">{trip.client_name}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Attachment */}
                            {trip.attachment_path && (
                                <div className="detail-section">
                                    <h3 className="detail-section-title">
                                        <FileText size={18} />
                                        Allegati
                                    </h3>
                                    <button className="btn btn-secondary">
                                        <Download size={16} />
                                        Scarica Documento
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'expenses' && (
                        <div className="detail-card card animate-fadeInUp">
                            <div className="empty-state">
                                <div className="empty-state-icon">
                                    <Receipt size={32} />
                                </div>
                                <h3 className="empty-state-title">Nessuna spesa registrata</h3>
                                <p className="empty-state-description">
                                    Le spese per questa trasferta appariranno qui una volta aggiunte alla nota spese.
                                </p>
                                <Link to="/expenses/new" className="btn btn-primary">
                                    <Plus size={18} />
                                    Crea Nota Spese
                                </Link>
                            </div>
                        </div>
                    )}

                    {activeTab === 'allowances' && (
                        <div className="detail-card card animate-fadeInUp">
                            <div className="empty-state">
                                <div className="empty-state-icon">
                                    <DollarSign size={32} />
                                </div>
                                <h3 className="empty-state-title">Diarie non calcolate</h3>
                                <p className="empty-state-description">
                                    Le diarie verranno calcolate automaticamente al completamento della trasferta.
                                </p>
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
                            {trip.status === 'draft' && (
                                <>
                                    <button
                                        className="btn btn-primary btn-lg"
                                        style={{ width: '100%' }}
                                        onClick={handleSubmit}
                                        disabled={actionLoading !== null}
                                    >
                                        {actionLoading === 'submit' ? <Loader size={18} className="animate-spin" /> : <Send size={18} />}
                                        Invia per Approvazione
                                    </button>
                                    <Link to={`/trips/${id}/edit`} className="btn btn-secondary" style={{ width: '100%' }}>
                                        <Edit size={18} />
                                        Modifica
                                    </Link>
                                </>
                            )}
                            {(trip.status === 'submitted' || trip.status === 'pending') && isApprover && (
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
                            {trip.status === 'approved' && (
                                <>
                                    <Link to={`/expenses/new?trip_id=${id}`} className="btn btn-primary btn-lg" style={{ width: '100%' }}>
                                        <Receipt size={18} />
                                        Crea Nota Spese
                                    </Link>
                                    <button
                                        className="btn btn-secondary"
                                        style={{ width: '100%' }}
                                        onClick={handleComplete}
                                        disabled={actionLoading !== null}
                                    >
                                        {actionLoading === 'complete' ? <Loader size={18} className="animate-spin" /> : <CheckCircle size={18} />}
                                        Completa Trasferta
                                    </button>
                                </>
                            )}
                            {(trip.status === 'completed' || trip.status === 'rejected' || trip.status === 'cancelled') && (
                                <p className="text-muted text-sm" style={{ textAlign: 'center' }}>
                                    Nessuna azione disponibile per questa trasferta.
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Summary Card */}
                    <div className="card">
                        <h3 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>Riepilogo</h3>
                        <div className="summary-list">
                            <div className="summary-item">
                                <span className="summary-label">Destinazione</span>
                                <span className="summary-value">{trip.destination}</span>
                            </div>
                            <div className="summary-item">
                                <span className="summary-label">Tipo</span>
                                <span className="summary-value">{getDestinationLabel(trip.destination_type)}</span>
                            </div>
                            <div className="summary-item">
                                <span className="summary-label">Durata</span>
                                <span className="summary-value font-semibold">{tripDays} giorni</span>
                            </div>
                            {trip.estimated_budget && (
                                <div className="summary-item">
                                    <span className="summary-label">Budget</span>
                                    <span className="summary-value font-semibold">€{Number(trip.estimated_budget).toFixed(2)}</span>
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
                            <h3>Rifiuta Trasferta</h3>
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

        .trip-hero {
          padding: var(--space-6);
        }

        .trip-hero-content {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--space-6);
        }

        .trip-hero-destination {
          display: flex;
          align-items: center;
          gap: var(--space-4);
        }

        .destination-icon {
          width: 56px;
          height: 56px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
          border-radius: var(--radius-xl);
          color: white;
        }

        .trip-hero-destination h2 {
          font-size: var(--font-size-xl);
          margin-bottom: var(--space-1);
        }

        .destination-type {
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
        }

        .trip-hero-stats {
          display: flex;
          gap: var(--space-6);
        }

        .hero-stat {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          color: var(--color-primary);
        }

        .hero-stat > div {
          display: flex;
          flex-direction: column;
        }

        .hero-stat-value {
          font-size: var(--font-size-xl);
          font-weight: var(--font-weight-bold);
          color: var(--color-text-primary);
        }

        .hero-stat-label {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .trip-hero-dates {
          display: flex;
          align-items: center;
          gap: var(--space-6);
          padding-top: var(--space-4);
          border-top: 1px solid var(--color-border-light);
        }

        .hero-date {
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
        }

        .hero-date-label {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .hero-date-value {
          font-weight: var(--font-weight-semibold);
          color: var(--color-text-primary);
        }

        .hero-date-arrow {
          font-size: var(--font-size-xl);
          color: var(--color-primary);
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

        .detail-notes {
          color: var(--color-text-secondary);
          line-height: var(--line-height-relaxed);
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: var(--space-4);
        }

        .info-item {
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
        }

        .info-label {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .info-value {
          font-weight: var(--font-weight-medium);
          color: var(--color-text-primary);
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

export default TripDetailPage;
