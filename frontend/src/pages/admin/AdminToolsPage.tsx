/**
 * KRONOS - Admin Tools Page
 * System maintenance and notification settings
 */
import { useState, useEffect } from 'react';
import {
    Zap,
    Bell,
    RefreshCcw,
    Database,
    Save,
    Loader,
    Shield,
    Users,
    ArrowRight,
    X,
    Check,
    Mail
} from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { leavesService } from '../../services/leaves.service';
import { Button } from '../../components/common';
import { configService } from '../../services/config.service';
import { EmailSettingsPanel } from '../../components/admin/EmailSettingsPanel';
import { EmailTemplatesPanel } from '../../components/admin/EmailTemplatesPanel';
import { Link } from 'react-router-dom';
import { GitBranch } from 'lucide-react';

interface NotificationSetting {
    key: string;
    value: boolean;
    label: string;
    description: string;
    category: 'email' | 'app' | 'business';
}

interface EmployeePreview {
    user_id: string;
    name: string;
    current_vacation: number;
    new_vacation: number;
    current_rol: number;
    new_rol: number;
    selected: boolean;
}

export function AdminToolsPage() {
    const toast = useToast();
    const [activeTab, setActiveTab] = useState<'maintenance' | 'notifications' | 'email' | 'approvals'>('notifications');
    const [isProcessing, setIsProcessing] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [previewMode, setPreviewMode] = useState<'recalc' | 'rollover' | null>(null);
    const [previewData, setPreviewData] = useState<EmployeePreview[]>([]);
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);
    const [previewYear] = useState<number>(new Date().getFullYear());

    const [settings, setSettings] = useState<NotificationSetting[]>([
        { key: 'notify_leave_request', value: true, label: 'Nuove Richieste Ferie', description: 'Invia email ai responsabili quando un dipendente richiede ferie.', category: 'email' },
        { key: 'notify_leave_approval', value: true, label: 'Esito Richieste', description: 'Notifica il dipendente quando la sua richiesta viene approvata o rifiutata.', category: 'email' },
        { key: 'notify_wallet_expiry', value: false, label: 'Scadenza Wallet', description: 'Avvisa i dipendenti un mese prima della scadenza delle ferie AP.', category: 'email' },
        { key: 'push_approvals', value: true, label: 'Notifiche App Approvatori', description: 'Notifiche push per gli approvatori in attesa.', category: 'app' },
        { key: 'leaves.block_insufficient_balance', value: true, label: 'Blocco Saldo Insufficiente', description: 'Impedisce l\'invio di richieste se il saldo disponibile non è sufficiente. Se disabilitato, mostra solo un avviso.', category: 'business' },
        { key: 'smart_deduction_enabled', value: false, label: 'Smart Deduction', description: 'Se abilitato, il sistema prioritizza lo scarico dei residui che scadono prima (es. ROL in scadenza).', category: 'business' },
        // Approval settings
        { key: 'approval.auto_escalate', value: true, label: 'Escalation Automatica', description: 'Scala automaticamente le approvazioni scadute al livello superiore.', category: 'business' },
        { key: 'approval.reminder_enabled', value: true, label: 'Promemoria Approvazioni', description: 'Invia promemoria agli approvatori prima della scadenza.', category: 'email' },
        { key: 'approval.allow_self_approval', value: false, label: 'Auto-Approvazione', description: 'Permette agli utenti di approvare le proprie richieste (sconsigliato).', category: 'business' },
    ]);

    useEffect(() => {
        const loadConfigs = async () => {
            try {
                const configs = await configService.getAllConfigs();
                if (configs && configs.length > 0) {
                    setSettings(prev => prev.map(s => {
                        const dbConfig = configs.find(c => c.key === s.key);
                        return dbConfig ? { ...s, value: dbConfig.value } : s;
                    }));
                }
            } catch (e) {
                console.log('Error loading system configs, using defaults');
            }
        };
        loadConfigs();
    }, []);

    const handleToggleSetting = (key: string) => {
        setSettings(prev => prev.map(s => s.key === key ? { ...s, value: !s.value } : s));
    };

    const handleSaveSettings = async () => {
        setIsSaving(true);
        try {
            // Save each setting to backend
            await Promise.all(settings.map(async (setting) => {
                try {
                    await configService.updateConfig(setting.key, setting.value);
                } catch (e: any) {
                    // If config doesn't exist (404), create it
                    if (e.response && e.response.status === 404) {
                        await configService.createConfig({
                            key: setting.key,
                            value: setting.value,
                            value_type: 'boolean',
                            category: setting.category,
                            description: setting.description
                        });
                    } else {
                        throw e;
                    }
                }
            }));

            toast.success('Impostazioni salvate con successo');

            // Clear backend cache to ensure immediate effect
            try {
                await configService.clearCache();
            } catch (err) {
                console.warn('Failed to clear system cache after save');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            toast.error('Errore nel salvataggio');
        } finally {
            setIsSaving(false);
        }
    };

    const runMaintenance = async (task: string, action: () => Promise<any>) => {
        setIsProcessing(task);
        try {
            await action();
            toast.success('Operazione completata con successo');
        } catch {
            toast.error('Errore durante l\'esecuzione');
        } finally {
            setIsProcessing(null);
        }
    };

    const loadPreview = async (type: 'recalc' | 'rollover') => {
        setIsLoadingPreview(true);
        setPreviewMode(type);
        try {
            const year = type === 'rollover' ? previewYear - 1 : previewYear;

            if (type === 'recalc') {
                const response = await leavesService.previewRecalculate(year);
                setPreviewData(response.employees.map(e => ({ ...e, selected: true })));
            } else {
                const response = await leavesService.previewRollover(year);
                setPreviewData(response.employees.map(e => ({ ...e, selected: true })));
            }
        } catch (error) {
            toast.error('Errore nel caricamento dell\'anteprima');
            setPreviewMode(null);
        } finally {
            setIsLoadingPreview(false);
        }
    };

    const toggleEmployeeSelection = (id: string) => {
        setPreviewData(prev => prev.map(e => e.user_id === id ? { ...e, selected: !e.selected } : e));
    };

    const toggleAllSelection = (selected: boolean) => {
        setPreviewData(prev => prev.map(e => ({ ...e, selected })));
    };

    const applySelectedChanges = async () => {
        const selectedIds = previewData.filter(e => e.selected).map(e => e.user_id);
        if (selectedIds.length === 0) {
            toast.error('Seleziona almeno un dipendente');
            return;
        }
        setIsProcessing(previewMode);
        try {
            if (previewMode === 'recalc') {
                await leavesService.applyRecalculateSelected(selectedIds, previewYear);
            } else {
                await leavesService.applyRolloverSelected(selectedIds, previewYear - 1);
            }
            toast.success(`Modifiche applicate a ${selectedIds.length} dipendenti`);
            setPreviewMode(null);
            setPreviewData([]);
        } catch {
            toast.error('Errore nell\'applicazione delle modifiche');
        } finally {
            setIsProcessing(null);
        }
    };

    const selectedCount = previewData.filter(e => e.selected).length;

    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1">
                        <Shield className="text-indigo-600" size={24} />
                        Strumenti Admin
                    </h1>
                    <p className="text-sm text-gray-500">Gestisci le notifiche di sistema e la manutenzione dei dati</p>
                </div>
                <div className="flex bg-gray-100 p-1 rounded-lg">
                    <button
                        onClick={() => setActiveTab('notifications')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'notifications' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <Bell size={16} /> Notifiche
                    </button>
                    <button
                        onClick={() => setActiveTab('maintenance')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'maintenance' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <RefreshCcw size={16} /> Manutenzione
                    </button>
                    <button
                        onClick={() => setActiveTab('email')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'email' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <Mail size={16} /> Email
                    </button>
                    <button
                        onClick={() => setActiveTab('approvals')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'approvals' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <GitBranch size={16} /> Approvazioni
                    </button>
                </div>
            </div>

            {activeTab === 'notifications' && (
                <div className="space-y-6">
                    {/* Email Notifications */}
                    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center justify-between">
                            <div>
                                <h3 className="font-semibold text-gray-900">Notifiche Email</h3>
                                <p className="text-xs text-gray-500 mt-0.5">Configura le comunicazioni automatiche via email</p>
                            </div>
                        </div>
                        <div className="divide-y divide-gray-100">
                            {settings.filter(s => s.category === 'email').map(setting => (
                                <div key={setting.key} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                                    <div className="flex-1 min-w-0 mr-4">
                                        <p className="font-medium text-gray-900">{setting.label}</p>
                                        <p className="text-sm text-gray-500">{setting.description}</p>
                                    </div>
                                    <button
                                        onClick={() => handleToggleSetting(setting.key)}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0 ${setting.value ? 'bg-indigo-600' : 'bg-gray-200'}`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm ${setting.value ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* App Notifications */}
                    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50">
                            <h3 className="font-semibold text-gray-900">Notifiche App</h3>
                            <p className="text-xs text-gray-500 mt-0.5">Impostazioni per le notifiche in-app e push</p>
                        </div>
                        <div className="divide-y divide-gray-100">
                            {settings.filter(s => s.category === 'app').map(setting => (
                                <div key={setting.key} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                                    <div className="flex-1 min-w-0 mr-4">
                                        <p className="font-medium text-gray-900">{setting.label}</p>
                                        <p className="text-sm text-gray-500">{setting.description}</p>
                                    </div>
                                    <button
                                        onClick={() => handleToggleSetting(setting.key)}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0 ${setting.value ? 'bg-indigo-600' : 'bg-gray-200'}`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm ${setting.value ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Business Rules */}
                    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center justify-between">
                            <div>
                                <h3 className="font-semibold text-gray-900">Logica di Business</h3>
                                <p className="text-xs text-gray-500 mt-0.5">Parametri globali per il calcolo delle assenze</p>
                            </div>
                        </div>
                        <div className="divide-y divide-gray-100">
                            {settings.filter(s => s.category === 'business').map(setting => (
                                <div key={setting.key} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                                    <div className="flex-1 min-w-0 mr-4">
                                        <p className="font-medium text-gray-900">{setting.label}</p>
                                        <p className="text-sm text-gray-500">{setting.description}</p>
                                    </div>
                                    <button
                                        onClick={() => handleToggleSetting(setting.key)}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0 ${setting.value ? 'bg-indigo-600' : 'bg-gray-200'}`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm ${setting.value ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Save Button */}
                    <div className="flex justify-end">
                        <Button
                            onClick={handleSaveSettings}
                            disabled={isSaving}
                            variant="primary"
                            icon={isSaving ? <Loader size={18} className="animate-spin" /> : <Save size={18} />}
                        >
                            {isSaving ? 'Salvataggio...' : 'Salva Impostazioni'}
                        </Button>
                    </div>
                </div>
            )}

            {activeTab === 'maintenance' && (
                <div className="space-y-6">
                    {/* Action Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-amber-500 text-white shadow-sm mb-4">
                                <Database size={20} />
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">Pulisci Cache Sistema</h3>
                            <p className="text-sm text-gray-500 mb-4">Svuota le tabelle temporanee e rinfresca le viste materializzate del database.</p>
                            <Button
                                onClick={() => runMaintenance('cache', async () => { /* cache logic */ })}
                                disabled={!!isProcessing || !!previewMode}
                                variant="secondary"
                                icon={isProcessing === 'cache' ? <Loader size={16} className="animate-spin" /> : <RefreshCcw size={16} />}
                                className="w-full justify-center"
                            >
                                Esegui Pulizia
                            </Button>
                        </div>

                        <div className={`bg-white border rounded-xl p-6 shadow-sm transition-all ${previewMode === 'recalc' ? 'border-indigo-300 ring-2 ring-indigo-100' : 'border-gray-200 hover:shadow-md'}`}>
                            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-indigo-500 text-white shadow-sm mb-4">
                                <Zap size={20} />
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">Ricalcola Saldi Globali</h3>
                            <p className="text-sm text-gray-500 mb-4">Ricalcola tutti i wallet dipendenti partendo dalle transazioni storiche.</p>
                            <Button
                                onClick={() => loadPreview('recalc')}
                                disabled={!!isProcessing || !!previewMode}
                                variant="primary"
                                icon={isLoadingPreview && previewMode === 'recalc' ? <Loader size={16} className="animate-spin" /> : <Users size={16} />}
                                className="w-full justify-center"
                            >
                                Anteprima Modifiche
                            </Button>
                        </div>

                        <div className={`bg-white border rounded-xl p-6 shadow-sm transition-all ${previewMode === 'rollover' ? 'border-purple-300 ring-2 ring-purple-100' : 'border-gray-200 hover:shadow-md'}`}>
                            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-purple-500 text-white shadow-sm mb-4">
                                <RefreshCcw size={20} />
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">Rollover ROL Annuale</h3>
                            <p className="text-sm text-gray-500 mb-4">Trasferisce le ore ROL residue nel pacchetto AP per tutti i dipendenti.</p>
                            <Button
                                onClick={() => loadPreview('rollover')}
                                disabled={!!isProcessing || !!previewMode}
                                variant="secondary"
                                icon={isLoadingPreview && previewMode === 'rollover' ? <Loader size={16} className="animate-spin" /> : <Users size={16} />}
                                className="w-full justify-center"
                            >
                                Anteprima Modifiche
                            </Button>
                        </div>
                    </div>

                    {/* Preview Report Section */}
                    {previewMode && (
                        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm animate-fadeIn">
                            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-lg ${previewMode === 'recalc' ? 'bg-indigo-100 text-indigo-600' : 'bg-purple-100 text-purple-600'}`}>
                                        {previewMode === 'recalc' ? <Zap size={18} /> : <RefreshCcw size={18} />}
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-gray-900">
                                            {previewMode === 'recalc' ? `Anteprima Ricalcolo Saldi ${previewYear}` : `Anteprima Rollover ${previewYear - 1} → ${previewYear}`}
                                        </h3>
                                        <p className="text-xs text-gray-500">Seleziona i dipendenti a cui applicare le modifiche</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => { setPreviewMode(null); setPreviewData([]); }}
                                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all"
                                >
                                    <X size={18} />
                                </button>
                            </div>

                            {isLoadingPreview ? (
                                <div className="flex items-center justify-center p-12 gap-3">
                                    <Loader className="animate-spin text-indigo-600" size={24} />
                                    <span className="text-sm text-gray-500">Caricamento anteprima dal server...</span>
                                </div>
                            ) : previewData.length === 0 ? (
                                <div className="flex flex-col items-center justify-center p-12 text-center">
                                    <Users className="text-gray-300 mb-4" size={48} />
                                    <p className="text-lg font-medium text-gray-600">Nessun dipendente trovato</p>
                                    <p className="text-sm text-gray-400">Non ci sono dati da elaborare per l'anno selezionato</p>
                                </div>
                            ) : (
                                <>
                                    <div className="overflow-x-auto">
                                        <table className="w-full">
                                            <thead>
                                                <tr className="bg-gray-50 border-b border-gray-200">
                                                    <th className="px-6 py-3 text-left">
                                                        <input
                                                            type="checkbox"
                                                            checked={previewData.every(e => e.selected)}
                                                            onChange={(e) => toggleAllSelection(e.target.checked)}
                                                            className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                                        />
                                                    </th>
                                                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Dipendente</th>
                                                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Ferie Attuali</th>
                                                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider"></th>
                                                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Ferie Nuove</th>
                                                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">ROL Attuali</th>
                                                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider"></th>
                                                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">ROL Nuovi</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-100">
                                                {previewData.map(employee => {
                                                    const vacationDiff = employee.new_vacation - employee.current_vacation;
                                                    const rolDiff = employee.new_rol - employee.current_rol;
                                                    return (
                                                        <tr key={employee.user_id} className={`transition-colors ${employee.selected ? 'bg-indigo-50/30' : 'hover:bg-gray-50'}`}>
                                                            <td className="px-6 py-4">
                                                                <input
                                                                    type="checkbox"
                                                                    checked={employee.selected}
                                                                    onChange={() => toggleEmployeeSelection(employee.user_id)}
                                                                    className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                                                />
                                                            </td>
                                                            <td className="px-6 py-4">
                                                                <span className="font-medium text-gray-900">{employee.name}</span>
                                                            </td>
                                                            <td className="px-6 py-4 text-center">
                                                                <span className="text-gray-600">{employee.current_vacation.toFixed(2)} gg</span>
                                                            </td>
                                                            <td className="px-6 py-4 text-center">
                                                                <ArrowRight size={14} className="text-gray-300 mx-auto" />
                                                            </td>
                                                            <td className="px-6 py-4 text-center">
                                                                <span className="font-semibold text-gray-900">{employee.new_vacation.toFixed(2)} gg</span>
                                                                {vacationDiff !== 0 && (
                                                                    <span className={`ml-2 text-xs font-medium ${vacationDiff > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                                                        {vacationDiff > 0 ? '+' : ''}{vacationDiff.toFixed(2)}
                                                                    </span>
                                                                )}
                                                            </td>
                                                            <td className="px-6 py-4 text-center">
                                                                <span className="text-gray-600">{employee.current_rol.toFixed(2)} h</span>
                                                            </td>
                                                            <td className="px-6 py-4 text-center">
                                                                <ArrowRight size={14} className="text-gray-300 mx-auto" />
                                                            </td>
                                                            <td className="px-6 py-4 text-center">
                                                                <span className="font-semibold text-gray-900">{employee.new_rol.toFixed(2)} h</span>
                                                                {rolDiff !== 0 && (
                                                                    <span className={`ml-2 text-xs font-medium ${rolDiff > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                                                        {rolDiff > 0 ? '+' : ''}{rolDiff.toFixed(2)}
                                                                    </span>
                                                                )}
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>

                                    {/* Action Bar */}
                                    <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
                                        <span className="text-sm text-gray-600">
                                            <strong>{selectedCount}</strong> di {previewData.length} dipendenti selezionati
                                        </span>
                                        <div className="flex gap-3">
                                            <Button
                                                variant="secondary"
                                                onClick={() => { setPreviewMode(null); setPreviewData([]); }}
                                            >
                                                Annulla
                                            </Button>
                                            <Button
                                                variant="primary"
                                                onClick={applySelectedChanges}
                                                disabled={selectedCount === 0 || !!isProcessing}
                                                icon={isProcessing ? <Loader size={16} className="animate-spin" /> : <Check size={16} />}
                                            >
                                                {isProcessing ? 'Applicazione...' : `Applica a ${selectedCount} Dipendenti`}
                                            </Button>
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                </div>
            )}

            {activeTab === 'email' && (
                <div className="space-y-6">
                    <EmailSettingsPanel />
                    <EmailTemplatesPanel />
                </div>
            )}

            {activeTab === 'approvals' && (
                <div className="space-y-6">
                    {/* Workflow Configuration Link */}
                    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50">
                            <h3 className="font-semibold text-gray-900">Configurazione Workflow</h3>
                            <p className="text-xs text-gray-500 mt-0.5">Gestisci i flussi di approvazione per ferie, trasferte e note spese</p>
                        </div>
                        <div className="p-6">
                            <Link
                                to="/admin/workflows"
                                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                            >
                                <GitBranch size={18} />
                                Gestisci Workflow
                            </Link>
                        </div>
                    </div>

                    {/* Approval Settings */}
                    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center justify-between">
                            <div>
                                <h3 className="font-semibold text-gray-900">Impostazioni Approvazioni</h3>
                                <p className="text-xs text-gray-500 mt-0.5">Configura il comportamento del sistema di approvazione</p>
                            </div>
                        </div>
                        <div className="divide-y divide-gray-100">
                            {settings.filter(s => s.key.startsWith('approval.')).map(setting => (
                                <div key={setting.key} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                                    <div className="flex-1 min-w-0 mr-4">
                                        <p className="font-medium text-gray-900">{setting.label}</p>
                                        <p className="text-sm text-gray-500">{setting.description}</p>
                                    </div>
                                    <button
                                        onClick={() => handleToggleSetting(setting.key)}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0 ${setting.value ? 'bg-indigo-600' : 'bg-gray-200'}`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm ${setting.value ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Save Button */}
                    <div className="flex justify-end">
                        <Button
                            onClick={handleSaveSettings}
                            disabled={isSaving}
                            className="flex items-center gap-2"
                        >
                            {isSaving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />}
                            {isSaving ? 'Salvataggio...' : 'Salva Impostazioni'}
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdminToolsPage;
