
import { useEffect, useRef, useState } from 'react';
import { tokenStorage } from '../utils/tokenStorage';
import { authService } from '../services/authService';
import { jwtDecode } from 'jwt-decode';
import type { Notification } from '../services/notification.service';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export function useNotificationStream(onMessage: (notification: Notification) => void) {
    const [isConnected, setIsConnected] = useState(false);
    const eventSourceRef = useRef<EventSource | null>(null);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        const connect = async () => {
            let token = tokenStorage.getAccessToken();

            if (!token) {
                return;
            }

            // Check expiration and refresh if needed
            try {
                const decoded = jwtDecode<{ exp: number }>(token);
                // Refresh if expired or expiring in < 30s
                if (Date.now() >= (decoded.exp * 1000) - 30000) {
                    const refreshToken = tokenStorage.getRefreshToken();
                    if (refreshToken) {
                        const newTokens = await authService.refreshToken(refreshToken);
                        tokenStorage.setTokens(newTokens.access_token, newTokens.refresh_token);
                        token = newTokens.access_token;
                    } else {
                        return;
                    }
                }
            } catch (e) {
                return;
            }

            // Close existing connection if any
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
            // Use the debug endpoint temporarily
            const streamUrl = `${API_URL}/notifications/sse-test?token=${encodeURIComponent(token)}`;
            // const streamUrl = `${API_URL}/notifications/stream?token=${encodeURIComponent(token)}`;
            console.log('[SSE] Connecting to:', streamUrl);

            const es = new EventSource(streamUrl);

            es.onopen = () => {
                setIsConnected(true);
            };

            es.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    // Initial connection message check
                    if (data.message === "Connected to notification stream") {
                        return;
                    }
                    console.log('[SSE] New Notification:', data);
                    onMessage(data);
                } catch (e) {
                    console.error('[SSE] Failed to parse message:', e);
                }
            };

            es.onerror = (e) => {
                console.error('[SSE] Error:', e);
                es.close();
                setIsConnected(false);
                eventSourceRef.current = null;

                // Attempt reconnect after 5 seconds
                if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
                reconnectTimeoutRef.current = setTimeout(connect, 5000);
            };

            eventSourceRef.current = es;
        };

        connect();

        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, []); // Run once on mount (reconnect logic calls connect again)

    return { isConnected };
}
