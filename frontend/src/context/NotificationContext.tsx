import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import notificationService from '../services/notification.service';
import { useAuth } from './AuthContext';

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

    // Poll for unread count
    useEffect(() => {
        if (!isAuthenticated) return;

        refreshUnreadCount();
        const interval = setInterval(refreshUnreadCount, 30000); // 30s
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
