import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import notificationService from '../services/notification.service';
import { useAuth } from './AuthContext';
import { useNotificationStream } from '../hooks/useNotificationStream';

interface NotificationContextType {
    unreadCount: number;
    refreshUnreadCount: () => Promise<void>;
    markAsRead: (ids: string[]) => Promise<void>;
    markAllAsRead: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
    const [unreadCount, setUnreadCount] = useState(0);
    const { isAuthenticated } = useAuth();

    const refreshUnreadCount = useCallback(async () => {
        if (!isAuthenticated) return;
        try {
            const count = await notificationService.getUnreadCount();
            setUnreadCount(count);
        } catch (error) {
            console.error('Failed to update unread count', error);
        }
    }, [isAuthenticated]);

    // SSE Integration
    const handleNotification = (notif: any) => {
        // Increment count
        setUnreadCount(prev => prev + 1);

        // Show Toast
        window.dispatchEvent(new CustomEvent('toast:show', {
            detail: {
                message: notif.title || 'Nuova notifica ricevuta',
                type: 'info', // or generic 'info'
                duration: 5000
            }
        }));

        // Dispatch app-wide event for components to update lists
        window.dispatchEvent(new CustomEvent('notification:received', { detail: notif }));
    };

    useNotificationStream(handleNotification);

    // Poll for unread count (Fallback / Sync)
    useEffect(() => {
        if (!isAuthenticated) return;

        refreshUnreadCount();
        const interval = setInterval(refreshUnreadCount, 300000); // 5 minutes fallback
        return () => clearInterval(interval);
    }, [isAuthenticated, refreshUnreadCount]);

    const markAsRead = async (ids: string[]) => {
        try {
            await notificationService.markAsRead(ids);
            // Optimistic update or refetch? Refetch is safer for count consistency
            await refreshUnreadCount();
        } catch (error) {
            console.error('Failed to mark as read', error);
            throw error;
        }
    };

    const markAllAsRead = async () => {
        try {
            await notificationService.markAllAsRead();
            setUnreadCount(0);
        } catch (error) {
            console.error('Failed to mark all as read', error);
            throw error;
        }
    };

    return (
        <NotificationContext.Provider
            value={{
                unreadCount,
                refreshUnreadCount,
                markAsRead,
                markAllAsRead,
            }}
        >
            {children}
        </NotificationContext.Provider>
    );
}

export function useNotification() {
    const context = useContext(NotificationContext);
    if (context === undefined) {
        throw new Error('useNotification must be used within a NotificationProvider');
    }
    return context;
}
