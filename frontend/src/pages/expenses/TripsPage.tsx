/**
 * KRONOS - Business Trips Page
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTrips } from '../../hooks/useApi';
import { Plus, MapPin, Calendar, FileText, Filter, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

export function TripsPage() {
    const [statusFilter, setStatusFilter] = useState<string>('');
    const { data: trips, isLoading, error } = useTrips(statusFilter || undefined);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner-lg" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-red-500">
                <AlertCircle size={48} className="mb-4" />
                <p>Errore nel caricamento delle trasferte</p>
            </div>
        );
    }

    return (
        <div className="trips-page animate-fadeIn">
            {/* Header */}
            <div className="page-header">
                <div>
                    <h1>Mie Trasferte</h1>
                    <p className="page-subtitle">Gestisci le tue missioni e trasferte</p>
                </div>
                <Link to="/trips/new" className="btn btn-primary">
                    <Plus size={18} />
                    Nuova Trasferta
                </Link>
            </div>

            {/* Filters */}
            <div className="filters-bar">
                <div className="filter-group">
                    <Filter size={16} className="text-gray-500" />
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="form-select"
                    >
                        <option value="">Tutti gli stati</option>
                        <option value="draft">Bozza</option>
                        <option value="submitted">Inviata</option>
                        <option value="approved">Approvata</option>
                        <option value="rejected">Rifiutata</option>
                        <option value="completed">Completata</option>
                    </select>
                </div>
            </div>

            {/* List */}
            <div className="trips-grid">
                {trips?.map((trip) => (
                    <Link key={trip.id} to={`/trips/${trip.id}`} className="trip-card">
                        <div className="trip-status-stripe" data-status={trip.status} />
                        <div className="trip-content">
                            <div className="trip-header">
                                <h3 className="trip-destination">
                                    <MapPin size={18} className="text-primary" />
                                    {trip.destination}
                                </h3>
                                <span className={`badge badge-${getStatusColor(trip.status)}`}>
                                    {getStatusLabel(trip.status)}
                                </span>
                            </div>

                            <p className="trip-purpose">{trip.purpose}</p>

                            <div className="trip-details">
                                <div className="trip-detail">
                                    <Calendar size={16} />
                                    <span>
                                        {format(new Date(trip.start_date), 'd MMM', { locale: it })} -{' '}
                                        {format(new Date(trip.end_date), 'd MMM yyyy', { locale: it })}
                                    </span>
                                </div>
                                {trip.estimated_budget && (
                                    <div className="trip-detail">
                                        <FileText size={16} />
                                        <span>€ {Number(trip.estimated_budget).toFixed(2)} previsti</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </Link>
                ))}

                {(!trips || trips.length === 0) && (
                    <div className="empty-state">
                        <MapPin size={48} />
                        <h3>Nessuna trasferta trovata</h3>
                        <p>Non ci sono trasferte corrispondenti ai criteri di ricerca.</p>
                        <Link to="/trips/new" className="btn btn-primary mt-4">
                            Crea Trasferta
                        </Link>
                    </div>
                )}
            </div>

            <style>{`
                .trips-page {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-6);
                }

                .page-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .page-header h1 {
                    font-size: var(--font-size-2xl);
                    margin-bottom: var(--space-1);
                }
                .page-subtitle {
                    color: var(--color-text-muted);
                }

                .filters-bar {
                    display: flex;
                    gap: var(--space-4);
                    padding: var(--space-4);
                    background: var(--glass-bg);
                    border: 1px solid var(--glass-border);
                    border-radius: var(--radius-lg);
                }

                .filter-group {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                }

                .form-select {
                    padding: var(--space-2) var(--space-8) var(--space-2) var(--space-3);
                    border-radius: var(--radius-md);
                    border: 1px solid var(--color-border-light);
                    background-color: var(--color-bg-primary);
                    font-size: var(--font-size-sm);
                }

                .trips-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: var(--space-4);
                }

                .trip-card {
                    position: relative;
                    background: var(--glass-bg);
                    border: 1px solid var(--glass-border);
                    border-radius: var(--radius-lg);
                    overflow: hidden;
                    text-decoration: none;
                    color: inherit;
                    transition: all var(--transition-fast);
                    display: flex;
                }

                .trip-card:hover {
                    border-color: var(--color-primary);
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                }

                .trip-status-stripe {
                    width: 6px;
                    background-color: var(--color-text-muted);
                }
                .trip-status-stripe[data-status="approved"] { background-color: var(--color-success); }
                .trip-status-stripe[data-status="pending"] { background-color: var(--color-warning); }
                .trip-status-stripe[data-status="rejected"] { background-color: var(--color-danger); }
                .trip-status-stripe[data-status="completed"] { background-color: var(--color-info); }

                .trip-content {
                    flex: 1;
                    padding: var(--space-4);
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-3);
                }

                .trip-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    gap: var(--space-2);
                }

                .trip-destination {
                    font-size: var(--font-size-lg);
                    font-weight: var(--font-weight-bold);
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                }

                .trip-purpose {
                    font-size: var(--font-size-sm);
                    color: var(--color-text-secondary);
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }

                .trip-details {
                    margin-top: auto;
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-2);
                    padding-top: var(--space-3);
                    border-top: 1px solid var(--color-border-light);
                }

                .trip-detail {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    font-size: var(--font-size-xs);
                    color: var(--color-text-muted);
                }

                .empty-state {
                    grid-column: 1 / -1;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: var(--space-12);
                    text-align: center;
                    color: var(--color-text-muted);
                    background: var(--glass-bg);
                    border-radius: var(--radius-lg);
                    border: 1px dashed var(--color-border-light);
                }
                .empty-state h3 {
                    margin-top: var(--space-4);
                    font-size: var(--font-size-lg);
                    color: var(--color-text-primary);
                }
            `}</style>
        </div>
    );
}

function getStatusColor(status: string): string {
    const colors: Record<string, string> = {
        draft: 'neutral',
        submitted: 'warning',
        approved: 'success',
        rejected: 'danger',
        completed: 'info',
        cancelled: 'neutral',
    };
    return colors[status] || 'neutral';
}

function getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
        draft: 'Bozza',
        submitted: 'In Approvazione',
        approved: 'Approvata',
        rejected: 'Rifiutata',
        completed: 'Completata',
        cancelled: 'Annullata',
    };
    return labels[status] || status;
}

export default TripsPage;
