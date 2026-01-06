/**
 * KRONOS - Contract Types Manager
 * Refactored for Guidelines Compliance: React Query + React Hook Form + Zod
 */
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useContractTypesList, useCreateContractType, useUpdateContractType } from '../../hooks/useContractTypesHooks';
import { Loader, Plus, Save, X, Edit, Clock, Calendar } from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common';
import type { ContractType } from '../../types';
import { contractTypeSchema, type ContractTypeFormValues } from '../../schemas/contractType.schema';

export function ContractTypesManager() {
    const { data: types, isLoading } = useContractTypesList();
    const createMutation = useCreateContractType();
    const updateMutation = useUpdateContractType();
    const toast = useToast();

    // UI State
    const [isCreating, setIsCreating] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);

    // Create Form
    const {
        register,
        handleSubmit,
        reset,
        watch,
        setValue,
        formState: { errors, isValid }
    } = useForm<ContractTypeFormValues>({
        resolver: zodResolver(contractTypeSchema),
        defaultValues: {
            name: '',
            is_part_time: false,
            part_time_percentage: 100,
            annual_vacation_days: 26,
            annual_rol_hours: 72,
            annual_permit_hours: 32,
            is_active: true
        }
    });

    // Edit Form (Inline)
    // For simplicity, we'll reuse the same form state structure but managed locally for the inline edit row,
    // or ideally, we should extract the row to a sub-component with its own form.
    // Given the constraints, let's keep it simple: strict form for creation, manual state for inline edit (or refactor inline edit to a proper form if strict compliance needed).
    // Guideline says: "Implement React Hook Form + Zod". Doing it for the creation form is the primary step. 
    // For proper Zod validation on edit, we should wrap the row in a form provider or use a modal.
    // Let's stick to the current UI pattern but improve validation.

    // Actually, to comply strictly, let's turn the Edit Row into a separate component or manage it via RHF.
    // Implementing "EditRow" subcomponent is cleaner.

    const handleCreate = async (data: ContractTypeFormValues) => {
        try {
            await createMutation.mutateAsync(data);
            toast.success('Nuovo template di contratto creato');
            setIsCreating(false);
            reset();
        } catch {
            toast.error('Errore durante la creazione');
        }
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center p-12 gap-3">
                <Loader className="animate-spin text-indigo-600" size={32} />
                <span className="text-sm text-gray-500">Caricamento modelli...</span>
            </div>
        );
    }

    const isPartTime = watch('is_part_time');

    return (
        <div className="space-y-6">
            {/* Create Button */}
            {!isCreating && (
                <div className="flex justify-end">
                    <Button onClick={() => setIsCreating(true)} variant="primary" icon={<Plus size={18} />}>
                        Crea Modello
                    </Button>
                </div>
            )}

            {/* Create Form */}
            {isCreating && (
                <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">Nuovo Modello Contrattuale</h4>
                    <form onSubmit={handleSubmit(handleCreate)}>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <div className="lg:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Nome Modello</label>
                                <input
                                    {...register('name')}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    placeholder="Es. Metalmeccanico Full Time"
                                />
                                {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Orario</label>
                                <select
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    {...register('is_part_time', {
                                        setValueAs: v => v === 'true' // Convert string to boolean
                                    })}
                                    onChange={(e) => {
                                        const isPT = e.target.value === 'true';
                                        setValue('is_part_time', isPT);
                                        if (!isPT) setValue('part_time_percentage', 100);
                                        else setValue('part_time_percentage', 50);
                                    }}
                                >
                                    <option value="false">Full Time</option>
                                    <option value="true">Part Time</option>
                                </select>
                            </div>
                            {isPartTime && (
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">% Carico</label>
                                    <input
                                        type="number"
                                        {...register('part_time_percentage', { valueAsNumber: true })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    {errors.part_time_percentage && <p className="text-xs text-red-500">{errors.part_time_percentage.message}</p>}
                                </div>
                            )}
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Ferie Annuali (gg)</label>
                                <input
                                    type="number"
                                    {...register('annual_vacation_days', { valueAsNumber: true })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                                {errors.annual_vacation_days && <p className="text-xs text-red-500">{errors.annual_vacation_days.message}</p>}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">ROL Annuali (h)</label>
                                <input
                                    type="number"
                                    {...register('annual_rol_hours', { valueAsNumber: true })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                                {errors.annual_rol_hours && <p className="text-xs text-red-500">{errors.annual_rol_hours.message}</p>}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Permessi (h)</label>
                                <input
                                    type="number"
                                    {...register('annual_permit_hours', { valueAsNumber: true })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                                {errors.annual_permit_hours && <p className="text-xs text-red-500">{errors.annual_permit_hours.message}</p>}
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 mt-6">
                            <Button variant="secondary" onClick={() => setIsCreating(false)} type="button">Annulla</Button>
                            <Button variant="primary" type="submit" disabled={!isValid}>Crea Modello</Button>
                        </div>
                    </form>
                </div>
            )}

            {/* Table */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center justify-between">
                    <div>
                        <h3 className="font-semibold text-gray-900">Modelli Contrattuali</h3>
                        <p className="text-xs text-gray-500 mt-0.5">I valori di Ferie, ROL e Permessi sono espressi su base annuale</p>
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-gray-50/50 border-b border-gray-200">
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Contratto</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Orario</th>
                                <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Ferie</th>
                                <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">ROL</th>
                                <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Permessi</th>
                                <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Stato</th>
                                <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Azioni</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {types?.map(type => (
                                <ContractTypeRow
                                    key={type.id}
                                    type={type}
                                    isEditing={editingId === type.id}
                                    onEdit={() => setEditingId(type.id)}
                                    onCancel={() => setEditingId(null)}
                                    onSave={(id, data) => updateMutation.mutateAsync({ id, data }).then(() => {
                                        toast.success('Aggiornato con successo');
                                        setEditingId(null);
                                    })}
                                />
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Info Banner */}
            <div className="flex items-start gap-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <Calendar className="text-amber-600 shrink-0" size={20} />
                <div>
                    <h5 className="font-medium text-amber-800">Audit Contrattuale</h5>
                    <p className="text-sm text-amber-700 mt-0.5">
                        I modelli definiti fungono da template per tutti i nuovi contratti dipendente. Le modifiche ai parametri di maturazione non sono retroattive.
                    </p>
                </div>
            </div>
        </div>
    );
}

// Subcomponent for Row to handle its own Form State if editing
function ContractTypeRow({ type, isEditing, onEdit, onCancel, onSave }: {
    type: ContractType,
    isEditing: boolean,
    onEdit: () => void,
    onCancel: () => void,
    onSave: (id: string, data: ContractTypeFormValues) => void
}) {
    const {
        register,
        handleSubmit,
        watch,
        setValue
    } = useForm<ContractTypeFormValues>({
        resolver: zodResolver(contractTypeSchema),
        defaultValues: {
            name: type.name,
            is_part_time: type.is_part_time,
            part_time_percentage: type.part_time_percentage || 100,
            annual_vacation_days: type.annual_vacation_days,
            annual_rol_hours: type.annual_rol_hours,
            annual_permit_hours: type.annual_permit_hours,
            is_active: type.is_active
        }
    });

    if (isEditing) {
        const isPartTime = watch('is_part_time');
        return (
            <tr className="bg-blue-50/30">
                <td className="px-6 py-4">
                    <input
                        className="w-full px-2 py-1 border border-gray-300 rounded-md text-sm"
                        {...register('name')}
                    />
                </td>
                <td className="px-6 py-4">
                    <div className="flex gap-2">
                        <select
                            className="px-2 py-1 border border-gray-300 rounded-md text-sm"
                            {...register('is_part_time', {
                                setValueAs: v => v === 'true'
                            })}
                            onChange={(e) => {
                                const isPT = e.target.value === 'true';
                                setValue('is_part_time', isPT);
                                if (!isPT) setValue('part_time_percentage', 100);
                            }}
                        >
                            <option value="false">FT</option>
                            <option value="true">PT</option>
                        </select>
                        {isPartTime && (
                            <input
                                type="number"
                                className="w-16 px-2 py-1 border border-gray-300 rounded-md text-sm"
                                {...register('part_time_percentage', { valueAsNumber: true })}
                            />
                        )}
                    </div>
                </td>
                <td className="px-6 py-4 text-center">
                    <input type="number" className="w-16 px-2 py-1 border border-gray-300 rounded-md text-sm text-center" {...register('annual_vacation_days', { valueAsNumber: true })} />
                </td>
                <td className="px-6 py-4 text-center">
                    <input type="number" className="w-16 px-2 py-1 border border-gray-300 rounded-md text-sm text-center" {...register('annual_rol_hours', { valueAsNumber: true })} />
                </td>
                <td className="px-6 py-4 text-center">
                    <input type="number" className="w-16 px-2 py-1 border border-gray-300 rounded-md text-sm text-center" {...register('annual_permit_hours', { valueAsNumber: true })} />
                </td>
                <td className="px-6 py-4 text-center">
                    <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" {...register('is_active')} />
                </td>
                <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                        <button className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-lg" onClick={handleSubmit((data) => onSave(type.id, data))}><Save size={16} /></button>
                        <button className="p-2 text-gray-400 hover:bg-gray-100 rounded-lg" onClick={onCancel}><X size={16} /></button>
                    </div>
                </td>
            </tr>
        );
    }

    return (
        <tr className="hover:bg-gray-50 transition-colors group">
            <td className="px-6 py-4">
                <div className="font-medium text-gray-900">{type.name}</div>
                <div className="text-xs text-gray-400 font-mono">{type.code || type.id.substring(0, 8)}</div>
            </td>
            <td className="px-6 py-4">
                <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${type.is_part_time ? 'bg-purple-50 text-purple-700 border border-purple-100' : 'bg-indigo-50 text-indigo-700 border border-indigo-100'}`}>
                    <Clock size={12} />
                    {type.is_part_time ? `PT ${type.part_time_percentage}%` : 'Full Time'}
                </span>
            </td>
            <td className="px-6 py-4 text-center">
                <span className="text-lg font-semibold text-gray-900">{type.annual_vacation_days}</span>
                <span className="text-xs text-gray-400 ml-1">gg</span>
            </td>
            <td className="px-6 py-4 text-center">
                <span className="text-lg font-semibold text-gray-900">{type.annual_rol_hours}</span>
                <span className="text-xs text-gray-400 ml-1">h</span>
            </td>
            <td className="px-6 py-4 text-center">
                <span className="text-lg font-semibold text-gray-900">{type.annual_permit_hours}</span>
                <span className="text-xs text-gray-400 ml-1">h</span>
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

export default ContractTypesManager;
