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
    ContractType
} from '../types';

export const userService = {
    getUsers: async (params?: any): Promise<UserWithProfile[]> => {
        const response = await authApi.get('/users', { params });
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
};
