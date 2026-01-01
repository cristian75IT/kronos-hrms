/**
 * KRONOS - Contract Types Manager
 */
import { useState } from 'react';
import { useContractTypes, useCreateContractType, useUpdateContractType } from '../../hooks/useApi';
import { Loader, Plus, Save, X, Edit, Clock, Calendar } from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common';
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
        annual_rol_hours: 72,
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
            toast.success('Dati contrattuali sincronizzati');
            setEditingId(null);
        } catch {
            toast.error('Errore durante l\'aggiornamento');
        }
    };

    const handleCreate = async () => {
        try {
            await createMutation.mutateAsync(newForm);
            toast.success('Nuovo template di contratto creato');
            setIsCreating(false);
            setNewForm({
                name: '',
                is_part_time: false,
                part_time_percentage: 100,
                annual_vacation_days: 26,
                annual_rol_hours: 72,
                annual_permit_hours: 32,
                is_active: true
            });
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
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="lg:col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Nome Modello</label>
                            <input
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                placeholder="Es. Metalmeccanico Full Time"
                                value={newForm.name}
                                onChange={e => setNewForm({ ...newForm, name: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Orario</label>
                            <select
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                value={newForm.is_part_time ? 'true' : 'false'}
                                onChange={e => setNewForm({ ...newForm, is_part_time: e.target.value === 'true', part_time_percentage: e.target.value === 'true' ? 50 : 100 })}
                            >
                                <option value="false">Full Time</option>
                                <option value="true">Part Time</option>
                            </select>
                        </div>
                        {newForm.is_part_time && (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">% Carico</label>
                                <input
                                    type="number"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    value={newForm.part_time_percentage}
                                    onChange={e => setNewForm({ ...newForm, part_time_percentage: parseInt(e.target.value) })}
                                />
                            </div>
                        )}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Ferie Annuali (gg)</label>
                            <input
                                type="number"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                value={newForm.annual_vacation_days}
                                onChange={e => setNewForm({ ...newForm, annual_vacation_days: parseInt(e.target.value) })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">ROL Annuali (h)</label>
                            <input
                                type="number"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                value={newForm.annual_rol_hours}
                                onChange={e => setNewForm({ ...newForm, annual_rol_hours: parseInt(e.target.value) })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Permessi (h)</label>
                            <input
                                type="number"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                value={newForm.annual_permit_hours}
                                onChange={e => setNewForm({ ...newForm, annual_permit_hours: parseInt(e.target.value) })}
                            />
                        </div>
                    </div>
                    <div className="flex justify-end gap-3 mt-6">
                        <Button variant="secondary" onClick={() => setIsCreating(false)}>Annulla</Button>
                        <Button variant="primary" onClick={handleCreate}>Crea Modello</Button>
                    </div>
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
                                <tr key={type.id} className="hover:bg-gray-50 transition-colors group">
                                    {editingId === type.id ? (
                                        <>
                                            <td className="px-6 py-4">
                                                <input
                                                    className="w-full px-2 py-1 border border-gray-300 rounded-md text-sm"
                                                    value={editForm.name}
                                                    onChange={e => setEditForm({ ...editForm, name: e.target.value })}
                                                />
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex gap-2">
                                                    <select
                                                        className="px-2 py-1 border border-gray-300 rounded-md text-sm"
                                                        value={editForm.is_part_time ? 'true' : 'false'}
                                                        onChange={e => setEditForm({ ...editForm, is_part_time: e.target.value === 'true' })}
                                                    >
                                                        <option value="false">FT</option>
                                                        <option value="true">PT</option>
                                                    </select>
                                                    {editForm.is_part_time && (
                                                        <input
                                                            type="number"
                                                            className="w-16 px-2 py-1 border border-gray-300 rounded-md text-sm"
                                                            value={editForm.part_time_percentage}
                                                            onChange={e => setEditForm({ ...editForm, part_time_percentage: parseInt(e.target.value) })}
                                                        />
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <input type="number" className="w-16 px-2 py-1 border border-gray-300 rounded-md text-sm text-center" value={editForm.annual_vacation_days} onChange={e => setEditForm({ ...editForm, annual_vacation_days: parseInt(e.target.value) })} />
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <input type="number" className="w-16 px-2 py-1 border border-gray-300 rounded-md text-sm text-center" value={editForm.annual_rol_hours} onChange={e => setEditForm({ ...editForm, annual_rol_hours: parseInt(e.target.value) })} />
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <input type="number" className="w-16 px-2 py-1 border border-gray-300 rounded-md text-sm text-center" value={editForm.annual_permit_hours} onChange={e => setEditForm({ ...editForm, annual_permit_hours: parseInt(e.target.value) })} />
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" checked={editForm.is_active} onChange={e => setEditForm({ ...editForm, is_active: e.target.checked })} />
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex justify-end gap-2">
                                                    <button className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-lg" onClick={handleSave}><Save size={16} /></button>
                                                    <button className="p-2 text-gray-400 hover:bg-gray-100 rounded-lg" onClick={() => setEditingId(null)}><X size={16} /></button>
                                                </div>
                                            </td>
                                        </>
                                    ) : (
                                        <>
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
                                                    onClick={() => handleEdit(type)}
                                                >
                                                    <Edit size={16} />
                                                </button>
                                            </td>
                                        </>
                                    )}
                                </tr>
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

export default ContractTypesManager;
