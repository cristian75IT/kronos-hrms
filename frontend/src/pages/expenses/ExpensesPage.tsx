/**
 * KRONOS - Expense Reports Page
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useExpenseReports } from '../../hooks/useApi';
import { Plus, FileText, Calendar, Filter, AlertCircle, DollarSign } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

export function ExpensesPage() {
    const [statusFilter, setStatusFilter] = useState<string>('');
    const { data: reports, isLoading, error } = useExpenseReports(statusFilter || undefined);

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
                <p>Errore nel caricamento delle note spese</p>
            </div>
        );
    }

    return (
        <div className="expenses-page animate-fadeIn">
            {/* Header */}
            <div className="page-header">
                <div>
                    <h1>Note Spese</h1>
                    <p className="page-subtitle">Gestisci le richieste di rimborso spese</p>
                </div>
                <Link to="/expenses/new" className="btn btn-primary">
                    <Plus size={18} />
                    Nuova Nota Spese
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
                        <option value="paid">Pagata</option>
                    </select>
                </div>
            </div>

            {/* List */}
            <div className="expenses-grid">
                {reports?.map((report) => (
                    <Link key={report.id} to={`/expenses/${report.id}`} className="expense-card">
                        <div className="expense-status-stripe" data-status={report.status} />
                        <div className="expense-content">
                            <div className="expense-header">
                                <h3 className="expense-title">
                                    <FileText size={18} className="text-primary" />
                                    {report.title}
                                </h3>
                                <span className={`badge badge-${getStatusColor(report.status)}`}>
                                    {getStatusLabel(report.status)}
                                </span>
                            </div>

                            <p className="expense-description">{report.employee_notes || 'Nessuna descrizione'}</p>

                            <div className="expense-details">
                                <div className="expense-detail">
                                    <Calendar size={16} />
                                    <span>
                                        Creata il {format(new Date(report.created_at), 'd MMM yyyy', { locale: it })}
                                    </span>
                                </div>
                                <div className="expense-detail highlight">
                                    <DollarSign size={16} />
                                    <span>€ {report.total_amount.toFixed(2)}</span>
                                </div>
                            </div>
                        </div>
                    </Link>
                ))}

                {(!reports || reports.length === 0) && (
                    <div className="empty-state">
                        <FileText size={48} />
                        <h3>Nessuna nota spese trovata</h3>
                        <p>Non ci sono note spese corrispondenti ai criteri di ricerca.</p>
                        <Link to="/expenses/new" className="btn btn-primary mt-4">
                            Crea Nota Spese
                        </Link>
                    </div>
                )}
            </div>

            <style>{`
                .expenses-page {
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

                .expenses-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: var(--space-4);
                }

                .expense-card {
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

                .expense-card:hover {
                    border-color: var(--color-primary);
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                }

                .expense-status-stripe {
                    width: 6px;
                    background-color: var(--color-text-muted);
                }
                .expense-status-stripe[data-status="approved"] { background-color: var(--color-success); }
                .expense-status-stripe[data-status="submitted"] { background-color: var(--color-warning); }
                .expense-status-stripe[data-status="rejected"] { background-color: var(--color-danger); }
                .expense-status-stripe[data-status="paid"] { background-color: var(--color-info); }

                .expense-content {
                    flex: 1;
                    padding: var(--space-4);
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-3);
                }

                .expense-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    gap: var(--space-2);
                }

                .expense-title {
                    font-size: var(--font-size-lg);
                    font-weight: var(--font-weight-bold);
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                }

                .expense-description {
                    font-size: var(--font-size-sm);
                    color: var(--color-text-secondary);
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }

                .expense-details {
                    margin-top: auto;
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-2);
                    padding-top: var(--space-3);
                    border-top: 1px solid var(--color-border-light);
                }

                .expense-detail {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    font-size: var(--font-size-xs);
                    color: var(--color-text-muted);
                }

                .expense-detail.highlight {
                    color: var(--color-text-primary);
                    font-weight: var(--font-weight-bold);
                    font-size: var(--font-size-sm);
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
        paid: 'info',
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
        paid: 'Pagata',
        cancelled: 'Annullata',
    };
    return labels[status] || status;
}

export default ExpensesPage;
