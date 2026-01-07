import api from './api';

export const setupService = {
    /**
     * Import National Contracts (CCNL)
     */
    importContracts: async (data: any) => {
        const response = await api.post('/config/setup/contracts', data);
        return response.data;
    },

    /**
     * Import Executive Levels
     */
    importExecutiveLevels: async (data: any) => {
        const response = await api.post('/auth/setup/executive-levels', data);
        return response.data;
    },

    /**
     * Import Organization Structure
     */
    importOrganization: async (data: any) => {
        const response = await api.post('/auth/setup/organization', data);
        return response.data;
    },

    /**
     * Import Users and Profiles
     */
    importUsers: async (data: any) => {
        const response = await api.post('/auth/setup/users', data);
        return response.data;
    },

    /**
     * Import Holiday Profiles
     */
    importHolidays: async (data: any) => {
        const response = await api.post('/calendar/setup/holidays', data);
        return response.data;
    },

    /**
     * Import Approval Workflows
     */
    importWorkflows: async (data: any) => {
        const response = await api.post('/approvals/setup/workflows', data);
        return response.data;
    },

    /**
     * Import Leave Types
     */
    importLeaveTypes: async (data: any) => {
        const response = await api.post('/config/setup/leave-types', data);
        return response.data;
    }
};
