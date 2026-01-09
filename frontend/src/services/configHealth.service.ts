/**
 * KRONOS - Config Health Service
 * Enterprise configuration validation - checks required system configs
 */
import api from './api';

export interface ConfigHealthItem {
    config_type: string;
    name: string;
    status: 'ok' | 'missing';
    message?: string;
}

export interface ConfigHealthResponse {
    overall_status: 'ok' | 'warning' | 'critical';
    items: ConfigHealthItem[];
    missing_count: number;
}

export const configHealthService = {
    /**
     * Get configuration health status
     * Returns status of all required configurations (workflows, etc.)
     */
    getConfigHealth: async (): Promise<ConfigHealthResponse> => {
        const response = await api.get('/approvals/internal/health/config');
        return response.data;
    },
};
