/**
 * KRONOS - Notification Dropdown Component
 * 
 * Dropdown bell menu for the header showing recent notifications.
 */
import { Bell, CheckCheck, ExternalLink } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import notificationService, { NotificationStatus, NotificationType } from '../../services/notification.service';
import type { Notification } from '../../services/notification.service';
import { useNavigate } from 'react-router-dom';

interface NotificationDropdownProps {

    onUnreadCountChange?: (count: number) => void;
}

export function NotificationDropdown({ onUnreadCountChange }: NotificationDropdownProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [loading, setLoading] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();

    // Fetch unread count on mount and periodically
    useEffect(() => {
        fetchUnreadCount();
        const interval = setInterval(fetchUnreadCount, 30000); // Poll every 30 seconds
        return () => clearInterval(interval);
    }, []);

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const fetchUnreadCount = async () => {
        try {
            const count = await notificationService.getUnreadCount();
            setUnreadCount(count);
            onUnreadCountChange?.(count);
        } catch (error) {
            console.error('Failed to fetch unread count:', error);
        }
    };

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
        }
        setIsOpen(!isOpen);
    };

    const handleMarkAsRead = async (notificationIds: string[]) => {
        try {
            await notificationService.markAsRead(notificationIds);
            setNotifications(prev =>
                prev.map(n =>
                    notificationIds.includes(n.id)
                        ? { ...n, status: NotificationStatus.READ, read_at: new Date().toISOString() }
                        : n
                )
            );
            fetchUnreadCount();
        } catch (error) {
            console.error('Failed to mark as read:', error);
        }
    };

    const handleMarkAllAsRead = async () => {
        try {
            await notificationService.markAllAsRead();
            setNotifications(prev =>
                prev.map(n => ({ ...n, status: NotificationStatus.READ, read_at: new Date().toISOString() }))
            );
            setUnreadCount(0);
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

    const getNotificationIcon = (type: NotificationType): string => {
        if (type.startsWith('leave_')) return '📋';
        if (type.startsWith('calendar_')) return '📅';
        if (type.startsWith('expense_') || type.startsWith('trip_')) return '💰';
        if (type === NotificationType.SYSTEM_ANNOUNCEMENT) return '📢';
        if (type === NotificationType.COMPLIANCE_ALERT) return '⚠️';
        return '🔔';
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
                            <div className="notification-loading">Caricamento...</div>
                        ) : notifications.length === 0 ? (
                            <div className="notification-empty">
                                <Bell size={32} className="notification-empty-icon" />
                                <p>Nessuna notifica</p>
                            </div>
                        ) : (
                            notifications.map(notification => (
                                <div
                                    key={notification.id}
                                    className={`notification-item ${notification.status !== NotificationStatus.READ ? 'unread' : ''}`}
                                    onClick={() => handleNotificationClick(notification)}
                                >
                                    <div className="notification-icon">
                                        {getNotificationIcon(notification.notification_type)}
                                    </div>
                                    <div className="notification-content">
                                        <span className="notification-title">{notification.title}</span>
                                        <span className="notification-message">{notification.message}</span>
                                        <span className="notification-time">{formatTimeAgo(notification.created_at)}</span>
                                    </div>
                                    {notification.action_url && (
                                        <ExternalLink size={14} className="notification-action-icon" />
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
          padding: var(--space-2);
          background: transparent;
          border: 1px solid transparent;
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .notification-dropdown-trigger:hover {
          background: var(--color-bg-hover);
          color: var(--color-text-primary);
          border-color: var(--color-border);
        }

        .notification-badge {
          position: absolute;
          top: 2px;
          right: 2px;
          min-width: 18px;
          height: 18px;
          padding: 0 4px;
          background: var(--color-danger);
          color: white;
          font-size: 10px;
          font-weight: 600;
          border-radius: var(--radius-full);
          display: flex;
          align-items: center;
          justify-content: center;
          border: 2px solid var(--color-bg-primary);
        }

        .notification-dropdown-menu {
          position: absolute;
          top: calc(100% + 8px);
          right: 0;
          width: 360px;
          max-height: 480px;
          background: var(--color-bg-primary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
          box-shadow: var(--shadow-lg);
          overflow: hidden;
          z-index: var(--z-popover);
          animation: slideDown 0.15s ease-out;
        }

        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .notification-dropdown-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--space-4);
          border-bottom: 1px solid var(--color-border);
        }

        .notification-dropdown-header h3 {
          font-size: var(--font-size-base);
          font-weight: 600;
          color: var(--color-text-primary);
          margin: 0;
        }

        .notification-mark-all {
          padding: var(--space-1) var(--space-2);
          background: transparent;
          border: none;
          border-radius: var(--radius-sm);
          color: var(--color-primary);
          cursor: pointer;
          transition: background var(--transition-fast);
        }

        .notification-mark-all:hover {
          background: var(--color-bg-hover);
        }

        .notification-dropdown-content {
          max-height: 360px;
          overflow-y: auto;
        }

        .notification-loading,
        .notification-empty {
          padding: var(--space-8);
          text-align: center;
          color: var(--color-text-muted);
        }

        .notification-empty-icon {
          color: var(--color-text-muted);
          margin-bottom: var(--space-2);
          opacity: 0.5;
        }

        .notification-item {
          display: flex;
          align-items: flex-start;
          gap: var(--space-3);
          padding: var(--space-3) var(--space-4);
          cursor: pointer;
          transition: background var(--transition-fast);
          border-bottom: 1px solid var(--color-border-light);
        }

        .notification-item:hover {
          background: var(--color-bg-hover);
        }

        .notification-item.unread {
          background: var(--color-bg-tertiary);
        }

        .notification-item.unread::before {
          content: '';
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 3px;
          background: var(--color-primary);
        }

        .notification-icon {
          font-size: 20px;
          flex-shrink: 0;
        }

        .notification-content {
          flex: 1;
          min-width: 0;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .notification-title {
          font-size: var(--font-size-sm);
          font-weight: 500;
          color: var(--color-text-primary);
        }

        .notification-message {
          font-size: var(--font-size-xs);
          color: var(--color-text-secondary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .notification-time {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .notification-action-icon {
          color: var(--color-text-muted);
          flex-shrink: 0;
          margin-top: 2px;
        }

        .notification-dropdown-footer {
          border-top: 1px solid var(--color-border);
          padding: var(--space-2);
        }

        .notification-dropdown-footer button {
          width: 100%;
          padding: var(--space-2);
          background: transparent;
          border: none;
          border-radius: var(--radius-md);
          color: var(--color-primary);
          font-size: var(--font-size-sm);
          font-weight: 500;
          cursor: pointer;
          transition: background var(--transition-fast);
        }

        .notification-dropdown-footer button:hover {
          background: var(--color-bg-hover);
        }
      `}</style>
        </div>
    );
}

export default NotificationDropdown;
