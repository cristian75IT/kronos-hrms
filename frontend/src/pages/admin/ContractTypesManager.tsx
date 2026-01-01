import { useState } from 'react';
import { useContractTypes, useCreateContractType, useUpdateContractType } from '../../hooks/useApi';
import { Loader, Plus, Save, X, Edit2, TrendingUp, Calendar, Zap, Users, Calculator } from 'lucide-react';
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
            toast.success('Dati contrattuali sincronizzati');
            setEditingId(null);
        } catch (error) {
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
                annual_rol_hours: 104,
                annual_permit_hours: 32,
                is_active: true
            });
        } catch (error) {
            toast.error('Errore durante la creazione');
        }
    };

    if (isLoading) return (
        <div className="flex flex-col items-center justify-center p-12 gap-3 opacity-50">
            <Loader className="animate-spin text-primary" size={32} />
            <span className="text-xs font-black uppercase tracking-widest">Inizializzazione Modelli Contratto...</span>
        </div>
    );

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Context Header */}
            <div className="flex flex-col md:flex-row justify-between items-end md:items-center gap-4">
                <div className="space-y-1">
                    <div className="inline-flex items-center gap-2 px-2 py-0.5 rounded-md bg-secondary/10 border border-secondary/20 text-secondary text-[0.6rem] font-black uppercase tracking-widest">
                        Legal Entity Rules
                    </div>
                    <h3 className="text-2xl font-black text-white flex items-center gap-3">
                        <Users className="text-secondary" size={24} /> Template Contrattuali
                    </h3>
                </div>
                {!isCreating && (
                    <button
                        className="btn btn-primary rounded-2xl px-6 shadow-xl shadow-primary/20 hover:scale-105 transition-transform"
                        onClick={() => setIsCreating(true)}
                    >
                        <Plus size={18} strokeWidth={3} /> Crea Modello
                    </button>
                )}
            </div>

            {isCreating && (
                <div className="relative overflow-hidden p-8 rounded-[2rem] bg-neutral-900 border border-white/5 shadow-2xl animate-fadeInUp">
                    <div className="absolute top-0 right-0 p-8 opacity-5">
                        <Plus size={120} />
                    </div>
                    <div className="relative z-10 space-y-8">
                        <div>
                            <h4 className="text-xl font-black text-white">Nuovo Template Contrattuale</h4>
                            <p className="text-sm text-white/40">Definisci i parametri di maturazione ferie e permessi per una nuova categoria.</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6">
                            <div className="lg:col-span-3 space-y-2">
                                <label className="text-[0.65rem] font-black uppercase tracking-widest text-white/30">Nome Modello</label>
                                <input className="input w-full bg-white/5 border-white/10 text-white rounded-xl focus:border-primary focus:ring-primary h-12" value={newForm.name} onChange={e => setNewForm({ ...newForm, name: e.target.value })} placeholder="Es. Metalmeccanico Full Time" />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[0.65rem] font-black uppercase tracking-widest text-white/30">Tipo Orario</label>
                                <select className="select w-full bg-white/5 border-white/10 text-white rounded-xl focus:border-primary h-12"
                                    value={newForm.is_part_time ? 'true' : 'false'}
                                    onChange={e => setNewForm({ ...newForm, is_part_time: e.target.value === 'true', part_time_percentage: e.target.value === 'true' ? 50 : 100 })}
                                >
                                    <option value="false" className="bg-neutral-900">Full Time</option>
                                    <option value="true" className="bg-neutral-900">Part Time</option>
                                </select>
                            </div>
                            {newForm.is_part_time && (
                                <div className="space-y-2">
                                    <label className="text-[0.65rem] font-black uppercase tracking-widest text-white/30">% Carico</label>
                                    <input type="number" className="input w-full bg-white/5 border-white/10 text-white rounded-xl focus:border-primary h-12" value={newForm.part_time_percentage} onChange={e => setNewForm({ ...newForm, part_time_percentage: parseInt(e.target.value) })} />
                                </div>
                            )}
                            <div className="space-y-2">
                                <label className="text-[0.65rem] font-black uppercase tracking-widest text-white/30 truncate">Ferie Annuali (gg)</label>
                                <input type="number" className="input w-full bg-white/5 border-white/10 text-white rounded-xl focus:border-primary h-12" value={newForm.annual_vacation_days} onChange={e => setNewForm({ ...newForm, annual_vacation_days: parseInt(e.target.value) })} />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="space-y-2">
                                <label className="text-[0.65rem] font-black uppercase tracking-widest text-white/30">ROL Annuali (h)</label>
                                <input type="number" className="input w-full bg-white/5 border-white/10 text-white rounded-xl focus:border-primary h-12" value={newForm.annual_rol_hours} onChange={e => setNewForm({ ...newForm, annual_rol_hours: parseInt(e.target.value) })} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[0.65rem] font-black uppercase tracking-widest text-white/30">Ex-Festività Annuali (h)</label>
                                <input type="number" className="input w-full bg-white/5 border-white/10 text-white rounded-xl focus:border-primary h-12" value={newForm.annual_permit_hours} onChange={e => setNewForm({ ...newForm, annual_permit_hours: parseInt(e.target.value) })} />
                            </div>
                            <div className="flex items-end gap-3">
                                <button className="btn btn-ghost flex-1 rounded-xl text-white/50" onClick={() => setIsCreating(false)}>Annulla</button>
                                <button className="btn btn-primary flex-1 rounded-xl shadow-lg shadow-primary/20" onClick={handleCreate}>Crea Template</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Premium Table Container */}
            <div className="group relative overflow-hidden rounded-[2.5rem] bg-base-100 border border-base-200 shadow-[0_20px_50px_-10px_rgba(0,0,0,0.05)] transition-all duration-700 hover:shadow-2xl">
                <div className="overflow-x-auto">
                    <table className="table w-full border-collapse">
                        <thead>
                            <tr className="bg-base-200/30">
                                <th className="px-8 py-6 text-[0.65rem] font-black uppercase tracking-widest text-base-content/40 border-none">Informazioni Contratto</th>
                                <th className="px-8 py-6 text-[0.65rem] font-black uppercase tracking-widest text-base-content/40 border-none">Configurazione Orario</th>
                                <th className="px-8 py-6 text-[0.65rem] font-black uppercase tracking-widest text-base-content/40 border-none text-center">Ferie (gg)</th>
                                <th className="px-8 py-6 text-[0.65rem] font-black uppercase tracking-widest text-base-content/40 border-none text-center">ROL (h)</th>
                                <th className="px-8 py-6 text-[0.65rem] font-black uppercase tracking-widest text-base-content/40 border-none text-center">Permessi (h)</th>
                                <th className="px-8 py-6 text-[0.65rem] font-black uppercase tracking-widest text-base-content/40 border-none text-center">Status</th>
                                <th className="px-8 py-6 text-[0.65rem] font-black uppercase tracking-widest text-base-content/40 border-none text-right">Azioni</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-base-200">
                            {types?.map(type => (
                                <tr key={type.id} className="group/row transition-all duration-300 hover:bg-primary/[0.02]">
                                    {editingId === type.id ? (
                                        <>
                                            <td className="px-8 py-6"><input className="input input-sm input-primary w-full font-bold h-10 rounded-xl" value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })} /></td>
                                            <td className="px-8 py-6">
                                                <div className="flex gap-2">
                                                    <select className="select select-sm select-bordered rounded-xl h-10"
                                                        value={editForm.is_part_time ? 'true' : 'false'}
                                                        onChange={e => setEditForm({ ...editForm, is_part_time: e.target.value === 'true' })}
                                                    >
                                                        <option value="false">FT</option>
                                                        <option value="true">PT</option>
                                                    </select>
                                                    {editForm.is_part_time && (
                                                        <input type="number" className="input input-sm input-bordered w-16 h-10 rounded-xl" value={editForm.part_time_percentage} onChange={e => setEditForm({ ...editForm, part_time_percentage: parseInt(e.target.value) })} />
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-8 py-6"><input type="number" className="input input-sm input-bordered w-20 mx-auto block h-10 rounded-xl" value={editForm.annual_vacation_days} onChange={e => setEditForm({ ...editForm, annual_vacation_days: parseInt(e.target.value) })} /></td>
                                            <td className="px-8 py-6"><input type="number" className="input input-sm input-bordered w-20 mx-auto block h-10 rounded-xl" value={editForm.annual_rol_hours} onChange={e => setEditForm({ ...editForm, annual_rol_hours: parseInt(e.target.value) })} /></td>
                                            <td className="px-8 py-6"><input type="number" className="input input-sm input-bordered w-20 mx-auto block h-10 rounded-xl" value={editForm.annual_permit_hours} onChange={e => setEditForm({ ...editForm, annual_permit_hours: parseInt(e.target.value) })} /></td>
                                            <td className="px-8 py-6 text-center">
                                                <input type="checkbox" className="toggle toggle-success" checked={editForm.is_active} onChange={e => setEditForm({ ...editForm, is_active: e.target.checked })} />
                                            </td>
                                            <td className="px-8 py-6">
                                                <div className="flex justify-end gap-2">
                                                    <button className="btn btn-sm btn-square btn-success rounded-xl shadow-lg shadow-success/20" onClick={handleSave}><Save size={16} /></button>
                                                    <button className="btn btn-sm btn-square btn-ghost rounded-xl" onClick={() => setEditingId(null)}><X size={16} /></button>
                                                </div>
                                            </td>
                                        </>
                                    ) : (
                                        <>
                                            <td className="px-8 py-6">
                                                <div className="flex flex-col">
                                                    <span className="font-black text-base text-base-content group-hover/row:text-primary transition-colors">{type.name}</span>
                                                    <span className="text-[0.65rem] text-base-content/30 font-mono italic">UUID: {type.id.substring(0, 8)}...</span>
                                                </div>
                                            </td>
                                            <td className="px-8 py-6">
                                                <div className="flex items-center gap-3">
                                                    <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-[0.65rem] font-black uppercase tracking-widest ${type.is_part_time ? 'bg-secondary/10 text-secondary border border-secondary/20' : 'bg-primary/10 text-primary border border-primary/20'}`}>
                                                        {type.is_part_time ? (
                                                            <>
                                                                <TrendingUp size={12} /> Part Time <strong>{type.part_time_percentage}%</strong>
                                                            </>
                                                        ) : (
                                                            <>
                                                                <Zap size={12} /> Full Time
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-8 py-6">
                                                <div className="flex flex-col items-center">
                                                    <span className="text-lg font-black text-base-content/80">{type.annual_vacation_days}</span>
                                                    <span className="text-[0.6rem] font-bold text-base-content/20 uppercase tracking-tighter">Accrued Day/Y</span>
                                                </div>
                                            </td>
                                            <td className="px-8 py-6 text-center">
                                                <div className="flex flex-col items-center">
                                                    <span className="text-lg font-black text-base-content/80">{type.annual_rol_hours}</span>
                                                    <span className="text-[0.6rem] font-bold text-base-content/20 uppercase tracking-tighter">Hours / Y</span>
                                                </div>
                                            </td>
                                            <td className="px-8 py-6 text-center">
                                                <div className="flex flex-col items-center">
                                                    <span className="text-lg font-black text-base-content/80">{type.annual_permit_hours}</span>
                                                    <span className="text-[0.6rem] font-bold text-base-content/20 uppercase tracking-tighter">Hours / Y</span>
                                                </div>
                                            </td>
                                            <td className="px-8 py-6 text-center">
                                                <div className={`w-3 h-3 rounded-full mx-auto shadow-sm ${type.is_active ? 'bg-success shadow-success/30 ring-4 ring-success/10' : 'bg-base-300'}`} />
                                            </td>
                                            <td className="px-8 py-6 text-right">
                                                <button
                                                    className="btn btn-ghost btn-circle btn-sm opacity-0 group-hover/row:opacity-100 transition-all hover:bg-primary/10 hover:text-primary"
                                                    onClick={() => handleEdit(type)}
                                                >
                                                    <Edit2 size={16} />
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

            {/* Compliance Banner */}
            <div className="p-8 rounded-[2rem] bg-amber-500/5 border border-amber-500/20 text-amber-600/80 flex flex-col md:flex-row items-center gap-6">
                <div className="p-4 bg-amber-500/10 rounded-2xl">
                    <Calendar size={32} strokeWidth={2.5} />
                </div>
                <div className="flex-1 space-y-1">
                    <h5 className="font-black text-lg text-amber-700">Audit Contrattuale Importante</h5>
                    <p className="text-sm font-medium leading-relaxed">
                        I modelli definiti in questa sezione fungono da **Blueprint** per tutti i nuovi contratti dipendente.
                        Qualsiasi modifica ai parametri di maturazione (Ferie/ROL) non è retroattiva a meno che non si utilizzi la funzione
                        <span className="px-2 py-0.5 bg-amber-500/10 rounded font-black mx-1 inline-flex items-center gap-1 leading-none"><Calculator size={12} /> Ricalcola Ratei</span>
                        nella Master Console precedente.
                    </p>
                </div>
            </div>
        </div>
    );
}
