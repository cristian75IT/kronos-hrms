import { authApi } from './api';
import type {
    Department,
    DepartmentCreate,
    DepartmentUpdate,
    OrganizationalService,
    OrganizationalServiceCreate,
    OrganizationalServiceUpdate,
    ExecutiveLevel,
    ExecutiveLevelCreate,
    ExecutiveLevelUpdate
} from '../types';

const BASE_URL = '/organization';

export const organizationService = {
    // ═══════════════════════════════════════════════════════════
    // Executive Levels
    // ═══════════════════════════════════════════════════════════

    async getExecutiveLevels(activeOnly = true): Promise<ExecutiveLevel[]> {
        const response = await authApi.get(`${BASE_URL}/executive-levels`, {
            params: { active_only: activeOnly }
        });
        return response.data;
    },

    async getExecutiveLevel(id: string): Promise<ExecutiveLevel> {
        const response = await authApi.get(`${BASE_URL}/executive-levels/${id}`);
        return response.data;
    },

    async createExecutiveLevel(data: ExecutiveLevelCreate): Promise<ExecutiveLevel> {
        const response = await authApi.post(`${BASE_URL}/executive-levels`, data);
        return response.data;
    },

    async updateExecutiveLevel(id: string, data: ExecutiveLevelUpdate): Promise<ExecutiveLevel> {
        const response = await authApi.put(`${BASE_URL}/executive-levels/${id}`, data);
        return response.data;
    },

    async deleteExecutiveLevel(id: string): Promise<void> {
        await authApi.delete(`${BASE_URL}/executive-levels/${id}`);
    },

    // ═══════════════════════════════════════════════════════════
    // Departments
    // ═══════════════════════════════════════════════════════════

    async getDepartments(activeOnly = true): Promise<Department[]> {
        const response = await authApi.get(`${BASE_URL}/departments`, {
            params: { active_only: activeOnly }
        });
        return response.data;
    },

    async getDepartmentTree(activeOnly = true): Promise<Department[]> {
        const response = await authApi.get(`${BASE_URL}/departments/tree`, {
            params: { active_only: activeOnly }
        });
        return response.data;
    },

    async getDepartment(id: string): Promise<Department> {
        const response = await authApi.get(`${BASE_URL}/departments/${id}`);
        return response.data;
    },

    async createDepartment(data: DepartmentCreate): Promise<Department> {
        const response = await authApi.post(`${BASE_URL}/departments`, data);
        return response.data;
    },

    async updateDepartment(id: string, data: DepartmentUpdate): Promise<Department> {
        const response = await authApi.put(`${BASE_URL}/departments/${id}`, data);
        return response.data;
    },

    async deleteDepartment(id: string): Promise<void> {
        await authApi.delete(`${BASE_URL}/departments/${id}`);
    },

    // ═══════════════════════════════════════════════════════════
    // Organizational Services
    // ═══════════════════════════════════════════════════════════

    async getServices(activeOnly = true): Promise<OrganizationalService[]> {
        const response = await authApi.get(`${BASE_URL}/services`, {
            params: { active_only: activeOnly }
        });
        return response.data;
    },

    async getServicesByDepartment(departmentId: string): Promise<OrganizationalService[]> {
        const response = await authApi.get(`${BASE_URL}/departments/${departmentId}/services`);
        return response.data;
    },

    async getService(id: string): Promise<OrganizationalService> {
        const response = await authApi.get(`${BASE_URL}/services/${id}`);
        return response.data;
    },

    async createService(data: OrganizationalServiceCreate): Promise<OrganizationalService> {
        const response = await authApi.post(`${BASE_URL}/services`, data);
        return response.data;
    },

    async updateService(id: string, data: OrganizationalServiceUpdate): Promise<OrganizationalService> {
        const response = await authApi.put(`${BASE_URL}/services/${id}`, data);
        return response.data;
    },

    async deleteService(id: string): Promise<void> {
        await authApi.delete(`${BASE_URL}/services/${id}`);
    }
};
