/**
 * KRONOS - Notifications Page
 * 
 * Full page view of all notifications with filters, bulk actions, and settings.
 */
import { useState, useEffect } from 'react';
import {
  Bell,
  Check,
  CheckCheck,
  RefreshCw,
  Settings,
  Mail,
  Smartphone,
  Monitor,
  Save,
  ClipboardList,
  Calendar,
  Receipt,
  Megaphone,
  ShieldAlert,
  Info
} from 'lucide-react';
import notificationService, { NotificationStatus, NotificationType } from '../services/notification.service';
import type { Notification, UserPreferences } from '../services/notification.service';
import { useToast } from '../context/ToastContext';
import { useNotification } from '../context/NotificationContext';


type FilterType = 'all' | 'unread' | 'leave' | 'calendar' | 'system';
type PageTab = 'notifications' | 'settings';

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterType>('all');
  const [channelFilter, setChannelFilter] = useState<string>('in_app');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<PageTab>('notifications');

  // Settings state
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [loadingPrefs, setLoadingPrefs] = useState(false);
  const [savingPrefs, setSavingPrefs] = useState(false);

  const toast = useToast();
  const { markAsRead, markAllAsRead } = useNotification();

  useEffect(() => {
    fetchNotifications();
  }, [filter, channelFilter]);

  useEffect(() => {
    if (activeTab === 'settings' && !preferences) {
      fetchPreferences();
    }
  }, [activeTab]);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const unreadOnly = filter === 'unread';
      const data = await notificationService.getNotifications(unreadOnly, 100, channelFilter);

      // Apply type filters
      let filtered = data;
      if (filter === 'leave') {
        filtered = data.filter(n => n.notification_type.startsWith('leave_'));
      } else if (filter === 'calendar') {
        filtered = data.filter(n => n.notification_type.startsWith('calendar_'));
      } else if (filter === 'system') {
        filtered = data.filter(n =>
          n.notification_type === NotificationType.SYSTEM_ANNOUNCEMENT ||
          n.notification_type === NotificationType.COMPLIANCE_ALERT
        );
      }

      setNotifications(filtered);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPreferences = async () => {
    setLoadingPrefs(true);
    try {
      const data = await notificationService.getPreferences();
      setPreferences(data);
    } catch (error) {
      console.error('Failed to fetch preferences:', error);
      // Set defaults if API fails
      setPreferences({
        email_enabled: true,
        in_app_enabled: true,
        push_enabled: true,
        preferences_matrix: {},
        digest_frequency: 'instant',
      });
    } finally {
      setLoadingPrefs(false);
    }
  };

  const handleSavePreferences = async () => {
    if (!preferences) return;

    setSavingPrefs(true);
    try {
      await notificationService.updatePreferences(preferences);
      toast.success('Preferenze salvate con successo');
    } catch (error) {
      console.error('Failed to save preferences:', error);
      toast.error('Errore nel salvataggio delle preferenze');
    } finally {
      setSavingPrefs(false);
    }
  };

  const updatePreference = (key: keyof UserPreferences, value: boolean | string) => {
    if (!preferences) return;
    setPreferences({ ...preferences, [key]: value });
  };

  /* Removed misplaced import */
  // ...

  const handleMarkAsRead = async (ids: string[]) => {
    try {
      await markAsRead(ids);
      // Update local list
      setNotifications(prev =>
        prev.map(n =>
          ids.includes(n.id)
            ? { ...n, status: NotificationStatus.READ, read_at: new Date().toISOString() }
            : n
        )
      );
      setSelectedIds(new Set());
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead();
      setNotifications(prev =>
        prev.map(n => ({ ...n, status: NotificationStatus.READ, read_at: new Date().toISOString() }))
      );
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const toggleSelection = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === notifications.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(notifications.map(n => n.id)));
    }
  };

  const getNotificationIcon = (type: string) => {
    if (type.startsWith('leave_')) return <ClipboardList size={22} className="text-blue-500" />;
    if (type.startsWith('calendar_')) return <Calendar size={22} className="text-indigo-500" />;
    if (type.startsWith('expense_') || type.startsWith('trip_')) return <Receipt size={22} className="text-purple-500" />;
    if (type === NotificationType.SYSTEM_ANNOUNCEMENT) return <Megaphone size={22} className="text-amber-500" />;
    if (type === NotificationType.COMPLIANCE_ALERT) return <ShieldAlert size={22} className="text-red-500" />;
    return <Info size={22} className="text-gray-500" />;
  };

  const getIconBackground = (type: string) => {
    if (type.startsWith('leave_')) return 'bg-blue-50';
    if (type.startsWith('calendar_')) return 'bg-indigo-50';
    if (type.startsWith('expense_') || type.startsWith('trip_')) return 'bg-purple-50';
    if (type === NotificationType.SYSTEM_ANNOUNCEMENT) return 'bg-amber-50';
    if (type === NotificationType.COMPLIANCE_ALERT) return 'bg-red-50';
    return 'bg-gray-50';
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      leave_request_submitted: 'Nuova Richiesta',
      leave_request_approved: 'Approvazione',
      leave_request_rejected: 'Rifiuto',
      leave_request_cancelled: 'Cancellazione',
      calendar_system_deadline: 'Scadenza Sistema',
      calendar_personal_deadline: 'Scadenza Personale',
      calendar_shared_deadline: 'Scadenza Condivisa',
      system_announcement: 'Annuncio',
      compliance_alert: 'Compliance',
    };
    return labels[type] || type;
  };

  const filters: { key: FilterType; label: string }[] = [
    { key: 'all', label: 'Tutte' },
    { key: 'unread', label: 'Non lette' },
    { key: 'leave', label: 'Ferie' },
    { key: 'calendar', label: 'Calendario' },
    { key: 'system', label: 'Sistema' },
  ];

  const digestOptions = [
    { value: 'instant', label: 'Istantanea' },
    { value: 'daily', label: 'Giornaliero' },
    { value: 'weekly', label: 'Settimanale' },
  ];

  return (
    <div className="notifications-page">
      <div className="notifications-header">
        <div className="notifications-title">
          <Bell size={24} />
          <h1>Notifiche</h1>
        </div>

        <div className="page-tabs">
          <button
            className={`tab-btn ${activeTab === 'notifications' ? 'active' : ''}`}
            onClick={() => setActiveTab('notifications')}
          >
            <Bell size={16} />
            Notifiche
          </button>
          <button
            className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <Settings size={16} />
            Impostazioni
          </button>
        </div>
      </div>

      {activeTab === 'notifications' ? (
        <>
          <div className="notifications-actions-bar">
            <div className="notifications-filters-row">
              <div className="notifications-filters">
                {filters.map(f => (
                  <button
                    key={f.key}
                    className={`filter-btn ${filter === f.key ? 'active' : ''}`}
                    onClick={() => setFilter(f.key)}
                  >
                    {f.label}
                  </button>
                ))}
              </div>

              <div className="channel-filters">
                <span className="filter-label">Canale:</span>
                <select
                  value={channelFilter}
                  onChange={(e) => setChannelFilter(e.target.value)}
                  className="channel-select"
                >
                  <option value="in_app">In-App</option>
                  <option value="email">Email</option>
                  <option value="push">Push</option>
                  <option value="all">Tutti</option>
                </select>
              </div>
            </div>

            <div className="notifications-actions">
              <button
                className="action-btn"
                onClick={fetchNotifications}
                title="Aggiorna"
              >
                <RefreshCw size={18} />
              </button>
              <button
                className="action-btn primary"
                onClick={handleMarkAllAsRead}
                title="Segna tutte come lette"
              >
                <CheckCheck size={18} />
                <span>Segna tutte lette</span>
              </button>
            </div>
          </div>

          {selectedIds.size > 0 && (
            <div className="notifications-bulk-actions">
              <span>{selectedIds.size} selezionate</span>
              <button onClick={() => handleMarkAsRead(Array.from(selectedIds))}>
                <Check size={16} />
                Segna come lette
              </button>
            </div>
          )}

          <div className="notifications-list">
            {loading ? (
              <div className="notifications-loading">
                <RefreshCw size={24} className="spinning" />
                <p>Caricamento...</p>
              </div>
            ) : notifications.length === 0 ? (
              <div className="notifications-empty">
                <Bell size={48} />
                <h3>Nessuna notifica</h3>
                <p>Non hai notifiche in questa categoria</p>
              </div>
            ) : (
              <>
                <div className="notifications-list-header">
                  <label className="checkbox-wrapper">
                    <input
                      type="checkbox"
                      checked={selectedIds.size === notifications.length && notifications.length > 0}
                      onChange={toggleSelectAll}
                    />
                    <span>Seleziona tutto</span>
                  </label>
                </div>
                {notifications.map(notification => (
                  <div
                    key={notification.id}
                    className={`notification-row ${notification.status !== NotificationStatus.READ ? 'unread' : ''}`}
                  >
                    <label className="checkbox-wrapper">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(notification.id)}
                        onChange={() => toggleSelection(notification.id)}
                      />
                    </label>
                    <div className={`notification-icon-wrapper ${getIconBackground(notification.notification_type)}`}>
                      {getNotificationIcon(notification.notification_type)}
                    </div>
                    <div className="notification-content">
                      <div className="notification-top">
                        <span className="notification-title">{notification.title}</span>
                        <span className="notification-type-badge">
                          {getTypeLabel(notification.notification_type)}
                        </span>
                        <span className="notification-time ml-auto">{formatDate(notification.created_at)}</span>
                      </div>
                      <p className="notification-message">{notification.message}</p>
                    </div>
                    <div className="notification-actions">
                      {notification.status !== NotificationStatus.READ && (
                        <button
                          className="icon-btn"
                          onClick={() => handleMarkAsRead([notification.id])}
                          title="Segna come letta"
                        >
                          <Check size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </>
      ) : (
        <div className="settings-section">
          {loadingPrefs ? (
            <div className="notifications-loading">
              <RefreshCw size={24} className="spinning" />
              <p>Caricamento preferenze...</p>
            </div>
          ) : preferences ? (
            <>
              <div className="settings-card">
                <h3>Canali di Notifica</h3>
                <p className="settings-description">
                  Scegli come vuoi ricevere le notifiche
                </p>

                <div className="settings-toggles">
                  <div className="toggle-row">
                    <div className="toggle-info">
                      <Mail size={20} />
                      <div>
                        <span className="toggle-label">Email</span>
                        <span className="toggle-desc">Ricevi notifiche via email</span>
                      </div>
                    </div>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={preferences.email_enabled}
                        onChange={(e) => updatePreference('email_enabled', e.target.checked)}
                      />
                      <span className="slider"></span>
                    </label>
                  </div>

                  <div className="toggle-row">
                    <div className="toggle-info">
                      <Monitor size={20} />
                      <div>
                        <span className="toggle-label">In-App</span>
                        <span className="toggle-desc">Notifiche nell'applicazione</span>
                      </div>
                    </div>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={preferences.in_app_enabled}
                        onChange={(e) => updatePreference('in_app_enabled', e.target.checked)}
                      />
                      <span className="slider"></span>
                    </label>
                  </div>

                  <div className="toggle-row">
                    <div className="toggle-info">
                      <Smartphone size={20} />
                      <div>
                        <span className="toggle-label">Push</span>
                        <span className="toggle-desc">Notifiche push sul browser</span>
                      </div>
                    </div>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={preferences.push_enabled}
                        onChange={(e) => updatePreference('push_enabled', e.target.checked)}
                      />
                      <span className="slider"></span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="settings-card">
                <h3>Frequenza Digest</h3>
                <p className="settings-description">
                  Scegli quando ricevere il riepilogo delle notifiche email
                </p>

                <div className="digest-options">
                  {digestOptions.map(opt => (
                    <label key={opt.value} className="digest-option">
                      <input
                        type="radio"
                        name="digest"
                        value={opt.value}
                        checked={preferences.digest_frequency === opt.value}
                        onChange={(e) => updatePreference('digest_frequency', e.target.value)}
                      />
                      <span className="radio-custom"></span>
                      <span>{opt.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="settings-actions">
                <button
                  className="save-btn"
                  onClick={handleSavePreferences}
                  disabled={savingPrefs}
                >
                  <Save size={18} />
                  {savingPrefs ? 'Salvataggio...' : 'Salva Preferenze'}
                </button>
              </div>
            </>
          ) : null}
        </div>
      )}

      <style>{`
        .notifications-page {
          padding: var(--space-6);
          max-width: 900px;
          margin: 0 auto;
        }

        .notifications-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--space-6);
        }

        .notifications-title {
          display: flex;
          align-items: center;
          gap: var(--space-3);
        }

        .notifications-title h1 {
          font-size: var(--font-size-2xl);
          font-weight: 600;
          color: var(--color-text-primary);
          margin: 0;
        }

        .page-tabs {
          display: flex;
          gap: var(--space-2);
          background: var(--color-bg-secondary);
          padding: 4px;
          border-radius: var(--radius-lg);
        }
        
        .tab-btn {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-2) var(--space-4);
          background: transparent;
          border: none;
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          font-size: var(--font-size-sm);
          font-weight: 500;
          cursor: pointer;
          transition: all var(--transition-fast);
        }
        
        .tab-btn:hover {
          color: var(--color-text-primary);
        }
        
        .tab-btn.active {
          background: var(--color-bg-primary);
          color: var(--color-primary);
          box-shadow: var(--shadow-sm);
        }

        .notifications-actions-bar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--space-4);
          padding-bottom: var(--space-4);
          border-bottom: 1px solid var(--color-border);
          flex-wrap: wrap;
          gap: var(--space-3);
        }

        .notifications-filters-row {
            display: flex;
            align-items: center;
            gap: var(--space-4);
            flex-wrap: wrap;
        }

        .channel-filters {
            display: flex;
            align-items: center;
            gap: var(--space-2);
            padding-left: var(--space-4);
            border-left: 1px solid var(--color-border);
        }

        .filter-label {
            font-size: var(--font-size-sm);
            color: var(--color-text-secondary);
            font-weight: 500;
        }

        .channel-select {
            padding: var(--space-1) var(--space-3) var(--space-1) var(--space-2);
            font-size: var(--font-size-sm);
            border-radius: var(--radius-md);
            border: 1px solid var(--color-border);
            background: var(--color-bg-primary);
            color: var(--color-text-primary);
            outline: none;
            cursor: pointer;
        }

        .notifications-actions {
          display: flex;
          gap: var(--space-2);
          margin-left: auto;
        }

        .action-btn {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-2) var(--space-3);
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          font-size: var(--font-size-sm);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .action-btn:hover {
          background: var(--color-bg-hover);
          color: var(--color-text-primary);
        }

        .action-btn.primary {
          background: var(--color-primary);
          border-color: var(--color-primary);
          color: white;
        }

        .action-btn.primary:hover {
          background: var(--color-primary-dark);
        }

        .notifications-filters {
          display: flex;
          gap: var(--space-2);
        }

        .filter-btn {
          padding: var(--space-2) var(--space-4);
          background: transparent;
          border: 1px solid var(--color-border);
          border-radius: var(--radius-full);
          color: var(--color-text-secondary);
          font-size: var(--font-size-sm);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .filter-btn:hover {
          background: var(--color-bg-hover);
        }

        .filter-btn.active {
          background: var(--color-primary);
          border-color: var(--color-primary);
          color: white;
        }

        .notifications-bulk-actions {
          display: flex;
          align-items: center;
          gap: var(--space-4);
          padding: var(--space-3);
          background: var(--color-bg-tertiary);
          border-radius: var(--radius-md);
          margin-bottom: var(--space-4);
        }

        .notifications-bulk-actions span {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
        }

        .notifications-bulk-actions button {
          display: flex;
          align-items: center;
          gap: var(--space-1);
          padding: var(--space-1) var(--space-2);
          background: transparent;
          border: none;
          color: var(--color-primary);
          font-size: var(--font-size-sm);
          cursor: pointer;
        }

        .notifications-list {
          background: var(--color-bg-primary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
          overflow: hidden;
        }

        .notifications-list-header {
          padding: var(--space-3) var(--space-4);
          border-bottom: 1px solid var(--color-border);
          background: var(--color-bg-secondary);
        }

        .notifications-loading,
        .notifications-empty {
          padding: var(--space-12);
          text-align: center;
          color: var(--color-text-muted);
        }

        .notifications-empty h3 {
          margin: var(--space-4) 0 var(--space-2);
          color: var(--color-text-secondary);
        }

        .spinning {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .notification-row {
          display: flex;
          align-items: flex-start;
          gap: var(--space-3);
          padding: var(--space-4);
          border-bottom: 1px solid var(--color-border-light);
          transition: background var(--transition-fast);
        }

        .notification-row:hover {
          background: var(--color-bg-hover);
        }

        .notification-row.unread {
          background: var(--color-bg-tertiary);
          border-left: 3px solid var(--color-primary);
        }

        .checkbox-wrapper {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          cursor: pointer;
        }

        .checkbox-wrapper input {
          width: 16px;
          height: 16px;
          cursor: pointer;
        }

        .notification-icon-wrapper {
          width: 42px;
          height: 42px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .notification-content {
          flex: 1;
          min-width: 0;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .notification-top {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          flex-wrap: wrap;
        }

        .notification-title {
          font-weight: 600;
          color: var(--color-text-primary);
          font-size: 15px;
        }
        
        .notification-message {
          font-size: 14px;
          color: var(--color-text-secondary);
          margin: 0;
          line-height: 1.5;
        }

        .notification-time {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          margin-left: auto;
        }

        .ml-auto {
          margin-left: auto;
        }

        /* Utility classes for colors (Tailwind-like) */
        .text-blue-500 { color: #3b82f6; }
        .text-indigo-500 { color: #6366f1; }
        .text-purple-500 { color: #a855f7; }
        .text-amber-500 { color: #f59e0b; }
        .text-red-500 { color: #ef4444; }
        .text-gray-500 { color: #64748b; }
        
        .bg-blue-50 { background-color: #eff6ff; }
        .bg-indigo-50 { background-color: #eef2ff; }
        .bg-purple-50 { background-color: #faf5ff; }
        .bg-amber-50 { background-color: #fffbeb; }
        .bg-red-50 { background-color: #fef2f2; }
        .bg-gray-50 { background-color: #f8fafc; }

        .settings-card h3 {
          margin: 0 0 var(--space-2);
          font-size: var(--font-size-lg);
          font-weight: 600;
          color: var(--color-text-primary);
        }
        
        .settings-description {
          margin: 0 0 var(--space-6);
          color: var(--color-text-secondary);
          font-size: var(--font-size-sm);
        }
        
        .settings-toggles {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }
        
        .toggle-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--space-4);
          background: var(--color-bg-secondary);
          border-radius: var(--radius-md);
        }
        
        .toggle-info {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          color: var(--color-text-secondary);
        }
        
        .toggle-info > div {
          display: flex;
          flex-direction: column;
        }
        
        .toggle-label {
          font-weight: 500;
          color: var(--color-text-primary);
        }
        
        .toggle-desc {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }
        
        .toggle-switch {
          position: relative;
          width: 48px;
          height: 26px;
          cursor: pointer;
        }
        
        .toggle-switch input {
          opacity: 0;
          width: 0;
          height: 0;
        }
        
        .toggle-switch .slider {
          position: absolute;
          inset: 0;
          background: var(--color-bg-tertiary);
          border-radius: 26px;
          transition: var(--transition-fast);
        }
        
        .toggle-switch .slider::before {
          content: '';
          position: absolute;
          width: 20px;
          height: 20px;
          left: 3px;
          bottom: 3px;
          background: white;
          border-radius: 50%;
          transition: var(--transition-fast);
          box-shadow: var(--shadow-sm);
        }
        
        .toggle-switch input:checked + .slider {
          background: var(--color-primary);
        }
        
        .toggle-switch input:checked + .slider::before {
          transform: translateX(22px);
        }
        
        .digest-options {
          display: flex;
          gap: var(--space-4);
        }
        
        .digest-option {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-3) var(--space-4);
          background: var(--color-bg-secondary);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: var(--transition-fast);
        }
        
        .digest-option:hover {
          background: var(--color-bg-hover);
        }
        
        .digest-option input {
          display: none;
        }
        
        .digest-option .radio-custom {
          width: 18px;
          height: 18px;
          border: 2px solid var(--color-border);
          border-radius: 50%;
          position: relative;
          transition: var(--transition-fast);
        }
        
        .digest-option input:checked + .radio-custom {
          border-color: var(--color-primary);
        }
        
        .digest-option input:checked + .radio-custom::after {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 10px;
          height: 10px;
          background: var(--color-primary);
          border-radius: 50%;
        }
        
        .settings-actions {
          display: flex;
          justify-content: flex-end;
        }
        
        .save-btn {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-3) var(--space-6);
          background: var(--color-primary);
          border: none;
          border-radius: var(--radius-md);
          color: white;
          font-size: var(--font-size-sm);
          font-weight: 500;
          cursor: pointer;
          transition: var(--transition-fast);
        }
        
        .save-btn:hover:not(:disabled) {
          background: var(--color-primary-dark);
        }
        
        .save-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}

export default NotificationsPage;
