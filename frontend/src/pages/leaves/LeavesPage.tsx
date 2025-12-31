/**
 * KRONOS - Advanced Leaves Calendar Page
 * Enterprise-grade calendar with filters for holidays, closures, and team leaves
 */
import { useState, useMemo, useRef } from 'react';
import { Link } from 'react-router-dom';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import {
  Plus,
  Calendar as CalendarIcon,
  ChevronDown,
  Building,
  Flag,
  Users,
  Settings,
  X,
} from 'lucide-react';
import { useCalendarEvents, useLeaveRequests, useBalanceSummary } from '../../hooks/useApi';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/common';
import { format, startOfMonth, endOfMonth, addMonths, subMonths } from 'date-fns';
import { it } from 'date-fns/locale';
import type { CompanyClosure, CalendarEvent } from '../../types';

interface CalendarFilters {
  showNationalHolidays: boolean;
  showLocalHolidays: boolean;
  showCompanyClosures: boolean;
  showTeamLeaves: boolean;
  teamScope: 'department' | 'company';
}

type CalendarView = 'dayGridMonth' | 'timeGridWeek' | 'timeGridDay';

export function LeavesPage() {
  const calendarRef = useRef<FullCalendar>(null);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [currentView, setCurrentView] = useState<CalendarView>('dayGridMonth');
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [filters, setFilters] = useState<CalendarFilters>({
    showNationalHolidays: true,
    showLocalHolidays: true,
    showCompanyClosures: true,
    showTeamLeaves: false,
    teamScope: 'department',
  });
  useAuth();

  const startDate = format(startOfMonth(subMonths(currentDate, 1)), 'yyyy-MM-dd');
  const endDate = format(endOfMonth(addMonths(currentDate, 2)), 'yyyy-MM-dd');

  const { data: calendarData } = useCalendarEvents(startDate, endDate, filters.showTeamLeaves);
  const { data: balance } = useBalanceSummary();
  const { data: requests } = useLeaveRequests(currentDate.getFullYear());

  // Build calendar events based on filters
  const events = useMemo(() => {
    if (!calendarData) return [];

    const result: any[] = [];

    // Leave events (own)
    const leaveEvents = (calendarData.events || []).map(event => ({
      ...event,
      allDay: true,
      classNames: [`event-${event.extendedProps?.status || 'default'}`, 'leave-event'],
    }));
    result.push(...leaveEvents);

    // National & Local Holidays
    if (filters.showNationalHolidays || filters.showLocalHolidays) {
      const holidays = (calendarData.holidays || []).filter(h => {
        if (h.is_national && filters.showNationalHolidays) return true;
        if (!h.is_national && filters.showLocalHolidays) return true;
        return false;
      }).map(holiday => ({
        id: `holiday-${holiday.id}`,
        title: `🏛️ ${holiday.title}`,
        start: holiday.start,
        allDay: true,
        display: 'background',
        backgroundColor: holiday.is_national ? 'rgba(239, 68, 68, 0.15)' : 'rgba(249, 115, 22, 0.15)',
        classNames: ['holiday-event', holiday.is_national ? 'national' : 'local'],
        extendedProps: { type: 'holiday', isNational: holiday.is_national },
      }));
      result.push(...holidays);
    }

    // Company Closures
    if (filters.showCompanyClosures) {
      const closures = ((calendarData as any).closures || []).map((closure: CompanyClosure) => ({
        id: `closure-${closure.id}`,
        title: `🏢 ${closure.name}`,
        start: closure.start_date,
        end: closure.end_date,
        allDay: true,
        display: 'background',
        backgroundColor: closure.closure_type === 'total'
          ? 'rgba(147, 51, 234, 0.15)'
          : 'rgba(147, 51, 234, 0.08)',
        classNames: ['closure-event', closure.closure_type],
        extendedProps: { type: 'closure', closureType: closure.closure_type },
      }));
      result.push(...closures);
    }

    // Team leaves (if showing)
    if (filters.showTeamLeaves && (calendarData as any).teamEvents) {
      const teamEvents = ((calendarData as any).teamEvents || []).map((event: CalendarEvent) => ({
        ...event,
        title: `${event.userName || 'Collega'} - Assente`,
        classNames: ['team-leave-event', `event-${event.extendedProps?.status || 'default'}`],
      }));
      result.push(...teamEvents);
    }

    return result;
  }, [calendarData, filters]);

  const pendingCount = requests?.filter(r => r.status === 'pending').length || 0;

  const handleViewChange = (view: CalendarView) => {
    setCurrentView(view);
    calendarRef.current?.getApi().changeView(view);
  };

  const toggleFilter = (key: keyof CalendarFilters) => {
    if (key === 'teamScope') return;
    setFilters(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const viewLabels: Record<CalendarView, string> = {
    'dayGridMonth': 'Mese',
    'timeGridWeek': 'Settimana',
    'timeGridDay': 'Giorno',
  };

  return (
    <div className="leaves-page animate-fadeIn">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Calendario Assenze</h1>
          <p className="page-subtitle">Gestisci ferie, permessi e visualizza il calendario aziendale</p>
        </div>
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
        <div className="balance-card glass-card">
          <div className="balance-icon" style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)' }}>
            <CalendarIcon size={20} />
          </div>
          <div className="balance-content">
            <div className="balance-label">Ferie AP</div>
            <div className="balance-value">{balance?.vacation_available_ap ?? '-'}</div>
          </div>
          {balance?.ap_expiry_date && (
            <div className="balance-expiry">Scade: {new Date(balance.ap_expiry_date).toLocaleDateString('it-IT')}</div>
          )}
        </div>
        <div className="balance-card glass-card">
          <div className="balance-icon" style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}>
            <CalendarIcon size={20} />
          </div>
          <div className="balance-content">
            <div className="balance-label">Ferie AC</div>
            <div className="balance-value">{balance?.vacation_available_ac ?? '-'}</div>
          </div>
        </div>
        <div className="balance-card glass-card">
          <div className="balance-icon" style={{ background: 'linear-gradient(135deg, #6366f1, #4f46e5)' }}>
            <CalendarIcon size={20} />
          </div>
          <div className="balance-content">
            <div className="balance-label">ROL</div>
            <div className="balance-value">{balance?.rol_available ?? '-'}<span className="unit">h</span></div>
          </div>
        </div>
        <div className="balance-card glass-card">
          <div className="balance-icon" style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' }}>
            <CalendarIcon size={20} />
          </div>
          <div className="balance-content">
            <div className="balance-label">Permessi</div>
            <div className="balance-value">{balance?.permits_available ?? '-'}<span className="unit">h</span></div>
          </div>
        </div>
      </div>

      {/* Calendar Section */}
      <div className="calendar-container card">
        {/* Toolbar */}
        <div className="calendar-toolbar">
          <div className="toolbar-left">
            <h2 className="calendar-title">
              <CalendarIcon size={20} />
              Calendario
            </h2>
          </div>

          <div className="toolbar-center">
            <div className="view-switcher">
              {(['dayGridMonth', 'timeGridWeek', 'timeGridDay'] as CalendarView[]).map(view => (
                <button
                  key={view}
                  className={`view-btn ${currentView === view ? 'active' : ''}`}
                  onClick={() => handleViewChange(view)}
                >
                  {viewLabels[view]}
                </button>
              ))}
            </div>
          </div>

          <div className="toolbar-right">
            <div className="filters-dropdown">
              <button
                className={`btn btn-secondary ${filtersOpen ? 'active' : ''}`}
                onClick={() => setFiltersOpen(!filtersOpen)}
              >
                <Settings size={16} />
                Visualizza
                <ChevronDown size={14} className={filtersOpen ? 'rotated' : ''} />
              </button>

              {filtersOpen && (
                <div className="filters-panel animate-fadeInUp">
                  <div className="filters-header">
                    <h4>Elementi Visibili</h4>
                    <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setFiltersOpen(false)}>
                      <X size={14} />
                    </button>
                  </div>

                  <div className="filters-section">
                    <div className="filter-group-title">
                      <Flag size={14} />
                      Festività
                    </div>
                    <label className="filter-item">
                      <input
                        type="checkbox"
                        checked={filters.showNationalHolidays}
                        onChange={() => toggleFilter('showNationalHolidays')}
                      />
                      <span className="filter-color" style={{ background: 'rgba(239, 68, 68, 0.5)' }} />
                      <span>Festività Nazionali</span>
                    </label>
                    <label className="filter-item">
                      <input
                        type="checkbox"
                        checked={filters.showLocalHolidays}
                        onChange={() => toggleFilter('showLocalHolidays')}
                      />
                      <span className="filter-color" style={{ background: 'rgba(249, 115, 22, 0.5)' }} />
                      <span>Festività Locali</span>
                    </label>
                  </div>

                  <div className="filters-section">
                    <div className="filter-group-title">
                      <Building size={14} />
                      Azienda
                    </div>
                    <label className="filter-item">
                      <input
                        type="checkbox"
                        checked={filters.showCompanyClosures}
                        onChange={() => toggleFilter('showCompanyClosures')}
                      />
                      <span className="filter-color" style={{ background: 'rgba(147, 51, 234, 0.5)' }} />
                      <span>Chiusure Aziendali</span>
                    </label>
                  </div>

                  <div className="filters-section">
                    <div className="filter-group-title">
                      <Users size={14} />
                      Colleghi
                    </div>
                    <label className="filter-item">
                      <input
                        type="checkbox"
                        checked={filters.showTeamLeaves}
                        onChange={() => toggleFilter('showTeamLeaves')}
                      />
                      <span className="filter-color" style={{ background: 'rgba(59, 130, 246, 0.5)' }} />
                      <span>Mostra Ferie Colleghi</span>
                    </label>
                    {filters.showTeamLeaves && (
                      <div className="filter-sub-options">
                        <label className="filter-radio">
                          <input
                            type="radio"
                            name="teamScope"
                            checked={filters.teamScope === 'department'}
                            onChange={() => setFilters(prev => ({ ...prev, teamScope: 'department' }))}
                          />
                          <span>Solo Dipartimento</span>
                        </label>
                        <label className="filter-radio">
                          <input
                            type="radio"
                            name="teamScope"
                            checked={filters.teamScope === 'company'}
                            onChange={() => setFilters(prev => ({ ...prev, teamScope: 'company' }))}
                          />
                          <span>Tutta l'Azienda</span>
                        </label>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="calendar-legend">
          <div className="legend-item">
            <span className="legend-dot" style={{ background: 'var(--color-success)' }} />
            <span>Approvate</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: 'var(--color-warning)' }} />
            <span>In Attesa</span>
          </div>
          {filters.showNationalHolidays && (
            <div className="legend-item">
              <span className="legend-dot" style={{ background: 'rgba(239, 68, 68, 0.6)' }} />
              <span>Festività</span>
            </div>
          )}
          {filters.showCompanyClosures && (
            <div className="legend-item">
              <span className="legend-dot" style={{ background: 'rgba(147, 51, 234, 0.6)' }} />
              <span>Chiusure</span>
            </div>
          )}
          {filters.showTeamLeaves && (
            <div className="legend-item">
              <span className="legend-dot" style={{ background: 'rgba(59, 130, 246, 0.6)' }} />
              <span>Colleghi</span>
            </div>
          )}
        </div>

        {/* Calendar */}
        <div className="calendar-wrapper">
          <FullCalendar
            ref={calendarRef}
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
            initialView={currentView}
            locale="it"
            headerToolbar={{
              left: 'prev,next today',
              center: 'title',
              right: '',
            }}
            events={events}
            eventClick={(info) => {
              const eventType = info.event.extendedProps?.type;
              if (eventType !== 'holiday' && eventType !== 'closure') {
                window.location.href = `/leaves/${info.event.id}`;
              }
            }}
            dateClick={(info) => {
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
              month: 'Mese',
              week: 'Settimana',
              day: 'Giorno',
            }}
            slotMinTime="08:00:00"
            slotMaxTime="20:00:00"
            allDaySlot={true}
            nowIndicator={true}
          />
        </div>
      </div>

      {/* Quick Requests List */}
      <div className="requests-section card">
        <div className="card-header">
          <h2 className="card-title">
            Le Mie Richieste
            {pendingCount > 0 && (
              <span className="badge badge-warning">{pendingCount} in attesa</span>
            )}
          </h2>
          <Link to="/leaves" className="btn btn-ghost btn-sm">
            Vedi tutte
          </Link>
        </div>

        <div className="requests-list">
          {requests?.slice(0, 5).map((request) => (
            <Link
              key={request.id}
              to={`/leaves/${request.id}`}
              className="request-item"
            >
              <div className={`request-status badge badge-${getStatusBadge(request.status)}`}>
                {getStatusLabel(request.status)}
              </div>
              <div className="request-info">
                <div className="request-type">{getLeaveTypeName(request.leave_type_code)}</div>
                <div className="request-dates">
                  {formatDateRange(request.start_date, request.end_date)}
                </div>
              </div>
              <div className="request-days">{request.days_requested} gg</div>
            </Link>
          ))}

          {(!requests || requests.length === 0) && (
            <div className="empty-state-inline">
              <p>Nessuna richiesta per il {currentDate.getFullYear()}</p>
              <Link to="/leaves/new" className="btn btn-primary btn-sm">
                Crea Richiesta
              </Link>
            </div>
          )}
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
          align-items: flex-start;
        }

        .page-title {
          font-size: var(--font-size-2xl);
          font-weight: var(--font-weight-bold);
          margin-bottom: var(--space-1);
        }

        .page-subtitle {
          color: var(--color-text-muted);
          font-size: var(--font-size-sm);
        }

        /* Balance Cards */
        .balance-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: var(--space-4);
        }

        .balance-card {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-4);
          position: relative;
        }

        .balance-icon {
          width: 44px;
          height: 44px;
          border-radius: var(--radius-lg);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          flex-shrink: 0;
        }

        .balance-content {
          flex: 1;
        }

        .balance-label {
          font-size: var(--font-size-xs);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--color-text-muted);
        }

        .balance-value {
          font-size: var(--font-size-xl);
          font-weight: var(--font-weight-bold);
          color: var(--color-text-primary);
        }

        .balance-value .unit {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-normal);
          color: var(--color-text-muted);
          margin-left: var(--space-1);
        }

        .balance-expiry {
          position: absolute;
          bottom: var(--space-2);
          right: var(--space-3);
          font-size: var(--font-size-2xs);
          color: var(--color-warning);
          background: var(--color-warning-bg);
          padding: 2px 6px;
          border-radius: var(--radius-sm);
        }

        /* Calendar Container */
        .calendar-container {
          padding: 0;
          overflow: hidden;
        }

        .calendar-toolbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--space-4) var(--space-5);
          border-bottom: 1px solid var(--color-border-light);
          gap: var(--space-4);
          flex-wrap: wrap;
        }

        .toolbar-left, .toolbar-right {
          display: flex;
          align-items: center;
          gap: var(--space-3);
        }

        .calendar-title {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--font-size-lg);
          font-weight: var(--font-weight-semibold);
          color: var(--color-primary);
        }

        /* View Switcher */
        .view-switcher {
          display: flex;
          background: var(--color-bg-tertiary);
          border-radius: var(--radius-lg);
          padding: var(--space-1);
        }

        .view-btn {
          padding: var(--space-2) var(--space-4);
          border: none;
          background: transparent;
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-medium);
          color: var(--color-text-muted);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .view-btn:hover {
          color: var(--color-text-primary);
        }

        .view-btn.active {
          background: var(--color-bg-primary);
          color: var(--color-primary);
          box-shadow: var(--shadow-sm);
        }

        /* Filters Dropdown */
        .filters-dropdown {
          position: relative;
        }

        .filters-dropdown .btn svg.rotated {
          transform: rotate(180deg);
        }

        .filters-panel {
          position: absolute;
          top: calc(100% + var(--space-2));
          right: 0;
          width: 280px;
          background: var(--color-bg-primary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-xl);
          box-shadow: var(--shadow-xl);
          z-index: 100;
          overflow: hidden;
        }

        .filters-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--space-3) var(--space-4);
          border-bottom: 1px solid var(--color-border-light);
          background: var(--color-bg-tertiary);
        }

        .filters-header h4 {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-semibold);
        }

        .filters-section {
          padding: var(--space-3) var(--space-4);
          border-bottom: 1px solid var(--color-border-light);
        }

        .filters-section:last-child {
          border-bottom: none;
        }

        .filter-group-title {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--font-size-xs);
          font-weight: var(--font-weight-semibold);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--color-text-muted);
          margin-bottom: var(--space-2);
        }

        .filter-item {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-2) 0;
          cursor: pointer;
          font-size: var(--font-size-sm);
        }

        .filter-item input[type="checkbox"] {
          width: 16px;
          height: 16px;
          accent-color: var(--color-primary);
        }

        .filter-color {
          width: 12px;
          height: 12px;
          border-radius: 3px;
        }

        .filter-sub-options {
          margin-left: var(--space-6);
          padding-top: var(--space-2);
        }

        .filter-radio {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-1) 0;
          cursor: pointer;
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
        }

        .filter-radio input[type="radio"] {
          accent-color: var(--color-primary);
        }

        /* Legend */
        .calendar-legend {
          display: flex;
          flex-wrap: wrap;
          gap: var(--space-4);
          padding: var(--space-3) var(--space-5);
          background: var(--color-bg-tertiary);
          border-bottom: 1px solid var(--color-border-light);
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .legend-dot {
          width: 10px;
          height: 10px;
          border-radius: var(--radius-sm);
        }

        /* Calendar Wrapper */
        .calendar-wrapper {
          padding: var(--space-4);
        }

        /* Requests Section */
        .requests-section {
          max-height: 400px;
          display: flex;
          flex-direction: column;
        }

        .requests-section .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .requests-list {
          flex: 1;
          overflow-y: auto;
        }

        .request-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3) var(--space-4);
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

        .empty-state-inline {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-6);
          text-align: center;
          color: var(--color-text-muted);
        }

        /* FullCalendar Overrides */
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

        .holiday-event, .closure-event {
          pointer-events: none;
        }

        .team-leave-event {
          opacity: 0.7;
          border-left: 3px solid var(--color-info) !important;
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

function getLeaveTypeName(code: string): string {
  const map: Record<string, string> = {
    FER: 'Ferie',
    ROL: 'ROL',
    PAR: 'Permessi',
    MAL: 'Malattia',
    MAT: 'Maternità/Paternità',
    LUT: 'Lutto',
    STU: 'Studio',
    DON: 'Donazione Sangue',
    L104: 'Legge 104',
    SW: 'Smart Working',
    NRT: 'Non Retribuito',
  };
  return map[code] || code;
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
