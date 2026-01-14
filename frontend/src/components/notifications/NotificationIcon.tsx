/**
 * KRONOS - Notification Icon Component
 */
import {
    ClipboardList,
    Calendar,
    Receipt,
    Megaphone,
    ShieldAlert,
    Info
} from 'lucide-react';
import { NotificationType } from '../../services/notification.service';

interface NotificationIconProps {
    type: string;
}

export function NotificationIcon({ type }: NotificationIconProps) {
    const getIcon = () => {
        if (type.startsWith('leave_')) return <ClipboardList size={22} className="text-blue-500" />;
        if (type.startsWith('calendar_')) return <Calendar size={22} className="text-indigo-500" />;
        if (type.startsWith('expense_') || type.startsWith('trip_')) return <Receipt size={22} className="text-purple-500" />;
        if (type === NotificationType.SYSTEM_ANNOUNCEMENT) return <Megaphone size={22} className="text-amber-500" />;
        if (type === NotificationType.COMPLIANCE_ALERT) return <ShieldAlert size={22} className="text-red-500" />;
        return <Info size={22} className="text-gray-500" />;
    };

    const getBackground = () => {
        if (type.startsWith('leave_')) return 'bg-blue-50';
        if (type.startsWith('calendar_')) return 'bg-indigo-50';
        if (type.startsWith('expense_') || type.startsWith('trip_')) return 'bg-purple-50';
        if (type === NotificationType.SYSTEM_ANNOUNCEMENT) return 'bg-amber-50';
        if (type === NotificationType.COMPLIANCE_ALERT) return 'bg-red-50';
        return 'bg-gray-50';
    };

    return (
        <div className={`notification-icon-wrapper ${getBackground()}`}>
            {getIcon()}
        </div>
    );
}
