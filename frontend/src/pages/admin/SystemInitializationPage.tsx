import { useState } from 'react';
import {
    Upload,
    CheckCircle2,
    AlertCircle,
    Info,
    FileJson,
    ArrowRight,
    Building2,
    Users,
    Briefcase,
    Calendar,
    GitBranch,
    ShieldCheck,
    Database,
    Shield
} from 'lucide-react';
import { setupService } from '../../services/setup.service';
import { useToast } from '../../context/ToastContext';
import { Button } from '../../components/common';

interface ImportStep {
    id: string;
    title: string;
    description: string;
    icon: React.ElementType;
    importFn: (data: any) => Promise<any>;
    order: number;
}

export function SystemInitializationPage() {
    const toast = useToast();
    const [isLoading, setIsLoading] = useState<Record<string, boolean>>({});
    const [results, setResults] = useState<Record<string, any>>({});
    const [files, setFiles] = useState<Record<string, File | null>>({});

    const steps: ImportStep[] = [
        {
            id: 'contracts',
            title: 'Contratti Nazionali (CCNL)',
            description: 'Carica le definizioni dei contratti collettivi, livelli e regole base.',
            icon: Briefcase,
            importFn: setupService.importContracts,
            order: 1
        },
        {
            id: 'exec_levels',
            title: 'Livelli Direttivi',
            description: 'Configura la gerarchia aziendale e i tetti di spesa per le approvazioni.',
            icon: ShieldCheck,
            importFn: setupService.importExecutiveLevels,
            order: 2
        },
        {
            id: 'organization',
            title: 'Struttura Organizzativa',
            description: 'Importa Dipartimenti e Servizi con i relativi responsabili.',
            icon: Building2,
            importFn: setupService.importOrganization,
            order: 3
        },
        {
            id: 'users',
            title: 'Utenti e Profili',
            description: 'Importa i dipendenti e associali alla struttura organizzativa.',
            icon: Users,
            importFn: setupService.importUsers,
            order: 4
        },
        {
            id: 'holidays',
            title: 'Calendari e Festività',
            description: 'Configura i profili delle festività nazionali e regionali.',
            icon: Calendar,
            importFn: setupService.importHolidays,
            order: 5
        },
        {
            id: 'workflows',
            title: 'Flussi Approvativi',
            description: 'Configura le regole di approvazione per ferie, trasferte e spese.',
            icon: GitBranch,
            importFn: setupService.importWorkflows,
            order: 6
        },
        {
            id: 'leave_types',
            title: 'Tipi Assenza',
            description: 'Configura i tipi di ferie/permessi con limiti e regole di business.',
            icon: Calendar,
            importFn: setupService.importLeaveTypes,
            order: 7
        }
    ];

    const handleFileChange = (id: string, file: File | null) => {
        setFiles(prev => ({ ...prev, [id]: file }));
    };

    const handleImport = async (step: ImportStep) => {
        const file = files[step.id];
        if (!file) {
            toast.error('Seleziona un file JSON prima di procedere');
            return;
        }

        setIsLoading(prev => ({ ...prev, [step.id]: true }));
        try {
            const text = await file.text();
            const data = JSON.parse(text);
            const res = await step.importFn(data);
            setResults(prev => ({ ...prev, [step.id]: res }));
            toast.success(`Importazione ${step.title} completata`);
        } catch (error: any) {
            console.error(error);
            toast.error(`Errore durante l'importazione: ${error.message || 'Controlla il formato del file'}`);
        } finally {
            setIsLoading(prev => ({ ...prev, [step.id]: false }));
        }
    };

    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1">
                        <Database className="text-indigo-600" size={24} />
                        Inizializzazione Sistema
                    </h1>
                    <p className="text-sm text-gray-500">Configura rapidamente l'ecosistema KRONOS caricando i file JSON</p>
                </div>
            </div>

            {/* Instructions Alert (Sober) */}
            <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-6 flex gap-4">
                <div className="p-2 bg-blue-100 rounded-lg text-blue-600 h-fit">
                    <Info size={20} />
                </div>
                <div>
                    <h3 className="font-semibold text-blue-900 mb-1">Guida all'Importazione</h3>
                    <p className="text-blue-800 text-sm leading-relaxed opacity-90">
                        L'importazione è idempotente: caricare lo stesso file aggiornerà i record esistenti senza creare duplicati.
                        Per garantire la corretta associazione (es. Manager, Dipartimenti), segui l'ordine numerico indicato.
                    </p>
                    <div className="mt-3 flex items-center gap-6 text-[13px] font-medium text-blue-900/70">
                        <div className="flex items-center gap-1.5">
                            <CheckCircle2 size={14} className="text-emerald-500" />
                            <span>Controlla il formato JSON</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <CheckCircle2 size={14} className="text-emerald-500" />
                            <span>Rispetta la sequenza consigliata (1-6)</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Steps Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {steps.sort((a, b) => a.order - b.order).map((step) => (
                    <div
                        key={step.id}
                        className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden"
                    >
                        <div className="p-6">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-4">
                                    <div className="p-3 bg-gray-50 rounded-lg text-gray-400 group-hover:text-indigo-600 transition-colors">
                                        <step.icon size={24} />
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className="flex items-center justify-center w-5 h-5 bg-indigo-50 text-indigo-700 text-[10px] font-bold rounded-full">
                                                {step.order}
                                            </span>
                                            <h3 className="font-bold text-gray-900">{step.title}</h3>
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">{step.description}</p>
                                    </div>
                                </div>
                                {results[step.id] && (
                                    <div className="bg-emerald-100 p-1 rounded-full text-emerald-600" title="Completato">
                                        <CheckCircle2 size={18} />
                                    </div>
                                )}
                            </div>

                            <div className="mt-6 space-y-4">
                                <div className="relative">
                                    <input
                                        type="file"
                                        accept=".json"
                                        onChange={(e) => handleFileChange(step.id, e.target.files?.[0] || null)}
                                        className="hidden"
                                        id={`file-${step.id}`}
                                    />
                                    <label
                                        htmlFor={`file-${step.id}`}
                                        className="flex items-center justify-center gap-2 w-full py-3 px-4 border border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-indigo-400 hover:bg-indigo-50/50 transition-all text-xs font-medium text-gray-500"
                                    >
                                        {files[step.id] ? (
                                            <span className="text-indigo-600 flex items-center gap-2 font-semibold">
                                                <FileJson size={14} />
                                                {files[step.id]?.name}
                                            </span>
                                        ) : (
                                            <>
                                                <Upload size={14} />
                                                Seleziona file JSON
                                            </>
                                        )}
                                    </label>
                                </div>

                                <Button
                                    onClick={() => handleImport(step)}
                                    disabled={!files[step.id] || isLoading[step.id]}
                                    variant="primary"
                                    className="w-full justify-center py-2.5"
                                    icon={isLoading[step.id] ? null : <ArrowRight size={16} />}
                                >
                                    {isLoading[step.id] ? 'Importazione...' : 'Importa Dati'}
                                </Button>

                                {results[step.id] && (
                                    <div className="bg-gray-50 rounded-lg p-3 text-[11px] font-mono text-gray-600 border border-gray-100">
                                        <div className="font-bold text-gray-400 mb-1 flex items-center gap-1 uppercase tracking-wider text-[9px]">
                                            <AlertCircle size={10} />
                                            Log Risultati:
                                        </div>
                                        <pre className="whitespace-pre-wrap">
                                            {JSON.stringify(results[step.id], null, 2)}
                                        </pre>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Support Message */}
            <div className="flex justify-center pt-4">
                <p className="text-xs text-gray-400 flex items-center gap-2">
                    <Shield size={12} />
                    Utility di Manutenzione KRONOS • Solo per amministratori autorizzati
                </p>
            </div>
        </div>
    );
}

export default SystemInitializationPage;
