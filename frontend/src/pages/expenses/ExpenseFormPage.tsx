import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Calendar as CalendarIcon, Save, X, AlertCircle, FileText, Briefcase, Receipt } from 'lucide-react';
import { useCreateExpenseReport, useUploadReportAttachment, useTrips } from '../../hooks/domain/useExpenses';
import { useState, useEffect } from 'react';
import { useToast } from '../../context/ToastContext';
import { formatApiError } from '../../utils/errorUtils';
import { FileUpload } from '../../components/common/FileUpload';

interface ExpenseFormValues {
    trip_id?: string;
    is_standalone: boolean;
    title: string;
    employee_notes?: string;
    period_start: string;
    period_end: string;
}

export function ExpenseFormPage() {
    const navigate = useNavigate();
    const createMutation = useCreateExpenseReport();
    const uploadMutation = useUploadReportAttachment();
    const { data: trips, isLoading: isLoadingTrips } = useTrips('approved,completed');
    const [attachments, setAttachments] = useState<File[]>([]);
    const [searchParams] = useSearchParams();
    const { success, error: showError } = useToast();

    // Determine initial mode from URL params
    const tripIdFromUrl = searchParams.get('trip_id');
    const isStandaloneFromUrl = searchParams.get('standalone') === 'true';

    const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<ExpenseFormValues>({
        defaultValues: {
            trip_id: tripIdFromUrl || '',
            is_standalone: !tripIdFromUrl && isStandaloneFromUrl,
            period_start: new Date().toISOString().split('T')[0],
            period_end: new Date().toISOString().split('T')[0],
        }
    });

    const isStandalone = watch('is_standalone');
    const selectedTripId = watch('trip_id');
    const startDate = watch('period_start');

    // Handle trip selection changes to sync dates
    useEffect(() => {
        if (!isStandalone && selectedTripId && trips) {
            const trip = trips.find(t => t.id === selectedTripId);
            if (trip) {
                setValue('period_start', trip.start_date);
                setValue('period_end', trip.end_date);
            }
        }
    }, [selectedTripId, trips, setValue, isStandalone]);

    const uploadAttachments = async (reportId: string) => {
        for (const file of attachments) {
            try {
                await new Promise<void>((resolve, reject) => {
                    uploadMutation.mutate(
                        { id: reportId, file },
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

    const onSubmit = (data: ExpenseFormValues) => {
        const payload = {
            ...data,
            trip_id: isStandalone ? undefined : data.trip_id,
            is_standalone: isStandalone,
        };

        createMutation.mutate(payload, {
            onSuccess: async (newReport) => {
                success('Nota spese creata con successo!');
                if (attachments.length > 0) {
                    await uploadAttachments(newReport.id);
                    success(`${attachments.length} allegat${attachments.length === 1 ? 'o' : 'i'} caricat${attachments.length === 1 ? 'o' : 'i'}`);
                }
                navigate(`/expenses/${newReport.id}`);
            },
        });
    };

    return (
        <div className="max-w-2xl mx-auto animate-fadeIn pb-8">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900 mb-1">Nuova Nota Spese</h1>
                <p className="text-gray-500">Crea un nuovo report per raggruppare le tue spese.</p>
            </div>

            <div className="card bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                    {/* Mode Toggle */}
                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-gray-700">Tipo di Nota Spese</label>
                        <div className="grid grid-cols-2 gap-3">
                            <button
                                type="button"
                                onClick={() => setValue('is_standalone', false)}
                                className={`p-4 rounded-lg border-2 flex flex-col items-center gap-2 transition-all ${!isStandalone
                                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                                    : 'border-gray-200 hover:border-gray-300 text-gray-600'
                                    }`}
                            >
                                <Briefcase size={24} />
                                <span className="text-sm font-medium">Collegata a Trasferta</span>
                                <span className="text-xs text-gray-500">Per spese durante una trasferta</span>
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setValue('is_standalone', true);
                                    setValue('trip_id', '');
                                }}
                                className={`p-4 rounded-lg border-2 flex flex-col items-center gap-2 transition-all ${isStandalone
                                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                                    : 'border-gray-200 hover:border-gray-300 text-gray-600'
                                    }`}
                            >
                                <Receipt size={24} />
                                <span className="text-sm font-medium">Autonoma</span>
                                <span className="text-xs text-gray-500">Spese senza trasferta</span>
                            </button>
                        </div>
                        <input type="hidden" {...register('is_standalone')} />
                    </div>

                    {/* Trip Selection (only when not standalone) */}
                    {!isStandalone && (
                        <div className="space-y-1.5">
                            <label className="block text-sm font-medium text-gray-700">Trasferta di Riferimento</label>
                            <select
                                {...register('trip_id', {
                                    required: !isStandalone ? 'Seleziona una trasferta' : false
                                })}
                                className="input w-full appearance-none bg-none"
                                disabled={isLoadingTrips}
                            >
                                <option value="">Seleziona una trasferta...</option>
                                {trips?.map((trip) => (
                                    <option key={trip.id} value={trip.id}>
                                        {trip.title} ({trip.destination}) - {new Date(trip.start_date).toLocaleDateString()}
                                    </option>
                                ))}
                            </select>
                            {errors.trip_id && <span className="text-red-500 text-xs">{errors.trip_id.message}</span>}
                            {trips?.length === 0 && !isLoadingTrips && (
                                <p className="text-xs text-amber-600 mt-1">
                                    Non hai trasferte approvate a cui collegare questa nota spese.
                                </p>
                            )}
                        </div>
                    )}

                    {/* Title */}
                    <div className="space-y-1.5">
                        <label className="block text-sm font-medium text-gray-700">Titolo Report</label>
                        <div className="relative">
                            <FileText size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                            <input
                                type="text"
                                {...register('title', { required: 'Il titolo è obbligatorio' })}
                                className="input w-full pl-10"
                                placeholder={isStandalone ? "Es. Spese Rappresentanza Gennaio" : "Es. Trasferta Milano Maggio 2024"}
                            />
                        </div>
                        {errors.title && <span className="text-red-500 text-xs">{errors.title.message}</span>}
                    </div>

                    {/* Dates */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-1.5">
                            <label className="block text-sm font-medium text-gray-700">Periodo Dal</label>
                            <div className="relative">
                                <CalendarIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                                <input
                                    type="date"
                                    {...register('period_start', { required: 'Data inizio obbligatoria' })}
                                    className="input w-full pl-10"
                                />
                            </div>
                            {errors.period_start && <span className="text-red-500 text-xs">{errors.period_start.message}</span>}
                        </div>

                        <div className="space-y-1.5">
                            <label className="block text-sm font-medium text-gray-700">Periodo Al</label>
                            <div className="relative">
                                <CalendarIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
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
                            {errors.period_end && <span className="text-red-500 text-xs">{errors.period_end.message}</span>}
                        </div>
                    </div>

                    {/* Notes */}
                    <div className="space-y-1.5">
                        <label className="block text-sm font-medium text-gray-700">Note (Opzionale)</label>
                        <textarea
                            {...register('employee_notes')}
                            className="input w-full min-h-[100px] resize-y p-3"
                            placeholder="Note aggiuntive per l'approvatore..."
                        />
                    </div>

                    {/* Attachments */}
                    <FileUpload
                        label="Allegati"
                        files={attachments}
                        onFilesChange={setAttachments}
                        accept=".pdf,.jpg,.jpeg,.png"
                        multiple={true}
                        maxSizeMB={5}
                        maxFiles={10}
                        helperText="Ricevute, scontrini, fatture o documenti giustificativi (max 10 file, 5MB per file)"
                    />

                    {/* Error Message */}
                    {createMutation.isError && (
                        <div className="p-4 bg-red-50 border border-red-100 rounded-lg flex items-start gap-3 text-red-600">
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
                    <div className="flex items-center justify-end gap-3 pt-6 border-t border-gray-100">
                        <button
                            type="button"
                            onClick={() => navigate(-1)}
                            className="btn btn-ghost text-gray-600 hover:bg-gray-100"
                        >
                            <X size={18} className="mr-2" />
                            Annulla
                        </button>
                        <button
                            type="submit"
                            disabled={createMutation.isPending}
                            className="btn btn-primary"
                        >
                            {createMutation.isPending ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                    Creazione in corso...
                                </>
                            ) : (
                                <>
                                    <Save size={18} className="mr-2" />
                                    Crea e Aggiungi Voci
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default ExpenseFormPage;
