import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rbacService } from '../../services/rbacService';
import type { Role, Permission } from '../../services/rbacService';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Save, Shield, Loader2 } from 'lucide-react';
import { useToast } from '../../context/ToastContext';

export default function RolesPage() {
    const queryClient = useQueryClient();
    const toast = useToast();
    const [pendingChanges, setPendingChanges] = useState<Record<string, string[]>>({}); // roleId -> permissionIds

    // Fetch Roles
    const { data: roles = [], isLoading: rolesLoading, error: rolesError } = useQuery<Role[]>({
        queryKey: ['roles'],
        queryFn: rbacService.getRoles
    });

    // Fetch Permissions
    const { data: permissions = [], isLoading: permsLoading, error: permsError } = useQuery({
        queryKey: ['permissions'],
        queryFn: rbacService.getPermissions
    });

    // Mutation for updating
    const updateRoleMutation = useMutation({
        mutationFn: async ({ roleId, permissionIds }: { roleId: string; permissionIds: string[] }) => {
            return rbacService.updateRolePermissions(roleId, permissionIds);
        },
        onSuccess: (data, variables) => {
            toast.success(`Permessi aggiornati per il ruolo ${data.name}`);
            setPendingChanges(prev => {
                const next = { ...prev };
                delete next[variables.roleId];
                return next;
            });
            queryClient.invalidateQueries({ queryKey: ['roles'] });
        },
        onError: (error) => {
            toast.error("Errore durante l'aggiornamento dei permessi");
            console.error(error);
        }
    });

    // Debug logging
    console.log('Roles Page Data:', { roles, permissions, rolesError, permsError });

    if (rolesLoading || permsLoading) {
        return (
            <div className="flex justify-center items-center h-screen">
                <Loader2 className="animate-spin mr-2" /> Caricamento...
            </div>
        );
    }

    if (rolesError || permsError) {
        return (
            <div className="p-6 text-red-600">
                <h3 className="font-bold">Errore di caricamento</h3>
                {rolesError && <p>Roles Error: {(rolesError as any).message}</p>}
                {permsError && <p>Permissions Error: {(permsError as any).message}</p>}
            </div>
        );
    }

    // Debug View
    if ((!roles || roles.length === 0) && (!permissions || permissions.length === 0)) {
        return (
            <div className="p-6">
                <h3 className="font-bold text-yellow-600">Nessun dato trovato</h3>
                <pre className="bg-gray-100 p-4 rounded text-xs mt-2">
                    Roles: {JSON.stringify(roles, null, 2)}
                    Permissions: {JSON.stringify(permissions, null, 2)}
                </pre>
            </div>
        )
    }

    // Group Permissions by Resource
    const permissionsByResource = (Array.isArray(permissions) && Array.isArray(roles)) ? permissions.reduce((acc, perm) => {
        if (!acc[perm.resource]) acc[perm.resource] = [];
        acc[perm.resource].push(perm);
        return acc;
    }, {} as Record<string, Permission[]>) : {};

    const handleToggle = (roleId: string, permissionId: string, currentPerms: Permission[]) => {
        setPendingChanges(prev => {
            const roleChanges = prev[roleId] || currentPerms.map(p => p.id);
            const exists = roleChanges.includes(permissionId);
            const newPerms = exists
                ? roleChanges.filter(id => id !== permissionId)
                : [...roleChanges, permissionId];

            return { ...prev, [roleId]: newPerms };
        });
    };

    const hasChanges = (roleId: string) => !!pendingChanges[roleId];

    const handleSaveRole = (roleId: string) => {
        const newPerms = pendingChanges[roleId];
        if (newPerms) {
            updateRoleMutation.mutate({ roleId, permissionIds: newPerms });
        }
    };

    return (
        <div className="p-6">
            <div className="mb-6 flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Shield className="w-6 h-6 text-primary" />
                        Gestione Permessi Ruoli
                    </h1>
                    <p className="text-gray-500">Configura i permessi di accesso per ogni ruolo.</p>
                </div>
            </div>

            <Card className="overflow-x-auto">
                <table className="w-full border-collapse">
                    <thead>
                        <tr className="bg-gray-50 border-b">
                            <th className="p-4 text-left min-w-[200px] font-semibold text-gray-700">Risorsa / Azione</th>
                            {Array.isArray(roles) && roles.map(role => (
                                <th key={role.id} className="p-4 text-center min-w-[150px] font-semibold text-gray-700">
                                    <div className="flex flex-col items-center gap-1">
                                        <span>{role.display_name || role.name}</span>
                                        {hasChanges(role.id) && (
                                            <Button
                                                size="sm"
                                                onClick={() => handleSaveRole(role.id)}
                                                className="h-7 text-xs bg-green-600 hover:bg-green-700 text-white flex items-center gap-1"
                                                disabled={updateRoleMutation.isPending}
                                            >
                                                <Save size={12} /> Salva
                                            </Button>
                                        )}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {Object.entries(permissionsByResource).map(([resource, perms]) => (
                            <React.Fragment key={resource}>
                                <tr className="bg-gray-100/50">
                                    <td colSpan={Array.isArray(roles) ? roles.length + 1 : 1} className="p-3 font-bold text-gray-700 border-y">
                                        {resource}
                                    </td>
                                </tr>
                                {perms.map(perm => (
                                    <tr key={perm.id} className="border-b hover:bg-gray-50">
                                        <td className="p-3 pl-6 text-gray-600 text-sm">
                                            {perm.name}
                                            <div className="text-xs text-gray-400">{perm.description}</div>
                                        </td>
                                        {Array.isArray(roles) && roles.map(role => {
                                            const rolePermIds = pendingChanges[role.id] || role.permissions?.map((p: any) => p.id) || [];
                                            const isChecked = rolePermIds.includes(perm.id);

                                            return (
                                                <td key={`${role.id}-${perm.id}`} className="p-3 text-center">
                                                    <label className="inline-flex items-center cursor-pointer">
                                                        <input
                                                            type="checkbox"
                                                            className="w-5 h-5 text-primary rounded border-gray-300 focus:ring-primary"
                                                            checked={isChecked}
                                                            onChange={() => handleToggle(role.id, perm.id, role.permissions || [])}
                                                        />
                                                    </label>
                                                </td>
                                            );
                                        })}
                                    </tr>
                                ))}
                            </React.Fragment>
                        ))}
                    </tbody>
                </table>
            </Card>
        </div>
    );
}
