/**
 * KRONOS - National Contracts (CCNL) Management Page
 * Enterprise-grade Italian labor contract configuration with versioning
 */
import { useState, useEffect } from 'react';
import {
    FileText,
    Plus,
    Edit,
    Trash2,
    ChevronRight,
    ChevronDown,
    Calendar,
    Clock,
    Users,
    AlertCircle,
    X,
    History,
    Save,
    Loader
} from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { useToast } from '../../context/ToastContext';
import { configApi } from '../../services/api';


interface NationalContractLevel {
    id: string;
    level_name: string;
    description: string | null;
    sort_order: number;
}

interface ContractTypeMinimal {
    id: string;
    name: string;
    code: string;
}

interface NationalContractTypeConfig {
    id: string;
    national_contract_version_id: string;
    contract_type_id: string;
    weekly_hours: number;
    annual_vacation_days: number;
    annual_rol_hours: number;
    annual_ex_festivita_hours: number;
    description: string | null;
    contract_type: ContractTypeMinimal;
}

interface NationalContractVersion {
    id: string;
    national_contract_id: string;
    version_name: string;
    valid_from: string;
    valid_to: string | null;
    weekly_hours_full_time: number;
    working_days_per_week: number;
    daily_hours: number;
    annual_vacation_days: number;
    vacation_accrual_method: string;
    vacation_carryover_months: number;
    vacation_carryover_deadline_month: number;
    vacation_carryover_deadline_day: number;
    annual_rol_hours: number;
    rol_accrual_method: string;
    rol_carryover_months: number;
    annual_ex_festivita_hours: number;
    ex_festivita_accrual_method: string;
    annual_study_leave_hours: number | null;
    blood_donation_paid_hours: number | null;
    marriage_leave_days: number | null;
    bereavement_leave_days: number | null;
    l104_monthly_days: number | null;
    sick_leave_carenza_days: number;
    sick_leave_max_days_year: number | null;
    seniority_vacation_bonus: any[] | null;
    seniority_rol_bonus: any[] | null;
    notes: string | null;
    created_at: string;
    contract_type_configs: NationalContractTypeConfig[];
}

interface NationalContract {
    id: string;
    code: string;
    name: string;
    sector: string | null;
    description: string | null;
    source_url: string | null;
    is_active: boolean;
    versions: NationalContractVersion[];
    levels: NationalContractLevel[];
    created_at: string;
}

export function NationalContractsPage() {
    const toast = useToast();
    const [contracts, setContracts] = useState<NationalContract[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [expandedContract, setExpandedContract] = useState<string | null>(null);
    const [showContractModal, setShowContractModal] = useState(false);
    const [showVersionModal, setShowVersionModal] = useState(false);
    const [editingContract, setEditingContract] = useState<NationalContract | null>(null);
    const [editingVersion, setEditingVersion] = useState<NationalContractVersion | null>(null);
    const [selectedContractId, setSelectedContractId] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    // Form state for contract
    const [contractForm, setContractForm] = useState({
        code: '',
        name: '',
        sector: '',
        description: '',
        source_url: '',
    });

    // Form state for type config
    const [editingTypeConfig, setEditingTypeConfig] = useState<NationalContractTypeConfig | null>(null);
    const [showTypeConfigModal, setShowTypeConfigModal] = useState(false);
    const [typeConfigForm, setTypeConfigForm] = useState({
        weekly_hours: 0,
        annual_vacation_days: 0,
        annual_rol_hours: 0,
        annual_ex_festivita_hours: 0,
        description: '',
    });

    const openEditTypeConfig = (conf: NationalContractTypeConfig) => {
        setEditingTypeConfig(conf);
        setTypeConfigForm({
            weekly_hours: conf.weekly_hours,
            annual_vacation_days: conf.annual_vacation_days,
            annual_rol_hours: conf.annual_rol_hours,
            annual_ex_festivita_hours: conf.annual_ex_festivita_hours,
            description: conf.description || '',
        });
        setShowTypeConfigModal(true);
    };

    const handleSaveTypeConfig = async () => {
        if (!editingTypeConfig) return;
        setIsSaving(true);
        try {
            await configApi.put(`/national-contracts/type-configs/${editingTypeConfig.id}`, typeConfigForm);
            toast.success('Parametri aggiornati con successo');
            setShowTypeConfigModal(false);
            loadContracts();
        } catch (error) {
            console.error(error);
            toast.error('Errore durante il salvataggio dei parametri');
        } finally {
            setIsSaving(false);
        }
    };

    // Form state for version
    const [versionForm, setVersionForm] = useState({
        version_name: '',
        valid_from: new Date().toISOString().split('T')[0],
        weekly_hours_full_time: 40,
        working_days_per_week: 5,
        daily_hours: 8,
        annual_vacation_days: 26,
        vacation_carryover_deadline_month: 6,
        vacation_carryover_deadline_day: 30,
        annual_rol_hours: 72,
        annual_ex_festivita_hours: 32,
        marriage_leave_days: 15,
        bereavement_leave_days: 3,
        l104_monthly_days: 3,
        sick_leave_carenza_days: 3,
        notes: '',
    });

    useEffect(() => {
        loadContracts();
    }, []);

    const loadContracts = async () => {
        try {
            console.log("Fetching contracts...");
            const response = await configApi.get('/national-contracts?active_only=false');
            console.log("Contracts response:", response);
            console.log("Items:", response.data.items);
            setContracts(response.data.items || []);
            setIsLoading(false);
        } catch (error) {
            console.error('Failed to load contracts:', error);
            toast.error('Errore nel caricamento dei contratti');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSaveContract = async () => {
        setIsSaving(true);
        try {
            if (editingContract) {
                await configApi.put(`/national-contracts/${editingContract.id}`, contractForm);
                toast.success('Contratto aggiornato');
            } else {
                await configApi.post('/national-contracts', contractForm);
                toast.success('Contratto creato');
            }
            setShowContractModal(false);
            loadContracts();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Errore nel salvataggio');
        } finally {
            setIsSaving(false);
        }
    };

    const handleSaveVersion = async () => {
        if (!selectedContractId) return;
        setIsSaving(true);
        try {
            const payload = {
                ...versionForm,
                national_contract_id: selectedContractId,
                vacation_accrual_method: 'monthly',
                vacation_carryover_months: 18,
                rol_accrual_method: 'monthly',
                rol_carryover_months: 24,
                ex_festivita_accrual_method: 'yearly',
            };

            if (editingVersion) {
                await configApi.put(`/national-contracts/versions/${editingVersion.id}`, payload);
                toast.success('Versione aggiornata');
            } else {
                await configApi.post('/national-contracts/versions', payload);
                toast.success('Nuova versione creata');
            }
            setShowVersionModal(false);
            loadContracts();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Errore nel salvataggio');
        } finally {
            setIsSaving(false);
        }
    };

    const handleDeleteContract = async (id: string) => {
        if (!window.confirm('Sei sicuro di voler disattivare questo contratto?')) return;
        try {
            await configApi.delete(`/national-contracts/${id}`);
            toast.success('Contratto disattivato');
            loadContracts();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Errore');
        }
    };

    const openNewContract = () => {
        setEditingContract(null);
        setContractForm({ code: '', name: '', sector: '', description: '', source_url: '' });
        setShowContractModal(true);
    };

    const openEditContract = (contract: NationalContract) => {
        setEditingContract(contract);
        setContractForm({
            code: contract.code,
            name: contract.name,
            sector: contract.sector || '',
            description: contract.description || '',
            source_url: contract.source_url || '',
        });
        setShowContractModal(true);
    };

    const openNewVersion = (contractId: string) => {
        setSelectedContractId(contractId);
        setEditingVersion(null);
        setVersionForm({
            version_name: '',
            valid_from: new Date().toISOString().split('T')[0],
            weekly_hours_full_time: 40,
            working_days_per_week: 5,
            daily_hours: 8,
            annual_vacation_days: 26,
            vacation_carryover_deadline_month: 6,
            vacation_carryover_deadline_day: 30,
            annual_rol_hours: 72,
            annual_ex_festivita_hours: 32,
            marriage_leave_days: 15,
            bereavement_leave_days: 3,
            l104_monthly_days: 3,
            sick_leave_carenza_days: 3,
            notes: '',
        });
        setShowVersionModal(true);
    };

    const openEditVersion = (version: NationalContractVersion) => {
        setSelectedContractId(version.national_contract_id);
        setEditingVersion(version);
        setVersionForm({
            version_name: version.version_name,
            valid_from: version.valid_from,
            weekly_hours_full_time: version.weekly_hours_full_time,
            working_days_per_week: version.working_days_per_week,
            daily_hours: version.daily_hours,
            annual_vacation_days: version.annual_vacation_days,
            vacation_carryover_deadline_month: version.vacation_carryover_deadline_month,
            vacation_carryover_deadline_day: version.vacation_carryover_deadline_day,
            annual_rol_hours: version.annual_rol_hours,
            annual_ex_festivita_hours: version.annual_ex_festivita_hours,
            marriage_leave_days: version.marriage_leave_days || 15,
            bereavement_leave_days: version.bereavement_leave_days || 3,
            l104_monthly_days: version.l104_monthly_days || 3,
            sick_leave_carenza_days: version.sick_leave_carenza_days,
            notes: version.notes || '',
        });
        setShowVersionModal(true);
    };

    const getCurrentVersion = (versions: NationalContractVersion[]): NationalContractVersion | null => {
        const today = new Date().toISOString().split('T')[0];
        return versions.find(v => v.valid_from <= today && (!v.valid_to || v.valid_to >= today)) || versions[0] || null;
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <Loader size={40} className="text-indigo-600 animate-spin mb-4" />
                <p className="text-gray-500 font-medium">Caricamento contratti nazionali...</p>
            </div>
        );
    }

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto pb-8 animate-fadeIn">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <FileText className="text-indigo-600" size={24} />
                        Contratti Nazionali (CCNL)
                    </h1>
                    <p className="text-sm text-gray-500 mt-1">
                        Gestisci i parametri dei CCNL italiani con storicizzazione delle versioni.
                    </p>
                </div>
                <button
                    onClick={openNewContract}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors shadow-sm"
                >
                    <Plus size={18} />
                    Nuovo CCNL
                </button>
            </div>

            {/* Info Banner */}
            <div className="p-4 bg-blue-50 border border-blue-100 rounded-lg flex gap-3 text-sm text-blue-800">
                <AlertCircle className="shrink-0 text-blue-600 mt-0.5" size={18} />
                <div>
                    <p className="font-semibold">Storicizzazione dei Parametri</p>
                    <p className="opacity-80 mt-1">
                        Ogni modifica ai parametri crea una nuova versione con data di validità.
                        I calcoli storici (es. ferie maturate in anni passati) utilizzeranno sempre i parametri validi a quella data.
                    </p>
                </div>
            </div>

            {/* Contracts List */}
            <div className="space-y-4">
                {contracts.map(contract => {
                    const isExpanded = expandedContract === contract.id;
                    const currentVersion = getCurrentVersion(contract.versions);

                    return (
                        <div key={contract.id} className={`bg-white border rounded-xl overflow-hidden transition-all ${contract.is_active ? 'border-gray-200' : 'border-gray-100 opacity-60'}`}>
                            {/* Contract Header */}
                            <div
                                className="flex items-center gap-4 p-5 cursor-pointer hover:bg-gray-50 transition-colors"
                                onClick={() => setExpandedContract(isExpanded ? null : contract.id)}
                            >
                                <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${contract.is_active ? 'bg-indigo-100 text-indigo-600' : 'bg-gray-100 text-gray-400'}`}>
                                    <FileText size={24} />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <h3 className="font-bold text-gray-900">{contract.name}</h3>
                                        <span className="px-2 py-0.5 text-xs font-mono bg-gray-100 text-gray-600 rounded">{contract.code}</span>
                                        {!contract.is_active && (
                                            <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded">Disattivato</span>
                                        )}
                                    </div>
                                    {contract.sector && (
                                        <p className="text-sm text-gray-500">{contract.sector}</p>
                                    )}
                                </div>
                                <div className="flex items-center gap-2 text-sm text-gray-500">
                                    <History size={14} />
                                    <span>{contract.versions.length} versioni</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={(e) => { e.stopPropagation(); openEditContract(contract); }}
                                        className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                        title="Modifica"
                                    >
                                        <Edit size={16} />
                                    </button>
                                    {contract.is_active && (
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handleDeleteContract(contract.id); }}
                                            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                            title="Disattiva"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    )}
                                    {isExpanded ? <ChevronDown size={20} className="text-gray-400" /> : <ChevronRight size={20} className="text-gray-400" />}
                                </div>
                            </div>

                            {/* Expanded Content */}
                            {isExpanded && (
                                <div className="border-t border-gray-100 bg-gray-50/50">
                                    {/* Current Version Summary */}
                                    {currentVersion && (
                                        <div className="p-5 border-b border-gray-100">
                                            <div className="flex items-center justify-between mb-4">
                                                <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wide">Versione Attuale</h4>
                                                <span className="text-xs text-gray-500">
                                                    Valida dal {format(new Date(currentVersion.valid_from), 'd MMMM yyyy', { locale: it })}
                                                </span>
                                            </div>
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                <div className="bg-white p-3 rounded-lg border border-gray-200">
                                                    <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                                                        <Clock size={12} />
                                                        Ore Settimanali
                                                    </div>
                                                    <div className="text-xl font-bold text-gray-900">{currentVersion.weekly_hours_full_time}h</div>
                                                </div>
                                                <div className="bg-white p-3 rounded-lg border border-gray-200">
                                                    <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                                                        <Calendar size={12} />
                                                        Ferie Annuali
                                                    </div>
                                                    <div className="text-xl font-bold text-emerald-600">{currentVersion.annual_vacation_days} gg</div>
                                                </div>
                                                <div className="bg-white p-3 rounded-lg border border-gray-200">
                                                    <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                                                        <Clock size={12} />
                                                        ROL Annuali
                                                    </div>
                                                    <div className="text-xl font-bold text-blue-600">{currentVersion.annual_rol_hours}h</div>
                                                </div>
                                                <div className="bg-white p-3 rounded-lg border border-gray-200">
                                                    <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                                                        <Calendar size={12} />
                                                        Ex-Festività
                                                    </div>
                                                    <div className="text-xl font-bold text-violet-600">{currentVersion.annual_ex_festivita_hours}h</div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Versions Timeline */}
                                    <div className="p-5">
                                        <div className="flex items-center justify-between mb-4">
                                            <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wide">Storico Versioni</h4>
                                            <button
                                                onClick={() => openNewVersion(contract.id)}
                                                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
                                            >
                                                <Plus size={14} />
                                                Nuova Versione
                                            </button>
                                        </div>

                                        {contract.versions.length === 0 ? (
                                            <div className="text-center py-8 text-gray-400">
                                                <History size={32} className="mx-auto mb-2 opacity-50" />
                                                <p className="text-sm">Nessuna versione configurata</p>
                                                <p className="text-xs">Crea la prima versione per definire i parametri del CCNL.</p>
                                            </div>
                                        ) : (
                                            <div className="space-y-2">
                                                {contract.versions.map((version) => {
                                                    const isCurrent = currentVersion?.id === version.id;
                                                    return (
                                                        <div
                                                            key={version.id}
                                                            className={`flex items-center gap-4 p-4 rounded-lg border transition-colors ${isCurrent ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-gray-200 hover:border-gray-300'}`}
                                                        >
                                                            <div className={`w-3 h-3 rounded-full ${isCurrent ? 'bg-emerald-500' : 'bg-gray-300'}`} />
                                                            <div className="flex-1 min-w-0">
                                                                <div className="flex items-center gap-2">
                                                                    <span className="font-medium text-gray-900">{version.version_name}</span>
                                                                    {isCurrent && (
                                                                        <span className="px-2 py-0.5 text-xs bg-emerald-100 text-emerald-700 rounded-full font-medium">Attuale</span>
                                                                    )}
                                                                </div>
                                                                <div className="text-xs text-gray-500 mt-0.5">
                                                                    Dal {format(new Date(version.valid_from), 'd MMM yyyy', { locale: it })}
                                                                    {version.valid_to && ` al ${format(new Date(version.valid_to), 'd MMM yyyy', { locale: it })}`}
                                                                </div>

                                                                {isCurrent && version.contract_type_configs && version.contract_type_configs.length > 0 && (
                                                                    <div className="mt-3 overflow-hidden rounded-lg border border-gray-200">
                                                                        <div className="bg-gray-50 px-3 py-1.5 text-[10px] font-bold text-gray-500 uppercase tracking-wider border-b border-gray-200">
                                                                            Parametri per Tipologia
                                                                        </div>
                                                                        <div className="overflow-x-auto">
                                                                            <table className="w-full text-xs">
                                                                                <thead>
                                                                                    <tr className="bg-white border-b border-gray-100 text-gray-500 text-left">
                                                                                        <th className="px-3 py-2 font-medium">Tipologia</th>
                                                                                        <th className="px-3 py-2 font-medium text-right">Ore/Set</th>
                                                                                        <th className="px-3 py-2 font-medium text-right">Ferie</th>
                                                                                        <th className="px-3 py-2 font-medium text-right">ROL</th>
                                                                                        <th className="px-3 py-2 font-medium text-right">Ex-Fest</th>
                                                                                        <th className="px-3 py-2 text-right"></th>
                                                                                    </tr>
                                                                                </thead>
                                                                                <tbody className="divide-y divide-gray-50">
                                                                                    {version.contract_type_configs.map((conf) => (
                                                                                        <tr key={conf.id} className="hover:bg-gray-50/50">
                                                                                            <td className="px-3 py-1.5 font-medium text-gray-700">{conf.contract_type?.name}</td>
                                                                                            <td className="px-3 py-1.5 text-right text-gray-600 font-mono">{conf.weekly_hours}</td>
                                                                                            <td className="px-3 py-1.5 text-right text-gray-600 font-mono">{conf.annual_vacation_days}</td>
                                                                                            <td className="px-3 py-1.5 text-right text-gray-600 font-mono">{conf.annual_rol_hours}</td>
                                                                                            <td className="px-3 py-1.5 text-right text-gray-600 font-mono">{conf.annual_ex_festivita_hours}</td>
                                                                                            <td className="px-3 py-1.5 text-right">
                                                                                                <button
                                                                                                    onClick={() => openEditTypeConfig(conf)}
                                                                                                    className="p-1 text-gray-400 hover:text-indigo-600 rounded hover:bg-indigo-50 transition-colors"
                                                                                                    title="Modifica parametri"
                                                                                                >
                                                                                                    <Edit size={12} />
                                                                                                </button>
                                                                                            </td>
                                                                                        </tr>
                                                                                    ))}
                                                                                </tbody>
                                                                            </table>
                                                                        </div>
                                                                    </div>
                                                                )}
                                                            </div>
                                                            <div className="hidden md:flex items-center gap-4 text-xs text-gray-500">
                                                                <span>{version.annual_vacation_days} gg ferie</span>
                                                                <span>{version.annual_rol_hours}h ROL</span>
                                                            </div>
                                                            <button
                                                                onClick={() => openEditVersion(version)}
                                                                className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                                            >
                                                                <Edit size={14} />
                                                            </button>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        )}
                                    </div>

                                    {/* Levels Section */}
                                    <div className="p-5 border-t border-gray-100 bg-white">
                                        <div className="flex items-center justify-between mb-4">
                                            <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wide">Livelli di Inquadramento</h4>
                                            {/* TODO: Add edit/create capability for levels */}
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                            {contract.levels && contract.levels.length > 0 ? (
                                                contract.levels.map((level) => (
                                                    <div key={level.id} className="p-3 border border-gray-200 rounded-lg bg-gray-50/50 hover:bg-gray-50 transition-colors">
                                                        <div className="flex items-center justify-between mb-1">
                                                            <span className="font-bold text-gray-900 bg-white border border-gray-200 px-2 py-0.5 rounded text-sm shadow-sm">{level.level_name}</span>
                                                            <span className="text-[10px] text-gray-400 uppercase tracking-wider font-medium">Pos. {level.sort_order}</span>
                                                        </div>
                                                        {level.description && (
                                                            <p className="text-xs text-gray-600 leading-snug">{level.description}</p>
                                                        )}
                                                    </div>
                                                ))
                                            ) : (
                                                <p className="text-sm text-gray-400 italic">Nessun livello configurato</p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}

                {contracts.length === 0 && (
                    <div className="text-center py-16 bg-white rounded-xl border border-dashed border-gray-200">
                        <FileText size={48} className="mx-auto text-gray-300 mb-4" />
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">Nessun CCNL Configurato</h3>
                        <p className="text-gray-500 text-sm mb-6">Inizia aggiungendo il contratto nazionale applicato dalla tua azienda.</p>
                        <button
                            onClick={openNewContract}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
                        >
                            <Plus size={18} />
                            Aggiungi CCNL
                        </button>
                    </div>
                )}
            </div>

            {/* Contract Modal */}
            {showContractModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowContractModal(false)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                            <h3 className="font-bold text-gray-900">{editingContract ? 'Modifica CCNL' : 'Nuovo CCNL'}</h3>
                            <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowContractModal(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div className="grid grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Codice *</label>
                                    <input
                                        type="text"
                                        value={contractForm.code}
                                        onChange={e => setContractForm({ ...contractForm, code: e.target.value.toUpperCase() })}
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
                                        placeholder="CCNL_COMM"
                                        disabled={!!editingContract}
                                    />
                                </div>
                                <div className="col-span-2">
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
                                    <input
                                        type="text"
                                        value={contractForm.name}
                                        onChange={e => setContractForm({ ...contractForm, name: e.target.value })}
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        placeholder="CCNL Commercio e Terziario"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Settore</label>
                                <input
                                    type="text"
                                    value={contractForm.sector}
                                    onChange={e => setContractForm({ ...contractForm, sector: e.target.value })}
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                    placeholder="Commercio"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                                <textarea
                                    value={contractForm.description}
                                    onChange={e => setContractForm({ ...contractForm, description: e.target.value })}
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm min-h-[80px]"
                                    placeholder="Descrizione del contratto..."
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Link Ufficiale</label>
                                <input
                                    type="url"
                                    value={contractForm.source_url}
                                    onChange={e => setContractForm({ ...contractForm, source_url: e.target.value })}
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                    placeholder="https://..."
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                            <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowContractModal(false)}>
                                Annulla
                            </button>
                            <button
                                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                onClick={handleSaveContract}
                                disabled={isSaving || !contractForm.code || !contractForm.name}
                            >
                                {isSaving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />}
                                Salva
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Type Config Modal */}
            {showTypeConfigModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowTypeConfigModal(false)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                            <h3 className="font-bold text-gray-900">Modifica Parametri: {editingTypeConfig?.contract_type?.name}</h3>
                            <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowTypeConfigModal(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Ore Settimanali</label>
                                    <input
                                        type="number"
                                        step="0.5"
                                        value={typeConfigForm.weekly_hours}
                                        onChange={e => setTypeConfigForm({ ...typeConfigForm, weekly_hours: parseFloat(e.target.value) })}
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Ferie Annuali (gg)</label>
                                    <input
                                        type="number"
                                        value={typeConfigForm.annual_vacation_days}
                                        onChange={e => setTypeConfigForm({ ...typeConfigForm, annual_vacation_days: parseInt(e.target.value) })}
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">ROL Annuali (h)</label>
                                    <input
                                        type="number"
                                        value={typeConfigForm.annual_rol_hours}
                                        onChange={e => setTypeConfigForm({ ...typeConfigForm, annual_rol_hours: parseInt(e.target.value) })}
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Ex-Festività (h)</label>
                                    <input
                                        type="number"
                                        value={typeConfigForm.annual_ex_festivita_hours}
                                        onChange={e => setTypeConfigForm({ ...typeConfigForm, annual_ex_festivita_hours: parseInt(e.target.value) })}
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Note / Descrizione Overrides</label>
                                <textarea
                                    value={typeConfigForm.description}
                                    onChange={e => setTypeConfigForm({ ...typeConfigForm, description: e.target.value })}
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm h-20"
                                    placeholder="Es. Part Time al 50% verticale..."
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                            <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowTypeConfigModal(false)}>
                                Annulla
                            </button>
                            <button
                                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                onClick={handleSaveTypeConfig}
                                disabled={isSaving}
                            >
                                {isSaving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />}
                                Salva
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Version Modal */}
            {showVersionModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn overflow-y-auto" onClick={() => setShowVersionModal(false)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden animate-scaleIn my-8" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-gray-50/50">
                            <h3 className="font-bold text-gray-900">{editingVersion ? 'Modifica Versione' : 'Nuova Versione CCNL'}</h3>
                            <button className="text-gray-400 hover:text-gray-600 p-1" onClick={() => setShowVersionModal(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
                            {/* Version Info */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Nome Versione *</label>
                                    <input
                                        type="text"
                                        value={versionForm.version_name}
                                        onChange={e => setVersionForm({ ...versionForm, version_name: e.target.value })}
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        placeholder="Rinnovo 2024-2027"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Valida dal *</label>
                                    <input
                                        type="date"
                                        value={versionForm.valid_from}
                                        onChange={e => setVersionForm({ ...versionForm, valid_from: e.target.value })}
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                    />
                                </div>
                            </div>

                            {/* Working Hours */}
                            <div>
                                <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3 flex items-center gap-2">
                                    <Clock size={14} />
                                    Orario di Lavoro
                                </h4>
                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Ore Settimanali FT</label>
                                        <input
                                            type="number"
                                            value={versionForm.weekly_hours_full_time}
                                            onChange={e => setVersionForm({ ...versionForm, weekly_hours_full_time: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Giorni/Settimana</label>
                                        <select
                                            value={versionForm.working_days_per_week}
                                            onChange={e => setVersionForm({ ...versionForm, working_days_per_week: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        >
                                            <option value={5}>5 giorni</option>
                                            <option value={6}>6 giorni</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Ore/Giorno</label>
                                        <input
                                            type="number"
                                            step="0.5"
                                            value={versionForm.daily_hours}
                                            onChange={e => setVersionForm({ ...versionForm, daily_hours: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Leave Parameters */}
                            <div>
                                <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3 flex items-center gap-2">
                                    <Calendar size={14} />
                                    Ferie e Permessi
                                </h4>
                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Ferie Annuali (gg)</label>
                                        <input
                                            type="number"
                                            value={versionForm.annual_vacation_days}
                                            onChange={e => setVersionForm({ ...versionForm, annual_vacation_days: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">ROL Annuali (h)</label>
                                        <input
                                            type="number"
                                            value={versionForm.annual_rol_hours}
                                            onChange={e => setVersionForm({ ...versionForm, annual_rol_hours: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Ex-Festività (h)</label>
                                        <input
                                            type="number"
                                            value={versionForm.annual_ex_festivita_hours}
                                            onChange={e => setVersionForm({ ...versionForm, annual_ex_festivita_hours: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4 mt-4">
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Scadenza Ferie AP - Mese</label>
                                        <select
                                            value={versionForm.vacation_carryover_deadline_month}
                                            onChange={e => setVersionForm({ ...versionForm, vacation_carryover_deadline_month: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        >
                                            {[...Array(12)].map((_, i) => (
                                                <option key={i + 1} value={i + 1}>
                                                    {format(new Date(2024, i, 1), 'MMMM', { locale: it })}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Scadenza Ferie AP - Giorno</label>
                                        <input
                                            type="number"
                                            min="1"
                                            max="31"
                                            value={versionForm.vacation_carryover_deadline_day}
                                            onChange={e => setVersionForm({ ...versionForm, vacation_carryover_deadline_day: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Other Leave */}
                            <div>
                                <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3 flex items-center gap-2">
                                    <Users size={14} />
                                    Altri Permessi
                                </h4>
                                <div className="grid grid-cols-4 gap-4">
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Matrimonio (gg)</label>
                                        <input
                                            type="number"
                                            value={versionForm.marriage_leave_days}
                                            onChange={e => setVersionForm({ ...versionForm, marriage_leave_days: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Lutto (gg)</label>
                                        <input
                                            type="number"
                                            value={versionForm.bereavement_leave_days}
                                            onChange={e => setVersionForm({ ...versionForm, bereavement_leave_days: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">L.104 (gg/mese)</label>
                                        <input
                                            type="number"
                                            value={versionForm.l104_monthly_days}
                                            onChange={e => setVersionForm({ ...versionForm, l104_monthly_days: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-medium text-gray-600 mb-1">Carenza Mal. (gg)</label>
                                        <input
                                            type="number"
                                            value={versionForm.sick_leave_carenza_days}
                                            onChange={e => setVersionForm({ ...versionForm, sick_leave_carenza_days: Number(e.target.value) })}
                                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Notes */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Note e Riferimenti</label>
                                <textarea
                                    value={versionForm.notes}
                                    onChange={e => setVersionForm({ ...versionForm, notes: e.target.value })}
                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm min-h-[80px]"
                                    placeholder="Riferimenti normativi, dettagli aggiuntivi..."
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 p-4 bg-gray-50 border-t border-gray-100">
                            <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors" onClick={() => setShowVersionModal(false)}>
                                Annulla
                            </button>
                            <button
                                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                onClick={handleSaveVersion}
                                disabled={isSaving || !versionForm.version_name || !versionForm.valid_from}
                            >
                                {isSaving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />}
                                Salva Versione
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default NationalContractsPage;
