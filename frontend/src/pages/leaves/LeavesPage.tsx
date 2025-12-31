/**
 * KRONOS - Leaves Calendar Page
 */
import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import { Plus, Filter, Calendar as CalendarIcon } from 'lucide-react';
import { useCalendarEvents, useLeaveRequests, useBalanceSummary } from '../../hooks/useApi';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/common';
import { format, startOfMonth, endOfMonth, addMonths, subMonths } from 'date-fns';
import { it } from 'date-fns/locale';

export function LeavesPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [showTeam, setShowTeam] = useState(false);
  const { isApprover } = useAuth();

  const startDate = format(startOfMonth(subMonths(currentDate, 1)), 'yyyy-MM-dd');
  const endDate = format(endOfMonth(addMonths(currentDate, 2)), 'yyyy-MM-dd');

  const { data: calendarData } = useCalendarEvents(startDate, endDate, showTeam);
  const { data: balance } = useBalanceSummary();
  const { data: requests } = useLeaveRequests(currentDate.getFullYear());

  const events = useMemo(() => {
    if (!calendarData) return [];

    const leaveEvents = (calendarData.events || []).map(event => ({
      ...event,
      allDay: true,
      classNames: [`event-${event.extendedProps?.status || 'default'}`],
    }));

    const holidayEvents = (calendarData.holidays || []).map(holiday => ({
      id: `holiday-${holiday.id}`,
      title: holiday.title,
      start: holiday.start,
      allDay: true,
      display: 'background',
      backgroundColor: 'rgba(239, 68, 68, 0.1)',
      classNames: ['holiday-event'],
    }));

    return [...leaveEvents, ...holidayEvents];
  }, [calendarData]);

  const pendingCount = requests?.filter(r => r.status === 'pending').length || 0;

  return (
    <div className="leaves-page animate-fadeIn">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Calendario Assenze</h1>
        <Button
          as={Link}
          to="/leaves/new"
          variant="primary"
          icon={<Plus size={18} />}
        >
          Nuova Richiesta
        </Button>
      </div>

      {/* Balance Summary */}
      <div className="balance-cards">
        <div className="balance-card">
          <div className="balance-label">Ferie AP (Anno Prec.)</div>
          <div className="balance-value">
            {balance?.vacation_available_ap ?? '-'}
            <span className="balance-unit">gg</span>
          </div>
          {balance?.ap_expiry_date && (
            <div className="balance-expiry">
              Scadenza: {new Date(balance.ap_expiry_date).toLocaleDateString('it-IT')}
            </div>
          )}
        </div>
        <div className="balance-card">
          <div className="balance-label">Ferie AC (Anno Corr.)</div>
          <div className="balance-value">
            {balance?.vacation_available_ac ?? '-'}
            <span className="balance-unit">gg</span>
          </div>
        </div>
        <div className="balance-card">
          <div className="balance-label">ROL Disponibili</div>
          <div className="balance-value">
            {balance?.rol_available ?? '-'}
            <span className="balance-unit">ore</span>
          </div>
        </div>
        <div className="balance-card">
          <div className="balance-label">Permessi</div>
          <div className="balance-value">
            {balance?.permits_available ?? '-'}
            <span className="balance-unit">ore</span>
          </div>
        </div>
      </div>

      {/* Calendar & List */}
      <div className="leaves-content">
        {/* Calendar */}
        <div className="calendar-section card">
          <div className="calendar-header">
            <h2 className="card-title">
              <CalendarIcon size={20} />
              Calendario
            </h2>
            {isApprover && (
              <button
                className={`btn btn-sm ${showTeam ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setShowTeam(!showTeam)}
              >
                <Filter size={14} />
                {showTeam ? 'Solo Mie' : 'Mostra Team'}
              </button>
            )}
          </div>

          <div className="calendar-wrapper">
            <FullCalendar
              plugins={[dayGridPlugin, interactionPlugin]}
              initialView="dayGridMonth"
              locale="it"
              headerToolbar={{
                left: 'prev,next today',
                center: 'title',
                right: '',
              }}
              events={events}
              eventClick={(info) => {
                // Navigate to request detail
                if (!info.event.id.startsWith('holiday-')) {
                  window.location.href = `/leaves/${info.event.id}`;
                }
              }}
              dateClick={(info) => {
                // Quick create from date click
                window.location.href = `/leaves/new?date=${info.dateStr}`;
              }}
              datesSet={(dateInfo) => {
                setCurrentDate(dateInfo.view.currentStart);
              }}
              height="auto"
              dayMaxEvents={3}
              weekends={true}
              firstDay={1}
              buttonText={{
                today: 'Oggi',
              }}
            />
          </div>
        </div>

        {/* Requests List */}
        <div className="requests-section card">
          <div className="card-header">
            <h2 className="card-title">
              Richieste {currentDate.getFullYear()}
              {pendingCount > 0 && (
                <span className="badge badge-warning">{pendingCount} in attesa</span>
              )}
            </h2>
          </div>

          <div className="requests-list">
            {requests?.map((request) => (
              <Link
                key={request.id}
                to={`/leaves/${request.id}`}
                className="request-item"
              >
                <div className={`request-status badge badge-${getStatusBadge(request.status)}`}>
                  {getStatusLabel(request.status)}
                </div>
                <div className="request-info">
                  <div className="request-type">{request.leave_type_code}</div>
                  <div className="request-dates">
                    {formatDateRange(request.start_date, request.end_date)}
                  </div>
                </div>
                <div className="request-days">{request.days_requested} gg</div>
              </Link>
            ))}

            {(!requests || requests.length === 0) && (
              <div className="empty-state">
                <CalendarIcon size={48} />
                <h3 className="empty-state-title">Nessuna richiesta</h3>
                <p className="empty-state-description">
                  Non hai ancora effettuato richieste per il {currentDate.getFullYear()}
                </p>
                <Link to="/leaves/new" className="btn btn-primary">
                  Crea la prima richiesta
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        .leaves-page {
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
          font-size: var(--font-size-sm);
        }

        .balance-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: var(--space-4);
        }

        .balance-card {
          background: var(--glass-bg);
          backdrop-filter: blur(var(--glass-blur));
          border: 1px solid var(--glass-border);
          border-radius: var(--radius-lg);
          padding: var(--space-4);
          text-align: center;
        }

        .balance-label {
          font-size: var(--font-size-xs);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--color-text-muted);
          margin-bottom: var(--space-2);
        }

        .balance-value {
          font-size: var(--font-size-2xl);
          font-weight: var(--font-weight-bold);
          color: var(--color-text-primary);
        }

        .balance-unit {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-normal);
          color: var(--color-text-muted);
          margin-left: var(--space-1);
        }

        .balance-expiry {
          font-size: var(--font-size-xs);
          color: var(--color-warning);
          margin-top: var(--space-1);
        }

        .leaves-content {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: var(--space-6);
        }

        @media (max-width: 1024px) {
          .leaves-content {
            grid-template-columns: 1fr;
          }
        }

        .calendar-section {
          padding: var(--space-4);
        }

        .calendar-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--space-4);
        }

        .calendar-header .card-title {
          display: flex;
          align-items: center;
          gap: var(--space-2);
        }

        .calendar-wrapper {
          border-radius: var(--radius-lg);
          overflow: hidden;
        }

        .requests-section {
          max-height: 600px;
          display: flex;
          flex-direction: column;
        }

        .requests-list {
          flex: 1;
          overflow-y: auto;
        }

        .request-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          border-bottom: 1px solid var(--color-border-light);
          text-decoration: none;
          transition: all var(--transition-fast);
        }

        .request-item:hover {
          background: var(--color-bg-hover);
        }

        .request-item:last-child {
          border-bottom: none;
        }

        .request-info {
          flex: 1;
        }

        .request-type {
          font-weight: var(--font-weight-semibold);
          color: var(--color-text-primary);
        }

        .request-dates {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .request-days {
          font-weight: var(--font-weight-semibold);
          color: var(--color-text-secondary);
        }

        /* FullCalendar event styles */
        .event-approved {
          background-color: var(--color-success) !important;
          border: none !important;
        }

        .event-pending {
          background-color: var(--color-warning) !important;
          border: none !important;
        }

        .event-rejected {
          background-color: var(--color-danger) !important;
          border: none !important;
        }

        .holiday-event {
          pointer-events: none;
        }
      `}</style>
    </div>
  );
}

// Helper functions
function getStatusBadge(status: string): string {
  const map: Record<string, string> = {
    draft: 'neutral',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    cancelled: 'neutral',
    approved_conditional: 'info',
    recalled: 'danger',
  };
  return map[status] || 'neutral';
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: 'Bozza',
    pending: 'In Attesa',
    approved: 'Approvata',
    rejected: 'Rifiutata',
    cancelled: 'Annullata',
    approved_conditional: 'Condizionale',
    recalled: 'Richiamato',
  };
  return map[status] || status;
}

function formatDateRange(start: string, end: string): string {
  const startDate = new Date(start);
  const endDate = new Date(end);

  if (start === end) {
    return format(startDate, 'd MMM yyyy', { locale: it });
  }

  return `${format(startDate, 'd MMM', { locale: it })} - ${format(endDate, 'd MMM yyyy', { locale: it })}`;
}

export default LeavesPage;
