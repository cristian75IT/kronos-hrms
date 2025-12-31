import { useState } from 'react';
import { useContractTypes, useCreateContractType, useUpdateContractType } from '../../hooks/useApi';
import { Loader, Plus, Save, X, Edit2, AlertCircle } from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import type { ContractType } from '../../types';

export function ContractTypesManager() {
    const { data: types, isLoading } = useContractTypes();
    const updateMutation = useUpdateContractType();
    const createMutation = useCreateContractType();
    const toast = useToast();

    const [editingId, setEditingId] = useState<string | null>(null);
    const [editForm, setEditForm] = useState<Partial<ContractType>>({});
    const [isCreating, setIsCreating] = useState(false);
    const [newForm, setNewForm] = useState<Partial<ContractType>>({
        name: '',
        is_part_time: false,
        part_time_percentage: 100,
        annual_vacation_days: 26,
        annual_rol_hours: 104,
        annual_permit_hours: 32,
        is_active: true
    });

    const handleEdit = (type: ContractType) => {
        setEditingId(type.id);
        setEditForm(type);
    };

    const handleSave = async () => {
        if (!editingId) return;
        try {
            await updateMutation.mutateAsync({ id: editingId, data: editForm });
            toast.success('Contratto aggiornato');
            setEditingId(null);
        } catch (error) {
            toast.error('Errore durante l\'aggiornamento');
        }
    };

    const handleCreate = async () => {
        try {
            await createMutation.mutateAsync(newForm);
            toast.success('Contratto creato');
            setIsCreating(false);
            setNewForm({
                name: '',
                is_part_time: false,
                part_time_percentage: 100,
                annual_vacation_days: 26,
                annual_rol_hours: 104,
                annual_permit_hours: 32,
                is_active: true
            });
        } catch (error) {
            toast.error('Errore durante la creazione');
        }
    };

    if (isLoading) return <div className="flex justify-center p-8"><Loader className="animate-spin" /></div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-base-content">Tipi di Contratto</h3>
                <button className="btn btn-primary btn-sm" onClick={() => setIsCreating(true)}>
                    <Plus size={16} /> Nuovo Tipo
                </button>
            </div>

            {isCreating && (
                <div className="card bg-base-100 shadow-lg border border-base-200 mb-6 p-6 animate-fadeIn">
                    <h4 className="font-medium mb-3">Nuovo Contratto</h4>
                    <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-4">
                        <div className="lg:col-span-2">
                            <label className="label">Nome</label>
                            <input className="input input-sm input-bordered w-full" value={newForm.name} onChange={e => setNewForm({ ...newForm, name: e.target.value })} placeholder="Es. Metalmeccanico Full Time" />
                        </div>
                        <div className="lg:col-span-1">
                            <label className="label">Tipo</label>
                            <select className="select select-sm select-bordered w-full"
                                value={newForm.is_part_time ? 'true' : 'false'}
                                onChange={e => setNewForm({ ...newForm, is_part_time: e.target.value === 'true', part_time_percentage: e.target.value === 'true' ? 50 : 100 })}
                            >
                                <option value="false">Full Time</option>
                                <option value="true">Part Time</option>
                            </select>
                        </div>
                        {newForm.is_part_time && (
                            <div className="lg:col-span-1">
                                <label className="label">% Part Time</label>
                                <input type="number" className="input input-sm input-bordered w-full" value={newForm.part_time_percentage} onChange={e => setNewForm({ ...newForm, part_time_percentage: parseInt(e.target.value) })} />
                            </div>
                        )}
                        <div className="lg:col-span-1">
                            <label className="label">Ferie (gg)</label>
                            <input type="number" className="input input-sm input-bordered w-full" value={newForm.annual_vacation_days} onChange={e => setNewForm({ ...newForm, annual_vacation_days: parseInt(e.target.value) })} />
                        </div>
                        <div className="lg:col-span-1">
                            <label className="label">ROL (h)</label>
                            <input type="number" className="input input-sm input-bordered w-full" value={newForm.annual_rol_hours} onChange={e => setNewForm({ ...newForm, annual_rol_hours: parseInt(e.target.value) })} />
                        </div>
                        <div className="lg:col-span-1">
                            <label className="label">Ex-Festività / Altri (h)</label>
                            <input type="number" className="input input-sm input-bordered w-full" value={newForm.annual_permit_hours} onChange={e => setNewForm({ ...newForm, annual_permit_hours: parseInt(e.target.value) })} />
                        </div>
                    </div>
                    <div className="flex justify-end gap-2">
                        <button className="btn btn-ghost btn-sm" onClick={() => setIsCreating(false)}>Annulla</button>
                        <button className="btn btn-primary btn-sm" onClick={handleCreate}>Salva</button>
                    </div>
                </div>
            )}

            <div className="overflow-x-auto bg-base-100 rounded-xl shadow-md border border-base-200">
                <table className="table w-full">
                    <thead className="bg-base-200/50 text-base-content/70 uppercase text-xs font-semibold tracking-wider">
                        <tr>
                            <th>Nome</th>
                            <th>Tipo</th>
                            <th>Ferie (giorni)</th>
                            <th>ROL (ore)</th>
                            <th>Ex-Festività / Altri (ore)</th>
                            <th>Status</th>
                            <th>Azioni</th>
                        </tr>
                    </thead>
                    <tbody>
                        {types?.map(type => (
                            <tr key={type.id} className="hover:bg-base-50">
                                {editingId === type.id ? (
                                    <>
                                        <td><input className="input input-sm input-bordered w-full" value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })} /></td>
                                        <td>
                                            <div className="flex flex-col gap-1">
                                                <select className="select select-xs select-bordered"
                                                    value={editForm.is_part_time ? 'true' : 'false'}
                                                    onChange={e => setEditForm({ ...editForm, is_part_time: e.target.value === 'true' })}
                                                >
                                                    <option value="false">Full Time</option>
                                                    <option value="true">Part Time</option>
                                                </select>
                                                {editForm.is_part_time && (
                                                    <input type="number" className="input input-xs input-bordered w-16" value={editForm.part_time_percentage} onChange={e => setEditForm({ ...editForm, part_time_percentage: parseInt(e.target.value) })} placeholder="%" />
                                                )}
                                            </div>
                                        </td>
                                        <td><input type="number" className="input input-sm input-bordered w-20" value={editForm.annual_vacation_days} onChange={e => setEditForm({ ...editForm, annual_vacation_days: parseInt(e.target.value) })} /></td>
                                        <td><input type="number" className="input input-sm input-bordered w-20" value={editForm.annual_rol_hours} onChange={e => setEditForm({ ...editForm, annual_rol_hours: parseInt(e.target.value) })} /></td>
                                        <td><input type="number" className="input input-sm input-bordered w-20" value={editForm.annual_permit_hours} onChange={e => setEditForm({ ...editForm, annual_permit_hours: parseInt(e.target.value) })} /></td>
                                        <td>
                                            <input type="checkbox" className="toggle toggle-sm toggle-success" checked={editForm.is_active} onChange={e => setEditForm({ ...editForm, is_active: e.target.checked })} />
                                        </td>
                                        <td>
                                            <div className="flex gap-1">
                                                <button className="btn btn-xs btn-success" onClick={handleSave}><Save size={14} /></button>
                                                <button className="btn btn-xs btn-ghost" onClick={() => setEditingId(null)}><X size={14} /></button>
                                            </div>
                                        </td>
                                    </>
                                ) : (
                                    <>
                                        <td className="font-medium">{type.name}</td>
                                        <td>
                                            <div className="flex items-center gap-2">
                                                <span className={`badge badge-sm ${type.is_part_time ? 'badge-secondary badge-outline' : 'badge-primary badge-outline'}`}>
                                                    {type.is_part_time ? 'Part Time' : 'Full Time'}
                                                </span>
                                                {type.is_part_time && <span className="text-xs opacity-70">{type.part_time_percentage}%</span>}
                                            </div>
                                        </td>
                                        <td>{type.annual_vacation_days}</td>
                                        <td>{type.annual_rol_hours}</td>
                                        <td>{type.annual_permit_hours}</td>
                                        <td>
                                            <span className={`badge badge-xs ${type.is_active ? 'badge-success' : 'badge-error'}`}></span>
                                        </td>
                                        <td>
                                            <button className="btn btn-xs btn-ghost" onClick={() => handleEdit(type)}><Edit2 size={14} /></button>
                                        </td>
                                    </>
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="alert alert-info shadow-sm mt-4 text-sm">
                <AlertCircle size={18} />
                <span>
                    Nota: Le modifiche ai parametri contrattuali avranno effetto sui calcoli futuri. Per aggiornare i saldi degli utenti esistenti in base a questi nuovi parametri, utilizza la funzione "Ricalcola Ratei" presente nella barra delle azioni in alto.
                </span>
            </div>
        </div>
    );
}
