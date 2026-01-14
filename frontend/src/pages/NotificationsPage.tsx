/**
 * KRONOS - Notifications Page (Refactored)
 * 
 * Full page view of all notifications with filters, bulk actions, and settings.
 * Uses React Query for server state management.
 */
import { useState } from 'react';
import {
  Bell,
  Check,
  CheckCheck,
  RefreshCw,
  Settings
} from 'lucide-react';
import { useToast } from '../context/ToastContext';
import {
  useNotifications,
  useNotificationPreferences,
  useUpdatePreferences,
  useMarkNotificationsAsRead,
  useMarkAllNotificationsAsRead,
  type NotificationFilters
} from '../hooks/domain/useNotifications';
import { NotificationItem } from '../components/notifications/NotificationItem';
import { NotificationPreferences } from '../components/notifications/NotificationPreferences';
import type { UserPreferences } from '../services/notification.service';

type FilterType = 'all' | 'unread' | 'leave' | 'calendar' | 'system';
type PageTab = 'notifications' | 'settings';

export function NotificationsPage() {
  // UI State (Client State)
  const [filter, setFilter] = useState<FilterType>('all');
  const [channelFilter, setChannelFilter] = useState<string>('in_app');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<PageTab>('notifications');
  const [localPrefs, setLocalPrefs] = useState<UserPreferences | null>(null);

  const toast = useToast();

  // Server State (React Query)
  const notificationFilters: NotificationFilters = {
    unreadOnly: filter === 'unread',
    channel: channelFilter,
    typeFilter: filter
  };

  const {
    data: notifications = [],
    isLoading,
    refetch
  } = useNotifications(notificationFilters);

  const {
    data: preferences,
    isLoading: loadingPrefs
  } = useNotificationPreferences();

  const updatePrefsMutation = useUpdatePreferences();
  const markAsReadMutation = useMarkNotificationsAsRead();
  const markAllAsReadMutation = useMarkAllNotificationsAsRead();

  // Use local prefs for form state, fallback to server data
  const currentPrefs = localPrefs || preferences;

  // Handlers
  const handleMarkAsRead = async (ids: string[]) => {
    try {
      await markAsReadMutation.mutateAsync(ids);
      setSelectedIds(new Set());
    } catch {
      toast.error('Errore nel segnare come lette');
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsReadMutation.mutateAsync();
    } catch {
      toast.error('Errore nel segnare tutte come lette');
    }
  };

  const handleSavePreferences = async () => {
    if (!currentPrefs) return;

    try {
      await updatePrefsMutation.mutateAsync(currentPrefs);
      toast.success('Preferenze salvate con successo');
      setLocalPrefs(null); // Clear local state
    } catch {
      toast.error('Errore nel salvataggio delle preferenze');
    }
  };

  const updatePreference = (key: keyof UserPreferences, value: boolean | string) => {
    if (!currentPrefs) return;
    setLocalPrefs({ ...currentPrefs, [key]: value });
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

  const filters: { key: FilterType; label: string }[] = [
    { key: 'all', label: 'Tutte' },
    { key: 'unread', label: 'Non lette' },
    { key: 'leave', label: 'Ferie' },
    { key: 'calendar', label: 'Calendario' },
    { key: 'system', label: 'Sistema' },
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
                onClick={() => refetch()}
                title="Aggiorna"
              >
                <RefreshCw size={18} />
              </button>
              <button
                className="action-btn primary"
                onClick={handleMarkAllAsRead}
                title="Segna tutte come lette"
                disabled={markAllAsReadMutation.isPending}
              >
                <CheckCheck size={18} />
                <span>Segna tutte lette</span>
              </button>
            </div>
          </div>

          {selectedIds.size > 0 && (
            <div className="notifications-bulk-actions">
              <span>{selectedIds.size} selezionate</span>
              <button
                onClick={() => handleMarkAsRead(Array.from(selectedIds))}
                disabled={markAsReadMutation.isPending}
              >
                <Check size={16} />
                Segna come lette
              </button>
            </div>
          )}

          <div className="notifications-list">
            {isLoading ? (
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
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    isSelected={selectedIds.has(notification.id)}
                    onToggleSelect={toggleSelection}
                    onMarkAsRead={handleMarkAsRead}
                  />
                ))}
              </>
            )}
          </div>
        </>
      ) : (
        <>
          {loadingPrefs ? (
            <div className="notifications-loading">
              <RefreshCw size={24} className="spinning" />
              <p>Caricamento preferenze...</p>
            </div>
          ) : currentPrefs ? (
            <NotificationPreferences
              preferences={currentPrefs}
              onUpdatePreference={updatePreference}
              onSave={handleSavePreferences}
              isSaving={updatePrefsMutation.isPending}
            />
          ) : null}
        </>
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

                .action-btn:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }

                .action-btn.primary {
                    background: var(--color-primary);
                    border-color: var(--color-primary);
                    color: white;
                }

                .action-btn.primary:hover:not(:disabled) {
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

                .notifications-bulk-actions button:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
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

                .notification-type-badge {
                    font-size: 11px;
                    font-weight: 500;
                    padding: 2px 8px;
                    background: var(--color-bg-secondary);
                    border-radius: var(--radius-full);
                    color: var(--color-text-secondary);
                }

                .notification-actions {
                    display: flex;
                    gap: var(--space-2);
                }

                .icon-btn {
                    width: 32px;
                    height: 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: transparent;
                    border: 1px solid var(--color-border);
                    border-radius: var(--radius-md);
                    color: var(--color-text-secondary);
                    cursor: pointer;
                    transition: all var(--transition-fast);
                }

                .icon-btn:hover {
                    background: var(--color-bg-hover);
                    color: var(--color-primary);
                }

                /* Utility classes */
                .text-blue-500 { color: #3b82f6; }
                .text-indigo-500 { color: #6366f1; }
                .text-purple-500 { color: #a855f7; }
                .text-amber-500 { color: #f59e0b; }
                .text-red-500 { color: #ef4444; }
                .text-gray-500 { color: #6b7280; }

                .bg-blue-50 { background-color: #eff6ff; }
                .bg-indigo-50 { background-color: #eef2ff; }
                .bg-purple-50 { background-color: #faf5ff; }
                .bg-amber-50 { background-color: #fffbeb; }
                .bg-red-50 { background-color: #fef2f2; }
                .bg-gray-50 { background-color: #f9fafb; }
            `}</style>
    </div>
  );
}

export default NotificationsPage;
