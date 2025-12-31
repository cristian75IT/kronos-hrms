/**
 * KRONOS - Dashboard Page
 */
import {
  Calendar,
  Clock,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Briefcase,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useBalanceSummary, usePendingApprovals, useLeaveRequests } from '../hooks/useApi';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common';
import type { LeaveRequest } from '../types';

export function DashboardPage() {
  const { user, isApprover } = useAuth();
  const { data: balance, isLoading: balanceLoading } = useBalanceSummary();
  const { data: pendingApprovals } = usePendingApprovals();
  const { data: recentRequests } = useLeaveRequests(new Date().getFullYear());

  const stats = [
    {
      label: 'Ferie Disponibili',
      value: balance?.vacation_total_available ?? '-',
      suffix: 'giorni',
      icon: <Calendar size={24} />,
      color: 'var(--color-success)',
      gradient: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
    },
    {
      label: 'ROL Disponibili',
      value: balance?.rol_available ?? '-',
      suffix: 'ore',
      icon: <Clock size={24} />,
      color: 'var(--color-info)',
      gradient: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
    },
    {
      label: 'Permessi Disponibili',
      value: balance?.permits_available ?? '-',
      suffix: 'ore',
      icon: <TrendingUp size={24} />,
      color: 'var(--color-secondary)',
      gradient: 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
    },
    {
      label: isApprover ? 'Da Approvare' : 'In Attesa',
      value: isApprover ? (pendingApprovals?.length ?? 0) : (recentRequests?.filter((r: LeaveRequest) => r.status === 'pending').length ?? 0),
      suffix: 'richieste',
      icon: <AlertCircle size={24} />,
      color: 'var(--color-warning)',
      gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    },
  ];

  const quickActions = [
    {
      label: 'Richiedi Ferie',
      description: 'Nuova richiesta ferie o permessi',
      path: '/leaves/new',
      icon: <Calendar size={20} />,
    },
    {
      label: 'Nuova Trasferta',
      description: 'Pianifica una trasferta di lavoro',
      path: '/trips/new',
      icon: <Briefcase size={20} />,
    },
  ];

  return (
    <div className="dashboard animate-fadeIn">
      {/* Welcome Section */}
      <section className="dashboard-welcome">
        <div className="welcome-content">
          <h1>Benvenuto, {user?.first_name}!</h1>
          <p>Ecco il riepilogo della tua situazione</p>
        </div>
        <div className="welcome-date">
          {new Date().toLocaleDateString('it-IT', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </div>
      </section>

      {/* Stats Grid */}
      <section className="dashboard-stats">
        {stats.map((stat, index) => (
          <div
            key={index}
            className="stat-card glass-card animate-slideUp"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="stat-icon" style={{ background: stat.gradient }}>
              {stat.icon}
            </div>
            <div className="stat-content">
              <div className="stat-value">
                {balanceLoading ? (
                  <div className="skeleton" style={{ width: 60, height: 32 }} />
                ) : (
                  <>
                    {typeof stat.value === 'number' || typeof stat.value === 'string'
                      ? stat.value
                      : '-'}
                    <span className="stat-suffix">{stat.suffix}</span>
                  </>
                )}
              </div>
              <div className="stat-label">{stat.label}</div>
            </div>
          </div>
        ))}
      </section>

      {/* AP Expiry Warning */}
      {balance?.days_until_ap_expiry && balance.days_until_ap_expiry <= 60 && (
        <section className="ap-warning glass-card">
          <AlertCircle size={20} />
          <div>
            <strong>Attenzione:</strong> Hai {balance.vacation_available_ap} giorni di ferie dell'anno precedente
            che scadranno tra {balance.days_until_ap_expiry} giorni ({balance.ap_expiry_date}).
          </div>
          <Button as={Link} to="/leaves/new" variant="primary" size="sm">
            Pianifica ora
          </Button>
        </section>
      )}

      {/* Quick Actions & Recent Activity */}
      <div className="dashboard-grid">
        {/* Quick Actions */}
        <section className="card">
          <div className="card-header">
            <h2 className="card-title">Azioni Rapide</h2>
          </div>
          <div className="quick-actions-grid">
            {quickActions.map((action, index) => (
              <Button
                key={index}
                as={Link}
                to={action.path}
                variant="secondary"
                className="quick-action-btn"
                icon={action.icon}
              >
                {action.label}
              </Button>
            ))}
          </div>
        </section>

        {/* Recent Requests */}
        <section className="card">
          <div className="card-header">
            <h2 className="card-title">Richieste Recenti</h2>
            <Link to="/leaves" className="btn btn-ghost btn-sm">
              Vedi tutte
            </Link>
          </div>
          <div className="recent-list">
            {recentRequests?.slice(0, 5).map((request) => (
              <div key={request.id} className="recent-item">
                <div className={`recent-status status-${request.status}`}>
                  {request.status === 'approved' && <CheckCircle size={14} />}
                  {request.status === 'pending' && <Clock size={14} />}
                  {request.status === 'rejected' && <AlertCircle size={14} />}
                </div>
                <div className="recent-content">
                  <div className="recent-title">{request.leave_type_code}</div>
                  <div className="recent-dates">
                    {new Date(request.start_date).toLocaleDateString('it-IT')} -
                    {new Date(request.end_date).toLocaleDateString('it-IT')}
                  </div>
                </div>
                <div className="recent-days">{request.days_requested} gg</div>
              </div>
            ))}
            {(!recentRequests || recentRequests.length === 0) && (
              <div className="empty-state">
                <p>Nessuna richiesta recente</p>
              </div>
            )}
          </div>
        </section>
      </div>

      <style>{`
        .dashboard {
          display: flex;
          flex-direction: column;
          gap: var(--space-6);
        }

        .dashboard-welcome {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .welcome-content h1 {
          font-size: var(--font-size-3xl);
          margin-bottom: var(--space-1);
        }

        .welcome-content p {
          color: var(--color-text-muted);
        }

        .welcome-date {
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
          text-transform: capitalize;
        }

        .dashboard-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: var(--space-4);
        }

        .stat-card {
          display: flex;
          align-items: center;
          gap: var(--space-4);
          padding: var(--space-5);
        }

        .stat-icon {
          width: 56px;
          height: 56px;
          border-radius: var(--radius-lg);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          flex-shrink: 0;
        }

        .stat-value {
          font-size: var(--font-size-2xl);
          font-weight: var(--font-weight-bold);
          color: var(--color-text-primary);
        }

        .stat-suffix {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-normal);
          color: var(--color-text-muted);
          margin-left: var(--space-1);
        }

        .stat-label {
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
        }

        .ap-warning {
          display: flex;
          align-items: center;
          gap: var(--space-4);
          padding: var(--space-4);
          background: rgba(245, 158, 11, 0.1);
          border-color: var(--color-warning);
          color: var(--color-warning-dark);
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
          gap: var(--space-6);
        }

        .quick-actions {
          display: flex;
          flex-direction: column;
          gap: var(--space-3);
        }

        .quick-action-card {
          display: flex;
          align-items: center;
          gap: var(--space-4);
          padding: var(--space-4);
          background: var(--color-bg-secondary);
          border-radius: var(--radius-lg);
          text-decoration: none;
          transition: all var(--transition-fast);
        }

        .quick-action-card:hover {
          background: var(--color-bg-hover);
          transform: translateX(4px);
        }

        .quick-action-icon {
          width: 44px;
          height: 44px;
          border-radius: var(--radius-md);
          background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
        }

        .quick-action-content {
          flex: 1;
        }

        .quick-action-label {
          font-weight: var(--font-weight-semibold);
          color: var(--color-text-primary);
        }

        .quick-action-desc {
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
        }

        .quick-action-arrow {
          color: var(--color-text-muted);
        }

        .recent-list {
          display: flex;
          flex-direction: column;
        }

        .recent-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3) 0;
          border-bottom: 1px solid var(--color-border-light);
        }

        .recent-item:last-child {
          border-bottom: none;
        }

        .recent-status {
          width: 28px;
          height: 28px;
          border-radius: var(--radius-full);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .status-approved {
          background: rgba(34, 197, 94, 0.1);
          color: var(--color-success);
        }

        .status-pending {
          background: rgba(245, 158, 11, 0.1);
          color: var(--color-warning);
        }

        .status-rejected {
          background: rgba(239, 68, 68, 0.1);
          color: var(--color-danger);
        }

        .recent-content {
          flex: 1;
        }

        .recent-title {
          font-weight: var(--font-weight-medium);
          color: var(--color-text-primary);
        }

        .recent-dates {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .recent-days {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-semibold);
          color: var(--color-text-secondary);
        }
      `}</style>
    </div>
  );
}

export default DashboardPage;
