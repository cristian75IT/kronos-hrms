/**
 * KRONOS - Notification Dropdown Component
 * 
 * Dropdown bell menu for the header showing recent notifications.
 */
import {
  Bell,
  CheckCheck,
  ClipboardList,
  Calendar,
  Receipt,
  Megaphone,
  ShieldAlert,
  Info,
} from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import notificationService, { NotificationStatus, NotificationType } from '../../services/notification.service';
import type { Notification } from '../../services/notification.service';
import { useNavigate } from 'react-router-dom';
import { useNotification } from '../../context/NotificationContext';

interface NotificationDropdownProps {
  onUnreadCountChange?: (count: number) => void;
}

export function NotificationDropdown({ onUnreadCountChange }: NotificationDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Use Context
  const { unreadCount, markAsRead, markAllAsRead, refreshUnreadCount } = useNotification();

  // Close dropdown when clicking outside
  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    // Listen for real-time notifications to update list if loaded
    function handleNewNotification(event: Event) {
      const customEvent = event as CustomEvent<Notification>;
      const newNotif = customEvent.detail;

      setNotifications(prev => {
        // Prevent duplicate if already in list (though unlikely with unique IDs)
        if (prev.some(n => n.id === newNotif.id)) return prev;
        return [newNotif, ...prev];
      });
    }

    document.addEventListener('mousedown', handleClickOutside);
    window.addEventListener('notification:received', handleNewNotification);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('notification:received', handleNewNotification);
    };
  }, []);

  // Fetch list when opening
  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const data = await notificationService.getNotifications(false, 10);
      setNotifications(data);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = () => {
    if (!isOpen) {
      fetchNotifications();
      refreshUnreadCount(); // Ensure count is fresh
    }
    setIsOpen(!isOpen);
  };

  const handleMarkAsRead = async (notificationIds: string[]) => {
    try {
      await markAsRead(notificationIds);
      // Update local list optimistic
      setNotifications(prev =>
        prev.map(n =>
          notificationIds.includes(n.id)
            ? { ...n, status: NotificationStatus.READ, read_at: new Date().toISOString() }
            : n
        )
      );
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
      onUnreadCountChange?.(0);
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const handleNotificationClick = (notification: Notification) => {
    if (notification.status !== NotificationStatus.READ) {
      handleMarkAsRead([notification.id]);
    }
    if (notification.action_url) {
      navigate(notification.action_url);
      setIsOpen(false);
    }
  };

  const getNotificationIcon = (type: NotificationType) => {
    if (type.startsWith('leave_')) return <ClipboardList size={18} className="text-blue-500" />;
    if (type.startsWith('calendar_')) return <Calendar size={18} className="text-indigo-500" />;
    if (type.startsWith('expense_') || type.startsWith('trip_')) return <Receipt size={18} className="text-purple-500" />;
    if (type === NotificationType.SYSTEM_ANNOUNCEMENT) return <Megaphone size={18} className="text-amber-500" />;
    if (type === NotificationType.COMPLIANCE_ALERT) return <ShieldAlert size={18} className="text-red-500" />;
    return <Info size={18} className="text-gray-500" />;
  };

  const getIconBackground = (type: NotificationType) => {
    if (type.startsWith('leave_')) return 'bg-blue-50';
    if (type.startsWith('calendar_')) return 'bg-indigo-50';
    if (type.startsWith('expense_') || type.startsWith('trip_')) return 'bg-purple-50';
    if (type === NotificationType.SYSTEM_ANNOUNCEMENT) return 'bg-amber-50';
    if (type === NotificationType.COMPLIANCE_ALERT) return 'bg-red-50';
    return 'bg-gray-50';
  };

  const formatTimeAgo = (dateStr: string): string => {
    const date = new Date(dateStr);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'Adesso';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min fa`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} ore fa`;
    return `${Math.floor(seconds / 86400)} giorni fa`;
  };

  return (
    <div className="notification-dropdown" ref={dropdownRef}>
      <button
        className="notification-dropdown-trigger"
        onClick={handleToggle}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="notification-badge">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown-menu">
          <div className="notification-dropdown-header">
            <h3>Notifiche</h3>
            {unreadCount > 0 && (
              <button
                className="notification-mark-all"
                onClick={handleMarkAllAsRead}
                title="Segna tutte come lette"
              >
                <CheckCheck size={16} />
              </button>
            )}
          </div>

          <div className="notification-dropdown-content">
            {loading ? (
              <div className="notification-loading">
                <div className="spinner"></div>
                <p>Caricamento...</p>
              </div>
            ) : notifications.length === 0 ? (
              <div className="notification-empty">
                <div className="empty-icon-wrapper">
                  <Bell size={24} />
                </div>
                <p>Nessuna notifica</p>
                <span className="empty-subtitle">Sei al passo con tutto!</span>
              </div>
            ) : (
              notifications.map(notification => (
                <div
                  key={notification.id}
                  className={`notification-item ${notification.status !== NotificationStatus.READ ? 'unread' : ''}`}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <div className={`notification-icon-wrapper ${getIconBackground(notification.notification_type as NotificationType)}`}>
                    {getNotificationIcon(notification.notification_type as NotificationType)}
                  </div>
                  <div className="notification-content">
                    <div className="notification-header-row">
                      <span className="notification-title">{notification.title}</span>
                      <span className="notification-time">{formatTimeAgo(notification.created_at)}</span>
                    </div>
                    <span className="notification-message">{notification.message}</span>
                  </div>
                  {notification.status !== NotificationStatus.READ && (
                    <div className="unread-dot"></div>
                  )}
                </div>
              ))
            )}
          </div>

          <div className="notification-dropdown-footer">
            <button onClick={() => { navigate('/notifications'); setIsOpen(false); }}>
              Vedi tutte le notifiche
            </button>
          </div>
        </div>
      )}

      <style>{`
        .notification-dropdown {
          position: relative;
        }

        .notification-dropdown-trigger {
          position: relative;
          padding: 8px;
          background: transparent;
          border: 1px solid transparent;
          border-radius: 8px;
          color: #64748b;
          cursor: pointer;
          transition: all 0.2s;
        }

        .notification-dropdown-trigger:hover {
          background: #f1f5f9;
          color: #0f172a;
        }

        .notification-badge {
          position: absolute;
          top: 0;
          right: 0;
          min-width: 18px;
          height: 18px;
          padding: 0 4px;
          background: #ef4444;
          color: white;
          font-size: 10px;
          font-weight: 600;
          border-radius: 9999px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 2px solid white;
          transform: translate(25%, -25%);
        }

        .notification-dropdown-menu {
          position: absolute;
          top: calc(100% + 12px);
          right: -10px;
          width: 380px;
          max-height: 500px;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
          overflow: hidden;
          z-index: 50;
          animation: slideDown 0.2s cubic-bezier(0.16, 1, 0.3, 1);
          transform-origin: top right;
        }

        @keyframes slideDown {
          from { opacity: 0; transform: scale(0.95) translateY(-10px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }

        .notification-dropdown-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px;
          border-bottom: 1px solid #f1f5f9;
        }

        .notification-dropdown-header h3 {
          font-size: 16px;
          font-weight: 600;
          color: #0f172a;
          margin: 0;
        }

        .notification-mark-all {
          padding: 6px;
          background: transparent;
          border: none;
          border-radius: 6px;
          color: #6366f1;
          cursor: pointer;
          transition: background 0.2s;
        }

        .notification-mark-all:hover {
          background: #eef2ff;
        }

        .notification-dropdown-content {
          max-height: 380px;
          overflow-y: auto;
        }

        .notification-loading {
          padding: 32px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          color: #64748b;
        }

        .spinner {
          width: 24px;
          height: 24px;
          border: 2px solid #e2e8f0;
          border-top-color: #6366f1;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin { to { transform: rotate(360deg); } }

        .notification-empty {
          padding: 48px 24px;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }

        .empty-icon-wrapper {
          width: 48px;
          height: 48px;
          background: #f1f5f9;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #94a3b8;
          margin-bottom: 16px;
        }

        .notification-empty p {
          font-weight: 500;
          color: #0f172a;
          margin: 0 0 4px;
        }

        .empty-subtitle {
          font-size: 13px;
          color: #64748b;
        }

        .notification-item {
          display: flex;
          gap: 12px;
          padding: 16px;
          cursor: pointer;
          transition: background 0.2s;
          border-bottom: 1px solid #f8fafc;
          position: relative;
        }

        .notification-item:hover {
          background: #f8fafc;
        }

        .notification-item.unread {
          background: #f0f9ff;
        }

        .notification-icon-wrapper {
          width: 36px;
          height: 36px;
          border-radius: 10px;
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

        .notification-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .notification-title {
          font-size: 14px;
          font-weight: 600;
          color: #1e293b;
        }

        .notification-time {
          font-size: 11px;
          color: #94a3b8;
          white-space: nowrap;
          margin-left: 8px;
        }

        .notification-message {
          font-size: 13px;
          color: #64748b;
          line-height: 1.4;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        
        .unread-dot {
          width: 8px;
          height: 8px;
          background: #3b82f6;
          border-radius: 50%;
          position: absolute;
          top: 16px;
          right: 16px;
        }

        .notification-dropdown-footer {
          border-top: 1px solid #f1f5f9;
          padding: 8px;
          background: #f8fafc;
        }

        .notification-dropdown-footer button {
          width: 100%;
          padding: 8px;
          background: transparent;
          border: none;
          border-radius: 6px;
          color: #6366f1;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }

        .notification-dropdown-footer button:hover {
          background: #eef2ff;
          color: #4f46e5;
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
      `}</style>
    </div>
  );
}

export default NotificationDropdown;
