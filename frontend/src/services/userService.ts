/**
 * KRONOS - User Service
 */
import { authApi } from './api';
import type {
    UserWithProfile,
    DataTableRequest,
    DataTableResponse,
    EmployeeContract,
    EmployeeContractCreate,
    ContractType,
    Department,
    EmployeeTraining,
    EmployeeTrainingCreate
} from '../types';

export const userService = {
    getUsers: async (params?: Record<string, unknown>): Promise<UserWithProfile[]> => {
        const response = await authApi.get('/users', { params });
        return response.data;
    },

    getAreas: async (activeOnly = true): Promise<Department[]> => {
        const response = await authApi.get('/areas', { params: { active_only: activeOnly } });
        return response.data;
    },

    getArea: async (id: string): Promise<Department> => {
        const response = await authApi.get(`/areas/${id}`);
        return response.data;
    },

    getUser: async (id: string): Promise<UserWithProfile> => {
        const response = await authApi.get(`/users/${id}`);
        return response.data;
    },

    createUser: async (data: Partial<UserWithProfile>): Promise<UserWithProfile> => {
        const response = await authApi.post('/users', data);
        return response.data;
    },

    updateUser: async (id: string, data: Partial<UserWithProfile>): Promise<UserWithProfile> => {
        const response = await authApi.put(`/users/${id}`, data);
        return response.data;
    },

    deleteUser: async (id: string): Promise<void> => {
        await authApi.delete(`/users/${id}`);
    },

    // DataTable support
    getUsersDataTable: async (request: DataTableRequest): Promise<DataTableResponse<UserWithProfile>> => {
        const response = await authApi.post('/users/datatable', request);
        return response.data;
    },

    // Contracts
    getContracts: async (userId: string): Promise<EmployeeContract[]> => {
        const response = await authApi.get(`/users/${userId}/contracts`);
        return response.data;
    },

    addContract: async (userId: string, data: EmployeeContractCreate): Promise<EmployeeContract> => {
        const response = await authApi.post(`/users/${userId}/contracts`, data);
        return response.data;
    },

    updateContract: async (userId: string, contractId: string, data: Partial<EmployeeContractCreate>): Promise<EmployeeContract> => {
        const response = await authApi.put(`/users/${userId}/contracts/${contractId}`, data);
        return response.data;
    },

    deleteContract: async (userId: string, contractId: string): Promise<void> => {
        await authApi.delete(`/users/${userId}/contracts/${contractId}`);
    },

    getContractTypes: async (): Promise<ContractType[]> => {
        const response = await authApi.get('/contract-types');
        return response.data;
    },

    createContractType: async (data: Partial<ContractType>): Promise<ContractType> => {
        const response = await authApi.post('/contract-types', data);
        return response.data;
    },

    updateContractType: async (id: string, data: Partial<ContractType>): Promise<ContractType> => {
        const response = await authApi.put(`/contract-types/${id}`, data);
        return response.data;
    },

    // Training
    getTrainings: async (userId: string): Promise<EmployeeTraining[]> => {
        const response = await authApi.get(`/users/${userId}/trainings`);
        return response.data;
    },

    createTraining: async (data: EmployeeTrainingCreate): Promise<EmployeeTraining> => {
        const response = await authApi.post('/trainings', data);
        return response.data;
    },

    updateTraining: async (id: string, data: Partial<EmployeeTrainingCreate>): Promise<EmployeeTraining> => {
        const response = await authApi.put(`/trainings/${id}`, data);
        return response.data;
    },

    deleteTraining: async (id: string): Promise<void> => {
        await authApi.delete(`/trainings/${id}`);
    },
};
