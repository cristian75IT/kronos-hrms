/**
 * KRONOS - System Configuration Page
 * Enterprise-grade configuration management
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
    Check,
    X,
    Loader,
    Shield,
    Clock,
    Database,
    Sliders,
    Files, // Icona per contratti
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

    // Filter configs to exclude obsolete contract params from general view
    // const filteredConfigs = configs?.filter(config =>
    // !['ferie_annuali', 'rol_annui', 'permessi_annui'].includes(config.key) &&
    // !config.key.startsWith('contratto_') // Future proofing
    // );

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
                    toast.success('Configurazione aggiornata');
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
        if (confirm('Sei sicuro di voler svuotare la cache Redis?')) {
            clearCacheMutation.mutate(undefined, {
                onSuccess: () => {
                    toast.success('Cache svuotata con successo');
                    refetch();
                },
                onError: () => {
                    toast.error('Errore durante lo svuotamento della cache');
                },
            });
        }
    };

    const handleRecalculate = () => {
        if (confirm('Attenzione: Questa operazione ricalcolerà i ratei maturati (Ferie/ROL) per tutti gli utenti, basandosi sui contratti storici. I valori manuali di "maturato" saranno sovrascritti. Continuare?')) {
            recalculateMutation.mutate(undefined, {
                onSuccess: () => {
                    toast.success('Ricalcolo ratei completato');
                },
                onError: () => {
                    toast.error('Errore durante il ricalcolo');
                }
            });
        }
    };

    const renderInput = (config: SystemConfig) => {
        if (config.key !== editingKey) {
            // Display value
            if (config.value_type === 'boolean') {
                return (
                    <span className={`config-badge ${config.value ? 'badge-success' : 'badge-muted'}`}>
                        {config.value ? 'Attivo' : 'Disattivo'}
                    </span>
                );
            }
            if (config.value_type === 'json') {
                return <code className="config-code">{JSON.stringify(config.value)}</code>;
            }
            return <span className="config-value-text">{String(config.value)}</span>;
        }

        // Edit mode
        if (config.value_type === 'boolean') {
            return (
                <div className="toggle-switch">
                    <button
                        className={`toggle-option ${editValue === true ? 'active' : ''}`}
                        onClick={() => setEditValue(true)}
                    >
                        Attivo
                    </button>
                    <button
                        className={`toggle-option ${editValue === false ? 'active' : ''}`}
                        onClick={() => setEditValue(false)}
                    >
                        Disattivo
                    </button>
                </div>
            );
        }

        return (
            <input
                type={config.value_type === 'integer' || config.value_type === 'float' || config.value_type === 'decimal' ? 'number' : 'text'}
                value={editValue ?? ''}
                onChange={(e) => {
                    const val = e.target.value;
                    if (config.value_type === 'integer') {
                        setEditValue(parseInt(val) || 0);
                    } else if (config.value_type === 'float' || config.value_type === 'decimal') {
                        setEditValue(parseFloat(val) || 0);
                    } else {
                        setEditValue(val);
                    }
                }}
                className="input input-sm"
                style={{ width: '200px' }}
                autoFocus
            />
        );
    };

    const getCategoryIcon = (category: string) => {
        switch (category.toLowerCase()) {
            case 'core':
            case 'sistema':
                return <Settings size={14} />;
            case 'leave':
            case 'ferie':
                return <Clock size={14} />;
            case 'security':
            case 'sicurezza':
                return <Shield size={14} />;
            default:
                return <Sliders size={14} />;
        }
    };

    if (isLoading) {
        return (
            <div className="config-page animate-fadeIn">
                <div className="loading-state">
                    <Loader size={32} className="animate-spin" />
                    <p>Caricamento configurazioni...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="config-page animate-fadeIn">
                <div className="error-state">
                    <AlertCircle size={48} />
                    <h2>Errore di caricamento</h2>
                    <p>Impossibile caricare le configurazioni di sistema.</p>
                    <button className="btn btn-primary" onClick={() => refetch()}>
                        <RefreshCw size={18} />
                        Riprova
                    </button>
                </div>
            </div>
        );
    }

    const list = configs || [];
    const categories = ['all', ...new Set(list.map(c => c.category))];

    const filteredConfigs = list.filter(config => {
        // Exclude contract params
        if (['ferie_annuali', 'rol_annui', 'permessi_annui'].includes(config.key)) return false;

        const matchesSearch = config.key.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (config.description?.toLowerCase().includes(searchTerm.toLowerCase()));
        const matchesCategory = selectedCategory === 'all' || config.category === selectedCategory;
        return matchesSearch && matchesCategory;
    });

    return (
        <div className="config-page animate-fadeIn">
            {/* Header */}
            <header className="page-header">
                <div className="header-left">
                    <div className="header-icon">
                        <Settings size={24} />
                    </div>
                    <div>
                        <h1 className="page-title">Configurazione Sistema</h1>
                        <p className="page-subtitle">Gestisci i parametri globali e le policy aziendali</p>
                    </div>
                </div>
                <div className="header-actions">
                    <button
                        className="btn btn-secondary"
                        onClick={handleRecalculate}
                        disabled={recalculateMutation.isPending}
                    >
                        {recalculateMutation.isPending ? (
                            <Loader size={18} className="animate-spin" />
                        ) : (
                            <Calculator size={18} />
                        )}
                        Ricalcola Ratei
                    </button>
                    <button
                        onClick={handleClearCache}
                        className="btn btn-warning"
                        disabled={clearCacheMutation.isPending}
                    >
                        {clearCacheMutation.isPending ? (
                            <Loader size={18} className="animate-spin" />
                        ) : (
                            <Trash2 size={18} />
                        )}
                        Svuota Cache
                    </button>
                    <button onClick={() => refetch()} className="btn btn-ghost btn-icon">
                        <RefreshCw size={18} />
                    </button>
                </div>
            </header>

            {/* Navigation Tabs */}
            {/* Navigation Tabs - Enterprise Style */}
            <div className="flex border-b border-base-200 mb-8 gap-8">
                <button
                    className={`pb-4 px-2 text-sm font-medium transition-all relative flex items-center gap-2 ${activeTab === 'system' ? 'text-primary' : 'text-base-content/60 hover:text-base-content'}`}
                    onClick={() => setActiveTab('system')}
                >
                    <Settings size={18} />
                    <span>Impostazioni Generali</span>
                    {activeTab === 'system' && (
                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-primary rounded-t-full animate-fadeIn" />
                    )}
                </button>
                <button
                    className={`pb-4 px-2 text-sm font-medium transition-all relative flex items-center gap-2 ${activeTab === 'contracts' ? 'text-primary' : 'text-base-content/60 hover:text-base-content'}`}
                    onClick={() => setActiveTab('contracts')}
                >
                    <Files size={18} />
                    <span>Tipi di Contratto</span>
                    {activeTab === 'contracts' && (
                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-primary rounded-t-full animate-fadeIn" />
                    )}
                </button>
            </div>

            {activeTab === 'contracts' && <ContractTypesManager />}

            {activeTab === 'system' && (
                <>
                    {/* Filters */}
                    <div className="config-filters card bg-base-100 shadow-sm border border-base-200 p-4">
                        <div className="search-box">
                            <Search size={18} className="search-icon" />
                            <input
                                type="text"
                                placeholder="Cerca configurazione..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="search-input"
                            />
                        </div>
                        <div className="category-tabs">
                            {categories.map(cat => (
                                <button
                                    key={cat}
                                    className={`category-tab ${selectedCategory === cat ? 'active' : ''}`}
                                    onClick={() => setSelectedCategory(cat)}
                                >
                                    {cat === 'all' ? <Database size={14} /> : getCategoryIcon(cat)}
                                    {cat === 'all' ? 'Tutte' : cat}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Config List */}
                    <div className="config-list">
                        {filteredConfigs.length === 0 ? (
                            <div className="empty-state card bg-base-100 shadow-sm border border-base-200 p-8 rounded-xl">
                                <Search size={48} />
                                <h3>Nessuna configurazione trovata</h3>
                                <p>Prova a modificare i filtri di ricerca</p>
                            </div>
                        ) : (
                            filteredConfigs.map((config) => (
                                <div key={config.key} className={`config-item card bg-base-100 shadow-sm border border-base-200 hover:shadow-md transition-all p-4 rounded-xl ${editingKey === config.key ? 'editing' : ''}`}>
                                    <div className="config-info">
                                        <div className="config-header">
                                            <span className="config-key">{config.key}</span>
                                            <span className={`category-badge cat-${config.category.toLowerCase()}`}>
                                                {getCategoryIcon(config.category)}
                                                {config.category}
                                            </span>
                                        </div>
                                        {config.description && (
                                            <p className="config-description">{config.description}</p>
                                        )}
                                    </div>
                                    <div className="config-value">
                                        {renderInput(config)}
                                    </div>
                                    <div className="config-actions">
                                        {editingKey === config.key ? (
                                            <>
                                                <button
                                                    onClick={() => handleSave(config.key)}
                                                    className="btn btn-success btn-sm btn-icon"
                                                    disabled={updateMutation.isPending}
                                                >
                                                    {updateMutation.isPending ? (
                                                        <Loader size={16} className="animate-spin" />
                                                    ) : (
                                                        <Check size={16} />
                                                    )}
                                                </button>
                                                <button
                                                    onClick={handleCancel}
                                                    className="btn btn-ghost btn-sm btn-icon"
                                                >
                                                    <X size={16} />
                                                </button>
                                            </>
                                        ) : (
                                            <button
                                                onClick={() => handleEdit(config)}
                                                className="btn btn-secondary btn-sm"
                                            >
                                                Modifica
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Info Banner */}
                    <div className="info-banner">
                        <AlertCircle size={20} />
                        <div>
                            <strong>Nota Compliance:</strong> La modifica di <code>leave.working_days_per_week</code> a 6 includerà il Sabato come giorno lavorativo per il conteggio ferie (CCNL compliant).
                        </div>
                    </div>

                    <style>{`
                .config-page {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-6);
                }

                .page-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .header-left {
                    display: flex;
                    align-items: center;
                    gap: var(--space-4);
                }

                .header-icon {
                    width: 56px;
                    height: 56px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
                    border-radius: var(--radius-xl);
                    color: white;
                }

                .page-title {
                    font-size: var(--font-size-2xl);
                    font-weight: var(--font-weight-bold);
                    margin-bottom: var(--space-1);
                }

                .page-subtitle {
                    color: var(--color-text-muted);
                    font-size: var(--font-size-sm);
                }

                .header-actions {
                    display: flex;
                    gap: var(--space-2);
                }

                .loading-state,
                .error-state {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 400px;
                    gap: var(--space-4);
                    text-align: center;
                    color: var(--color-text-muted);
                }

                .error-state h2 {
                    color: var(--color-text-primary);
                    margin: 0;
                }

                .config-filters {
                    display: flex;
                    gap: var(--space-4);
                    padding: var(--space-4);
                    flex-wrap: wrap;
                }

                .search-box {
                    position: relative;
                    flex: 1;
                    min-width: 250px;
                }

                .search-icon {
                    position: absolute;
                    left: var(--space-3);
                    top: 50%;
                    transform: translateY(-50%);
                    color: var(--color-text-muted);
                }

                .search-input {
                    width: 100%;
                    padding: var(--space-2) var(--space-3) var(--space-2) var(--space-10);
                    border: 1px solid var(--color-border);
                    border-radius: var(--radius-lg);
                    background: var(--color-bg-secondary);
                    font-size: var(--font-size-sm);
                }

                .search-input:focus {
                    outline: none;
                    border-color: var(--color-primary);
                    box-shadow: 0 0 0 3px var(--color-primary-transparent);
                }

                .category-tabs {
                    display: flex;
                    gap: var(--space-2);
                    flex-wrap: wrap;
                }

                .category-tab {
                    display: flex;
                    align-items: center;
                    gap: var(--space-1);
                    padding: var(--space-2) var(--space-3);
                    border: 1px solid var(--color-border);
                    border-radius: var(--radius-full);
                    background: transparent;
                    font-size: var(--font-size-xs);
                    font-weight: var(--font-weight-medium);
                    color: var(--color-text-secondary);
                    cursor: pointer;
                    transition: all var(--transition-fast);
                    text-transform: capitalize;
                }

                .category-tab:hover {
                    border-color: var(--color-primary);
                    color: var(--color-primary);
                }

                .category-tab.active {
                    background: var(--color-primary);
                    border-color: var(--color-primary);
                    color: white;
                }

                .config-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-3);
                }

                .config-item {
                    display: grid;
                    grid-template-columns: 1fr auto auto;
                    gap: var(--space-4);
                    align-items: center;
                    padding: var(--space-4);
                    transition: all var(--transition-fast);
                }

                .config-item.editing {
                    border-color: var(--color-primary);
                    box-shadow: 0 0 0 3px var(--color-primary-transparent);
                }

                .config-item:hover {
                    border-color: var(--color-border-hover);
                }

                .config-info {
                    min-width: 0;
                }

                .config-header {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    margin-bottom: var(--space-1);
                    flex-wrap: wrap;
                }

                .config-key {
                    font-family: var(--font-mono);
                    font-size: var(--font-size-sm);
                    font-weight: var(--font-weight-semibold);
                    color: var(--color-text-primary);
                }

                .category-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--space-1);
                    padding: 2px var(--space-2);
                    border-radius: var(--radius-full);
                    font-size: var(--font-size-xs);
                    font-weight: var(--font-weight-medium);
                    text-transform: capitalize;
                    background: var(--color-bg-tertiary);
                    color: var(--color-text-muted);
                }

                .cat-core, .cat-sistema {
                    background: var(--color-primary-bg);
                    color: var(--color-primary);
                }

                .cat-leave, .cat-ferie {
                    background: var(--color-success-bg);
                    color: var(--color-success);
                }

                .cat-security, .cat-sicurezza {
                    background: var(--color-warning-bg);
                    color: var(--color-warning);
                }

                .config-description {
                    font-size: var(--font-size-xs);
                    color: var(--color-text-muted);
                    margin: 0;
                    line-height: 1.4;
                }

                .config-value {
                    display: flex;
                    align-items: center;
                    min-width: 150px;
                }

                .config-badge {
                    padding: var(--space-1) var(--space-3);
                    border-radius: var(--radius-full);
                    font-size: var(--font-size-xs);
                    font-weight: var(--font-weight-medium);
                }

                .badge-success {
                    background: var(--color-success-bg);
                    color: var(--color-success);
                }

                .badge-muted {
                    background: var(--color-bg-tertiary);
                    color: var(--color-text-muted);
                }

                .config-code {
                    font-family: var(--font-mono);
                    font-size: var(--font-size-xs);
                    background: var(--color-bg-tertiary);
                    padding: var(--space-1) var(--space-2);
                    border-radius: var(--radius-sm);
                    max-width: 200px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .config-value-text {
                    font-weight: var(--font-weight-medium);
                    color: var(--color-text-primary);
                }

                .toggle-switch {
                    display: flex;
                    background: var(--color-bg-tertiary);
                    border-radius: var(--radius-lg);
                    padding: 2px;
                }

                .toggle-option {
                    padding: var(--space-1) var(--space-3);
                    border: none;
                    background: transparent;
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-xs);
                    font-weight: var(--font-weight-medium);
                    color: var(--color-text-muted);
                    cursor: pointer;
                    transition: all var(--transition-fast);
                }

                .toggle-option.active {
                    background: white;
                    color: var(--color-text-primary);
                    box-shadow: var(--shadow-sm);
                }

                [data-theme='dark'] .toggle-option.active {
                    background: var(--color-bg-secondary);
                }

                .config-actions {
                    display: flex;
                    gap: var(--space-2);
                }

                .empty-state {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: var(--space-12);
                    text-align: center;
                    color: var(--color-text-muted);
                    gap: var(--space-3);
                }

                .empty-state h3 {
                    color: var(--color-text-primary);
                    margin: 0;
                }

                .info-banner {
                    display: flex;
                    align-items: flex-start;
                    gap: var(--space-3);
                    padding: var(--space-4);
                    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
                    border: 1px solid rgba(59, 130, 246, 0.2);
                    border-radius: var(--radius-lg);
                    font-size: var(--font-size-sm);
                    color: var(--color-text-secondary);
                }

                .info-banner code {
                    background: rgba(59, 130, 246, 0.15);
                    padding: 2px 6px;
                    border-radius: var(--radius-sm);
                    font-family: var(--font-mono);
                    font-size: var(--font-size-xs);
                }

                @media (max-width: 768px) {
                    .config-item {
                        grid-template-columns: 1fr;
                        gap: var(--space-3);
                    }

                    .config-value {
                        min-width: auto;
                    }

                    .config-actions {
                        justify-content: flex-end;
                    }
                }
            `}</style>
                </>
            )}
        </div>
    );
}

export default ConfigPage;
