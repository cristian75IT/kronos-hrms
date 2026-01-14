/**
 * KRONOS - Real-time Sync Hook
 * 
 * Listens for SSE events and custom window events to invalidate
 * React Query cache, enabling automatic UI updates.
 */
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

// Notification type mapping to query keys
const notificationTypeToQueryKeys: Record<string, string[][]> = {
    // Leave related
    'leave_request_submitted': [['leaves'], ['approvals']],
    'leave_request_approved': [['leaves'], ['balances'], ['calendar']],
    'leave_request_rejected': [['leaves']],
    'leave_request_cancelled': [['leaves'], ['balances']],

    // Calendar related
    'calendar_event_created': [['calendar'], ['events']],
    'calendar_event_updated': [['calendar'], ['events']],
    'calendar_holiday_added': [['holidays'], ['calendar']],

    // Expense/Trip related
    'trip_request_submitted': [['trips'], ['approvals']],
    'trip_request_approved': [['trips']],
    'trip_request_rejected': [['trips']],
    'expense_report_submitted': [['expenses'], ['approvals']],
    'expense_report_approved': [['expenses']],

    // System
    'system_announcement': [['notifications']],
    'compliance_alert': [['hr'], ['compliance']],

    // Approvals
    'approval_needed': [['approvals']],
    'approval_completed': [['approvals'], ['leaves'], ['trips'], ['expenses']],
};

/**
 * Hook to sync React Query cache with real-time events
 */
export function useRealtimeSync() {
    const queryClient = useQueryClient();

    useEffect(() => {
        const handleNotification = (event: CustomEvent<any>) => {
            const notification = event.detail;
            const notificationType = notification?.notification_type || notification?.type;

            console.log('[RealtimeSync] Received notification:', notificationType);

            // Invalidate notification queries always
            queryClient.invalidateQueries({ queryKey: ['notifications'] });

            // Invalidate specific queries based on notification type
            const queryKeysToInvalidate = notificationTypeToQueryKeys[notificationType];
            if (queryKeysToInvalidate) {
                queryKeysToInvalidate.forEach((queryKey) => {
                    console.log('[RealtimeSync] Invalidating:', queryKey);
                    queryClient.invalidateQueries({ queryKey });
                });
            }

            // Also invalidate dashboard/overview data
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
            queryClient.invalidateQueries({ queryKey: ['hr', 'dashboard'] });
        };

        // Listen for custom notification events
        window.addEventListener('notification:received', handleNotification as EventListener);

        // Listen for manual refresh events
        const handleManualRefresh = () => {
            queryClient.invalidateQueries();
        };
        window.addEventListener('data:refresh', handleManualRefresh);

        return () => {
            window.removeEventListener('notification:received', handleNotification as EventListener);
            window.removeEventListener('data:refresh', handleManualRefresh);
        };
    }, [queryClient]);
}

/**
 * Utility to trigger a manual refresh of all data
 */
export function triggerDataRefresh() {
    window.dispatchEvent(new CustomEvent('data:refresh'));
}
