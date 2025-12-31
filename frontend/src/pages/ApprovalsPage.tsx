/**
 * KRONOS - Approvals Management Page
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { Calendar, MapPin, FileText, Clock } from 'lucide-react';
import { usePendingApprovals, usePendingTrips, usePendingReports } from '../hooks/useApi';
import type { LeaveRequest, BusinessTrip, ExpenseReport } from '../types';

type TabType = 'leaves' | 'trips' | 'expenses';

export function ApprovalsPage() {
    const [activeTab, setActiveTab] = useState<TabType>('leaves');

    // Fetch data
    const { data: pendingLeaves, isLoading: loadingLeaves } = usePendingApprovals();
    const { data: pendingTrips, isLoading: loadingTrips } = usePendingTrips();
    const { data: pendingReports, isLoading: loadingReports } = usePendingReports();

    // Calculate counts
    const leavesCount = pendingLeaves?.length || 0;
    const tripsCount = pendingTrips?.length || 0;
    const reportsCount = pendingReports?.length || 0;

    return (
        <div className="approvals-page animate-fadeIn">
            <div className="page-header">
                <div>
                    <h1>Approvazioni</h1>
                    <p className="page-subtitle">Gestisci le richieste in attesa</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs">
                <button
                    className={`tab-btn ${activeTab === 'leaves' ? 'active' : ''}`}
                    onClick={() => setActiveTab('leaves')}
                >
                    <Calendar size={18} />
                    Ferie e Permessi
                    {leavesCount > 0 && <span className="badge badge-warning ml-2">{leavesCount}</span>}
                </button>
                <button
                    className={`tab-btn ${activeTab === 'trips' ? 'active' : ''}`}
                    onClick={() => setActiveTab('trips')}
                >
                    <MapPin size={18} />
                    Trasferte
                    {tripsCount > 0 && <span className="badge badge-warning ml-2">{tripsCount}</span>}
                </button>
                <button
                    className={`tab-btn ${activeTab === 'expenses' ? 'active' : ''}`}
                    onClick={() => setActiveTab('expenses')}
                >
                    <FileText size={18} />
                    Note Spese
                    {reportsCount > 0 && <span className="badge badge-warning ml-2">{reportsCount}</span>}
                </button>
            </div>

            {/* Content */}
            <div className="tab-content">
                {activeTab === 'leaves' && (
                    <LeavesApprovalsList requests={pendingLeaves} isLoading={loadingLeaves} />
                )}
                {activeTab === 'trips' && (
                    <TripsApprovalsList trips={pendingTrips} isLoading={loadingTrips} />
                )}
                {activeTab === 'expenses' && (
                    <ReportsApprovalsList reports={pendingReports} isLoading={loadingReports} />
                )}
            </div>

            <style>{`
                .approvals-page {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-6);
                }
                .page-header h1 {
                    font-size: var(--font-size-2xl);
                    margin-bottom: var(--space-1);
                }
                .page-subtitle {
                    color: var(--color-text-muted);
                }

                .tabs {
                    display: flex;
                    gap: var(--space-2);
                    border-bottom: 1px solid var(--color-border-light);
                    padding-bottom: var(--space-1);
                }

                .tab-btn {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    padding: var(--space-3) var(--space-4);
                    background: transparent;
                    border: none;
                    border-bottom: 2px solid transparent;
                    color: var(--color-text-secondary);
                    font-weight: var(--font-weight-medium);
                    cursor: pointer;
                    transition: all var(--transition-fast);
                }

                .tab-btn:hover {
                    color: var(--color-primary);
                    background: var(--color-bg-hover);
                    border-radius: var(--radius-md) var(--radius-md) 0 0;
                }

                .tab-btn.active {
                    color: var(--color-primary);
                    border-bottom-color: var(--color-primary);
                }

                .approvals-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-4);
                }

                .approval-card {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: var(--glass-bg);
                    border: 1px solid var(--glass-border);
                    border-radius: var(--radius-lg);
                    padding: var(--space-4);
                    transition: all var(--transition-fast);
                }

                .approval-card:hover {
                    border-color: var(--color-primary);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                }

                .approval-info {
                    flex: 1;
                }

                .approval-header {
                    display: flex;
                    align-items: center;
                    gap: var(--space-3);
                    margin-bottom: var(--space-2);
                }

                .approval-title {
                    font-weight: var(--font-weight-bold);
                    font-size: var(--font-size-lg);
                }

                .approval-user {
                    font-size: var(--font-size-sm);
                    color: var(--color-text-secondary);
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                }

                .approval-meta {
                    display: flex;
                    gap: var(--space-4);
                    font-size: var(--font-size-sm);
                    color: var(--color-text-muted);
                    margin-top: var(--space-2);
                }

                .approval-actions {
                    display: flex;
                    gap: var(--space-2);
                }

                .empty-state {
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
            `}</style>
        </div>
    );
}

// Sub-components for lists
function LeavesApprovalsList({ requests, isLoading }: { requests: LeaveRequest[] | undefined; isLoading: boolean }) {
    if (isLoading) return <div className="spinner-lg mx-auto" />;

    const list = requests || [];
    if (list.length === 0) return <EmptyState label="Nessuna richiesta ferie in attesa" icon={Calendar} />;

    return (
        <div className="approvals-list">
            {list.map((req) => (
                <div key={req.id} className="approval-card">
                    <div className="approval-info">
                        <div className="approval-header">
                            <span className="approval-title">{req.leave_type_code}</span>
                            <span className="badge badge-warning">In attesa</span>
                        </div>
                        <div className="approval-user">
                            Richiesto da: {req.user_id}
                        </div>
                        <div className="approval-meta">
                            <span>
                                <Calendar size={14} className="inline mr-1" />
                                {format(new Date(req.start_date), 'd MMM', { locale: it })} -{' '}
                                {format(new Date(req.end_date), 'd MMM yyyy', { locale: it })}
                            </span>
                            <span>{req.days_requested} giorni</span>
                        </div>
                    </div>
                    <div className="approval-actions">
                        <Link to={`/leaves/${req.id}`} className="btn btn-secondary btn-sm">
                            Vedi Dettagli
                        </Link>
                    </div>
                </div>
            ))}
        </div>
    );
}

function TripsApprovalsList({ trips, isLoading }: { trips: BusinessTrip[] | undefined; isLoading: boolean }) {
    if (isLoading) return <div className="spinner-lg mx-auto" />;

    const list = trips || [];
    if (list.length === 0) return <EmptyState label="Nessuna trasferta in attesa" icon={MapPin} />;

    return (
        <div className="approvals-list">
            {list.map((trip) => (
                <div key={trip.id} className="approval-card">
                    <div className="approval-info">
                        <div className="approval-header">
                            <span className="approval-title">{trip.destination}</span>
                            <span className="badge badge-warning">In attesa</span>
                        </div>
                        <div className="approval-meta">
                            <span>
                                <Calendar size={14} className="inline mr-1" />
                                {format(new Date(trip.start_date), 'd MMM', { locale: it })} -{' '}
                                {format(new Date(trip.end_date), 'd MMM yyyy', { locale: it })}
                            </span>
                            <span>{trip.purpose}</span>
                        </div>
                        {trip.estimated_budget && (
                            <div className="mt-2 text-sm font-medium">
                                Costo stimato: € {trip.estimated_budget}
                            </div>
                        )}
                    </div>
                    <div className="approval-actions">
                        <Link to={`/trips/${trip.id}`} className="btn btn-secondary btn-sm">
                            Vedi Dettagli
                        </Link>
                    </div>
                </div>
            ))}
        </div>
    );
}

function ReportsApprovalsList({ reports, isLoading }: { reports: ExpenseReport[] | undefined; isLoading: boolean }) {
    if (isLoading) return <div className="spinner-lg mx-auto" />;

    const list = reports || [];
    if (list.length === 0) return <EmptyState label="Nessuna nota spese in attesa" icon={FileText} />;

    return (
        <div className="approvals-list">
            {list.map((report) => (
                <div key={report.id} className="approval-card">
                    <div className="approval-info">
                        <div className="approval-header">
                            <span className="approval-title">{report.title}</span>
                            <span className="badge badge-warning">In attesa</span>
                        </div>
                        <div className="approval-meta">
                            <span>
                                <Clock size={14} className="inline mr-1" />
                                Creata il {format(new Date(report.created_at), 'd MMM yyyy', { locale: it })}
                            </span>
                        </div>
                        <div className="mt-2 text-sm font-bold text-primary">
                            Totale: € {report.total_amount.toFixed(2)}
                        </div>
                    </div>
                    <div className="approval-actions">
                        <Link to={`/expenses/${report.id}`} className="btn btn-secondary btn-sm">
                            Vedi Dettagli
                        </Link>
                    </div>
                </div>
            ))}
        </div>
    );
}

function EmptyState({ label, icon: Icon }: { label: string; icon: any }) {
    return (
        <div className="empty-state">
            <Icon size={48} className="mb-4 text-gray-400" />
            <h3>{label}</h3>
            <p className="text-gray-500">Non ci sono elementi da approvare al momento.</p>
        </div>
    );
}

export default ApprovalsPage;
