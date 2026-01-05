import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useToast } from '../../context/ToastContext';
import { organizationService } from '../../services/organization.service';
import { Modal } from '../../components/common/Modal';
import { Button } from '../../components/common';
import type {
    Department,
    DepartmentCreate,
    OrganizationalService,
    OrganizationalServiceCreate,
    ExecutiveLevel,
    ExecutiveLevelCreate
} from '../../types';

// ═══════════════════════════════════════════════════════════
// Executive Level Modal
// ═══════════════════════════════════════════════════════════
interface ExecutiveLevelModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    initialData?: ExecutiveLevel | null;
}

export function ExecutiveLevelModal({ isOpen, onClose, onSuccess, initialData }: ExecutiveLevelModalProps) {
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<ExecutiveLevelCreate>();
    const toast = useToast();
    const isEditing = !!initialData;

    useEffect(() => {
        if (isOpen) {
            reset(initialData ? {
                code: initialData.code,
                title: initialData.title,
                hierarchy_level: initialData.hierarchy_level,
                max_approval_amount: initialData.max_approval_amount,
                can_override_workflow: initialData.can_override_workflow
            } : {
                code: '',
                title: '',
                hierarchy_level: 10,
                max_approval_amount: 0,
                can_override_workflow: false
            });
        }
    }, [isOpen, initialData, reset]);

    const onSubmit = async (data: ExecutiveLevelCreate) => {
        try {
            if (isEditing && initialData) {
                await organizationService.updateExecutiveLevel(initialData.id, data);
                toast.success('Livello aggiornato');
            } else {
                await organizationService.createExecutiveLevel(data);
                toast.success('Livello creato');
            }
            onSuccess();
            onClose();
        } catch (error) {
            console.error(error);
            toast.error('Errore nel salvataggio');
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={isEditing ? "Modifica Livello Executive" : "Nuovo Livello Executive"}>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Codice</label>
                        <input className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1"
                            {...register('code', { required: 'Richiesto' })} disabled={isEditing} />
                        {errors.code && <p className="text-red-500 text-xs mt-1">{errors.code.message}</p>}
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Livello Gerarchico</label>
                        <input type="number" className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1" {...register('hierarchy_level', { valueAsNumber: true, required: 'Richiesto' })} />
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700">Titolo</label>
                    <input className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1" {...register('title', { required: 'Richiesto' })} />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700">Limite Approvazione Spesa (€)</label>
                    <input type="number" className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1" {...register('max_approval_amount', { valueAsNumber: true })} />
                </div>
                <div className="flex items-center gap-2">
                    <input type="checkbox" id="override" className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" {...register('can_override_workflow')} />
                    <label htmlFor="override" className="text-sm font-medium text-gray-700">Può sovrascrivere flussi approvativi</label>
                </div>
                <div className="flex justify-end gap-2 pt-4">
                    <Button variant="outline" onClick={onClose} type="button">Annulla</Button>
                    <Button variant="primary" type="submit" isLoading={isSubmitting}>Salva</Button>
                </div>
            </form>
        </Modal>
    );
}

// ═══════════════════════════════════════════════════════════
// Department Modal
// ═══════════════════════════════════════════════════════════
interface DepartmentModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    initialData?: Department | null;
    parentDepartments: Department[]; // Flat list for select
}

export function DepartmentModal({ isOpen, onClose, onSuccess, initialData, parentDepartments }: DepartmentModalProps) {
    const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<DepartmentCreate>();
    const toast = useToast();
    const isEditing = !!initialData;

    useEffect(() => {
        if (isOpen) {
            reset(initialData ? {
                code: initialData.code,
                name: initialData.name,
                description: initialData.description || '',
                parent_id: initialData.parent_id,
                cost_center_code: initialData.cost_center_code || ''
            } : {
                code: '',
                name: '',
                description: '',
                parent_id: '',
                cost_center_code: ''
            });
        }
    }, [isOpen, initialData, reset]);

    const onSubmit = async (data: DepartmentCreate) => {
        try {
            // Clean up empty strings
            if (!data.parent_id) delete (data as any).parent_id;

            if (isEditing && initialData) {
                await organizationService.updateDepartment(initialData.id, data);
                toast.success('Dipartimento aggiornato');
            } else {
                await organizationService.createDepartment(data);
                toast.success('Dipartimento creato');
            }
            onSuccess();
            onClose();
        } catch (error) {
            console.error(error);
            toast.error('Errore nel salvataggio');
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={isEditing ? "Modifica Dipartimento" : "Nuovo Dipartimento"}>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Codice</label>
                        <input className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1"
                            {...register('code', { required: 'Richiesto' })} disabled={isEditing} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Centro di Costo</label>
                        <input className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1"
                            {...register('cost_center_code')} />
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700">Nome Dipartimento</label>
                    <input className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1" {...register('name', { required: 'Richiesto' })} />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700">Descrizione</label>
                    <textarea className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1" rows={3} {...register('description')} />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700">Dipartimento Padre</label>
                    <select className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1" {...register('parent_id')}>
                        <option value="">Nessuno (Root)</option>
                        {parentDepartments
                            .filter(d => !isEditing || d.id !== initialData?.id) // Prevent selecting self as parent (basic check)
                            .map(d => (
                                <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
                            ))}
                    </select>
                </div>
                <div className="flex justify-end gap-2 pt-4">
                    <Button variant="outline" onClick={onClose} type="button">Annulla</Button>
                    <Button variant="primary" type="submit" isLoading={isSubmitting}>Salva</Button>
                </div>
            </form>
        </Modal>
    );
}

// ═══════════════════════════════════════════════════════════
// Service Modal
// ═══════════════════════════════════════════════════════════
interface ServiceModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    initialData?: OrganizationalService | null;
    departments: Department[];
}

export function ServiceModal({ isOpen, onClose, onSuccess, initialData, departments }: ServiceModalProps) {
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<OrganizationalServiceCreate>();
    const toast = useToast();
    const isEditing = !!initialData;

    useEffect(() => {
        if (isOpen) {
            reset(initialData ? {
                code: initialData.code,
                name: initialData.name,
                description: initialData.description || '',
                department_id: initialData.department_id
            } : {
                code: '',
                name: '',
                description: '',
                department_id: ''
            });
        }
    }, [isOpen, initialData, reset]);

    const onSubmit = async (data: OrganizationalServiceCreate) => {
        try {
            if (isEditing && initialData) {
                await organizationService.updateService(initialData.id, data);
                toast.success('Servizio aggiornato');
            } else {
                await organizationService.createService(data);
                toast.success('Servizio creato');
            }
            onSuccess();
            onClose();
        } catch (error) {
            console.error(error);
            toast.error('Errore nel salvataggio');
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={isEditing ? "Modifica Servizio" : "Nuovo Servizio"}>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700">Dipartimento <span className="text-red-500">*</span></label>
                    <select className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1" {...register('department_id', { required: 'Seleziona un dipartimento' })}>
                        <option value="">Seleziona...</option>
                        {departments.map(d => (
                            <option key={d.id} value={d.id}>{d.name}</option>
                        ))}
                    </select>
                    {errors.department_id && <p className="text-red-500 text-xs mt-1">{errors.department_id.message}</p>}
                </div>
                <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-1">
                        <label className="block text-sm font-medium text-gray-700">Codice</label>
                        <input className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1" {...register('code', { required: 'Richiesto' })} disabled={isEditing} />
                    </div>
                    <div className="col-span-2">
                        <label className="block text-sm font-medium text-gray-700">Nome Servizio</label>
                        <input className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1" {...register('name', { required: 'Richiesto' })} />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700">Descrizione</label>
                    <textarea className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm mt-1" rows={3} {...register('description')} />
                </div>
                <div className="flex justify-end gap-2 pt-4">
                    <Button variant="outline" onClick={onClose} type="button">Annulla</Button>
                    <Button variant="primary" type="submit" isLoading={isSubmitting}>Salva</Button>
                </div>
            </form>
        </Modal>
    );
}
