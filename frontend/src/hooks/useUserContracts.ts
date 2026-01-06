
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '../services/userService';
import { leavesService } from '../services/leaves.service';
import { configService } from '../services/config.service';
import type { EmployeeContractCreate } from '../types';

export const userContractKeys = {
    all: ['user-contracts'] as const,
    list: (userId: string) => [...userContractKeys.all, userId] as const,
    nationalContracts: ['national-contracts'] as const,
};

export function useUserContracts(userId: string) {
    return useQuery({
        queryKey: userContractKeys.list(userId),
        queryFn: () => userService.getContracts(userId),
        enabled: !!userId,
    });
}

export function useNationalContracts() {
    return useQuery({
        queryKey: userContractKeys.nationalContracts,
        queryFn: () => configService.getNationalContracts(),
    });
}

export function useAddContract(userId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: EmployeeContractCreate) => userService.addContract(userId, data),
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: userContractKeys.list(userId) });
            // Recalculate accruals implies balance updates
            try {
                await leavesService.recalculateUserAccruals(userId);
                await queryClient.invalidateQueries({ queryKey: ['leave-balance'] });
            } catch (error) {
                console.warn('Accrual recalculation failed silently', error);
            }
        },
    });
}

export function useUpdateContract(userId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ contractId, data }: { contractId: string; data: Partial<EmployeeContractCreate> }) =>
            userService.updateContract(userId, contractId, data),
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: userContractKeys.list(userId) });
            try {
                await leavesService.recalculateUserAccruals(userId);
                await queryClient.invalidateQueries({ queryKey: ['leave-balance'] });
            } catch (error) {
                console.warn('Accrual recalculation failed silently', error);
            }
        },
    });
}

export function useDeleteContract(userId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (contractId: string) => userService.deleteContract(userId, contractId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: userContractKeys.list(userId) });
        },
    });
}
