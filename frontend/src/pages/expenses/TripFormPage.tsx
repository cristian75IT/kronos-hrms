/**
 * KRONOS - New Business Trip Form
 */
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Calendar as CalendarIcon, Save, X, AlertCircle, MapPin, DollarSign, Globe, Paperclip } from 'lucide-react';
import { useCreateTrip, useUploadTripAttachment } from '../../hooks/useApi';
import { useState } from 'react';
import { useToast } from '../../context/ToastContext';
import type { DestinationType } from '../../types';
import { formatApiError } from '../../utils/errorUtils';

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
    const [attachment, setAttachment] = useState<File | null>(null);
    const { success, error: showError } = useToast();

    const { register, handleSubmit, watch, formState: { errors } } = useForm<TripFormValues>({
        defaultValues: {
            destination_type: 'national',
            start_date: new Date().toISOString().split('T')[0],
            end_date: new Date().toISOString().split('T')[0],
        }
    });

    const startDate = watch('start_date');

    const onSubmit = (data: TripFormValues) => {
        createMutation.mutate(data, {
            onSuccess: (newTrip) => {
                success('Trasferta creata con successo!');
                if (attachment) {
                    uploadMutation.mutate({ id: newTrip.id, file: attachment }, {
                        onSuccess: () => {
                            success('Allegato caricato correttamente');
                            navigate('/trips');
                        },
                        onError: () => {
                            showError('Errore durante il caricamento dell\'allegato');
                            navigate('/trips');
                        },
                    });
                } else {
                    navigate('/trips');
                }
            },
        });
    };

    return (
        <div className="max-w-2xl mx-auto animate-fadeIn">
            <div className="mb-6">
                <h1 className="text-2xl font-bold mb-1">Nuova Trasferta</h1>
                <p className="text-secondary">Richiedi l'autorizzazione per una nuova missione.</p>
            </div>

            <div className="card">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                    {/* Title */}
                    <div className="form-group">
                        <label className="input-label block mb-2">Titolo Trasferta</label>
                        <input
                            type="text"
                            {...register('title', { required: 'Il titolo è obbligatorio' })}
                            className="input w-full"
                            placeholder="Es. Visita Cliente Milano, Fiera Parigi..."
                        />
                        {errors.title && <span className="text-danger text-xs">{errors.title.message}</span>}
                    </div>

                    {/* Destination */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="form-group">
                            <label className="input-label block mb-2">Destinazione</label>
                            <div className="relative">
                                <MapPin size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                                <input
                                    type="text"
                                    {...register('destination', { required: 'La destinazione è obbligatoria' })}
                                    className="input w-full pl-10"
                                    placeholder="Es. Milano, Parigi..."
                                />
                            </div>
                            {errors.destination && <span className="text-danger text-xs">{errors.destination.message}</span>}
                        </div>

                        <div className="form-group">
                            <label className="input-label block mb-2">Tipo Destinazione</label>
                            <div className="relative">
                                <Globe size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                                <select
                                    {...register('destination_type')}
                                    className="input w-full pl-10"
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
                        <div className="form-group">
                            <label className="input-label block mb-2">Data Inizio</label>
                            <div className="relative">
                                <CalendarIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                                <input
                                    type="date"
                                    {...register('start_date', { required: 'Data inizio obbligatoria' })}
                                    className="input w-full pl-10"
                                />
                            </div>
                            {errors.start_date && <span className="text-danger text-xs">{errors.start_date.message}</span>}
                        </div>

                        <div className="form-group">
                            <label className="input-label block mb-2">Data Fine</label>
                            <div className="relative">
                                <CalendarIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                                <input
                                    type="date"
                                    {...register('end_date', {
                                        required: 'Data fine obbligatoria',
                                        validate: value =>
                                            !startDate || new Date(value) >= new Date(startDate) || 'La data fine deve essere successiva alla data inizio'
                                    })}
                                    className="input w-full pl-10"
                                />
                            </div>
                            {errors.end_date && <span className="text-danger text-xs">{errors.end_date.message}</span>}
                        </div>
                    </div>

                    {/* Budget */}
                    <div className="form-group">
                        <label className="input-label block mb-2">Budget Stimato (€)</label>
                        <div className="relative max-w-xs">
                            <DollarSign size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                            <input
                                type="number"
                                step="0.01"
                                min="0"
                                {...register('estimated_budget', { valueAsNumber: true })}
                                className="input w-full pl-10"
                                placeholder="0.00"
                            />
                        </div>
                    </div>

                    {/* Purpose */}
                    <div className="form-group">
                        <label className="input-label block mb-2">Scopo / Motivo</label>
                        <textarea
                            {...register('purpose', { required: 'Il motivo è obbligatorio' })}
                            className="input w-full min-h-[100px] resize-y"
                            placeholder="Descrivi il motivo della trasferta..."
                        />
                        {errors.purpose && <span className="text-danger text-xs">{errors.purpose.message}</span>}
                    </div>

                    {/* Attachment */}
                    <div className="form-group">
                        <label className="input-label block mb-2">Allegato (PDF max 2MB)</label>
                        <div className="relative">
                            <Paperclip size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                            <input
                                type="file"
                                accept=".pdf"
                                onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file && file.size > 2 * 1024 * 1024) {
                                        showError("Il file non può superare i 2MB");
                                        e.target.value = "";
                                        setAttachment(null);
                                    } else {
                                        setAttachment(file || null);
                                    }
                                }}
                                className="input w-full pl-10"
                                style={{ paddingTop: '0.5rem' }}
                            />
                        </div>
                        <p className="text-xs text-secondary mt-1">Carica un piano di viaggio o altri documenti rilevanti.</p>
                    </div>

                    {/* Error Message */}
                    {createMutation.isError && (
                        <div className="p-4 bg-danger/10 border border-danger/20 rounded-lg flex items-start gap-3 text-danger">
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
                    <div className="flex items-center justify-end gap-3 pt-4 border-t border-border">
                        <button
                            type="button"
                            onClick={() => navigate('/trips')}
                            className="btn btn-ghost"
                        >
                            <X size={18} />
                            Annulla
                        </button>
                        <button
                            type="submit"
                            disabled={createMutation.isPending}
                            className="btn btn-primary"
                        >
                            {createMutation.isPending ? (
                                <>
                                    <div className="spinner w-4 h-4 border-2 border-white/30 border-t-white mr-2" />
                                    Invio...
                                </>
                            ) : (
                                <>
                                    <Save size={18} />
                                    Salva Bozza
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>

            <style>{`
        .grid { display: grid; }
        .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
        .gap-3 { gap: 0.75rem; }
        .gap-6 { gap: 1.5rem; }
        .mb-1 { margin-bottom: 0.25rem; }
        .mb-2 { margin-bottom: 0.5rem; }
        .mb-6 { margin-bottom: 1.5rem; }
        .mt-0.5 { margin-top: 0.125rem; }
        .p-4 { padding: 1rem; }
        .pt-4 { padding-top: 1rem; }
        .pl-10 { padding-left: 2.5rem; }
        .w-full { width: 100%; }
        .w-4 { width: 1rem; }
        .h-4 { height: 1rem; }
        .max-w-xs { max-width: 20rem; }
        .border-t { border-top-width: 1px; }
        .border-border { border-color: var(--color-border); }
        .bg-danger\\/10 { background-color: rgba(239, 68, 68, 0.1); }
        .text-sm { font-size: var(--font-size-sm); }
        .text-xs { font-size: var(--font-size-xs); }
        .text-2xl { font-size: var(--font-size-2xl); }
        .text-secondary { color: var(--color-text-secondary); }
        .text-danger { color: var(--color-danger); }
        .font-bold { font-weight: 700; }
        .font-semibold { font-weight: 600; }
        .block { display: block; }
        .flex { display: flex; }
        .items-center { align-items: center; }
        .justify-end { justify-content: flex-end; }
        .relative { position: relative; }
        .absolute { position: absolute; }
        .left-3 { left: 0.75rem; }
        .top-1\\/2 { top: 50%; }
        .-translate-y-1\\/2 { transform: translateY(-50%); }
        .resize-y { resize: vertical; }
        .space-y-6 > * + * { margin-top: 1.5rem; }
        
        @media (min-width: 768px) {
          .md\\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
            `}</style>
        </div>
    );
}

export default TripFormPage;
