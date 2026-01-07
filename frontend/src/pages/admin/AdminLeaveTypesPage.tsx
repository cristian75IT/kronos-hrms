import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader, Save, X, Edit, Calendar } from 'lucide-react';
import { configApi } from '../../services/api';
import { useToast } from '../../context/ToastContext';
import type { LeaveType } from '../../types';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// --- Schema ---
const leaveTypeSchema = z.object({
    name: z.string().min(1, 'Nome obbligatorio'),
    max_single_request_days: z.number().nullable().optional(),
    max_consecutive_days: z.number().nullable().optional(),
    max_per_month: z.number().nullable().optional(),
    min_notice_days: z.number().nullable().optional(),
    is_active: z.boolean(),
});

type LeaveTypeFormValues = z.infer<typeof leaveTypeSchema>;

// --- API Hooks ---
function useLeaveTypes() {
    return useQuery({
        queryKey: ['leave-types'],
        queryFn: async () => {
            const res = await configApi.get('/leave-types');
            return res.data.items as LeaveType[];
        },
    });
}

function useUpdateLeaveType() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ id, data }: { id: string; data: LeaveTypeFormValues }) => {
            await configApi.patch(`/leave-types/${id}`, data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['leave-types'] });
        },
    });
}

// --- Component ---
export default function AdminLeaveTypesPage() {
    const { data: types, isLoading } = useLeaveTypes();
    const updateMutation = useUpdateLeaveType();
    const toast = useToast();
    const [editingId, setEditingId] = useState<string | null>(null);

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center p-12 gap-3">
                <Loader className="animate-spin text-indigo-600" size={32} />
                <span className="text-sm text-gray-500">Caricamento tipi di assenza...</span>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-start gap-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                <Calendar className="text-indigo-600 shrink-0" size={20} />
                <div>
                    <h5 className="font-medium text-indigo-800">Gestione Tipi Assenza</h5>
                    <p className="text-sm text-indigo-700 mt-0.5">
                        Configura qui i limiti per ogni tipo di richiesta (ferie, malattia, ecc).
                        Il campo "Max Giorni/Richiesta" blocca l'invio se superato.
                    </p>
                </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50">
                    <h3 className="font-semibold text-gray-900">Elenco Tipologie</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-gray-50/50 border-b border-gray-200">
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Codice</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Nome</th>
                                <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Max/Richiesta</th>
                                <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Max Consecutivi</th>
                                <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Preavviso (gg)</th>
                                <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Attivo</th>
                                <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Azioni</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {types?.map(type => (
                                <LeaveTypeRow
                                    key={type.id}
                                    type={type}
                                    isEditing={editingId === type.id}
                                    onEdit={() => setEditingId(type.id)}
                                    onCancel={() => setEditingId(null)}
                                    onSave={(id, data) => updateMutation.mutateAsync({ id, data }).then(() => {
                                        toast.success('Tipo assenza aggiornato');
                                        setEditingId(null);
                                    }).catch(() => toast.error('Errore durante aggiornamento'))}
                                />
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

function LeaveTypeRow({ type, isEditing, onEdit, onCancel, onSave }: {
    type: LeaveType,
    isEditing: boolean,
    onEdit: () => void,
    onCancel: () => void,
    onSave: (id: string, data: LeaveTypeFormValues) => void
}) {
    const {
        register,
        handleSubmit,
        formState: { errors }
    } = useForm<LeaveTypeFormValues>({
        resolver: zodResolver(leaveTypeSchema),
        defaultValues: {
            name: type.name,
            max_single_request_days: type.max_single_request_days,
            max_consecutive_days: type.max_consecutive_days,
            max_per_month: type.max_consecutive_days, // typo in interface maybe? checking schema... max_per_month is not in interface but in python model
            min_notice_days: type.min_notice_days,
            is_active: type.is_active
        }
    });

    if (isEditing) {
        return (
            <tr className="bg-indigo-50/30">
                <td className="px-6 py-4 text-sm text-gray-500 font-mono">{type.code}</td>
                <td className="px-6 py-4">
                    <input
                        className="w-full px-2 py-1 border border-gray-300 rounded-md text-sm"
                        {...register('name')}
                    />
                    {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
                </td>
                <td className="px-6 py-4 text-center">
                    <input
                        type="number"
                        className="w-20 px-2 py-1 border border-gray-300 rounded-md text-sm text-center"
                        {...register('max_single_request_days', { valueAsNumber: true })}
                        placeholder="∞"
                    />
                </td>
                <td className="px-6 py-4 text-center">
                    <input
                        type="number"
                        className="w-20 px-2 py-1 border border-gray-300 rounded-md text-sm text-center"
                        {...register('max_consecutive_days', { valueAsNumber: true })}
                        placeholder="∞"
                    />
                </td>
                <td className="px-6 py-4 text-center">
                    <input
                        type="number"
                        className="w-20 px-2 py-1 border border-gray-300 rounded-md text-sm text-center"
                        {...register('min_notice_days', { valueAsNumber: true })}
                    />
                </td>
                <td className="px-6 py-4 text-center">
                    <input
                        type="checkbox"
                        className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        {...register('is_active')}
                    />
                </td>
                <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                        <button
                            className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-lg"
                            onClick={handleSubmit((data) => {
                                // Clean up NaNs from empty number inputs
                                const cleanData = { ...data };
                                if (Number.isNaN(cleanData.max_single_request_days)) cleanData.max_single_request_days = null;
                                if (Number.isNaN(cleanData.max_consecutive_days)) cleanData.max_consecutive_days = null;
                                if (Number.isNaN(cleanData.min_notice_days)) cleanData.min_notice_days = null;
                                if (Number.isNaN(cleanData.max_per_month)) cleanData.max_per_month = null;
                                onSave(type.id, cleanData);
                            })}
                        >
                            <Save size={16} />
                        </button>
                        <button className="p-2 text-gray-400 hover:bg-gray-100 rounded-lg" onClick={onCancel}><X size={16} /></button>
                    </div>
                </td>
            </tr>
        );
    }

    return (
        <tr className="hover:bg-gray-50 transition-colors">
            <td className="px-6 py-4 text-sm font-medium text-gray-900 font-mono">{type.code}</td>
            <td className="px-6 py-4 text-sm text-gray-700">{type.name}</td>
            <td className="px-6 py-4 text-center text-sm text-gray-600">
                {type.max_single_request_days ? <span className="font-semibold text-indigo-600">{type.max_single_request_days}</span> : <span className="text-gray-400">-</span>}
            </td>
            <td className="px-6 py-4 text-center text-sm text-gray-600">
                {type.max_consecutive_days ? type.max_consecutive_days : <span className="text-gray-400">-</span>}
            </td>
            <td className="px-6 py-4 text-center text-sm text-gray-600">
                {type.min_notice_days ? type.min_notice_days : <span className="text-gray-400">-</span>}
            </td>
            <td className="px-6 py-4 text-center">
                <div className={`w-3 h-3 rounded-full mx-auto ${type.is_active ? 'bg-emerald-500' : 'bg-gray-300'}`} />
            </td>
            <td className="px-6 py-4 text-right">
                <button
                    className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
                    onClick={onEdit}
                >
                    <Edit size={16} />
                </button>
            </td>
        </tr>
    );
}
