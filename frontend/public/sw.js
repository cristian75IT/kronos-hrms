/**
 * KRONOS - Service Worker for Push Notifications
 * 
 * This file should be placed in the public folder (e.g., public/sw.js)
 * and registered from the main application.
 */

// Cache name for offline support
const CACHE_NAME = 'kronos-v1';

// Install event - cache essential resources
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    event.waitUntil(clients.claim());
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
    console.log('[SW] Push received:', event);

    let data = {
        title: 'KRONOS',
        body: 'Nuova notifica',
        icon: '/icons/notification-icon.png',
        badge: '/icons/badge-icon.png',
        data: { url: '/notifications' }
    };

    // Parse push data if available
    if (event.data) {
        try {
            data = { ...data, ...event.data.json() };
        } catch (e) {
            console.error('[SW] Error parsing push data:', e);
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body,
        icon: data.icon || '/icons/notification-icon.png',
        badge: data.badge || '/icons/badge-icon.png',
        tag: data.tag || 'kronos-notification',
        renotify: true,
        requireInteraction: false,
        vibrate: [200, 100, 200],
        data: data.data || {},
        actions: [
            { action: 'open', title: 'Apri' },
            { action: 'dismiss', title: 'Ignora' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click event - handle user interaction
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event);

    event.notification.close();

    if (event.action === 'dismiss') {
        return;
    }

    // Open the URL from notification data
    const urlToOpen = event.notification.data?.url || '/notifications';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Check if app is already open
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        client.navigate(urlToOpen);
                        return client.focus();
                    }
                }
                // Open new window if not
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Notification close event
self.addEventListener('notificationclose', (event) => {
    console.log('[SW] Notification closed:', event);
});

// Background sync for marking notifications as read
self.addEventListener('sync', (event) => {
    if (event.tag === 'mark-notification-read') {
        console.log('[SW] Syncing notification read status...');
        // Implementation for background sync if needed
    }
});
