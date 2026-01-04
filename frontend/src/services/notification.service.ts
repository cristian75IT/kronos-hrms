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
    channel?: string;
}

export interface EmailEvent {
    event: string;
    email: string;
    date: string;
    messageId?: string;
    subject?: string;
    tag?: string;
    from?: string;
    templateId?: number;
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
        if (filters.channel) queryParams.append('channel', filters.channel);

        const response = await api.get<Notification[]>(`/notifications/history?${queryParams.toString()}`);
        return response.data;
    },

    getNotifications: async (unreadOnly = false, limit = 50, channel?: string) => {
        const response = await api.get<Notification[]>('/notifications', {
            params: { unread_only: unreadOnly, limit, channel },
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

    // Email Logs
    getEmailLogs: async (filters: { limit?: number; offset?: number; status?: string; template_code?: string; to_email?: string } = {}) => {
        const queryParams = new URLSearchParams();
        if (filters.limit) queryParams.append('limit', filters.limit.toString());
        if (filters.offset) queryParams.append('offset', filters.offset.toString());
        if (filters.status) queryParams.append('status', filters.status);
        if (filters.template_code) queryParams.append('template_code', filters.template_code);
        if (filters.to_email) queryParams.append('to_email', filters.to_email);

        const response = await api.get<EmailLog[]>(`/notifications/email-logs?${queryParams.toString()}`);
        return response.data;
    },

    getEmailStats: async (days: number = 7) => {
        const response = await api.get<any>(`/notifications/email-logs/stats?days=${days}`);
        return response.data;
    },

    retryEmail: async (id: string) => {
        const response = await api.post<EmailLog>(`/notifications/email-logs/${id}/retry`);
        return response.data;
    },

    getEmailEvents: async (id: string): Promise<EmailEvent[]> => {
        const response = await api.get<EmailEvent[]>(`/notifications/email-logs/${id}/events`);
        return response.data;
    },

    // Email Provider Settings
    getProviderSettings: async () => {
        const response = await api.get<EmailProviderSettings>('/notifications/settings');
        return response.data;
    },

    createProviderSettings: async (data: EmailProviderSettingsCreate) => {
        const response = await api.post<EmailProviderSettings>('/notifications/settings', data);
        return response.data;
    },

    updateProviderSettings: async (id: string, data: EmailProviderSettingsUpdate) => {
        const response = await api.put<EmailProviderSettings>(`/notifications/settings/${id}`, data);
        return response.data;
    },

    testEmailSettings: async (email: string) => {
        const response = await api.post<{ success: boolean; error?: string }>('/notifications/settings/test', { to_email: email });
        return response.data;
    },

    // Templates
    getTemplates: async (activeOnly = true) => {
        const response = await api.get<EmailTemplate[]>('/notifications/templates', { params: { active_only: activeOnly } });
        return response.data;
    },

    getTemplate: async (id: string) => {
        const response = await api.get<EmailTemplate>(`/notifications/templates/${id}`);
        return response.data;
    },

    createTemplate: async (data: EmailTemplateCreate) => {
        const response = await api.post<EmailTemplate>('/notifications/templates', data);
        return response.data;
    },

    updateTemplate: async (id: string, data: EmailTemplateUpdate) => {
        const response = await api.put<EmailTemplate>(`/notifications/templates/${id}`, data);
        return response.data;
    },

    syncTemplateToBrevo: async (id: string) => {
        const response = await api.post<{ created?: boolean; updated?: boolean; brevo_template_id: number }>(`/notifications/templates/${id}/sync`);
        return response.data;
    },
};

export interface EmailLog {
    id: string;
    to_email: string;
    to_name?: string;
    template_code: string;
    subject?: string;
    variables?: Record<string, any>;
    status: string;
    message_id?: string;
    notification_id?: string;
    error_message?: string;
    retry_count: number;
    next_retry_at?: string;
    created_at: string;
    updated_at: string;
}

export interface EmailProviderSettings {
    id: string;
    provider: string;
    api_key_masked: string;
    sender_email: string;
    sender_name: string;
    reply_to_email?: string;
    reply_to_name?: string;
    is_active: boolean;
    test_mode: boolean;
    test_email?: string;
    daily_limit?: number;
    emails_sent_today: number;
    created_at: string;
    updated_at: string;
}

export interface EmailProviderSettingsCreate {
    provider?: string;
    api_key: string;
    sender_email: string;
    sender_name?: string;
    reply_to_email?: string;
    reply_to_name?: string;
    is_active?: boolean;
    test_mode?: boolean;
    test_email?: string;
    daily_limit?: number;
}

export interface EmailProviderSettingsUpdate {
    api_key?: string;
    sender_email?: string;
    sender_name?: string;
    reply_to_email?: string;
    reply_to_name?: string;
    is_active?: boolean;
    test_mode?: boolean;
    test_email?: string;
    daily_limit?: number;
}

export interface EmailTemplate {
    id: string;
    code: string;
    name: string;
    description?: string;
    notification_type: string;
    brevo_template_id?: number;
    subject?: string;
    html_content?: string;
    text_content?: string;
    available_variables?: string[];
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface EmailTemplateCreate {
    code: string;
    name: string;
    description?: string;
    notification_type: string;
    brevo_template_id?: number;
    subject?: string;
    html_content?: string;
    text_content?: string;
    available_variables?: string[];
}

export interface EmailTemplateUpdate {
    name?: string;
    description?: string;
    brevo_template_id?: number;
    subject?: string;
    html_content?: string;
    text_content?: string;
    available_variables?: string[];
    is_active?: boolean;
}

export default notificationService;
