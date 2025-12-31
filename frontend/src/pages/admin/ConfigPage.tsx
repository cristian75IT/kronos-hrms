/**
 * KRONOS - Configuration Page
 */
import { useState } from 'react';
import { useConfigs, useUpdateConfig, useClearCache } from '../../hooks/useApi';
import { Settings, Save, AlertCircle, RefreshCw, Trash2 } from 'lucide-react';
import type { SystemConfig } from '../../services/config.service';

export function ConfigPage() {
    const { data: configs, isLoading, error, refetch } = useConfigs();
    const updateMutation = useUpdateConfig();
    const clearCacheMutation = useClearCache();
    const [editingKey, setEditingKey] = useState<string | null>(null);
    const [editValue, setEditValue] = useState<any>(null);

    const handleEdit = (config: SystemConfig) => {
        setEditingKey(config.key);
        setEditValue(config.value);
    };

    const handleSave = (key: string) => {
        updateMutation.mutate(
            { key, value: editValue },
            {
                onSuccess: () => {
                    setEditingKey(null);
                },
            }
        );
    };

    const handleClearCache = () => {
        if (confirm('Sei sicuro di voler svuotare la cache Redis? Può essere utile se vedi dati non aggiornati.')) {
            clearCacheMutation.mutate(undefined, {
                onSuccess: () => {
                    alert('Cache svuotata con successo');
                    refetch();
                },
                onError: () => {
                    alert('Errore durante lo svuotamento della cache');
                }
            });
        }
    };

    const renderInput = (config: SystemConfig) => {
        if (config.key !== editingKey) return <span>{String(config.value)}</span>;

        if (config.value_type === 'boolean') {
            return (
                <select
                    value={String(editValue)}
                    onChange={(e) => setEditValue(e.target.value === 'true')}
                    className="input py-1 px-2"
                >
                    <option value="true">True</option>
                    <option value="false">False</option>
                </select>
            );
        }

        return (
            <input
                type={config.value_type === 'integer' || config.value_type === 'float' ? 'number' : 'text'}
                value={editValue}
                onChange={(e) => setEditValue(config.value_type === 'integer' ? parseInt(e.target.value) : e.target.value)}
                className="input py-1 px-2 w-full max-w-[200px]"
            />
        );
    };

    if (isLoading) return <div className="spinner-lg mx-auto" />;
    if (error) return <div className="text-danger text-center">Errore nel caricamento configurazioni</div>;

    const list = configs || [];

    // Group by category if needed, or simple list
    // Let's filter useful ones or show all

    return (
        <div className="config-page animate-fadeIn">
            <div className="page-header mb-6">
                <div>
                    <h1 className="flex items-center gap-2 text-2xl font-bold">
                        <Settings /> Configurazione Sistema
                    </h1>
                    <p className="text-secondary">Modifica parametri globali e policy</p>
                </div>
                <button
                    onClick={handleClearCache}
                    className="btn btn-warning mr-2 gap-2"
                    title="Svuota Cache Redis"
                    disabled={clearCacheMutation.isPending}
                >
                    <Trash2 size={18} />
                    <span className="hidden sm:inline">Svuota Cache</span>
                </button>
                <button onClick={() => refetch()} className="btn btn-ghost" title="Aggiorna lista">
                    <RefreshCw size={18} />
                </button>
            </div>

            <div className="card overflow-hidden">
                <table className="table w-full">
                    <thead>
                        <tr>
                            <th className="text-left p-4 bg-bg-secondary">Parametro</th>
                            <th className="text-left p-4 bg-bg-secondary">Valore</th>
                            <th className="text-left p-4 bg-bg-secondary">Descrizione</th>
                            <th className="text-right p-4 bg-bg-secondary">Azioni</th>
                        </tr>
                    </thead>
                    <tbody>
                        {list.length === 0 && (
                            <tr>
                                <td colSpan={4} className="p-8 text-center text-secondary">
                                    Nessuna configurazione trovata.
                                </td>
                            </tr>
                        )}
                        {list.map((config) => (
                            <tr key={config.key} className="border-t border-border hover:bg-bg-secondary/30">
                                <td className="p-4 font-mono text-sm font-semibold">{config.key}</td>
                                <td className="p-4">
                                    {renderInput(config)}
                                </td>
                                <td className="p-4 text-sm text-secondary">
                                    {config.category && <span className="badge badge-neutral mr-2">{config.category}</span>}
                                    {config.description || '-'}
                                </td>
                                <td className="p-4 text-right">
                                    {editingKey === config.key ? (
                                        <div className="flex justify-end gap-2">
                                            <button
                                                onClick={() => handleSave(config.key)}
                                                className="btn btn-primary btn-sm"
                                                disabled={updateMutation.isPending}
                                            >
                                                <Save size={14} />
                                            </button>
                                            <button
                                                onClick={() => setEditingKey(null)}
                                                className="btn btn-ghost btn-sm"
                                            >
                                                Antigravity
                                            </button>
                                        </div>
                                    ) : (
                                        <button
                                            onClick={() => handleEdit(config)}
                                            className="btn btn-secondary btn-sm"
                                        >
                                            Modifica
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                        {/* Hardcoded row for demo if backend is empty/mocked */}
                        {!list.find(c => c.key === 'leave.working_days_per_week') && (
                            <tr className="border-t border-border bg-yellow-50/5">
                                <td className="p-4 font-mono text-sm">leave.working_days_per_week</td>
                                <td className="p-4 text-secondary italic">5 (Default)</td>
                                <td className="p-4 text-sm">
                                    <span className="badge badge-warning mr-2">Core</span>
                                    Giorni lavorativi/settimana
                                </td>
                                <td className="p-4 text-right">
                                    <button disabled className="btn btn-sm btn-ghost opacity-50">Demo</button>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            <div className="mt-4 p-4 bg-blue-50/10 border border-blue-200/20 rounded-lg flex gap-3 text-sm">
                <AlertCircle className="text-blue-400 flex-shrink-0" />
                <div>
                    <strong>Nota Compliance:</strong> Impostando <code>leave.working_days_per_week</code> a 6, il sistema includerà il Sabato come giorno lavorativo per il conteggio ferie.
                </div>
            </div>
        </div>
    );
}

export default ConfigPage;
