/**
 * KRONOS - Notifications Domain Hook
 * 
 * React Query hooks for notification data fetching and mutations.
 * Replaces manual useState + useEffect patterns.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import notificationService, { NotificationStatus } from '../../services/notification.service';
import type { Notification, UserPreferences } from '../../services/notification.service';

// Query Keys
export const notificationKeys = {
    all: ['notifications'] as const,
    list: (filters: NotificationFilters) => [...notificationKeys.all, 'list', filters] as const,
    preferences: ['notifications', 'preferences'] as const,
};

export interface NotificationFilters {
    unreadOnly: boolean;
    channel: string;
    typeFilter: 'all' | 'unread' | 'leave' | 'calendar' | 'system';
}

/**
 * Hook to fetch notifications with filtering
 */
export function useNotifications(filters: NotificationFilters) {
    return useQuery({
        queryKey: notificationKeys.list(filters),
        queryFn: async () => {
            const data = await notificationService.getNotifications(
                filters.unreadOnly || filters.typeFilter === 'unread',
                100,
                filters.channel
            );

            // Apply type filters client-side (could be moved to backend)
            let filtered = data;
            if (filters.typeFilter === 'leave') {
                filtered = data.filter(n => n.notification_type.startsWith('leave_'));
            } else if (filters.typeFilter === 'calendar') {
                filtered = data.filter(n => n.notification_type.startsWith('calendar_'));
            } else if (filters.typeFilter === 'system') {
                filtered = data.filter(n =>
                    n.notification_type === 'system_announcement' ||
                    n.notification_type === 'compliance_alert'
                );
            }

            return filtered;
        },
        staleTime: 30 * 1000, // 30 seconds
    });
}

/**
 * Hook to fetch user preferences
 */
export function useNotificationPreferences() {
    return useQuery({
        queryKey: notificationKeys.preferences,
        queryFn: async () => {
            try {
                return await notificationService.getPreferences();
            } catch {
                // Return defaults if API fails
                return {
                    email_enabled: true,
                    in_app_enabled: true,
                    push_enabled: true,
                    preferences_matrix: {},
                    digest_frequency: 'instant',
                } as UserPreferences;
            }
        },
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

/**
 * Hook to update user preferences
 */
export function useUpdatePreferences() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (preferences: UserPreferences) =>
            notificationService.updatePreferences(preferences),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: notificationKeys.preferences });
        },
    });
}

/**
 * Hook to mark notifications as read
 */
export function useMarkNotificationsAsRead() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (ids: string[]) => notificationService.markAsRead(ids),
        onSuccess: () => {
            // Invalidate all notification queries to refetch
            queryClient.invalidateQueries({ queryKey: notificationKeys.all });
        },
        onMutate: async (ids: string[]) => {
            // Optimistic update: mark as read immediately in cache
            await queryClient.cancelQueries({ queryKey: notificationKeys.all });

            // Update all cached notification lists
            queryClient.setQueriesData<Notification[]>(
                { queryKey: notificationKeys.all },
                (old) => old?.map(n =>
                    ids.includes(n.id)
                        ? { ...n, status: NotificationStatus.READ, read_at: new Date().toISOString() }
                        : n
                )
            );
        },
    });
}

/**
 * Hook to mark all notifications as read
 */
export function useMarkAllNotificationsAsRead() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: () => notificationService.markAllAsRead(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: notificationKeys.all });
        },
        onMutate: async () => {
            await queryClient.cancelQueries({ queryKey: notificationKeys.all });

            queryClient.setQueriesData<Notification[]>(
                { queryKey: notificationKeys.all },
                (old) => old?.map(n => ({
                    ...n,
                    status: NotificationStatus.READ,
                    read_at: new Date().toISOString()
                }))
            );
        },
    });
}
