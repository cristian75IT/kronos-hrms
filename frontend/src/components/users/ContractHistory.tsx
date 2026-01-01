/**
 * KRONOS - Contract History Component
 * Enterprise-grade contract management with timeline
 */
import { useState, useEffect } from 'react';
import { userService } from '../../services/userService';
import { leavesService } from '../../services/leaves.service';
import type { EmployeeContract, ContractType, EmployeeContractCreate } from '../../types';
import {
    Plus,
    X,
    Calendar,
    Briefcase,
    Clock,
    FileText,
    CheckCircle,
    AlertCircle,
    ChevronDown,
    ChevronUp,
    Edit,
} from 'lucide-react';

interface ContractHistoryProps {
    userId: string;
    userName?: string;
    onClose: () => void;
}

export function ContractHistory({ userId, userName, onClose }: ContractHistoryProps) {
    const [contracts, setContracts] = useState<EmployeeContract[]>([]);
    const [contractTypes, setContractTypes] = useState<ContractType[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Form state
    const [newContract, setNewContract] = useState<Partial<EmployeeContractCreate>>({
        weekly_hours: 40,
        start_date: new Date().toISOString().split('T')[0],
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
        } catch (err: any) {
            setError('Errore nel caricamento dei contratti');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async () => {
        if (!newContract.contract_type_id || !newContract.start_date) {
            setError('Compila tutti i campi obbligatori');
            return;
        }

        try {
            await userService.addContract(userId, newContract as EmployeeContractCreate);

            // Integration: Recalculate leave accruals for this user immediately after contract change
            try {
                await leavesService.recalculateUserAccruals(userId);
            } catch (recalcErr) {
                console.error('Non-critical error: failed to auto-recalculate accruals', recalcErr);
                // We don't block the user, as the manual button is available in Config
            }

            setIsAdding(false);
            setNewContract({ weekly_hours: 40, start_date: new Date().toISOString().split('T')[0] });
            loadData();
        } catch (err: any) {
            setError(err.message || 'Errore durante il salvataggio');
        }
    };

    const getTypeName = (id: string) => contractTypes.find(t => t.id === id)?.name || id;
    const getTypeCode = (id: string) => contractTypes.find(t => t.id === id)?.code || '';

    const activeContract = contracts.find(c => !c.end_date);
    const pastContracts = contracts.filter(c => c.end_date);

    const formatDate = (dateStr: string) => {
        try {
            const date = new Date(dateStr);
            if (isNaN(date.getTime())) return '-';
            return date.toLocaleDateString('it-IT', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
            });
        } catch (e) {
            return '-';
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4" onClick={e => e.target === e.currentTarget && onClose()}>
            <div className="bg-white w-full max-w-2xl max-h-[90vh] rounded-xl shadow-2xl flex flex-col overflow-hidden animate-scaleIn">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-blue-50/50 to-transparent">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-slate-700 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-200">
                            <Briefcase size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-900 leading-tight">Gestione Contratti</h2>
                            {userName && <p className="text-sm text-gray-500">{userName}</p>}
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 p-6 overflow-y-auto">
                    {error && (
                        <div className="flex items-center gap-3 p-4 bg-red-50 text-red-700 border border-red-100 rounded-lg mb-4">
                            <AlertCircle size={16} className="shrink-0" />
                            <span className="flex-1 text-sm font-medium">{error}</span>
                            <button onClick={() => setError(null)} className="p-1 hover:bg-red-100 rounded text-red-500">
                                <X size={14} />
                            </button>
                        </div>
                    )}

                    {/* Add Contract Button */}
                    {!isAdding && (
                        <button
                            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium shadow-sm transition-all hover:shadow-md hover:-translate-y-0.5 mb-6"
                            onClick={() => setIsAdding(true)}
                        >
                            <Plus size={18} />
                            Nuovo Contratto
                        </button>
                    )}

                    {/* Add Contract Form */}
                    {isAdding && (
                        <div className="bg-white border border-gray-200 rounded-xl shadow-sm mb-6 overflow-hidden animate-fadeInUp">
                            <div className="px-5 py-4 bg-gray-50 border-b border-gray-200">
                                <h3 className="flex items-center gap-2 text-base font-semibold text-blue-700">
                                    <FileText size={18} />
                                    Nuovo Contratto
                                </h3>
                            </div>
                            <div className="p-5 space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="block text-sm font-medium text-gray-700 flex items-center gap-1">
                                            Tipo Contratto <span className="text-red-500">*</span>
                                        </label>
                                        <select
                                            className="w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                                            value={newContract.contract_type_id || ''}
                                            onChange={e => {
                                                const typeId = e.target.value;
                                                const type = contractTypes.find(t => t.id === typeId);
                                                // Default 40h base, adjusted by part-time percentage
                                                const defaultHours = type ? Math.round(40 * ((type.part_time_percentage || 100) / 100)) : 40;

                                                setNewContract({
                                                    ...newContract,
                                                    contract_type_id: typeId,
                                                    weekly_hours: defaultHours
                                                });
                                            }}
                                        >
                                            <option value="">Seleziona tipo...</option>
                                            {contractTypes.map(t => (
                                                <option key={t.id} value={t.id}>
                                                    {t.name} ({t.code})
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="block text-sm font-medium text-gray-700 flex items-center gap-1">
                                            Ore Settimanali <span className="text-red-500">*</span>
                                        </label>
                                        <input
                                            type="number"
                                            className="w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                                            value={newContract.weekly_hours}
                                            onChange={e => setNewContract({ ...newContract, weekly_hours: parseInt(e.target.value) })}
                                            min={1}
                                            max={48}
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="block text-sm font-medium text-gray-700 flex items-center gap-1">
                                            Data Inizio <span className="text-red-500">*</span>
                                        </label>
                                        <input
                                            type="date"
                                            className="w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                                            value={newContract.start_date}
                                            onChange={e => setNewContract({ ...newContract, start_date: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="block text-sm font-medium text-gray-700">Data Fine (opzionale)</label>
                                        <input
                                            type="date"
                                            className="w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                                            value={newContract.end_date || ''}
                                            onChange={e => setNewContract({ ...newContract, end_date: e.target.value || undefined })}
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-700">Mansione</label>
                                    <input
                                        type="text"
                                        className="w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                                        value={newContract.job_title || ''}
                                        onChange={e => setNewContract({ ...newContract, job_title: e.target.value })}
                                        placeholder="es. Software Engineer Senior"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-700">Livello / Inquadramento</label>
                                    <input
                                        type="text"
                                        className="w-full px-3 py-2.5 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                                        value={newContract.level || ''}
                                        onChange={e => setNewContract({ ...newContract, level: e.target.value })}
                                        placeholder="es. Quadro, Impiegato III Livello"
                                    />
                                </div>

                                <div className="flex justify-end gap-3 pt-4 border-t border-gray-100 mt-4">
                                    <button className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setIsAdding(false)}>
                                        Annulla
                                    </button>
                                    <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium shadow-sm transition-colors" onClick={handleSave}>
                                        <CheckCircle size={16} />
                                        Salva Contratto
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Loading State */}
                    {isLoading && (
                        <div className="flex flex-col items-center justify-center py-12 text-gray-400 gap-3">
                            <div className="w-8 h-8 border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin" />
                            <p className="text-sm">Caricamento contratti...</p>
                        </div>
                    )}

                    {/* Contracts List */}
                    {!isLoading && (
                        <div className="space-y-6">
                            {/* Active Contract */}
                            {activeContract && (
                                <div className="space-y-3">
                                    <h4 className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                        <CheckCircle size={14} className="text-emerald-500" />
                                        Contratto Attivo
                                    </h4>
                                    <div className="bg-white border border-emerald-200 rounded-xl p-4 shadow-sm ring-1 ring-emerald-500/10 transition-all">
                                        <div className="flex items-start gap-3 mb-3">
                                            <div className="px-2.5 py-1.5 bg-emerald-50 text-emerald-700 rounded-md text-xs font-bold uppercase border border-emerald-200">
                                                {getTypeCode(activeContract.contract_type_id)}
                                            </div>
                                            <div className="flex-1">
                                                <h4 className="font-semibold text-gray-900 mb-1">{getTypeName(activeContract.contract_type_id)}</h4>
                                                {activeContract.job_title && (
                                                    <p className="text-sm text-gray-500">{activeContract.job_title}</p>
                                                )}
                                            </div>
                                            <button
                                                className="p-1 hover:bg-gray-100 rounded text-gray-400 transition-colors"
                                                onClick={() => setExpandedId(expandedId === activeContract.id ? null : activeContract.id)}
                                            >
                                                {expandedId === activeContract.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                            </button>
                                        </div>

                                        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                                            <span className="flex items-center gap-1.5">
                                                <Calendar size={14} className="text-gray-400" />
                                                Dal {formatDate(activeContract.start_date)}
                                            </span>
                                            <span className="flex items-center gap-1.5">
                                                <Clock size={14} className="text-gray-400" />
                                                {activeContract.weekly_hours}h/settimana
                                            </span>
                                        </div>

                                        {expandedId === activeContract.id && (
                                            <div className="mt-4 pt-4 border-t border-gray-100 animate-fadeInUp">
                                                <div className="grid grid-cols-3 gap-4 mb-4">
                                                    {activeContract.level && (
                                                        <div className="flex flex-col gap-1">
                                                            <span className="text-xs font-bold text-gray-400 uppercase tracking-wide">Livello</span>
                                                            <span className="font-semibold text-gray-900">{activeContract.level}</span>
                                                        </div>
                                                    )}
                                                    <div className="flex flex-col gap-1">
                                                        <span className="text-xs font-bold text-gray-400 uppercase tracking-wide">Ore Settimanali</span>
                                                        <span className="font-semibold text-gray-900">{activeContract.weekly_hours}</span>
                                                    </div>
                                                </div>
                                                <div className="flex gap-2">
                                                    <button className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md text-sm font-medium transition-colors">
                                                        <Edit size={14} />
                                                        Modifica
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Past Contracts */}
                            {pastContracts.length > 0 && (
                                <div className="space-y-3">
                                    <h4 className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                        <Clock size={14} />
                                        Storico Contratti ({pastContracts.length})
                                    </h4>
                                    <div className="relative pl-2">
                                        {pastContracts.map((contract, index) => (
                                            <div key={contract.id} className="flex gap-4 group">
                                                <div className="flex flex-col items-center pt-2">
                                                    <div className="w-3 h-3 bg-gray-300 rounded-full shrink-0 group-hover:bg-gray-400 transition-colors" />
                                                    {index < pastContracts.length - 1 && <div className="w-0.5 flex-1 bg-gray-200 mt-2" />}
                                                </div>
                                                <div className="flex-1 pb-6">
                                                    <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 transition-all hover:bg-white hover:shadow-sm">
                                                        <div className="flex items-start gap-3 mb-3">
                                                            <div className="px-2.5 py-1.5 bg-gray-200 text-gray-600 rounded-md text-xs font-bold uppercase">
                                                                {getTypeCode(contract.contract_type_id)}
                                                            </div>
                                                            <div className="flex-1">
                                                                <h4 className="font-semibold text-gray-900 mb-1">{getTypeName(contract.contract_type_id)}</h4>
                                                                {contract.job_title && (
                                                                    <p className="text-sm text-gray-500">{contract.job_title}</p>
                                                                )}
                                                            </div>
                                                        </div>
                                                        <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                                                            <span className="flex items-center gap-1.5">
                                                                <Calendar size={14} />
                                                                {formatDate(contract.start_date)} - {formatDate(contract.end_date!)}
                                                            </span>
                                                            <span className="flex items-center gap-1.5">
                                                                <Clock size={14} />
                                                                {contract.weekly_hours}h/settimana
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Empty State */}
                            {contracts.length === 0 && (
                                <div className="flex flex-col items-center justify-center py-12 text-center">
                                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center text-gray-400 mb-4">
                                        <FileText size={32} />
                                    </div>
                                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Nessun contratto</h3>
                                    <p className="text-sm text-gray-500 max-w-xs">
                                        Non ci sono contratti registrati per questo dipendente. Aggiungine uno per iniziare.
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

