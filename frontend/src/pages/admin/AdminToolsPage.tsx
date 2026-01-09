/**
 * KRONOS - Admin Tools Page
 * Enterprise System Configuration Hub
 */
import { useState, useEffect } from 'react';
import {
    Bell,
    RefreshCcw,
    Database,
    Save,
    Loader,
    Shield,
    Users,
    X,
    Mail,
    FileJson,
    Settings,
    AlertTriangle,
    GitBranch,
    Briefcase,
    CheckCircle,
    XCircle,
} from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { leavesService } from '../../services/leaves.service';
import { Button } from '../../components/common';
import { configService } from '../../services/config.service';
import { configHealthService, type ConfigHealthResponse } from '../../services/configHealth.service';
import { EmailSettingsPanel } from '../../components/admin/EmailSettingsPanel';
import { EmailTemplatesPanel } from '../../components/admin/EmailTemplatesPanel';
import { Link } from 'react-router-dom';
import { BalanceImportTool } from './BalanceImportTool';

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

type TabType = 'general' | 'notifications' | 'workflow' | 'maintenance';

export function AdminToolsPage() {
    const toast = useToast();
    const [activeTab, setActiveTab] = useState<TabType>('general');
    const [isProcessing, setIsProcessing] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [previewMode, setPreviewMode] = useState<'recalc' | 'rollover' | null>(null);
    const [previewData, setPreviewData] = useState<EmployeePreview[]>([]);
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);
    const [previewYear] = useState<number>(new Date().getFullYear());
    const [configHealth, setConfigHealth] = useState<ConfigHealthResponse | null>(null);

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

        // Load config health
        const loadHealthCheck = async () => {
            try {
                const health = await configHealthService.getConfigHealth();
                setConfigHealth(health);
            } catch (e) {
                console.warn('Failed to load config health');
            }
        };
        loadHealthCheck();
    }, []);

    const handleToggleSetting = (key: string) => {
        setSettings(prev => prev.map(s => s.key === key ? { ...s, value: !s.value } : s));
    };

    const handleSaveSettings = async () => {
        setIsSaving(true);
        try {
            await Promise.all(settings.map(async (setting) => {
                try {
                    await configService.updateConfig(setting.key, setting.value);
                } catch (e: any) {
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

    const SettingRow = ({ item }: { item: NotificationSetting }) => (
        <div className="flex items-center justify-between p-4 bg-white border border-slate-200 rounded-lg shadow-sm hover:shadow-md transition-all duration-200">
            <div className="flex-1 mr-4">
                <h4 className="font-medium text-slate-900 mb-1">{item.label}</h4>
                <p className="text-sm text-slate-500 leading-relaxed">{item.description}</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer shrink-0">
                <input
                    type="checkbox"
                    checked={item.value}
                    onChange={() => handleToggleSetting(item.key)}
                    className="sr-only peer"
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
            </label>
        </div>
    );

    const selectedCount = previewData.filter(e => e.selected).length;

    const sections = {
        general: { label: 'Generali & Business', icon: Settings, color: 'text-slate-600' },
        notifications: { label: 'Notifiche & Email', icon: Bell, color: 'text-amber-600' },
        workflow: { label: 'Workflow & Compliance', icon: Shield, color: 'text-indigo-600' },
        maintenance: { label: 'Manutenzione Dati', icon: Database, color: 'text-rose-600' },
    };

    return (
        <div className="space-y-8 animate-fadeIn pb-12">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-slate-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
                        <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                            <Settings size={28} />
                        </div>
                        Configurazione Sistema
                    </h1>
                    <p className="text-sm text-slate-500 mt-2 max-w-2xl">
                        Gestisci le impostazioni globali, i flussi di lavoro, le notifiche e la manutenzione dei dati del sistema KRONOS.
                    </p>
                </div>
            </div>

            {/* Config Health Alert - Enterprise Configuration Validation */}
            {configHealth && configHealth.missing_count > 0 && (
                <div className={`p-4 rounded-xl border flex items-start gap-4 ${configHealth.overall_status === 'critical'
                        ? 'bg-red-50 border-red-200'
                        : 'bg-amber-50 border-amber-200'
                    }`}>
                    <div className={`p-2 rounded-lg ${configHealth.overall_status === 'critical'
                            ? 'bg-red-100 text-red-600'
                            : 'bg-amber-100 text-amber-600'
                        }`}>
                        <AlertTriangle size={20} />
                    </div>
                    <div className="flex-1">
                        <h3 className={`font-bold ${configHealth.overall_status === 'critical'
                                ? 'text-red-900'
                                : 'text-amber-900'
                            }`}>
                            {configHealth.overall_status === 'critical'
                                ? 'Configurazione Sistema Incompleta'
                                : 'Attenzione: Configurazioni Mancanti'}
                        </h3>
                        <p className={`text-sm mt-1 ${configHealth.overall_status === 'critical'
                                ? 'text-red-700'
                                : 'text-amber-700'
                            }`}>
                            {configHealth.missing_count} configurazion{configHealth.missing_count === 1 ? 'e' : 'i'} richiest{configHealth.missing_count === 1 ? 'a' : 'e'} non configurata:
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                            {configHealth.items.filter(i => i.status === 'missing').map(item => (
                                <span key={item.config_type} className="inline-flex items-center gap-1 px-2 py-1 bg-white rounded-lg text-xs font-medium border">
                                    <XCircle size={12} className="text-red-500" />
                                    {item.name}
                                </span>
                            ))}
                        </div>
                        <p className="text-xs mt-3 text-slate-500">
                            Vai in <Link to="/admin/workflows" className="font-medium text-indigo-600 hover:underline">Workflow Approvazioni</Link> per configurare.
                        </p>
                    </div>
                </div>
            )}

            {/* Config Health OK Badge */}
            {configHealth && configHealth.overall_status === 'ok' && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3">
                    <div className="p-1.5 bg-emerald-100 rounded-lg text-emerald-600">
                        <CheckCircle size={16} />
                    </div>
                    <span className="text-sm text-emerald-800 font-medium">Tutte le configurazioni di sistema sono attive</span>
                </div>
            )}

            {/* Main Layout Tabs */}
            <div className="flex flex-col lg:flex-row gap-8">
                {/* Sidebar Navigation */}
                <div className="w-full lg:w-64 shrink-0 space-y-2">
                    {(Object.keys(sections) as TabType[]).map((key) => {
                        const section = sections[key];
                        const isActive = activeTab === key;
                        const Icon = section.icon;
                        return (
                            <button
                                key={key}
                                onClick={() => setActiveTab(key)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 text-left ${isActive
                                    ? 'bg-white shadow-md ring-1 ring-slate-200 text-slate-900 font-medium'
                                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
                                    }`}
                            >
                                <Icon size={18} className={isActive ? section.color : 'text-slate-400'} />
                                {section.label}
                            </button>
                        );
                    })}
                </div>

                {/* Content Area */}
                <div className="flex-1 min-w-0 space-y-8">

                    {/* 1. General & Business Tab */}
                    {activeTab === 'general' && (
                        <div className="space-y-6">
                            <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
                                <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                                    <Briefcase size={20} className="text-slate-500" />
                                    Regole di Business
                                </h3>
                                <div className="grid grid-cols-1 gap-4">
                                    {settings.filter(s => s.category === 'business' && !s.key.startsWith('approval.')).map(s => (
                                        <SettingRow key={s.key} item={s} />
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 2. Notifications Tab */}
                    {activeTab === 'notifications' && (
                        <div className="space-y-8">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-4">
                                    <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">Canali Attivi</h3>
                                    {settings.filter(s => ['email', 'app'].includes(s.category) && !s.key.startsWith('approval.')).map(s => (
                                        <SettingRow key={s.key} item={s} />
                                    ))}
                                </div>
                                <div className="bg-slate-50 p-6 rounded-xl border border-slate-200">
                                    <h3 className="font-bold text-slate-800 mb-2">Configurazione SMTP</h3>
                                    <p className="text-sm text-slate-500 mb-6">Gestisci i provider di posta e le credenziali di invio.</p>
                                    <EmailSettingsPanel />
                                </div>
                            </div>

                            <div className="border-t border-slate-200 pt-8">
                                <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                                    <Mail size={20} className="text-indigo-500" />
                                    Template Email
                                </h3>
                                <EmailTemplatesPanel />
                            </div>
                        </div>
                    )}

                    {/* 3. Workflow Tab */}
                    {activeTab === 'workflow' && (
                        <div className="space-y-6">
                            <div className="bg-gradient-to-br from-indigo-50 to-white p-6 rounded-xl border border-indigo-100 shadow-sm flex items-center justify-between">
                                <div>
                                    <h3 className="font-bold text-indigo-900 text-lg">Editor Grafico Workflow</h3>
                                    <p className="text-indigo-700/80 text-sm mt-1">Configura visivamente i passaggi di approvazione per ferie e note spese.</p>
                                </div>
                                <Link to="/admin/workflows">
                                    <Button variant="primary" icon={<GitBranch size={16} />}>
                                        Apri Editor
                                    </Button>
                                </Link>
                            </div>

                            <div className="space-y-4">
                                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Policy di Approvazione</h3>
                                {settings.filter(s => s.key.startsWith('approval.')).map(s => (
                                    <SettingRow key={s.key} item={s} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 4. Maintenance Tab */}
                    {activeTab === 'maintenance' && (
                        <div className="space-y-8">
                            {/* Operational Tools */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                <div className="bg-white border boundary-slate-200 rounded-xl p-6 shadow-sm">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg"><Users size={20} /></div>
                                        <h3 className="font-bold text-slate-800">Ricalcolo Saldi</h3>
                                    </div>
                                    <p className="text-sm text-slate-500 mb-4 h-10">Rigenera i wallet di tutti i dipendenti basandosi sullo storico transazioni.</p>
                                    <Button
                                        onClick={() => loadPreview('recalc')}
                                        className="w-full justify-center"
                                        variant="outline"
                                        disabled={!!isProcessing || !!previewMode}
                                    >
                                        Anteprima Ricalcolo
                                    </Button>
                                </div>

                                <div className="bg-white border boundary-slate-200 rounded-xl p-6 shadow-sm">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="p-2 bg-purple-100 text-purple-600 rounded-lg"><RefreshCcw size={20} /></div>
                                        <h3 className="font-bold text-slate-800">Rollover Annuale</h3>
                                    </div>
                                    <p className="text-sm text-slate-500 mb-4 h-10">Trasferisci i residui ROL/Banca Ore all'anno successivo.</p>
                                    <Button
                                        onClick={() => loadPreview('rollover')}
                                        className="w-full justify-center"
                                        variant="outline"
                                        disabled={!!isProcessing || !!previewMode}
                                    >
                                        Anteprima Rollover
                                    </Button>
                                </div>

                                <div className="bg-white border boundary-slate-200 rounded-xl p-6 shadow-sm">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="p-2 bg-cyan-100 text-cyan-600 rounded-lg"><Briefcase size={20} /></div>
                                        <h3 className="font-bold text-slate-800">Importazione Dati</h3>
                                    </div>
                                    <p className="text-sm text-slate-500 mb-4">Importa saldi iniziali o storico presenze da CSV/Excel.</p>
                                    <BalanceImportTool />
                                </div>

                                <div className="bg-white border boundary-slate-200 rounded-xl p-6 shadow-sm">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg"><FileJson size={20} /></div>
                                        <h3 className="font-bold text-slate-800">Setup Guidato</h3>
                                    </div>
                                    <p className="text-sm text-slate-500 mb-4">Wizard per l'inizializzazione massiva del sistema.</p>
                                    <Link to="/admin/setup" className="block w-full">
                                        <Button className="w-full justify-center" variant="outline">Avvia Wizard</Button>
                                    </Link>
                                </div>
                            </div>

                            {/* Danger Zone */}
                            <div className="border border-red-200 bg-red-50 rounded-xl p-6">
                                <h3 className="text-red-800 font-bold mb-4 flex items-center gap-2">
                                    <AlertTriangle size={20} />
                                    Area Critica
                                </h3>
                                <div className="flex flex-col md:flex-row gap-4 justify-between items-center">
                                    <div className="text-sm text-red-700/80">
                                        <strong className="block text-red-900">Pulizia Cache e Riconciliazione</strong>
                                        Operazioni che impattano le performance o la consistenza dei dati. Eseguire solo se necessario.
                                    </div>
                                    <div className="flex gap-3">
                                        <Button
                                            variant="danger"
                                            size="sm"
                                            onClick={() => runMaintenance('cache', async () => {/* cache logic */ })}
                                            disabled={!!isProcessing}
                                        >
                                            Svuota Cache
                                        </Button>
                                        <Button
                                            variant="danger"
                                            size="sm"
                                            onClick={() => runMaintenance('reconciliation', async () => {
                                                const msg = await leavesService.runReconciliation();
                                                toast.info(msg);
                                            })}
                                            disabled={!!isProcessing}
                                        >
                                            Verifica Integrità
                                        </Button>
                                    </div>
                                </div>
                            </div>

                            {/* Preview Modal Area (Kept logic from original) */}
                            {previewMode && (
                                <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
                                        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                                            <h3 className="font-bold text-slate-900 text-lg">
                                                {previewMode === 'recalc' ? `Anteprima Ricalcolo ${previewYear}` : `Anteprima Rollover ${previewYear}`}
                                            </h3>
                                            <button onClick={() => setPreviewMode(null)} className="p-2 hover:bg-slate-100 rounded-lg"><X size={20} /></button>
                                        </div>

                                        <div className="flex-1 overflow-y-auto p-0">
                                            {isLoadingPreview ? (
                                                <div className="p-12 text-center text-slate-500">Caricamento in corso...</div>
                                            ) : (
                                                <table className="w-full text-left text-sm">
                                                    <thead className="bg-slate-50 text-slate-500 font-semibold uppercase sticky top-0">
                                                        <tr>
                                                            <th className="px-6 py-3 w-10">
                                                                <input type="checkbox" onChange={(e) => toggleAllSelection(e.target.checked)} />
                                                            </th>
                                                            <th className="px-6 py-3">Dipendente</th>
                                                            <th className="px-6 py-3 text-center">Ferie Attuali</th>
                                                            <th className="px-6 py-3 text-center">Ferie Nuove</th>
                                                            <th className="px-6 py-3 text-center">ROL Attuali</th>
                                                            <th className="px-6 py-3 text-center">ROL Nuovi</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-slate-100">
                                                        {previewData.map(e => (
                                                            <tr key={e.user_id} className="hover:bg-slate-50">
                                                                <td className="px-6 py-4">
                                                                    <input type="checkbox" checked={e.selected} onChange={() => toggleEmployeeSelection(e.user_id)} />
                                                                </td>
                                                                <td className="px-6 py-4 font-medium">{e.name}</td>
                                                                <td className="px-6 py-4 text-center text-slate-500">{e.current_vacation.toFixed(2)}</td>
                                                                <td className="px-6 py-4 text-center font-bold">{e.new_vacation.toFixed(2)}</td>
                                                                <td className="px-6 py-4 text-center text-slate-500">{e.current_rol.toFixed(2)}</td>
                                                                <td className="px-6 py-4 text-center font-bold">{e.new_rol.toFixed(2)}</td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            )}
                                        </div>

                                        <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end gap-3 rounded-b-2xl">
                                            <Button variant="secondary" onClick={() => setPreviewMode(null)}>Annulla</Button>
                                            <Button variant="primary" onClick={applySelectedChanges} disabled={selectedCount === 0 || !!isProcessing}>
                                                {isProcessing ? 'Applicazione...' : `Applica a ${selectedCount} Selezionati`}
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Global Save Button (visible for settings tabs) */}
                    {activeTab !== 'maintenance' && (
                        <div className="fixed bottom-8 right-8 z-40">
                            <Button
                                onClick={handleSaveSettings}
                                disabled={isSaving}
                                className="shadow-xl rounded-full px-6 py-3 h-auto"
                                icon={isSaving ? <Loader size={20} className="animate-spin" /> : <Save size={20} />}
                            >
                                {isSaving ? 'Salvataggio...' : 'Salva Modifiche'}
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default AdminToolsPage;
