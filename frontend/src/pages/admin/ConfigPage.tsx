/**
 * KRONOS - System Configuration Page
 * Premium Enterprise-grade configuration management
 */
import { useState } from 'react';
import { useConfigs, useUpdateConfig, useClearCache, useRecalculateAccruals } from '../../hooks/useApi';
import {
    Settings,
    AlertCircle,
    RefreshCw,
    Calculator,
    Trash2,
    Search,
    X,
    Loader,
    Shield,
    Clock,
    Database,
    Sliders,
    Files,
    ArrowRight,
} from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { ContractTypesManager } from './ContractTypesManager';
import type { SystemConfig } from '../../services/config.service';

export function ConfigPage() {
    const toast = useToast();
    const { data: configs, isLoading, error, refetch } = useConfigs();
    const updateMutation = useUpdateConfig();
    const clearCacheMutation = useClearCache();
    const recalculateMutation = useRecalculateAccruals();
    const [editingKey, setEditingKey] = useState<string | null>(null);
    const [editValue, setEditValue] = useState<any>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    const [activeTab, setActiveTab] = useState<'system' | 'contracts'>('system');

    const handleEdit = (config: SystemConfig) => {
        setEditingKey(config.key);
        setEditValue(config.value);
    };

    const handleSave = async (key: string) => {
        updateMutation.mutate(
            { key, value: editValue },
            {
                onSuccess: () => {
                    setEditingKey(null);
                    toast.success('Configurazione aggiornata con successo');
                    refetch();
                },
                onError: () => {
                    toast.error('Errore durante il salvataggio');
                },
            }
        );
    };

    const handleCancel = () => {
        setEditingKey(null);
        setEditValue(null);
    };

    const handleClearCache = () => {
        if (confirm('Sei sicuro di voler svuotare la cache Redis? Questa operazione potrebbe rallentare temporaneamente il sistema.')) {
            clearCacheMutation.mutate(undefined, {
                onSuccess: () => {
                    toast.success('Cache Redis svuotata');
                    refetch();
                },
                onError: () => {
                    toast.error('Errore durante lo svuotamento della cache');
                },
            });
        }
    };

    const handleRecalculate = () => {
        if (confirm('Attenzione: Il ricalcolo dei ratei è un operazione intensiva che sovrascriverà i saldi attuali basandosi sullo storico contrattuale. Continuare?')) {
            recalculateMutation.mutate(undefined, {
                onSuccess: () => {
                    toast.success('Ricalcolo ratei completato con successo');
                },
                onError: () => {
                    toast.error('Errore durante il ricalcolo dei ratei');
                }
            });
        }
    };

    const renderInput = (config: SystemConfig) => {
        if (config.key !== editingKey) {
            if (config.value_type === 'boolean') {
                return (
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.value
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                        {config.value ? 'Attivo' : 'Disattivo'}
                    </span>
                );
            }
            if (config.value_type === 'json') {
                return (
                    <code className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs font-mono break-all line-clamp-2">
                        {JSON.stringify(config.value)}
                    </code>
                );
            }
            return <span className="font-medium text-gray-900">{String(config.value)}</span>;
        }

        if (config.value_type === 'boolean') {
            return (
                <div className="flex bg-gray-100 p-1 rounded-lg border border-gray-200">
                    <button
                        className={`flex-1 px-3 py-1 rounded-md text-xs font-medium transition-all ${editValue === true
                                ? 'bg-white text-green-700 shadow-sm border border-gray-200'
                                : 'text-gray-500 hover:text-gray-900'
                            }`}
                        onClick={() => setEditValue(true)}
                    >
                        Attivo
                    </button>
                    <button
                        className={`flex-1 px-3 py-1 rounded-md text-xs font-medium transition-all ${editValue === false
                                ? 'bg-white text-gray-900 shadow-sm border border-gray-200'
                                : 'text-gray-500 hover:text-gray-900'
                            }`}
                        onClick={() => setEditValue(false)}
                    >
                        Disattivo
                    </button>
                </div>
            );
        }

        return (
            <input
                type={['integer', 'float', 'decimal'].includes(config.value_type) ? 'number' : 'text'}
                value={editValue ?? ''}
                onChange={(e) => {
                    const val = e.target.value;
                    if (config.value_type === 'integer') setEditValue(parseInt(val) || 0);
                    else if (['float', 'decimal'].includes(config.value_type)) setEditValue(parseFloat(val) || 0);
                    else setEditValue(val);
                }}
                className="input w-48 h-9 text-sm"
                autoFocus
            />
        );
    };

    const getCategoryIcon = (category: string) => {
        switch (category.toLowerCase()) {
            case 'core': case 'sistema': return <Settings size={16} />;
            case 'leave': case 'ferie': return <Clock size={16} />;
            case 'security': case 'sicurezza': return <Shield size={16} />;
            default: return <Sliders size={16} />;
        }
    };

    if (isLoading) return (
        <div className="flex flex-col items-center justify-center py-20">
            <Loader size={32} className="animate-spin text-primary mb-3" />
            <span className="text-sm text-gray-500 font-medium">Caricamento configurazioni...</span>
        </div>
    );

    if (error) {
        return (
            <div className="max-w-md mx-auto mt-20 p-6 bg-red-50 border border-red-100 rounded-lg text-center">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <AlertCircle size={24} className="text-red-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Impossibile caricare le configurazioni</h3>
                <p className="text-gray-600 mb-6">Si è verificato un errore durante la comunicazione con il server.</p>
                <button className="btn btn-outline border-red-200 text-red-700 hover:bg-red-50" onClick={() => refetch()}>
                    <RefreshCw size={16} className="mr-2" /> Riprova
                </button>
            </div>
        );
    }

    const list = configs || [];
    const categories = ['all', ...new Set(list.map(c => c.category))];
    const filteredConfigs = list.filter(config => {
        if (['ferie_annuali', 'rol_annui', 'permessi_annui'].includes(config.key)) return false;
        const matchesSearch = config.key.toLowerCase().includes(searchTerm.toLowerCase()) || (config.description?.toLowerCase().includes(searchTerm.toLowerCase()));
        const matchesCategory = selectedCategory === 'all' || config.category === selectedCategory;
        return matchesSearch && matchesCategory;
    });

    return (
        <div className="space-y-6 animate-fadeIn max-w-[1400px] mx-auto pb-12 px-4 sm:px-6 lg:px-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pt-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Configurazione Sistema</h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Gestione dei parametri globali e delle policy applicative.
                    </p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                    <div className="bg-gray-100 p-1 rounded-lg inline-flex">
                        <button
                            onClick={() => setActiveTab('system')}
                            className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === 'system' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            <Settings size={16} /> Impostazioni
                        </button>
                        <button
                            onClick={() => setActiveTab('contracts')}
                            className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === 'contracts' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            <Files size={16} /> Contratti
                        </button>
                    </div>

                    <div className="h-6 w-px bg-gray-300 mx-2 hidden md:block" />

                    <div className="flex gap-2">
                        <button
                            onClick={handleRecalculate}
                            disabled={recalculateMutation.isPending}
                            className="btn btn-ghost btn-sm text-gray-600 hover:bg-gray-100"
                            title="Ricalcola Ratei"
                        >
                            {recalculateMutation.isPending ? <Loader className="animate-spin" size={18} /> : <Calculator size={18} />}
                        </button>
                        <button
                            onClick={handleClearCache}
                            disabled={clearCacheMutation.isPending}
                            className="btn btn-ghost btn-sm text-gray-600 hover:bg-gray-100 hover:text-red-600"
                            title="Svuota Cache"
                        >
                            {clearCacheMutation.isPending ? <Loader className="animate-spin" size={18} /> : <Trash2 size={18} />}
                        </button>
                    </div>
                </div>
            </div>

            {activeTab === 'contracts' && (
                <div className="animate-fadeIn">
                    <ContractTypesManager />
                </div>
            )}

            {activeTab === 'system' && (
                <div className="space-y-6 animate-fadeIn">
                    {/* Toolbar */}
                    <div className="flex flex-col sm:flex-row gap-4">
                        <div className="relative flex-1 max-w-md">
                            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Cerca parametro..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="input w-full pl-10"
                            />
                        </div>

                        <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0 scrollbar-hide">
                            {categories.map(cat => (
                                <button
                                    key={cat}
                                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap border transition-colors ${selectedCategory === cat
                                            ? 'bg-primary/10 border-primary text-primary'
                                            : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                                        }`}
                                    onClick={() => setSelectedCategory(cat)}
                                >
                                    {cat === 'all' ? <Database size={14} /> : getCategoryIcon(cat)}
                                    <span className="capitalize">{cat === 'all' ? 'Tutte' : cat}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Config Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredConfigs.length === 0 ? (
                            <div className="col-span-full py-20 text-center bg-white rounded-lg border border-dashed border-gray-300">
                                <Search size={48} className="mx-auto text-gray-300 mb-4" />
                                <h3 className="text-lg font-medium text-gray-900">Nessun risultato</h3>
                                <p className="text-gray-500">Prova a modificare i filtri di ricerca.</p>
                            </div>
                        ) : (
                            filteredConfigs.map((config) => (
                                <div key={config.key}
                                    className={`bg-white rounded-xl border p-5 flex flex-col transition-all ${editingKey === config.key
                                            ? 'border-primary ring-1 ring-primary shadow-md'
                                            : 'border-gray-200 shadow-sm hover:border-gray-300'
                                        }`}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide bg-gray-100 text-gray-600">
                                            {config.category}
                                        </span>
                                        {editingKey !== config.key && (
                                            <button
                                                onClick={() => handleEdit(config)}
                                                className="text-primary text-xs font-medium hover:underline opacity-0 group-hover:opacity-100 transition-opacity"
                                            >
                                                Modifica
                                            </button>
                                        )}
                                    </div>

                                    <div className="mb-4">
                                        <h3 className="text-sm font-bold text-gray-900 break-all mb-1 font-mono">{config.key}</h3>
                                        <p className="text-xs text-gray-500 line-clamp-2 min-h-[2.5em]">
                                            {config.description || 'Nessuna descrizione disponibile.'}
                                        </p>
                                    </div>

                                    <div className="mt-auto pt-4 border-t border-gray-100">
                                        <div className="flex items-center justify-between gap-3">
                                            <div className="flex-1 min-w-0">
                                                {renderInput(config)}
                                            </div>

                                            {editingKey === config.key && (
                                                <div className="flex items-center gap-1 shrink-0">
                                                    <button
                                                        onClick={handleCancel}
                                                        className="p-1.5 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100"
                                                    >
                                                        <X size={18} />
                                                    </button>
                                                    <button
                                                        onClick={() => handleSave(config.key)}
                                                        className="p-1.5 text-white bg-primary hover:bg-primary-focus rounded shadow-sm"
                                                        disabled={updateMutation.isPending}
                                                    >
                                                        {updateMutation.isPending ? <Loader size={16} className="animate-spin" /> : <ArrowRight size={18} />}
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Alert Banner */}
                    <div className="rounded-lg bg-blue-50 border border-blue-100 p-4 flex items-start gap-4">
                        <AlertCircle className="text-blue-600 mt-0.5 shrink-0" size={20} />
                        <div className="flex-1">
                            <h4 className="text-sm font-semibold text-blue-900">Nota importante</h4>
                            <p className="text-sm text-blue-700 mt-1">
                                La modifica di <code className="bg-blue-100 px-1 py-0.5 rounded text-blue-900 font-mono text-xs">leave.working_days_per_week</code> attiva un ricalcolo automatico delle proiezioni ferie nel calendario.
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ConfigPage;
