import { authApi } from './api';

export interface Permission {
    id: string;
    code: string;
    resource: string;
    action: string;
    name: string;
    description?: string;
}

export interface Role {
    id: string;
    name: string;
    display_name?: string;
    description?: string;
    is_system: boolean;
    permissions: Permission[];
}

export const rbacService = {
    getRoles: async (): Promise<Role[]> => {
        const response = await authApi.get('/roles');
        return response.data;
    },

    getPermissions: async (): Promise<Permission[]> => {
        const response = await authApi.get('/permissions');
        return response.data;
    },

    updateRolePermissions: async (roleId: string, permissionIds: string[]): Promise<Role> => {
        const response = await authApi.put(`/roles/${roleId}/permissions`, { permission_ids: permissionIds });
        return response.data;
    },
};
