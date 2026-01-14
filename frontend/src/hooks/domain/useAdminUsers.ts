/**
 * KRONOS - Admin Users Domain Hook
 * 
 * React Query hooks for user management in admin context.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '../../services/userService';
import { leavesService } from '../../services/leaves.service';
import type { UserWithProfile, LeaveBalanceSummary } from '../../types';

export interface UserWithBalance extends UserWithProfile {
    balance?: LeaveBalanceSummary | null;
}

// Query Keys
export const adminUserKeys = {
    all: ['admin', 'users'] as const,
    list: () => [...adminUserKeys.all, 'list'] as const,
    listWithBalances: () => [...adminUserKeys.all, 'list-with-balances'] as const,
    detail: (id: string) => [...adminUserKeys.all, 'detail', id] as const,
};

/**
 * Hook to fetch all users for admin management
 */
export function useAdminUsers() {
    return useQuery({
        queryKey: adminUserKeys.list(),
        queryFn: async () => {
            const users = await userService.getUsers();
            return users as UserWithBalance[];
        },
        staleTime: 60 * 1000, // 1 minute
    });
}

/**
 * Hook to fetch users with their leave balances
 * This makes parallel calls to fetch balances for all users
 */
export function useAdminUsersWithBalances() {
    const { data: users = [], isLoading: usersLoading } = useAdminUsers();

    const balancesQuery = useQuery({
        queryKey: adminUserKeys.listWithBalances(),
        queryFn: async () => {
            if (users.length === 0) return [];

            const usersWithBalances = await Promise.all(
                users.map(async (user) => {
                    try {
                        const balance = await leavesService.getBalanceSummary(user.id);
                        return { ...user, balance };
                    } catch {
                        return { ...user, balance: null };
                    }
                })
            );
            return usersWithBalances;
        },
        enabled: users.length > 0 && !usersLoading,
        staleTime: 2 * 60 * 1000, // 2 minutes (balances change less frequently)
    });

    return {
        users: balancesQuery.data || users,
        isLoading: usersLoading,
        isLoadingBalances: balancesQuery.isLoading || balancesQuery.isFetching,
        refetch: balancesQuery.refetch,
    };
}

/**
 * Hook to delete a user
 */
export function useDeleteUser() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (userId: string) => userService.deleteUser(userId),
        onSuccess: (_, userId) => {
            // Optimistic update: remove from cache
            queryClient.setQueryData<UserWithBalance[]>(
                adminUserKeys.list(),
                (old) => old?.filter(u => u.id !== userId)
            );
            queryClient.setQueryData<UserWithBalance[]>(
                adminUserKeys.listWithBalances(),
                (old) => old?.filter(u => u.id !== userId)
            );
            queryClient.invalidateQueries({ queryKey: adminUserKeys.all });
        },
    });
}

/**
 * Hook for batch operations on leave balances
 */
export function useBatchLeaveOperations() {
    const queryClient = useQueryClient();

    const processAccruals = useMutation({
        mutationFn: ({ year, month }: { year: number; month: number }) =>
            leavesService.processAccruals(year, month),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: adminUserKeys.listWithBalances() });
        },
    });

    const processExpirations = useMutation({
        mutationFn: () => leavesService.processExpirations(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: adminUserKeys.listWithBalances() });
        },
    });

    const recalculateAccruals = useMutation({
        mutationFn: () => leavesService.recalculateAccruals(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: adminUserKeys.listWithBalances() });
        },
    });

    const processRollover = useMutation({
        mutationFn: (year: number) => leavesService.processRollover(year),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: adminUserKeys.listWithBalances() });
        },
    });

    return {
        processAccruals,
        processExpirations,
        recalculateAccruals,
        processRollover,
    };
}
