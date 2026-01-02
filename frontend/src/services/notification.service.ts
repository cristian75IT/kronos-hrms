import api from './api';

export const NotificationChannel = {
    EMAIL: 'email',
    IN_APP: 'in_app',
    PUSH: 'push',
    SMS: 'sms',
} as const;
export type NotificationChannel = typeof NotificationChannel[keyof typeof NotificationChannel];

export const NotificationStatus = {
    PENDING: 'pending',
    SENT: 'sent',
    DELIVERED: 'delivered',
    READ: 'read',
    FAILED: 'failed',
} as const;
export type NotificationStatus = typeof NotificationStatus[keyof typeof NotificationStatus];

export const NotificationType = {
    LEAVE_REQUEST_SUBMITTED: 'leave_request_submitted',
    LEAVE_REQUEST_APPROVED: 'leave_request_approved',
    LEAVE_REQUEST_REJECTED: 'leave_request_rejected',
    LEAVE_REQUEST_CANCELLED: 'leave_request_cancelled',
    LEAVE_CONDITIONAL_APPROVAL: 'leave_conditional_approval',
    LEAVE_BALANCE_LOW: 'leave_balance_low',
    LEAVE_UPCOMING_REMINDER: 'leave_upcoming_reminder',
    TRIP_SUBMITTED: 'trip_submitted',
    TRIP_APPROVED: 'trip_approved',
    TRIP_REJECTED: 'trip_rejected',
    EXPENSE_SUBMITTED: 'expense_submitted',
    EXPENSE_APPROVED: 'expense_approved',
    EXPENSE_REJECTED: 'expense_rejected',
    EXPENSE_PAID: 'expense_paid',
    CALENDAR_SYSTEM_DEADLINE: 'calendar_system_deadline',
    CALENDAR_PERSONAL_DEADLINE: 'calendar_personal_deadline',
    CALENDAR_SHARED_DEADLINE: 'calendar_shared_deadline',
    SYSTEM_ANNOUNCEMENT: 'system_announcement',
    COMPLIANCE_ALERT: 'compliance_alert',
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'error',
    SUCCESS: 'success',
} as const;
export type NotificationType = typeof NotificationType[keyof typeof NotificationType];

export interface Notification {
    id: string;
    user_id: string;
    notification_type: NotificationType;
    title: string;
    message: string;
    channel: NotificationChannel;
    status: NotificationStatus;
    sent_at?: string;
    read_at?: string;
    action_url?: string;
    created_at: string;
}

export interface UserPreferences {
    email_enabled: boolean;
    in_app_enabled: boolean;
    push_enabled: boolean;
    preferences_matrix: Record<string, Record<string, boolean>>;
    digest_frequency: 'instant' | 'daily' | 'weekly';
}

export interface BulkNotificationRequest {
    notification_type: string;
    title: string;
    message: string;
    user_ids: string[];
    channels: NotificationChannel[];
    action_url?: string;
    payload?: Record<string, any>;
}

export interface HistoryFilters {
    limit?: number;
    offset?: number;
    user_id?: string;
    notification_type?: string;
    status?: string;
}

const notificationService = {
    sendBulk: async (data: BulkNotificationRequest) => {
        await api.post('/notifications/bulk', data);
    },

    getHistory: async (filters: HistoryFilters = {}) => {
        const queryParams = new URLSearchParams();
        if (filters.limit) queryParams.append('limit', filters.limit.toString());
        if (filters.offset) queryParams.append('offset', filters.offset.toString());
        if (filters.user_id) queryParams.append('user_id', filters.user_id);
        if (filters.notification_type) queryParams.append('notification_type', filters.notification_type);
        if (filters.status) queryParams.append('status', filters.status);

        const response = await api.get<Notification[]>(`/notifications/history?${queryParams.toString()}`);
        return response.data;
    },

    getNotifications: async (unreadOnly = false, limit = 50) => {
        const response = await api.get<Notification[]>('/notifications', {
            params: { unread_only: unreadOnly, limit },
        });
        return response.data;
    },

    getUnreadCount: async () => {
        const response = await api.get<{ count: number }>('/notifications/unread-count');
        return response.data.count;
    },

    markAsRead: async (notificationIds: string[]) => {
        await api.post('/notifications/mark-read', { notification_ids: notificationIds });
    },

    markAllAsRead: async () => {
        await api.post('/notifications/mark-all-read');
    },

    getPreferences: async () => {
        const response = await api.get<UserPreferences>('/notifications/preferences');
        return response.data;
    },

    updatePreferences: async (preferences: Partial<UserPreferences>) => {
        const response = await api.put<UserPreferences>('/notifications/preferences', preferences);
        return response.data;
    },

    // Push Subscription Placeholder
    subscribeToPush: async (subscription: unknown) => {
        await api.post('/notifications/push-subscriptions', subscription);
    },
};

export default notificationService;
