import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '../../services/userService';
import { queryKeys } from './queryKeys';
import type { UserWithProfile } from '../../types';

export function useUsers() {
    return useQuery({
        queryKey: queryKeys.users,
        queryFn: () => userService.getUsers(),
    });
}

export function useUser(id: string) {
    return useQuery({
        queryKey: queryKeys.user(id),
        queryFn: () => userService.getUser(id),
        enabled: !!id,
    });
}

export function useCreateUser() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: Partial<UserWithProfile>) => userService.createUser(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.users });
        },
    });
}

export function useUpdateUser() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<UserWithProfile> }) =>
            userService.updateUser(id, data),
        onSuccess: (_, { id }) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.user(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.users });
        },
    });
}

export function useContractTypes() {
    return useQuery({
        queryKey: queryKeys.contractTypes,
        queryFn: () => userService.getContractTypes(),
    });
}

export function useCreateContractType() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: any) => userService.createContractType(data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.contractTypes }),
    });
}

export function useUpdateContractType() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: any }) => userService.updateContractType(id, data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.contractTypes }),
    });
}
