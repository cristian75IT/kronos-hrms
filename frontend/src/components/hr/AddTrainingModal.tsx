import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Modal, Button } from '../common';
import { userService } from '../../services/userService';
import { hrReportingService } from '../../services/hrReporting.service';
import { useToast } from '../../context/ToastContext';
import {
    User,
    Calendar,
    BookOpen,
    Award,
    AlertCircle,
    CheckCircle2,
    Building2,
    Hash,
    GraduationCap,
    Clock,
    FileText
} from 'lucide-react';

interface AddTrainingModalProps {
    isOpen: boolean;
    onClose: () => void;
    onValuesSaved: () => void;
}

interface TrainingFormData {
    employee_id: string;
    training_type: string;
    training_name: string;
    description?: string;
    provider_name?: string;
    provider_code?: string;
    training_date: string;
    expiry_date?: string;
    hours?: number;
    certificate_number?: string;
    notes?: string;
}

export function AddTrainingModal({ isOpen, onClose, onValuesSaved }: AddTrainingModalProps) {
    const { register, handleSubmit, reset, formState: { errors } } = useForm<TrainingFormData>();
    const [employees, setEmployees] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const toast = useToast();

    useEffect(() => {
        if (isOpen) {
            loadEmployees();
            reset();
        }
    }, [isOpen, reset]);

    const loadEmployees = async () => {
        try {
            const users = await userService.getUsers();
            setEmployees(users);
        } catch (error) {
            console.error("Failed to load employees", error);
            toast.error("Errore caricamento dipendenti");
        }
    };

    const onSubmit = async (data: TrainingFormData) => {
        setLoading(true);
        try {
            const payload = {
                user_id: data.employee_id,
                title: data.training_name,
                description: data.description,
                provider: data.provider_name,
                hours: data.hours ? Number(data.hours) : undefined,
                start_date: data.training_date,
                expiry_date: data.expiry_date || undefined,
                status: 'completed' as const,
            };

            await hrReportingService.createTrainingRecord(payload);
            toast.success('Registrazione creata con successo');
            onValuesSaved();
            onClose();
        } catch (error) {
            console.error(error);
            toast.error('Errore durante il salvataggio');
        } finally {
            setLoading(false);
        }
    };

    const InputLabel = ({ label, required, error, icon: Icon }: any) => (
        <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
            {Icon && <Icon size={16} className="text-slate-400" />}
            <span>
                {label} {required && <span className="text-indigo-600 ml-0.5">*</span>}
            </span>
            {error && <span className="text-red-500 text-xs font-normal ml-auto">{error.message}</span>}
        </label>
    );

    const inputClasses = (error: any) => `
        block w-full rounded-lg border-slate-200 bg-white shadow-sm
        focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 focus:outline-none
        transition-all duration-200 sm:text-sm py-2.5 px-3
        placeholder:text-slate-400
        ${error ? 'border-red-300 bg-red-50/10 focus:border-red-500 focus:ring-red-200' : 'hover:border-slate-300'}
    `;

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Nuova Registrazione Formazione" size="3xl">
            <div className="space-y-8 pb-4">

                {/* Enterprise Header */}
                <div className="relative overflow-hidden rounded-2xl border border-white/40 bg-white/60 p-6 shadow-sm backdrop-blur-md">
                    <div className="flex items-start gap-5">
                        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-100/80 text-indigo-700 shadow-inner">
                            <GraduationCap size={28} strokeWidth={1.5} />
                        </div>
                        <div className="space-y-1">
                            <h3 className="text-lg font-bold text-slate-900 tracking-tight">Registra Nuovo Corso</h3>
                            <p className="text-sm text-slate-500 leading-relaxed max-w-lg">
                                Inserisci i dettagli del corso di formazione completato dal dipendente.
                                Assicurati di caricare i dati corretti per la conformità normativa.
                            </p>
                        </div>
                    </div>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">

                    {/* Main Content Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                        {/* Left Column: Core Info */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                                <User className="text-indigo-500" size={18} />
                                <h4 className="font-semibold text-slate-800">Destinatario e Tipo</h4>
                            </div>

                            <div className="space-y-5">
                                <div className="space-y-1">
                                    <InputLabel label="Dipendente" required error={errors.employee_id} />
                                    <select
                                        {...register('employee_id', { required: 'Seleziona un dipendente' })}
                                        className={inputClasses(errors.employee_id)}
                                    >
                                        <option value="">Seleziona dipendente...</option>
                                        {employees.map(emp => (
                                            <option key={emp.id} value={emp.id}>
                                                {emp.first_name} {emp.last_name} ({emp.email})
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="space-y-1">
                                    <InputLabel label="Tipologia Corso" required error={errors.training_type} />
                                    <select
                                        {...register('training_type', { required: 'Tipo richiesto' })}
                                        className={inputClasses(errors.training_type)}
                                    >
                                        <option value="">Seleziona tipologia...</option>
                                        <option value="formazione_generale">Formazione Generale</option>
                                        <option value="formazione_specifica">Formazione Specifica</option>
                                        <option value="preposto">Preposto</option>
                                        <option value="antincendio">Antincendio</option>
                                        <option value="primo_soccorso">Primo Soccorso</option>
                                        <option value="rls">RLS</option>
                                        <option value="altro">Altro</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Right Column: Course Details */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                                <BookOpen className="text-indigo-500" size={18} />
                                <h4 className="font-semibold text-slate-800">Dettagli Corso</h4>
                            </div>

                            <div className="space-y-5">
                                <div className="space-y-1">
                                    <InputLabel label="Titolo Corso" required error={errors.training_name} />
                                    <input
                                        type="text"
                                        placeholder="Es. Sicurezza Lavoratori - Modulo A"
                                        {...register('training_name', { required: 'Nome corso richiesto' })}
                                        className={inputClasses(errors.training_name)}
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1">
                                        <InputLabel label="Data Corso" required error={errors.training_date} icon={Calendar} />
                                        <input
                                            type="date"
                                            {...register('training_date', { required: 'Richiesta' })}
                                            className={inputClasses(errors.training_date)}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <InputLabel label="Durata (Ore)" icon={Clock} />
                                        <input
                                            type="number"
                                            placeholder="0"
                                            {...register('hours')}
                                            className={inputClasses(errors.hours)}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Full Width: Certification Section */}
                    <div className="bg-slate-50 rounded-xl p-6 border border-slate-100 space-y-6">
                        <div className="flex items-center gap-2 pb-2 border-b border-slate-200/60">
                            <Award className="text-amber-500" size={18} />
                            <h4 className="font-semibold text-slate-800">Certificazione & Scadenze</h4>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-1">
                                <InputLabel label="Ente Formatore" icon={Building2} />
                                <input
                                    type="text"
                                    placeholder="Es. SicurForm Srl"
                                    {...register('provider_name')}
                                    className={inputClasses(null)}
                                />
                            </div>

                            <div className="space-y-1">
                                <InputLabel label="Numero Attestato" icon={Hash} />
                                <input
                                    type="text"
                                    placeholder="Codice identificativo"
                                    {...register('certificate_number')}
                                    className={inputClasses(null)}
                                />
                            </div>

                            <div className="space-y-1">
                                <InputLabel label="Scadenza" icon={AlertCircle} />
                                <input
                                    type="date"
                                    {...register('expiry_date')}
                                    className={inputClasses(null)}
                                />
                                <p className="text-xs text-slate-500 mt-1.5 ml-1">Lasciare vuoto se ha validità illimitata</p>
                            </div>

                            <div className="space-y-1">
                                <InputLabel label="Tutor / Note" icon={FileText} />
                                <textarea
                                    rows={1}
                                    placeholder="Note aggiuntive..."
                                    {...register('notes')}
                                    className={inputClasses(null)}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-6 border-t border-slate-100">
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                            <AlertCircle size={14} />
                            <span>I campi con <span className="text-indigo-600 font-bold">*</span> sono obbligatori</span>
                        </div>

                        <div className="flex w-full sm:w-auto gap-3">
                            <Button variant="outline" type="button" onClick={onClose} disabled={loading} className="flex-1 sm:flex-none justify-center">
                                Annulla
                            </Button>
                            <Button
                                variant="primary"
                                type="submit"
                                disabled={loading}
                                className="flex-1 sm:flex-none justify-center min-w-[140px] shadow-lg shadow-indigo-500/20"
                            >
                                {loading ? (
                                    <><span className="loading loading-spinner loading-xs mr-2"></span> Salvataggio...</>
                                ) : (
                                    <><CheckCircle2 size={18} className="mr-2" /> Registra</>
                                )}
                            </Button>
                        </div>
                    </div>
                </form>
            </div>
        </Modal>
    );
}
