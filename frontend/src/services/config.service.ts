/**
 * KRONOS - Configuration Service
 */
import { configApi } from './api';

export interface SystemConfig {
    key: string;
    value: any;
    value_type: 'string' | 'integer' | 'boolean' | 'float' | 'json';
    category: string;
    description?: string;
}

export const configService = {
    getAllConfigs: async (): Promise<SystemConfig[]> => {
        const response = await configApi.get('/config');
        return response.data;
    },

    getConfig: async (key: string): Promise<SystemConfig> => {
        const response = await configApi.get(`/config/${key}`);
        return response.data;
    },

    updateConfig: async (key: string, value: any): Promise<SystemConfig> => {
        const response = await configApi.put(`/config/${key}`, { value });
        return response.data;
    },

    clearCache: async (): Promise<{ message: string }> => {
        const response = await configApi.post('/config/cache/clear');
        return response.data;
    },
};
