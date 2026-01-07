/**
 * KRONOS - API Client with Axios
 */
import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { tokenStorage } from '../utils/tokenStorage';
import { authService } from './authService';

// Create axios instance
const api: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Helper to add auth token and handle refresh
const setupInterceptors = (instance: AxiosInstance) => {
    // Request interceptor
    instance.interceptors.request.use(
        async (config: InternalAxiosRequestConfig) => {
            let token = tokenStorage.getAccessToken();

            // Check expiration proactively
            if (token) {
                try {
                    const parts = token.split('.');
                    if (parts.length === 3) {
                        const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
                        const exp = payload.exp * 1000;
                        if (Date.now() > exp - 10000) { // Refresh if exp < 10s away
                            const refresh = tokenStorage.getRefreshToken();
                            if (refresh) {
                                // Double check if another refresh is already running?
                                // For simplicity, just refresh
                                const newTokens = await authService.refreshToken(refresh);
                                tokenStorage.setTokens(newTokens.access_token, newTokens.refresh_token);
                                token = newTokens.access_token;
                            }
                        }
                    }
                } catch (e) {
                    // Ignore decoding errors
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

            // 2. Global Error Handling
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data as any;

                // Extract meaningful message
                let message = 'Si è verificato un errore imprevisto'; // Default fallback

                // Priority 1: KRONOS Standard Error format { error: { message: ... } }
                if (data?.error?.message) {
                    message = data.error.message;
                }
                // Priority 2: FastAPI HTTP Exception format { detail: ... }
                else if (data?.detail) {
                    if (typeof data.detail === 'string') {
                        message = data.detail;
                    } else if (Array.isArray(data.detail)) {
                        // Pydantic validation errors
                        message = data.detail.map((e: any) => e.msg).join(', ');
                    }
                }
                // Priority 3: Generic message field
                else if (data?.message) {
                    message = data.message;
                }

                // Dispatch Global Toast Event
                // We skip 401 because it's handled by refresh or logout flow above
                if (status !== 401) {
                    window.dispatchEvent(new CustomEvent('toast:show', {
                        detail: {
                            message: `[${status}] ${message}`,
                            type: 'error',
                            duration: 6000
                        }
                    }));
                }
            } else if (error.request) {
                // Network Error (no response)
                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: {
                        message: 'Impossibile contattare il server. Verifica la connessione.',
                        type: 'error',
                        duration: 6000
                    }
                }));
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
