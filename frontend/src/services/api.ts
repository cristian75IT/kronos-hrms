/**
 * KRONOS - API Client with Axios
 */
import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { tokenStorage } from '../utils/tokenStorage';
import { jwtDecode } from 'jwt-decode';
import { authService } from './authService';

// Create axios instance
const api: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Error deduplication: prevents the same error from triggering multiple toasts
const recentErrors = new Set<string>();



interface ApiErrorResponse {
    error?: {
        message: string;
        code?: string;
        request_id?: string;
    };
    detail?: string | Array<{ loc: string[]; msg: string }>;
    message?: string;
}

// ... imports remain the same

// Helper to add auth token and handle refresh
const setupInterceptors = (instance: AxiosInstance) => {
    // Request interceptor
    instance.interceptors.request.use(
        async (config: InternalAxiosRequestConfig) => {
            let token = tokenStorage.getAccessToken();

            // Check expiration proactively
            if (token) {
                try {
                    const decoded = jwtDecode<{ exp: number }>(token);
                    const exp = decoded.exp * 1000;
                    if (Date.now() > exp - 10000) { // Refresh if exp < 10s away
                        const refresh = tokenStorage.getRefreshToken();
                        if (refresh) {
                            try {
                                const newTokens = await authService.refreshToken(refresh);
                                tokenStorage.setTokens(newTokens.access_token, newTokens.refresh_token);
                                token = newTokens.access_token;
                            } catch (refreshError) {
                                // Refresh failed - session expired, trigger logout
                                console.warn('Proactive token refresh failed, logging out');
                                tokenStorage.clear();
                                window.dispatchEvent(new Event('auth:logout'));
                                return Promise.reject(refreshError);
                            }
                        } else {
                            // No refresh token available - logout
                            tokenStorage.clear();
                            window.dispatchEvent(new Event('auth:logout'));
                            return Promise.reject(new Error('Session expired'));
                        }
                    }
                } catch (e) {
                    // Token decoding error - token is malformed, logout
                    console.warn('Token decode error, logging out');
                    tokenStorage.clear();
                    window.dispatchEvent(new Event('auth:logout'));
                    return Promise.reject(e);
                }

                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        },
        (error) => Promise.reject(error)
    );

    // Response interceptor
    instance.interceptors.response.use(
        (response) => response,
        async (error: AxiosError) => {
            const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

            // 1. Handle Token Expiration (401)
            if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
                originalRequest._retry = true;

                try {
                    const refresh = tokenStorage.getRefreshToken();
                    if (!refresh) throw new Error('No refresh token');

                    const newTokens = await authService.refreshToken(refresh);
                    tokenStorage.setTokens(newTokens.access_token, newTokens.refresh_token);

                    originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`;
                    return instance(originalRequest);
                } catch (refreshError) {
                    tokenStorage.clear();
                    window.dispatchEvent(new Event('auth:logout'));
                    return Promise.reject(refreshError);
                }
            }

            // 2. Enterprise Error Handling with Smart Parsing
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data as ApiErrorResponse;

                // Extract meaningful message with priority parsing
                let message = 'Si è verificato un errore imprevisto';
                let requestId: string | undefined;
                let errorCode: string | undefined;

                // Priority 1: KRONOS Standard Error format { error: { message: ..., code: ..., request_id: ... } }
                if (data?.error?.message) {
                    message = data.error.message;
                    requestId = data.error.request_id;
                    errorCode = data.error.code;
                }
                // Priority 2: FastAPI HTTP Exception format { detail: ... }
                else if (data?.detail) {
                    if (typeof data.detail === 'string') {
                        message = data.detail;
                    } else if (Array.isArray(data.detail)) {
                        // Pydantic validation errors
                        message = data.detail.map((e) => `${e.loc?.slice(-1)?.[0] || 'campo'}: ${e.msg}`).join('; ');
                    }
                }
                // Priority 3: Generic message field
                else if (data?.message) {
                    message = data.message;
                }

                // Categorize error severity
                const severity = status >= 500 ? 'critical' : status >= 400 ? 'error' : 'warning';

                // Build display message
                let displayMessage = `[${status}] ${message}`;

                // For 5xx errors, append request ID for debugging
                if (status >= 500 && requestId) {
                    displayMessage += ` (Ref: ${requestId.slice(0, 8)})`;
                }

                // Deduplication: prevent same error toast within 2 seconds
                const errorKey = `${status}-${errorCode || message.slice(0, 50)}`;
                if (!recentErrors.has(errorKey)) {
                    recentErrors.add(errorKey);
                    setTimeout(() => recentErrors.delete(errorKey), 2000);

                    // Dispatch Global Toast Event (skip 401 - handled by refresh/logout)
                    if (status !== 401) {
                        // Special handling for CONFIG_MISSING errors (HTTP 503)
                        // Enterprise Pattern: Fail Fast with actionable guidance
                        if (status === 503 && errorCode === 'CONFIG_MISSING') {
                            const configType = (data?.error as any)?.details?.config_type || 'sconosciuta';
                            const guidance = (data?.error as any)?.details?.guidance ||
                                'Contatta l\'amministratore di sistema per configurare questa funzionalità.';

                            displayMessage = `⚠️ Funzionalità non disponibile: ${message}`;

                            // Show extended toast with guidance
                            window.dispatchEvent(new CustomEvent('toast:show', {
                                detail: {
                                    message: displayMessage,
                                    type: 'warning',
                                    duration: 10000 // Longer duration for config errors
                                }
                            }));

                            // Log for debugging
                            console.warn(`[CONFIG_MISSING] ${configType}: ${guidance}`);
                        } else {
                            window.dispatchEvent(new CustomEvent('toast:show', {
                                detail: {
                                    message: displayMessage,
                                    type: severity === 'critical' ? 'error' : severity,
                                    duration: severity === 'critical' ? 8000 : 6000
                                }
                            }));
                        }
                    }
                }
            } else if (error.request) {
                // Network Error (no response)
                const errorKey = 'network-error';
                if (!recentErrors.has(errorKey)) {
                    recentErrors.add(errorKey);
                    setTimeout(() => recentErrors.delete(errorKey), 3000);

                    window.dispatchEvent(new CustomEvent('toast:show', {
                        detail: {
                            message: 'Impossibile contattare il server. Verifica la connessione.',
                            type: 'error',
                            duration: 6000
                        }
                    }));
                }
            }

            return Promise.reject(error);
        }
    );
};

setupInterceptors(api);

export default api;

// ═══════════════════════════════════════════════════════════════════
// Service-specific API instances
// ═══════════════════════════════════════════════════════════════════

const GATEWAY_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const authApi = axios.create({
    baseURL: GATEWAY_URL,
    timeout: 10000,
});

export const leavesApi = axios.create({
    baseURL: GATEWAY_URL,
    timeout: 10000,
});

export const expensesApi = axios.create({
    baseURL: GATEWAY_URL,
    timeout: 10000,
});

export const configApi = axios.create({
    baseURL: GATEWAY_URL,
    timeout: 10000,
});

export const auditApi = axios.create({
    baseURL: GATEWAY_URL,
    timeout: 10000,
});

export const walletsApi = axios.create({
    baseURL: GATEWAY_URL,
    timeout: 10000,
});

export const hrApi = axios.create({
    baseURL: GATEWAY_URL,
    timeout: 30000,
});

// Setup interceptors for all services
[authApi, leavesApi, expensesApi, configApi, auditApi, walletsApi, hrApi].forEach(setupInterceptors);
