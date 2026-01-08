import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { configService } from '../../services/config.service';


import { queryKeys } from './queryKeys';

export function useExpenseTypes(activeOnly = true) {
    return useQuery({
        queryKey: ['expense-types', activeOnly],
        queryFn: () => configService.getExpenseTypes(activeOnly),
    });
}

export function useConfigs() {
    return useQuery({
        queryKey: queryKeys.configs,
        queryFn: () => configService.getAllConfigs(),
    });
}

export function useUpdateConfig() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ key, value }: { key: string; value: any }) =>
            configService.updateConfig(key, value),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.configs });
        },
    });
}

export function useClearCache() {
    return useMutation({
        mutationFn: () => configService.clearCache(),
    });
}
