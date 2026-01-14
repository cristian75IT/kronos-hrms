/**
 * KRONOS - Notification List Item Component
 */
import { Check } from 'lucide-react';
import { NotificationStatus } from '../../services/notification.service';
import type { Notification } from '../../services/notification.service';
import { NotificationIcon } from './NotificationIcon';

interface NotificationItemProps {
    notification: Notification;
    isSelected: boolean;
    onToggleSelect: (id: string) => void;
    onMarkAsRead: (ids: string[]) => void;
}

export function NotificationItem({
    notification,
    isSelected,
    onToggleSelect,
    onMarkAsRead
}: NotificationItemProps) {
    const isUnread = notification.status !== NotificationStatus.READ;

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

    return (
        <div className={`notification-row ${isUnread ? 'unread' : ''}`}>
            <label className="checkbox-wrapper">
                <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => onToggleSelect(notification.id)}
                />
            </label>
            <NotificationIcon type={notification.notification_type} />
            <div className="notification-content">
                <div className="notification-top">
                    <span className="notification-title">{notification.title}</span>
                    <span className="notification-type-badge">
                        {getTypeLabel(notification.notification_type)}
                    </span>
                    <span className="notification-time ml-auto">
                        {formatDate(notification.created_at)}
                    </span>
                </div>
                <p className="notification-message">{notification.message}</p>
            </div>
            <div className="notification-actions">
                {isUnread && (
                    <button
                        className="icon-btn"
                        onClick={() => onMarkAsRead([notification.id])}
                        title="Segna come letta"
                    >
                        <Check size={16} />
                    </button>
                )}
            </div>
        </div>
    );
}
