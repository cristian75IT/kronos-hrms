/**
 * KRONOS - Push Notification Utilities
 * 
 * Utility functions for managing Web Push notifications.
 */

// Check if push notifications are supported
export function isPushSupported(): boolean {
    return 'serviceWorker' in navigator && 'PushManager' in window;
}

// Check current permission status
export function getPushPermission(): NotificationPermission | 'unsupported' {
    if (!isPushSupported()) return 'unsupported';
    return Notification.permission;
}

// Request push notification permission
export async function requestPushPermission(): Promise<NotificationPermission> {
    if (!isPushSupported()) {
        throw new Error('Push notifications are not supported');
    }

    const permission = await Notification.requestPermission();
    return permission;
}

// Register service worker and get push subscription
export async function subscribeToPush(
    vapidPublicKey: string
): Promise<PushSubscriptionJSON | null> {
    if (!isPushSupported()) {
        console.warn('Push notifications are not supported');
        return null;
    }

    try {
        // Register service worker
        const registration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/'
        });

        console.log('[Push] Service worker registered:', registration);

        // Wait for service worker to be ready
        await navigator.serviceWorker.ready;

        // Check and request permission
        let permission = Notification.permission;
        if (permission === 'default') {
            permission = await requestPushPermission();
        }

        if (permission !== 'granted') {
            console.warn('[Push] Permission denied');
            return null;
        }

        // Subscribe to push
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
        });

        console.log('[Push] Subscription created:', subscription);

        return subscription.toJSON();
    } catch (error) {
        console.error('[Push] Failed to subscribe:', error);
        throw error;
    }
}

// Unsubscribe from push notifications
export async function unsubscribeFromPush(): Promise<boolean> {
    if (!isPushSupported()) return false;

    try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();

        if (subscription) {
            await subscription.unsubscribe();
            console.log('[Push] Unsubscribed successfully');
            return true;
        }

        return false;
    } catch (error) {
        console.error('[Push] Failed to unsubscribe:', error);
        return false;
    }
}

// Get current push subscription
export async function getCurrentSubscription(): Promise<PushSubscriptionJSON | null> {
    if (!isPushSupported()) return null;

    try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        return subscription?.toJSON() || null;
    } catch (error) {
        console.error('[Push] Failed to get subscription:', error);
        return null;
    }
}

// Convert VAPID public key to Uint8Array for subscription
function urlBase64ToUint8Array(base64String: string): ArrayBuffer {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray.buffer as ArrayBuffer;
}


// Format subscription for backend API
export function formatSubscriptionForApi(subscription: PushSubscriptionJSON) {
    return {
        endpoint: subscription.endpoint,
        p256dh: subscription.keys?.p256dh || '',
        auth: subscription.keys?.auth || '',
        device_info: {
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            timestamp: new Date().toISOString(),
        }
    };
}
