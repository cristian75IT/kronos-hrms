import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import {
    ArrowLeft,
    Save,
    Calendar,
    History,
    CheckCircle,
    Info,
    Settings,
    Layers,
    Trash2,
    Edit2,
    Plus,
    BarChart3,
    Calculator,
    X
} from 'lucide-react';
import { configService } from '../../services/config.service';
import { useToast } from '../../context/ToastContext';
import { ConfirmModal } from '../../components/common';
import type { NationalContract, NationalContractVersion, NationalContractLevel } from '../../types';

export function NationalContractDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const toast = useToast();

    // Data State
    const [contract, setContract] = useState<NationalContract | null>(null);
    const [versions, setVersions] = useState<NationalContractVersion[]>([]);
    const [levels, setLevels] = useState<NationalContractLevel[]>([]);
    const [contractTypes, setContractTypes] = useState<any[]>([]);
    const [selectedVersion, setSelectedVersion] = useState<NationalContractVersion | null>(null);

    // UI State
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [activeTab, setActiveTab] = useState<'versions' | 'levels' | 'type_configs' | 'calc_modes'>('versions');
    const [calculationModes, setCalculationModes] = useState<any[]>([]);
    const [isSavingConfig, setIsSavingConfig] = useState(false);

    // Level Editing State
    const [isEditingLevel, setIsEditingLevel] = useState(false);
    const [currentLevel, setCurrentLevel] = useState<NationalContractLevel | null>(null);

    // Config Editing State
    const [editingConfig, setEditingConfig] = useState<any | null>(null);
    const { register: registerConfig, handleSubmit: handleSubmitConfig, reset: resetConfig } = useForm();

    // Calc Mode State
    const [isEditingMode, setIsEditingMode] = useState(false);
    const [currentMode, setCurrentMode] = useState<any | null>(null);
    const { register: registerMode, handleSubmit: handleSubmitMode, reset: resetMode } = useForm();

    // Confirm States
    const [deleteLevelId, setDeleteLevelId] = useState<string | null>(null);
    const [deleteModeId, setDeleteModeId] = useState<string | null>(null);
    const [deleteConfigId, setDeleteConfigId] = useState<string | null>(null);

    // Forms
    const {
        register: registerVersion,
        handleSubmit: handleSubmitVersion,
        reset: resetVersion
    } = useForm<NationalContractVersion>();

    const {
        register: registerLevel,
        handleSubmit: handleSubmitLevel,
        reset: resetLevel
    } = useForm<NationalContractLevel>();

    useEffect(() => {
        if (id) {
            loadData(id);
        }
    }, [id]);

    useEffect(() => {
        if (selectedVersion) {
            resetVersion(selectedVersion);
        }
    }, [selectedVersion, resetVersion]);

    useEffect(() => {
        if (currentLevel) {
            resetLevel(currentLevel);
        } else {
            resetLevel({
                level_name: '',
                description: '',
                sort_order: (levels.length > 0 ? Math.max(...levels.map(l => l.sort_order)) + 10 : 10)
            } as any);
        }
    }, [currentLevel, resetLevel, levels]);

    const loadData = async (contractId: string) => {
        setIsLoading(true);
        try {
            const [contractData, versionsData, typesData, modesData] = await Promise.all([
                configService.getNationalContract(contractId),
                configService.getNationalContractVersions(contractId),
                configService.getContractTypes(),
                configService.getCalculationModes()
            ]);

            setContract(contractData);
            setVersions(versionsData);
            setContractTypes(typesData);
            setCalculationModes(modesData);
            // Assuming contractData contains levels as per schema
            if (contractData.levels) {
                setLevels(contractData.levels.sort((a: any, b: any) => a.sort_order - b.sort_order));
            }

            if (versionsData.length > 0) {
                setSelectedVersion(versionsData[0]);
            }
        } catch (error) {
            console.error('Failed to load contract details', error);
            toast.error('Errore caricamento dati');
            navigate('/admin/national-contracts');
        } finally {
            setIsLoading(false);
        }
    };

    const onSubmitVersion = async (data: NationalContractVersion) => {
        if (!selectedVersion) return;

        setIsSaving(true);
        try {
            // Only update allowed fields
            const updatePayload = {
                annual_vacation_days: Number(data.annual_vacation_days),
                vacation_carryover_months: Number(data.vacation_carryover_months),
                annual_rol_hours: Number(data.annual_rol_hours),
                rol_carryover_months: Number(data.rol_carryover_months),
                annual_ex_festivita_hours: Number(data.annual_ex_festivita_hours),
                weekly_hours_full_time: Number(data.weekly_hours_full_time),
                working_days_per_week: Number(data.working_days_per_week),
                count_saturday_as_leave: data.count_saturday_as_leave,
                vacation_calc_mode_id: data.vacation_calc_mode_id || null,
                rol_calc_mode_id: data.rol_calc_mode_id || null,
                notes: data.notes
            };

            const updated = await configService.updateNationalContractVersion(selectedVersion.id, updatePayload);

            setVersions(versions.map(v => v.id === updated.id ? updated : v));
            setSelectedVersion(updated);

            toast.success('Parametri aggiornati con successo');
        } catch (error: any) {
            console.error('Failed to update version', error);
            toast.error(error.detail || 'Errore salvataggio modifiche');
        } finally {
            setIsSaving(false);
        }
    };

    const onSubmitLevel = async (data: NationalContractLevel) => {
        if (!contract) return;

        try {
            if (currentLevel?.id) {
                // Update
                const updated = await configService.updateNationalContractLevel(currentLevel.id, {
                    ...data,
                    sort_order: Number(data.sort_order)
                });
                setLevels(levels.map(l => l.id === updated.id ? updated : l).sort((a, b) => a.sort_order - b.sort_order));
                toast.success('Livello aggiornato');
            } else {
                // Create
                const created = await configService.createNationalContractLevel({
                    ...data,
                    sort_order: Number(data.sort_order),
                    national_contract_id: contract.id
                });
                setLevels([...levels, created].sort((a, b) => a.sort_order - b.sort_order));
                toast.success('Livello creato');
            }
            setIsEditingLevel(false);
            setCurrentLevel(null);
        } catch (error: any) {
            console.error('Failed to save level', error);
            toast.error(error.detail || 'Errore salvataggio livello');
        }
    };

    const onRequestDeleteLevel = (id: string) => {
        setDeleteLevelId(id);
    };

    const confirmDeleteLevel = async () => {
        if (!deleteLevelId) return;

        try {
            await configService.deleteNationalContractLevel(deleteLevelId);
            setLevels(prev => prev.filter(l => l.id !== deleteLevelId));
            toast.success('Livello eliminato');
        } catch (error: any) {
            toast.error(error.detail || 'Errore eliminazione livello');
        } finally {
            setDeleteLevelId(null);
        }
    };

    // Mode Handlers
    useEffect(() => {
        if (currentMode) {
            resetMode(currentMode);
        } else {
            resetMode({
                name: '',
                code: '',
                description: '',
                function_name: '',
                default_parameters: {}
            });
        }
    }, [currentMode, resetMode]);

    const onSubmitMode = async (data: any) => {
        try {
            if (currentMode?.id) {
                const updated = await configService.updateCalculationMode(currentMode.id, data);
                setCalculationModes(calculationModes.map(m => m.id === updated.id ? updated : m));
                toast.success('Modalità aggiornata');
            } else {
                const created = await configService.createCalculationMode(data);
                setCalculationModes([...calculationModes, created]);
                toast.success('Modalità creata');
            }
            setIsEditingMode(false);
            setCurrentMode(null);
        } catch (error: any) {
            console.error(error);
            toast.error(error.detail || 'Errore salvataggio modalità');
        }
    };

    const onRequestDeleteMode = (id: string) => {
        setDeleteModeId(id);
    };

    const confirmDeleteMode = async () => {
        if (!deleteModeId) return;
        try {
            await configService.deleteCalculationMode(deleteModeId);
            setCalculationModes(prev => prev.filter(m => m.id !== deleteModeId));
            toast.success('Modalità eliminata');
        } catch (e: any) {
            toast.error('Errore eliminazione');
        } finally {
            setDeleteModeId(null);
        }
    };

    // Config Handlers
    useEffect(() => {
        if (editingConfig) {
            resetConfig(editingConfig);
        } else {
            resetConfig({
                contract_type_id: '',
                weekly_hours: 40,
                annual_vacation_days: 26,
                annual_rol_hours: 72,
                annual_ex_festivita_hours: 32
            });
        }
    }, [editingConfig, resetConfig]);

    const onSaveConfig = async (data: any) => {
        if (!selectedVersion || !id) return;
        setIsSavingConfig(true);
        try {
            // Force number conversion for safety
            const payload = {
                ...data,
                weekly_hours: Number(data.weekly_hours),
                annual_vacation_days: Number(data.annual_vacation_days),
                annual_rol_hours: Number(data.annual_rol_hours),
                annual_ex_festivita_hours: Number(data.annual_ex_festivita_hours)
            };

            if (editingConfig?.id) {
                await configService.updateNationalContractTypeConfig(editingConfig.id, payload);
                toast.success('Configurazione aggiornata');
            } else {
                await configService.createNationalContractTypeConfig({
                    ...payload,
                    national_contract_version_id: selectedVersion.id
                });
                toast.success('Configurazione aggiunta');
            }
            setEditingConfig(null);

            // Refresh
            const updatedVersions = await configService.getNationalContractVersions(id);
            setVersions(updatedVersions);
            const updatedCurrent = updatedVersions.find((v: any) => v.id === selectedVersion.id);
            if (updatedCurrent) setSelectedVersion(updatedCurrent);

        } catch (error: any) {
            console.error(error);
            toast.error(error.detail || 'Errore salvataggio config');
        } finally {
            setIsSavingConfig(false);
        }
    };

    const onRequestDeleteConfig = (configId: string) => {
        setDeleteConfigId(configId);
    };

    const confirmDeleteConfig = async () => {
        if (!deleteConfigId || !id) return;
        try {
            await configService.deleteNationalContractTypeConfig(deleteConfigId);

            // Refresh
            const updatedVersions = await configService.getNationalContractVersions(id);
            setVersions(updatedVersions);
            const updatedCurrent = updatedVersions.find((v: any) => v.id === selectedVersion?.id);
            if (updatedCurrent) setSelectedVersion(updatedCurrent);

            toast.success('Configurazione eliminata');
        } catch (e: any) {
            toast.error(e.detail || 'Errore eliminazione');
        } finally {
            setDeleteConfigId(null);
        }
    };

    if (isLoading || !contract) {
        return (
            <div className="flex justify-center items-center h-screen">
                <div className="spinner-lg" />
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fadeIn pb-12 p-6 max-w-7xl mx-auto">
            {/* Header */}
            <header className="flex items-center gap-4 border-b border-gray-200 pb-6">
                <button onClick={() => navigate('/admin/national-contracts')} className="btn btn-ghost p-2 rounded-full hover:bg-gray-100">
                    <ArrowLeft size={20} className="text-gray-500" />
                </button>
                <div>
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                        <Link to="/admin/national-contracts" className="hover:text-primary transition-colors">Contratti</Link>
                        <span>/</span>
                        <span>{contract.code}</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-2xl font-bold text-gray-900">{contract.name}</h1>
                        {contract.sector && <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs uppercase font-medium tracking-wide">{contract.sector}</span>}
                    </div>
                </div>
            </header>

            {/* Tabs */}
            <div className="flex border-b border-gray-200 overflow-x-auto">
                <button
                    onClick={() => setActiveTab('versions')}
                    className={`px-6 py-3 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${activeTab === 'versions' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                >
                    <Settings size={18} />
                    Parametri & Versioni
                </button>
                <button
                    onClick={() => setActiveTab('levels')}
                    className={`px-6 py-3 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${activeTab === 'levels' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                >
                    <Layers size={18} />
                    Livelli Contrattuali
                </button>
                <button
                    onClick={() => setActiveTab('type_configs')}
                    className={`px-6 py-3 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${activeTab === 'type_configs' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                >
                    <Layers size={18} />
                    Specifiche Tipi Contratto
                </button>
                <button
                    onClick={() => setActiveTab('calc_modes')}
                    className={`px-6 py-3 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${activeTab === 'calc_modes' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                >
                    <Calculator size={18} />
                    Modalità Calcolo
                </button>
            </div>

            {/* Content Versions */}
            {activeTab === 'versions' && (
                <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-8 animate-fadeIn">

                    {/* Sidebar - Version Selector */}
                    <div className="space-y-6">
                        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                            <div className="p-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                                    <History size={18} />
                                    Versioni CCNL
                                </h3>
                                {/* Disabled for now as backend logic for new version (closing old one) should be carefully handled */}
                                <button className="text-xs text-indigo-600 font-medium hover:underline cursor-not-allowed opacity-50">+ Nuova</button>
                            </div>
                            <div className="divide-y divide-gray-100 max-h-[400px] overflow-y-auto">
                                {versions.map(version => (
                                    <button
                                        key={version.id}
                                        onClick={() => setSelectedVersion(version)}
                                        className={`w-full text-left p-4 hover:bg-gray-50 transition-colors flex items-center justify-between group ${selectedVersion?.id === version.id ? 'bg-indigo-50/50 border-l-4 border-indigo-500' : 'border-l-4 border-transparent'}`}
                                    >
                                        <div>
                                            <p className={`font-medium ${selectedVersion?.id === version.id ? 'text-indigo-700' : 'text-gray-900'}`}>{version.version_name}</p>
                                            <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                                                <Calendar size={12} />
                                                Dal {new Date(version.valid_from).toLocaleDateString()}
                                            </p>
                                        </div>
                                        {selectedVersion?.id === version.id && <CheckCircle size={16} className="text-indigo-500" />}
                                    </button>
                                ))}
                                {versions.length === 0 && (
                                    <div className="p-4 text-center text-gray-500 text-sm">Nessuna versione configurata.</div>
                                )}
                            </div>
                        </div>

                        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
                            <div className="flex gap-3">
                                <Info size={20} className="text-blue-600 shrink-0 mt-0.5" />
                                <div className="text-sm text-blue-800">
                                    <p className="font-bold mb-1">Nota Importante</p>
                                    <p className="opacity-90">I calcoli di maturazione vengono eseguiti mensilmente in base alla versione del CCNL attiva in quel periodo. Modificare i parametri storici non ricalcola automaticamente il passato.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Main Form Area */}
                    <div className="space-y-6">
                        {selectedVersion ? (<>
                            <form onSubmit={handleSubmitVersion(onSubmitVersion)} className="animate-fadeIn">
                                {/* Calculated Rules Section */}
                                <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden mb-6">
                                    <div className="p-5 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                                        <div className="flex items-center gap-3 text-indigo-700">
                                            <Settings size={20} />
                                            <h2 className="text-lg font-bold">Parametri di Maturazione</h2>
                                        </div>
                                        <span className="text-xs bg-white border border-gray-200 px-2 py-1 rounded text-gray-500">
                                            Versione: {selectedVersion.version_name}
                                        </span>
                                    </div>

                                    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">

                                        {/* Ferie */}
                                        <div className="space-y-4">
                                            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider border-b pb-2 mb-4">Ferie</h3>

                                            <div className="space-y-2">
                                                <label className="block text-sm font-medium text-gray-700">Modalità Calcolo</label>
                                                <select
                                                    className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                                    {...registerVersion('vacation_calc_mode_id')}
                                                >
                                                    <option value="">Seleziona...</option>
                                                    {calculationModes.map((mode: any) => (
                                                        <option key={mode.id} value={mode.id}>{mode.name}</option>
                                                    ))}
                                                </select>
                                            </div>

                                            <div className="space-y-2">
                                                <label className="block text-sm font-medium text-gray-700">Giorni Annuali (Full Time)</label>
                                                <div className="relative rounded-md shadow-sm">
                                                    <input
                                                        type="number"
                                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm pl-3 pr-12"
                                                        {...registerVersion('annual_vacation_days', { required: true, min: 0 })}
                                                    />
                                                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-gray-400 text-sm">
                                                        giorni
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="space-y-2">
                                                <label className="block text-sm font-medium text-gray-700">Scadenza Consumo (mesi)</label>
                                                <div className="relative rounded-md shadow-sm">
                                                    <input
                                                        type="number"
                                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm pl-3 pr-12"
                                                        {...registerVersion('vacation_carryover_months')}
                                                    />
                                                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-gray-400 text-sm">
                                                        mesi
                                                    </div>
                                                </div>
                                                <p className="text-xs text-gray-500">Solitamente 18 mesi</p>
                                            </div>
                                        </div>

                                        {/* ROL / Permessi */}
                                        <div className="space-y-4">
                                            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider border-b pb-2 mb-4">ROL / Permessi</h3>

                                            <div className="space-y-2">
                                                <label className="block text-sm font-medium text-gray-700">Modalità Calcolo</label>
                                                <select
                                                    className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                                    {...registerVersion('rol_calc_mode_id')}
                                                >
                                                    <option value="">Seleziona...</option>
                                                    {calculationModes.map((mode: any) => (
                                                        <option key={mode.id} value={mode.id}>{mode.name}</option>
                                                    ))}
                                                </select>
                                            </div>

                                            <div className="space-y-2">
                                                <label className="block text-sm font-medium text-gray-700">Ore ROL Annuali</label>
                                                <div className="relative rounded-md shadow-sm">
                                                    <input
                                                        type="number"
                                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm pl-3 pr-12"
                                                        {...registerVersion('annual_rol_hours', { required: true, min: 0 })}
                                                    />
                                                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-gray-400 text-sm">
                                                        ore
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="space-y-2">
                                                <label className="block text-sm font-medium text-gray-700">Ore Ex-Festività Annuali</label>
                                                <div className="relative rounded-md shadow-sm">
                                                    <input
                                                        type="number"
                                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm pl-3 pr-12"
                                                        {...registerVersion('annual_ex_festivita_hours')}
                                                    />
                                                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-gray-400 text-sm">
                                                        ore
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="space-y-2">
                                                <label className="block text-sm font-medium text-gray-700">Scadenza ROL (mesi)</label>
                                                <div className="relative rounded-md shadow-sm">
                                                    <input
                                                        type="number"
                                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm pl-3 pr-12"
                                                        {...registerVersion('rol_carryover_months')}
                                                    />
                                                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-gray-400 text-sm">
                                                        mesi
                                                    </div>
                                                </div>
                                                <p className="text-xs text-gray-500">Solitamente 12 o 24 mesi</p>
                                            </div>
                                        </div>

                                        {/* Orario Lavoro Base */}
                                        <div className="md:col-span-2 mt-4 pt-4 border-t border-gray-100">
                                            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">Base Oraria Full Time</h3>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                                <div className="space-y-4">
                                                    <div className="space-y-2">
                                                        <label className="block text-sm font-medium text-gray-700">Ore Settimanali</label>
                                                        <input
                                                            type="number"
                                                            step="0.1"
                                                            className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                                            {...registerVersion('weekly_hours_full_time')}
                                                        />
                                                    </div>
                                                    <div className="space-y-2">
                                                        <label className="block text-sm font-medium text-gray-700">Giorni Lavorativi / Settimana</label>
                                                        <select
                                                            className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                                            {...registerVersion('working_days_per_week')}
                                                        >
                                                            <option value="5">5 giorni (Lun-Ven)</option>
                                                            <option value="6">6 giorni (Lun-Sab)</option>
                                                        </select>
                                                    </div>
                                                </div>

                                                <div className="space-y-4">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <label className="block text-sm font-medium text-gray-700">Regola Sabato</label>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <label className="relative inline-flex items-center cursor-pointer">
                                                            <input
                                                                type="checkbox"
                                                                className="sr-only peer"
                                                                {...registerVersion('count_saturday_as_leave')}
                                                            />
                                                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                                                        </label>
                                                        <span className="text-sm text-gray-600">Conteggia Sabato come Ferie</span>
                                                    </div>
                                                    <p className="text-xs text-gray-500">
                                                        Se attivo, il sabato viene conteggiato come giorno di ferie anche se la settimana lavorativa è di 5 giorni (lun-ven).
                                                    </p>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Note */}
                                        <div className="md:col-span-2 mt-4 pt-4 border-t border-gray-100">
                                            <div className="space-y-2">
                                                <label className="block text-sm font-medium text-gray-700">Note Interne</label>
                                                <textarea
                                                    className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                                    rows={3}
                                                    {...registerVersion('notes')}
                                                    placeholder="Note sulle specificità di questo rinnovo..."
                                                />
                                            </div>
                                        </div>

                                    </div>
                                    <div className="bg-gray-50 px-6 py-4 flex items-center justify-end gap-3 border-t border-gray-200">
                                        <button
                                            type="submit"
                                            disabled={isSaving}
                                            className="btn btn-primary flex items-center gap-2"
                                        >
                                            {isSaving ? <span className="spinner spinner-white spinner-sm" /> : <Save size={18} />}
                                            Salva Modifiche
                                        </button>
                                    </div>
                                </div>
                            </form>


                        </>) : (
                            <div className="bg-gray-50 border border-dashed border-gray-300 rounded-xl p-12 text-center text-gray-500">
                                Seleziona una versione dal menu a sinistra per visualizzarne i parametri.
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Content Levels */}
            {activeTab === 'levels' && (
                <div className="grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-8 animate-fadeIn">

                    {/* Levels List */}
                    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col">
                        <div className="p-4 bg-gray-50 border-b border-gray-200">
                            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                                <BarChart3 size={18} />
                                Lista Livelli
                            </h3>
                        </div>
                        <div className="flex-1 overflow-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Livello</th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrizione</th>
                                        <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Ordine</th>
                                        <th scope="col" className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {levels.map(level => (
                                        <tr key={level.id} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{level.level_name}</td>
                                            <td className="px-6 py-4 text-sm text-gray-500">{level.description}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">{level.sort_order}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                <button onClick={() => { setCurrentLevel(level); setIsEditingLevel(true); }} className="text-indigo-600 hover:text-indigo-900 mr-4">
                                                    <Edit2 size={16} />
                                                </button>
                                                <button onClick={() => onRequestDeleteLevel(level.id)} className="text-red-600 hover:text-red-900">
                                                    <Trash2 size={16} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {levels.length === 0 && (
                                        <tr>
                                            <td colSpan={4} className="px-6 py-8 text-center text-gray-500 text-sm">
                                                Nessun livello configurato.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Add/Edit Level Form */}
                    <div className="space-y-6">
                        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden p-5">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-semibold text-gray-900">
                                    {isEditingLevel ? 'Modifica Livello' : 'Nuovo Livello'}
                                </h3>
                                {isEditingLevel && (
                                    <button onClick={() => { setIsEditingLevel(false); setCurrentLevel(null); }} className="text-xs text-gray-500 hover:text-gray-700">Annulla</button>
                                )}
                            </div>

                            <form onSubmit={handleSubmitLevel(onSubmitLevel)} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Nome Livello</label>
                                    <input
                                        type="text"
                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                        placeholder="es. 1° Livello, Livello A"
                                        {...registerLevel('level_name', { required: true })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                                    <textarea
                                        rows={3}
                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                        placeholder="Descrizione opzionale..."
                                        {...registerLevel('description')}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Ordine Visualizzazione</label>
                                    <input
                                        type="number"
                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                        {...registerLevel('sort_order', { required: true })}
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="w-full btn btn-primary flex justify-center items-center gap-2 mt-2"
                                >
                                    {isEditingLevel ? 'Salva Modifiche' : <><Plus size={16} /> Aggiungi Livello</>}
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            )}

            {/* Content Type Configs */}
            {activeTab === 'type_configs' && (
                <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-8 animate-fadeIn">

                    {/* Sidebar - Version Selector (Reused) */}
                    <div className="space-y-6">
                        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                            <div className="p-4 bg-gray-50 border-b border-gray-200">
                                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                                    <History size={18} />
                                    Seleziona Versione
                                </h3>
                            </div>
                            <div className="divide-y divide-gray-100 max-h-[400px] overflow-y-auto">
                                {versions.map(version => (
                                    <button
                                        key={version.id}
                                        onClick={() => setSelectedVersion(version)}
                                        className={`w-full text-left p-4 hover:bg-gray-50 transition-colors flex items-center justify-between group ${selectedVersion?.id === version.id ? 'bg-indigo-50/50 border-l-4 border-indigo-500' : 'border-l-4 border-transparent'}`}
                                    >
                                        <div>
                                            <p className={`font-medium ${selectedVersion?.id === version.id ? 'text-indigo-700' : 'text-gray-900'}`}>{version.version_name}</p>
                                            <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                                                <Calendar size={12} />
                                                Dal {new Date(version.valid_from).toLocaleDateString()}
                                            </p>
                                        </div>
                                        {selectedVersion?.id === version.id && <CheckCircle size={16} className="text-indigo-500" />}
                                    </button>
                                ))}
                                {versions.length === 0 && (
                                    <div className="p-4 text-center text-gray-500 text-sm">Nessuna versione configurata.</div>
                                )}
                            </div>
                        </div>
                        <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
                            <p className="text-xs text-amber-800">
                                <strong>Nota:</strong> Qui puoi definire eccezioni per specifici tipi di contratto (es. Part Time, Apprendistato) rispetto ai parametri generali della versione selezionata.
                            </p>
                        </div>
                    </div>

                    {/* Main Content */}
                    <div>
                        {selectedVersion ? (
                            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden animate-fadeIn">
                                <div className="p-5 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                                    <div>
                                        <div className="flex items-center gap-3 text-gray-800">
                                            <Layers size={20} className="text-gray-500" />
                                            <h3 className="text-sm font-bold uppercase tracking-wider">Specifiche per Tipo Contratto</h3>
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">Versione: {selectedVersion.version_name}</p>
                                    </div>
                                    <button
                                        onClick={() => setEditingConfig({})}
                                        type="button"
                                        className="btn btn-sm btn-outline gap-2 bg-white hover:bg-gray-50"
                                    >
                                        <Plus size={16} /> Aggiungi Specifica
                                    </button>
                                </div>

                                {/* List */}
                                <div className="divide-y divide-gray-100">
                                    {selectedVersion.contract_type_configs && selectedVersion.contract_type_configs.length > 0 ? (
                                        selectedVersion.contract_type_configs.map((config: any) => (
                                            <div key={config.id} className="p-4 hover:bg-gray-50 flex justify-between items-center group transition-colors">
                                                <div>
                                                    <div className="font-medium text-gray-900 flex items-center gap-2">
                                                        {config.contract_type?.name || 'Tipo sconosciuto'}
                                                        <span className="text-xs text-gray-400 font-normal">({config.contract_type?.code})</span>
                                                    </div>
                                                    <div className="text-xs text-gray-500 mt-1 flex gap-3">
                                                        <span className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded border border-blue-100">{config.weekly_hours}h / sett</span>
                                                        <span className="bg-orange-50 text-orange-700 px-1.5 py-0.5 rounded border border-orange-100">{config.annual_vacation_days} gg ferie</span>
                                                        <span className="bg-green-50 text-green-700 px-1.5 py-0.5 rounded border border-green-100">{config.annual_rol_hours}h ROL</span>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <button onClick={() => setEditingConfig(config)} className="p-1.5 hover:bg-white hover:shadow-sm rounded-lg text-indigo-600 border border-transparent hover:border-gray-200 transition-all" title="Modifica">
                                                        <Edit2 size={16} />
                                                    </button>
                                                    <button onClick={() => onRequestDeleteConfig(config.id)} className="p-1.5 hover:bg-white hover:shadow-sm rounded-lg text-red-600 border border-transparent hover:border-gray-200 transition-all" title="Elimina">
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="p-12 text-center">
                                            <div className="bg-gray-50 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                                                <Layers size={24} className="text-gray-400" />
                                            </div>
                                            <p className="text-gray-900 font-medium text-sm mb-1">Nessuna specifica configurata</p>
                                            <p className="text-xs text-gray-500 max-w-xs mx-auto">Tutti i dipendenti useranno i parametri generali definiti nella tab "Parametri & Versioni".</p>
                                        </div>
                                    )}
                                </div>


                            </div>
                        ) : (
                            <div className="bg-gray-50 border border-dashed border-gray-300 rounded-xl p-12 text-center text-gray-500">
                                Seleziona una versione dal menu a sinistra per gestirne le specifiche.
                            </div>
                        )}
                    </div>
                </div>
            )}
            {/* Content Calc Modes */}
            {activeTab === 'calc_modes' && (
                <div className="grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-8 animate-fadeIn">
                    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col">
                        <div className="p-4 bg-gray-50 border-b border-gray-200">
                            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                                <Calculator size={18} />
                                Modalità di Calcolo
                            </h3>
                        </div>
                        <div className="flex-1 overflow-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Codice</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Funzione</th>
                                        <th className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {calculationModes.map((mode: any) => (
                                        <tr key={mode.id} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{mode.name}</td>
                                            <td className="px-6 py-4 text-sm text-gray-500">{mode.code}</td>
                                            <td className="px-6 py-4 text-sm text-gray-500 font-mono text-xs">{mode.function_name}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                <button onClick={() => { setCurrentMode(mode); setIsEditingMode(true); }} className="text-indigo-600 hover:text-indigo-900 mr-4">
                                                    <Edit2 size={16} />
                                                </button>
                                                <button onClick={() => onRequestDeleteMode(mode.id)} className="text-red-600 hover:text-red-900">
                                                    <Trash2 size={16} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Edit Form */}
                    <div className="space-y-6">
                        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden p-5">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-semibold text-gray-900">
                                    {isEditingMode ? 'Modifica Modalità' : 'Nuova Modalità'}
                                </h3>
                                {isEditingMode && (
                                    <button onClick={() => { setIsEditingMode(false); setCurrentMode(null); }} className="text-xs text-gray-500 hover:text-gray-700">Annulla</button>
                                )}
                            </div>

                            <form onSubmit={handleSubmitMode(onSubmitMode)} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
                                    <input type="text" {...registerMode('name', { required: true })} className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 sm:text-sm" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Codice</label>
                                    <input type="text" {...registerMode('code', { required: true })} className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 sm:text-sm" placeholder="es. MONTHLY_STD" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Funzione Backend</label>
                                    <input
                                        type="text"
                                        list="backend-functions"
                                        {...registerMode('function_name', { required: true })}
                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 sm:text-sm"
                                        placeholder="es. calculate_accrual_monthly_std"
                                    />
                                    <datalist id="backend-functions">
                                        <option value="calculate_accrual_monthly_std" />
                                        <option value="calculate_accrual_daily_365" />
                                        <option value="calculate_accrual_hourly_worked" />
                                    </datalist>
                                    <div className="text-xs text-gray-500 mt-2 bg-gray-50 p-2 rounded border border-gray-100">
                                        <p className="font-medium mb-1">Funzioni Supportate:</p>
                                        <ul className="space-y-1">
                                            <li className="flex flex-col"><code className="text-indigo-600 font-bold">calculate_accrual_monthly_std</code> <span className="text-gray-400">Mensile 1/12</span></li>
                                            <li className="flex flex-col"><code className="text-indigo-600 font-bold">calculate_accrual_daily_365</code> <span className="text-gray-400">Giornaliero 1/365</span></li>
                                            <li className="flex flex-col"><code className="text-indigo-600 font-bold">calculate_accrual_hourly_worked</code> <span className="text-gray-400">Su ore lavorate</span></li>
                                        </ul>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                                    <textarea {...registerMode('description')} rows={3} className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 sm:text-sm" />
                                </div>
                                <button type="submit" className="w-full btn btn-primary flex justify-center items-center gap-2 mt-2">
                                    {isEditingMode ? 'Salva Modifiche' : <><Plus size={16} /> Aggiungi Modalità</>}
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            )}
            {/* Modal for Contract Type Config */}
            {editingConfig && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-scaleIn">
                        <div className="p-5 border-b border-gray-100 flex justify-between items-center">
                            <h3 className="font-bold text-lg text-gray-900">
                                {editingConfig.id ? 'Modifica Specifica' : 'Nuova Specifica'}
                            </h3>
                            <button onClick={() => setEditingConfig(null)} className="text-gray-400 hover:text-gray-600 transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={handleSubmitConfig(onSaveConfig)}>
                            <div className="p-6 space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Contratto</label>
                                    <select
                                        {...registerConfig('contract_type_id', { required: true })}
                                        className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                        disabled={!!editingConfig.id}
                                    >
                                        <option value="">Seleziona...</option>
                                        {contractTypes.map(t => (
                                            <option key={t.id} value={t.id}>{t.name} ({t.code})</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Ore Settimanali</label>
                                        <input type="number" step="0.1" {...registerConfig('weekly_hours', { required: true })} className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Giorni Ferie</label>
                                        <input type="number" {...registerConfig('annual_vacation_days', { required: true })} className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Ore ROL</label>
                                        <input type="number" {...registerConfig('annual_rol_hours', { required: true })} className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Ore Ex-Fest.</label>
                                        <input type="number" {...registerConfig('annual_ex_festivita_hours', { required: true })} className="block w-full rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                                    </div>
                                </div>
                            </div>

                            <div className="p-5 border-t border-gray-100 flex justify-end gap-3 bg-gray-50">
                                <button type="button" onClick={() => setEditingConfig(null)} className="btn btn-ghost hover:bg-gray-200" disabled={isSavingConfig}>Annulla</button>
                                <button type="submit" className="btn btn-primary px-6 text-white" disabled={isSavingConfig} style={{ minWidth: '120px' }}>
                                    {isSavingConfig ? <span className="spinner spinner-white spinner-sm" /> : 'Salva Specifica'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modals */}
            <ConfirmModal
                isOpen={!!deleteLevelId}
                onClose={() => setDeleteLevelId(null)}
                onConfirm={confirmDeleteLevel}
                title="Elimina Livello"
                message="Sei sicuro di voler eliminare questo livello contrattuale? L'azione è irreversibile."
                variant="danger"
                confirmLabel="Elimina"
            />

            <ConfirmModal
                isOpen={!!deleteModeId}
                onClose={() => setDeleteModeId(null)}
                onConfirm={confirmDeleteMode}
                title="Elimina Modalità"
                message="Sei sicuro di voler eliminare questa modalità di calcolo? Potrebbe essere in uso da altri contratti."
                variant="danger"
                confirmLabel="Elimina"
            />

            <ConfirmModal
                isOpen={!!deleteConfigId}
                onClose={() => setDeleteConfigId(null)}
                onConfirm={confirmDeleteConfig}
                title="Elimina Configurazione"
                message="Sei sicuro di voler eliminare questa specifica configurazione per il tipo di contratto?"
                variant="danger"
                confirmLabel="Elimina"
            />
        </div>
    );
}

export default NationalContractDetailPage;
