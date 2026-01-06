
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '../services/userService';
import type { ContractType } from '../types';

export const contractTypesKeys = {
    all: ['contract-types'] as const,
};

export function useContractTypesList() {
    return useQuery({
        queryKey: contractTypesKeys.all,
        queryFn: () => userService.getContractTypes(),
    });
}

export function useCreateContractType() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: Partial<ContractType>) => userService.createContractType(data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: contractTypesKeys.all }),
    });
}

export function useUpdateContractType() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<ContractType> }) => userService.updateContractType(id, data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: contractTypesKeys.all }),
    });
}
