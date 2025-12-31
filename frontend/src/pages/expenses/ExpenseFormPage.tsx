/**
 * KRONOS - New Expense Report Form
 */
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Calendar as CalendarIcon, Save, X, AlertCircle, FileText, Paperclip } from 'lucide-react';
import { useCreateExpenseReport, useUploadReportAttachment, useTrips } from '../../hooks/useApi';
import { useState } from 'react';
import { useToast } from '../../context/ToastContext';
import { formatApiError } from '../../utils/errorUtils';

interface ExpenseFormValues {
    trip_id: string;
    title: string;
    employee_notes?: string;
    period_start: string;
    period_end: string;
}

export function ExpenseFormPage() {
    const navigate = useNavigate();
    const createMutation = useCreateExpenseReport();
    const uploadMutation = useUploadReportAttachment();
    const { data: trips, isLoading: isLoadingTrips } = useTrips('approved,completed'); // Only link to approved or completed trips
    const [attachment, setAttachment] = useState<File | null>(null);
    const { success, error: showError } = useToast();

    const { register, handleSubmit, watch, formState: { errors } } = useForm<ExpenseFormValues>({
        defaultValues: {
            period_start: new Date().toISOString().split('T')[0],
            period_end: new Date().toISOString().split('T')[0],
        }
    });

    const startDate = watch('period_start');

    const onSubmit = (data: ExpenseFormValues) => {
        createMutation.mutate(data, {
            onSuccess: (newReport) => {
                success('Nota spese creata con successo!');
                if (attachment) {
                    uploadMutation.mutate({ id: newReport.id, file: attachment }, {
                        onSuccess: () => {
                            success('Allegato caricato correttamente');
                            navigate(`/expenses/${newReport.id}`);
                        },
                        onError: () => {
                            showError('Errore durante il caricamento dell\'allegato');
                            navigate(`/expenses/${newReport.id}`);
                        },
                    });
                } else {
                    navigate(`/expenses/${newReport.id}`);
                }
            },
        });
    };

    return (
        <div className="max-w-2xl mx-auto animate-fadeIn">
            <div className="mb-6">
                <h1 className="text-2xl font-bold mb-1">Nuova Nota Spese</h1>
                <p className="text-secondary">Crea un nuovo report per raggruppare le tue spese.</p>
            </div>

            <div className="card">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                    {/* Trip Selection */}
                    <div className="form-group">
                        <label className="input-label block mb-2">Trasferta di Riferimento</label>
                        <select
                            {...register('trip_id', { required: 'Seleziona una trasferta' })}
                            className="input w-full"
                            disabled={isLoadingTrips}
                        >
                            <option value="">Seleziona una trasferta...</option>
                            {trips?.map((trip) => (
                                <option key={trip.id} value={trip.id}>
                                    {trip.title} ({trip.destination}) - {new Date(trip.start_date).toLocaleDateString()}
                                </option>
                            ))}
                        </select>
                        {errors.trip_id && <span className="text-danger text-xs">{errors.trip_id.message}</span>}
                        {trips?.length === 0 && !isLoadingTrips && (
                            <p className="text-xs text-warning mt-1">
                                Non hai trasferte approvate a cui collegare questa nota spese.
                            </p>
                        )}
                    </div>

                    {/* Title */}
                    <div className="form-group">
                        <label className="input-label block mb-2">Titolo Report</label>
                        <div className="relative">
                            <FileText size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                            <input
                                type="text"
                                {...register('title', { required: 'Il titolo è obbligatorio' })}
                                className="input w-full pl-10"
                                placeholder="Es. Trasferta Milano Maggio 2024"
                            />
                        </div>
                        {errors.title && <span className="text-danger text-xs">{errors.title.message}</span>}
                    </div>

                    {/* Dates */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="form-group">
                            <label className="input-label block mb-2">Periodo Dal</label>
                            <div className="relative">
                                <CalendarIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                                <input
                                    type="date"
                                    {...register('period_start', { required: 'Data inizio obbligatoria' })}
                                    className="input w-full pl-10"
                                />
                            </div>
                            {errors.period_start && <span className="text-danger text-xs">{errors.period_start.message}</span>}
                        </div>

                        <div className="form-group">
                            <label className="input-label block mb-2">Periodo Al</label>
                            <div className="relative">
                                <CalendarIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                                <input
                                    type="date"
                                    {...register('period_end', {
                                        required: 'Data fine obbligatoria',
                                        validate: value =>
                                            !startDate || new Date(value) >= new Date(startDate) || 'La data fine deve essere successiva alla data inizio'
                                    })}
                                    className="input w-full pl-10"
                                />
                            </div>
                            {errors.period_end && <span className="text-danger text-xs">{errors.period_end.message}</span>}
                        </div>
                    </div>

                    {/* Notes */}
                    <div className="form-group">
                        <label className="input-label block mb-2">Note (Opzionale)</label>
                        <textarea
                            {...register('employee_notes')}
                            className="input w-full min-h-[100px] resize-y"
                            placeholder="Note aggiuntive per l'approvatore..."
                        />
                    </div>

                    {/* Attachment */}
                    <div className="form-group">
                        <label className="input-label block mb-2">Allegato Riepilogativo (PDF max 2MB)</label>
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
                        <p className="text-xs text-secondary mt-1">Carica un PDF riepilogativo o documenti giustificativi aggiuntivi.</p>
                    </div>

                    {/* Error Message */}
                    {createMutation.isError && (
                        <div className="p-4 bg-danger/10 border border-danger/20 rounded-lg flex items-start gap-3 text-danger">
                            <AlertCircle size={20} className="mt-0.5 flex-shrink-0" />
                            <div>
                                <div className="font-semibold text-sm">Errore durante la creazione</div>
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
                            onClick={() => navigate('/expenses')}
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
                                    Creazione in corso...
                                </>
                            ) : (
                                <>
                                    <Save size={18} />
                                    Crea e Aggiungi Voci
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

export default ExpenseFormPage;
