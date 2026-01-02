/**
 * KRONOS - Configuration Service
 */
import { configApi } from './api';

export interface SystemConfig {
    key: string;
    value: any;
    value_type: 'string' | 'integer' | 'boolean' | 'float' | 'decimal' | 'json';
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

    createConfig: async (data: Omit<SystemConfig, 'value_type'> & { value_type: string }): Promise<SystemConfig> => {
        const response = await configApi.post('/config', data);
        return response.data;
    },

    clearCache: async (): Promise<{ message: string }> => {
        const response = await configApi.post('/config/cache/clear');
        return response.data;
    },

    getNationalContracts: async (): Promise<any[]> => {
        const response = await configApi.get('/national-contracts');
        // Backend returns { items: [...], total: ... }
        return response.data.items || [];
    },

    getNationalContract: async (id: string): Promise<any> => {
        const response = await configApi.get(`/national-contracts/${id}`);
        return response.data;
    },

    createNationalContract: async (data: any): Promise<any> => {
        const response = await configApi.post('/national-contracts', data);
        return response.data;
    },


    updateNationalContract: async (id: string, data: any): Promise<any> => {
        const response = await configApi.put(`/national-contracts/${id}`, data);
        return response.data;
    },

    // Versions
    getNationalContractVersions: async (contractId: string): Promise<any[]> => {
        const response = await configApi.get(`/national-contracts/${contractId}/versions`);
        return response.data.items || [];
    },

    createNationalContractVersion: async (data: any): Promise<any> => {
        const response = await configApi.post('/national-contracts/versions', data);
        return response.data;
    },

    updateNationalContractVersion: async (versionId: string, data: any): Promise<any> => {
        const response = await configApi.put(`/national-contracts/versions/${versionId}`, data);
        return response.data;
    },

    // Levels
    createNationalContractLevel: async (data: any): Promise<any> => {
        const response = await configApi.post('/national-contracts/levels', data);
        return response.data;
    },

    updateNationalContractLevel: async (levelId: string, data: any): Promise<any> => {
        const response = await configApi.put(`/national-contracts/levels/${levelId}`, data);
        return response.data;
    },

    deleteNationalContractLevel: async (levelId: string): Promise<any> => {
        const response = await configApi.delete(`/national-contracts/levels/${levelId}`);
        return response.data;
    },

    // Contract Types & Configs
    getContractTypes: async (): Promise<any[]> => {
        const response = await configApi.get('/contract-types');
        return response.data;
    },

    createNationalContractTypeConfig: async (data: any): Promise<any> => {
        const response = await configApi.post('/national-contracts/type-configs', data);
        return response.data;
    },

    updateNationalContractTypeConfig: async (configId: string, data: any): Promise<any> => {
        const response = await configApi.put(`/national-contracts/type-configs/${configId}`, data);
        return response.data;
    },

    deleteNationalContractTypeConfig: async (configId: string): Promise<any> => {
        const response = await configApi.delete(`/national-contracts/type-configs/${configId}`);
        return response.data;
    },

    // Calculation Modes
    getCalculationModes: async (): Promise<any[]> => {
        const response = await configApi.get('/calculation-modes');
        return response.data.items || [];
    },

    createCalculationMode: async (data: any): Promise<any> => {
        const response = await configApi.post('/calculation-modes', data);
        return response.data;
    },

    updateCalculationMode: async (id: string, data: any): Promise<any> => {
        const response = await configApi.put(`/calculation-modes/${id}`, data);
        return response.data;
    },

    deleteCalculationMode: async (id: string): Promise<any> => {
        const response = await configApi.delete(`/calculation-modes/${id}`);
        return response.data;
    },
};
