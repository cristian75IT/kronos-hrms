/**
 * KRONOS - Contract History Management Component
 * Full CRUD for employee contracts attached to a user
 */
import { useState, useEffect } from 'react';
import { X, Plus, Briefcase, Calendar, Trash2, Edit, Save, AlertCircle, Check } from 'lucide-react';
import { userService } from '../../services/userService';
import type { EmployeeContract, EmployeeContractCreate, ContractType } from '../../types';
import { useToast } from '../../context/ToastContext';

interface ContractHistoryProps {
    userId: string;
    userName?: string;
    onClose: () => void;
}

export function ContractHistory({ userId, userName, onClose }: ContractHistoryProps) {
    const toast = useToast();
    const [contracts, setContracts] = useState<EmployeeContract[]>([]);
    const [contractTypes, setContractTypes] = useState<ContractType[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Form state - matches EmployeeContractCreate interface
    const [formData, setFormData] = useState<Partial<EmployeeContractCreate>>({
        contract_type_id: '',
        start_date: new Date().toISOString().split('T')[0],
        job_title: '',
        department: '',
        weekly_hours: 40,
    });

    useEffect(() => {
        loadData();
    }, [userId]);

    const loadData = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const [contractsData, typesData] = await Promise.all([
                userService.getContracts(userId),
                userService.getContractTypes(),
            ]);
            setContracts(contractsData);
            setContractTypes(typesData);
        } catch (err: unknown) {
            setError('Errore nel caricamento dei contratti');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const resetForm = () => {
        setFormData({
            contract_type_id: '',
            start_date: new Date().toISOString().split('T')[0],
            job_title: '',
            department: '',
            weekly_hours: 40,
        });
        setEditingId(null);
        setIsAdding(false);
    };

    const handleSave = async () => {
        if (!formData.contract_type_id || !formData.start_date) {
            setError('Tipo contratto e data inizio sono obbligatori');
            return;
        }

        try {
            if (editingId) {
                await userService.updateContract(userId, editingId, formData);
                toast.success('Contratto aggiornato');
            } else {
                await userService.addContract(userId, formData as EmployeeContractCreate);
                toast.success('Contratto creato');
            }
            resetForm();
            loadData();
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Errore durante il salvataggio';
            setError(message);
            toast.error(message);
        }
    };

    const handleEdit = (contract: EmployeeContract) => {
        setEditingId(contract.id);
        setFormData({
            contract_type_id: contract.contract_type_id,
            national_contract_id: contract.national_contract_id,
            level_id: contract.level_id,
            start_date: contract.start_date.toString().split('T')[0],
            end_date: contract.end_date?.toString().split('T')[0],
            job_title: contract.job_title || '',
            department: contract.department || '',
            weekly_hours: contract.weekly_hours || 40,
        });
        setIsAdding(true);
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm('Sei sicuro di voler eliminare questo contratto?')) return;
        try {
            await userService.deleteContract(userId, id);
            toast.success('Contratto eliminato');
            loadData();
        } catch (err: unknown) {
            toast.error('Errore durante l\'eliminazione');
            console.error(err);
        }
    };

    const formatDate = (dateStr: string | undefined) => {
        if (!dateStr) return '-';
        try {
            return new Date(dateStr).toLocaleDateString('it-IT', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
            });
        } catch {
            return dateStr;
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-indigo-50 to-white">
                    <div>
                        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                            <Briefcase className="text-indigo-600" size={22} />
                            Gestione Contratti
                        </h2>
                        {userName && <p className="text-sm text-gray-500">{userName}</p>}
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                        <X size={20} className="text-gray-400" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {error && (
                        <div className="p-4 bg-red-50 text-red-700 border border-red-100 rounded-xl flex items-center gap-3">
                            <AlertCircle size={18} />
                            <span className="text-sm font-medium">{error}</span>
                            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">
                                <X size={16} />
                            </button>
                        </div>
                    )}

                    {/* Add/Edit Form */}
                    {isAdding ? (
                        <div className="bg-gray-50 p-5 rounded-xl border border-gray-200 space-y-4 animate-fadeInUp">
                            <div className="flex justify-between items-center">
                                <h3 className="font-bold text-gray-900">
                                    {editingId ? 'Modifica Contratto' : 'Nuovo Contratto'}
                                </h3>
                                <button onClick={resetForm} className="text-gray-400 hover:text-gray-600">
                                    <X size={18} />
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Tipo Contratto *</label>
                                    <select
                                        className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 shadow-sm"
                                        value={formData.contract_type_id}
                                        onChange={e => {
                                            const selectedType = contractTypes.find(ct => ct.id === e.target.value);
                                            const weeklyHours = selectedType
                                                ? (selectedType.is_part_time
                                                    ? Math.round(40 * (selectedType.part_time_percentage / 100))
                                                    : 40)
                                                : 40;
                                            setFormData({
                                                ...formData,
                                                contract_type_id: e.target.value,
                                                weekly_hours: weeklyHours
                                            });
                                        }}
                                    >
                                        <option value="">Seleziona...</option>
                                        {contractTypes.map(ct => (
                                            <option key={ct.id} value={ct.id}>{ct.name}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Mansione</label>
                                    <input
                                        type="text"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                        value={formData.job_title || ''}
                                        onChange={e => setFormData({ ...formData, job_title: e.target.value })}
                                        placeholder="es. Sviluppatore Senior"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Data Inizio *</label>
                                    <input
                                        type="date"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                        value={formData.start_date}
                                        onChange={e => setFormData({ ...formData, start_date: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Data Fine</label>
                                    <input
                                        type="date"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                        value={formData.end_date || ''}
                                        onChange={e => setFormData({ ...formData, end_date: e.target.value || undefined })}
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Reparto</label>
                                    <input
                                        type="text"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                        value={formData.department || ''}
                                        onChange={e => setFormData({ ...formData, department: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Ore Settimanali</label>
                                    <input
                                        type="number"
                                        min="0"
                                        max="60"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                        value={formData.weekly_hours || 40}
                                        onChange={e => setFormData({ ...formData, weekly_hours: parseInt(e.target.value) || 40 })}
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 pt-2">
                                <button onClick={resetForm} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg">
                                    Annulla
                                </button>
                                <button onClick={handleSave} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold flex items-center gap-2">
                                    <Save size={16} /> Salva
                                </button>
                            </div>
                        </div>
                    ) : (
                        <button
                            onClick={() => setIsAdding(true)}
                            className="w-full py-3 border-2 border-dashed border-gray-300 rounded-xl text-gray-500 hover:border-indigo-400 hover:text-indigo-600 transition-colors flex items-center justify-center gap-2"
                        >
                            <Plus size={18} /> Aggiungi Nuovo Contratto
                        </button>
                    )}

                    {/* Contract List */}
                    {isLoading ? (
                        <div className="flex flex-col items-center py-12 gap-3">
                            <div className="w-10 h-10 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin" />
                            <p className="text-sm text-gray-400">Caricamento contratti...</p>
                        </div>
                    ) : contracts.length === 0 ? (
                        <div className="text-center py-12 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
                            <Briefcase className="mx-auto text-gray-300 mb-3" size={40} />
                            <p className="text-gray-500 font-medium">Nessun contratto registrato</p>
                            <p className="text-sm text-gray-400 mt-1">Aggiungi il primo contratto per questo dipendente</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {contracts.map(contract => (
                                <div
                                    key={contract.id}
                                    className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:border-gray-300 transition-colors group"
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex items-start gap-3">
                                            <div className={`p-2.5 rounded-lg ${!contract.end_date ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                                <Briefcase size={20} />
                                            </div>
                                            <div>
                                                <div className="font-bold text-gray-900 flex items-center gap-2">
                                                    {contract.contract_type?.name || 'Contratto'}
                                                    {!contract.end_date && (
                                                        <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-green-100 text-green-700 flex items-center gap-1">
                                                            <Check size={10} /> Attivo
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="text-sm text-gray-500 mt-1 flex items-center gap-1">
                                                    <Calendar size={12} />
                                                    {formatDate(contract.start_date?.toString())}
                                                    {contract.end_date ? ` → ${formatDate(contract.end_date.toString())}` : ' → In corso'}
                                                </div>
                                                {contract.job_title && (
                                                    <div className="text-xs text-gray-400 mt-1">{contract.job_title}</div>
                                                )}
                                                <div className="flex gap-4 mt-2 text-xs text-gray-400">
                                                    {contract.weekly_hours && <span>Ore/sett: {contract.weekly_hours}h</span>}
                                                    {contract.department && <span>Reparto: {contract.department}</span>}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={() => handleEdit(contract)}
                                                className="p-2 hover:bg-gray-100 rounded-lg text-gray-500"
                                                title="Modifica"
                                            >
                                                <Edit size={16} />
                                            </button>
                                            <button
                                                onClick={() => handleDelete(contract.id)}
                                                className="p-2 hover:bg-red-50 rounded-lg text-red-500"
                                                title="Elimina"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-5 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                    >
                        Chiudi
                    </button>
                </div>
            </div>
        </div>
    );
}
