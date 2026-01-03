import React, { useEffect, useState } from 'react';
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
    Hash
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
                ...data,
                hours: data.hours ? Number(data.hours) : undefined,
                expiry_date: data.expiry_date || null
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

    const SectionHeader = ({ icon: Icon, title }: { icon: any, title: string }) => (
        <div className="flex items-center gap-3 mb-6 pb-2 border-b border-gray-100">
            <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                <Icon size={20} strokeWidth={2} />
            </div>
            <h3 className="font-bold text-gray-900 text-lg">{title}</h3>
        </div>
    );

    const InputLabel = ({ label, required, error }: any) => (
        <label className="block text-sm font-semibold text-gray-700 mb-1.5 flex justify-between">
            <span>
                {label} {required && <span className="text-indigo-600 ml-0.5">*</span>}
            </span>
            {error && <span className="text-red-500 text-xs font-normal">{error.message}</span>}
        </label>
    );

    const inputClasses = (error: any) => `
        block w-full rounded-xl border-gray-200 bg-gray-50/30 
        focus:border-indigo-500 focus:ring-indigo-500 focus:bg-white 
        transition-all duration-200 sm:text-sm py-2.5
        ${error ? 'border-red-300 bg-red-50/50 focus:border-red-500 focus:ring-red-500' : 'hover:border-gray-300'}
    `;

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Nuova Registrazione Formazione" size="2xl">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">

                {/* Section 1: Employee & Type */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="md:col-span-2">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-8 h-1 rounded-full bg-indigo-500"></div>
                            <h4 className="font-semibold text-gray-900 uppercase text-xs tracking-wider">Informazioni Base</h4>
                        </div>
                    </div>

                    <div className="space-y-1">
                        <InputLabel label="Dipendente" required error={errors.employee_id} />
                        <div className="relative">
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
                            <User className="absolute right-3 top-3 text-gray-400 pointer-events-none" size={18} />
                        </div>
                    </div>

                    <div className="space-y-1">
                        <InputLabel label="Tipologia Corso" required error={errors.training_type} />
                        <div className="relative">
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

                {/* Section 2: Course Details */}
                <div className="bg-gray-50/50 -mx-6 px-6 py-6 border-y border-gray-100">
                    <SectionHeader icon={BookOpen} title="Dettagli Corso" />

                    <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                        <div className="md:col-span-8 space-y-1">
                            <InputLabel label="Nome del Corso" required error={errors.training_name} />
                            <input
                                type="text"
                                placeholder="Es. Sicurezza Generale Lavoratori - Rischio Basso"
                                {...register('training_name', { required: 'Nome corso richiesto' })}
                                className={inputClasses(errors.training_name)}
                            />
                        </div>

                        <div className="md:col-span-2 space-y-1">
                            <InputLabel label="Ore" />
                            <div className="relative">
                                <input
                                    type="number"
                                    placeholder="0"
                                    {...register('hours')}
                                    className={inputClasses(errors.hours)}
                                />
                                <span className="absolute right-3 top-2.5 text-gray-400 text-xs font-bold">H</span>
                            </div>
                        </div>

                        <div className="md:col-span-2 space-y-1">
                            <InputLabel label="Data" required error={errors.training_date} />
                            <input
                                type="date"
                                {...register('training_date', { required: 'Richiesta' })}
                                className={inputClasses(errors.training_date)}
                            />
                        </div>
                    </div>
                </div>

                {/* Section 3: Certification */}
                <div>
                    <SectionHeader icon={Award} title="Certificazione e Scadenze" />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-1">
                            <InputLabel label="Ente Formatore" />
                            <div className="relative">
                                <input
                                    type="text"
                                    placeholder="Es. SicurForm Srl"
                                    {...register('provider_name')}
                                    className={`${inputClasses(null)} pl-10`}
                                />
                                <Building2 className="absolute left-3 top-3 text-gray-400" size={18} />
                            </div>
                        </div>

                        <div className="space-y-1">
                            <InputLabel label="Numero Attestato" />
                            <div className="relative">
                                <input
                                    type="text"
                                    placeholder="Codice identificativo"
                                    {...register('certificate_number')}
                                    className={`${inputClasses(null)} pl-10`}
                                />
                                <Hash className="absolute left-3 top-3 text-gray-400" size={18} />
                            </div>
                        </div>

                        <div className="space-y-1">
                            <InputLabel label="Data Scadenza" />
                            <div className="relative">
                                <input
                                    type="date"
                                    {...register('expiry_date')}
                                    className={inputClasses(null)}
                                />
                                <Calendar className="absolute right-3 top-2.5 text-gray-400 pointer-events-none" size={18} />
                            </div>
                            <p className="text-xs text-gray-500 mt-1">Lasciare vuoto se non scade</p>
                        </div>

                        <div className="space-y-1">
                            <InputLabel label="Note Aggiuntive" />
                            <textarea
                                {...register('notes')}
                                rows={1}
                                className={inputClasses(null)}
                                placeholder="Note opzionali..."
                            />
                        </div>
                    </div>
                </div>

                <div className="flex justify-between items-center pt-6 border-t border-gray-100">
                    <p className="text-xs text-gray-400 flex items-center gap-1">
                        <AlertCircle size={12} />
                        I campi contrassegnati con <span className="text-indigo-600 font-bold">*</span> sono obbligatori
                    </p>
                    <div className="flex gap-3">
                        <Button variant="outline" type="button" onClick={onClose} disabled={loading} className="px-6">
                            Annulla
                        </Button>
                        <Button variant="primary" type="submit" disabled={loading} className="px-6 min-w-[160px] shadow-lg shadow-indigo-200">
                            {loading ? (
                                <><span className="loading loading-spinner loading-xs mr-2"></span> Salvataggio...</>
                            ) : (
                                <><CheckCircle2 size={18} className="mr-2" /> Registra Corso</>
                            )}
                        </Button>
                    </div>
                </div>
            </form>
        </Modal>
    );
}
