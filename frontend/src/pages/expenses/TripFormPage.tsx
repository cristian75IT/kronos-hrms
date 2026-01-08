/**
 * KRONOS - New Business Trip Form
 */
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Calendar as CalendarIcon, Save, X, AlertCircle, MapPin, DollarSign, Globe } from 'lucide-react';
import { useCreateTrip, useUploadTripAttachment } from '../../hooks/domain/useExpenses';
import { useState } from 'react';
import { useToast } from '../../context/ToastContext';
import type { DestinationType } from '../../types';
import { formatApiError } from '../../utils/errorUtils';
import { FileUpload } from '../../components/common/FileUpload';

interface TripFormValues {
    title: string;
    destination: string;
    destination_type: DestinationType;
    purpose: string;
    start_date: string;
    end_date: string;
    estimated_budget?: number;
}

export function TripFormPage() {
    const navigate = useNavigate();
    const createMutation = useCreateTrip();
    const uploadMutation = useUploadTripAttachment();
    const [attachments, setAttachments] = useState<File[]>([]);
    const { success, error: showError } = useToast();


    const { register, handleSubmit, watch, formState: { errors } } = useForm<TripFormValues>({
        defaultValues: {
            destination_type: 'national',
            start_date: new Date().toISOString().split('T')[0],
            end_date: new Date().toISOString().split('T')[0],
        }
    });

    const startDate = watch('start_date');

    const uploadAttachments = async (tripId: string) => {
        for (const file of attachments) {
            try {
                await new Promise<void>((resolve, reject) => {
                    uploadMutation.mutate(
                        { id: tripId, file },
                        {
                            onSuccess: () => resolve(),
                            onError: () => reject(),
                        }
                    );
                });
            } catch {
                showError(`Errore durante il caricamento di "${file.name}"`);
            }
        }
    };

    const onSubmit = (data: TripFormValues) => {
        createMutation.mutate(data, {
            onSuccess: async (newTrip) => {
                success('Trasferta creata con successo!');
                if (attachments.length > 0) {
                    await uploadAttachments(newTrip.id);
                    success(`${attachments.length} allegat${attachments.length === 1 ? 'o' : 'i'} caricat${attachments.length === 1 ? 'o' : 'i'}`);
                }
                navigate('/trips');
            },
        });
    };


    return (
        <div className="max-w-2xl mx-auto animate-fadeIn pb-8">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900 mb-1 mt-2">Nuova Trasferta</h1>
                <p className="text-gray-500">Richiedi l'autorizzazione per una nuova missione.</p>
            </div>

            <div className="card bg-white p-8 rounded-xl border border-slate-200 shadow-sm">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                    {/* Title */}
                    <div className="space-y-1.5">
                        <label className="block text-sm font-semibold text-slate-700">Titolo Trasferta</label>
                        <input
                            type="text"
                            {...register('title', { required: 'Il titolo è obbligatorio' })}
                            className="input w-full border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                            placeholder="Es. Visita Cliente Milano, Fiera Parigi..."
                        />
                        {errors.title && <span className="text-red-500 text-xs">{errors.title.message}</span>}
                    </div>

                    {/* Destination */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-1.5">
                            <label className="block text-sm font-semibold text-slate-700">Destinazione</label>
                            <div className="relative">
                                <MapPin size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                                <input
                                    type="text"
                                    {...register('destination', { required: 'La destinazione è obbligatoria' })}
                                    className="input w-full pl-10 border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                                    placeholder="Es. Milano, Parigi..."
                                />
                            </div>
                            {errors.destination && <span className="text-red-500 text-xs">{errors.destination.message}</span>}
                        </div>

                        <div className="space-y-1.5">
                            <label className="block text-sm font-semibold text-slate-700">Tipo Destinazione</label>
                            <div className="relative">
                                <Globe size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                                <select
                                    {...register('destination_type')}
                                    className="input w-full pl-10 appearance-none bg-none border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                                >
                                    <option value="national">Italia</option>
                                    <option value="eu">Europa (UE)</option>
                                    <option value="extra_eu">Extra UE</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Dates */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-1.5">
                            <label className="block text-sm font-semibold text-slate-700">Data Inizio</label>
                            <div className="relative">
                                <CalendarIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                                <input
                                    type="date"
                                    {...register('start_date', { required: 'Data inizio obbligatoria' })}
                                    className="input w-full pl-10 border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                                />
                            </div>
                            {errors.start_date && <span className="text-red-500 text-xs">{errors.start_date.message}</span>}
                        </div>

                        <div className="space-y-1.5">
                            <label className="block text-sm font-semibold text-slate-700">Data Fine</label>
                            <div className="relative">
                                <CalendarIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                                <input
                                    type="date"
                                    {...register('end_date', {
                                        required: 'Data fine obbligatoria',
                                        validate: value =>
                                            !startDate || new Date(value) >= new Date(startDate) || 'La data fine deve essere successiva alla data inizio'
                                    })}
                                    className="input w-full pl-10 border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                                />
                            </div>
                            {errors.end_date && <span className="text-red-500 text-xs">{errors.end_date.message}</span>}
                        </div>
                    </div>

                    {/* Budget */}
                    <div className="space-y-1.5">
                        <label className="block text-sm font-semibold text-slate-700">Budget Stimato (€)</label>
                        <div className="relative max-w-xs">
                            <DollarSign size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                            <input
                                type="number"
                                step="0.01"
                                min="0"
                                {...register('estimated_budget', { valueAsNumber: true })}
                                className="input w-full pl-10 border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                                placeholder="0.00"
                            />
                        </div>
                    </div>

                    {/* Purpose */}
                    <div className="space-y-1.5">
                        <label className="block text-sm font-semibold text-slate-700">Scopo / Motivo</label>
                        <textarea
                            {...register('purpose', { required: 'Il motivo è obbligatorio' })}
                            className="input w-full min-h-[100px] resize-y p-3 border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                            placeholder="Descrivi il motivo della trasferta..."
                        />
                        {errors.purpose && <span className="text-red-500 text-xs">{errors.purpose.message}</span>}
                    </div>

                    {/* Attachments */}
                    <FileUpload
                        label="Allegati"
                        files={attachments}
                        onFilesChange={setAttachments}
                        accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                        multiple={true}
                        maxSizeMB={5}
                        maxFiles={5}
                        helperText="Piano di viaggio, prenotazioni, inviti o altri documenti (max 5 file, 5MB per file)"
                    />


                    {/* Error Message */}
                    {createMutation.isError && (
                        <div className="p-4 bg-red-50 border border-red-100 rounded-lg flex items-start gap-3 text-red-600">
                            <AlertCircle size={20} className="mt-0.5 flex-shrink-0" />
                            <div>
                                <div className="font-semibold text-sm">Errore durante l'invio</div>
                                <div className="text-sm opacity-90">
                                    {formatApiError(createMutation.error)}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center justify-end gap-3 pt-6 border-t border-slate-100">
                        <button
                            type="button"
                            onClick={() => navigate('/trips')}
                            className="btn btn-ghost text-slate-600 hover:bg-slate-100"
                        >
                            <X size={18} className="mr-2" />
                            Annulla
                        </button>
                        <button
                            type="submit"
                            disabled={createMutation.isPending}
                            className="btn btn-primary bg-slate-900 hover:bg-slate-800 text-white border-none"
                        >
                            {createMutation.isPending ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                    Invio...
                                </>
                            ) : (
                                <>
                                    <Save size={18} className="mr-2" />
                                    Salva Bozza
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default TripFormPage;
