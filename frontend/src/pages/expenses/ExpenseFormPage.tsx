/**
 * KRONOS - Expense Form Page
 * Refactored with FormField component and improved UX
 */
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Calendar as CalendarIcon, Save, AlertCircle, FileText, Briefcase, Receipt, ArrowLeft } from 'lucide-react';
import { useCreateExpenseReport, useUploadReportAttachment, useTrips } from '../../hooks/domain/useExpenses';
import { useState, useEffect } from 'react';
import { useToast } from '../../context/ToastContext';
import { formatApiError } from '../../utils/errorUtils';
import { FileUpload, FormField, PageHeader, Button } from '../../components/common';

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
            {/* Page Header with Breadcrumb */}
            <PageHeader
                title="Nuova Nota Spese"
                description="Crea un nuovo report per raggruppare le tue spese."
                breadcrumbs={[
                    { label: 'Note Spese', path: '/expenses' },
                    { label: 'Nuova' }
                ]}
            />

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                    {/* Mode Toggle */}
                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-slate-700">Tipo di Nota Spese</label>
                        <div className="grid grid-cols-2 gap-3">
                            <button
                                type="button"
                                onClick={() => setValue('is_standalone', false)}
                                className={`p-4 rounded-lg border-2 flex flex-col items-center gap-2 transition-all ${!isStandalone
                                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                                    : 'border-slate-200 hover:border-slate-300 text-slate-600'
                                    }`}
                            >
                                <Briefcase size={24} />
                                <span className="text-sm font-medium">Collegata a Trasferta</span>
                                <span className="text-xs text-slate-500">Per spese durante una trasferta</span>
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setValue('is_standalone', true);
                                    setValue('trip_id', '');
                                }}
                                className={`p-4 rounded-lg border-2 flex flex-col items-center gap-2 transition-all ${isStandalone
                                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                                    : 'border-slate-200 hover:border-slate-300 text-slate-600'
                                    }`}
                            >
                                <Receipt size={24} />
                                <span className="text-sm font-medium">Autonoma</span>
                                <span className="text-xs text-slate-500">Spese senza trasferta</span>
                            </button>
                        </div>
                        <input type="hidden" {...register('is_standalone')} />
                    </div>

                    {/* Trip Selection (only when not standalone) */}
                    {!isStandalone && (
                        <FormField
                            label="Trasferta di Riferimento"
                            
                            as="select"
                            required
                            error={errors.trip_id?.message}
                            helperText={trips?.length === 0 && !isLoadingTrips
                                ? "Non hai trasferte approvate a cui collegare questa nota spese."
                                : undefined
                            }
                            disabled={isLoadingTrips}
                            options={[
                                { value: '', label: 'Seleziona una trasferta...' },
                                ...(trips?.map((trip) => ({
                                    value: trip.id,
                                    label: `${trip.title} (${trip.destination}) - ${new Date(trip.start_date).toLocaleDateString()}`
                                })) || [])
                            ]}
                            {...register('trip_id', {
                                required: !isStandalone ? 'Seleziona una trasferta' : false
                            })}
                        />
                    )}

                    {/* Title */}
                    <FormField
                        label="Titolo Report"
                        
                        required
                        leftIcon={<FileText size={18} />}
                        error={errors.title?.message}
                        placeholder={isStandalone ? "Es. Spese Rappresentanza Gennaio" : "Es. Trasferta Milano Maggio 2024"}
                        {...register('title', { required: 'Il titolo è obbligatorio' })}
                    />

                    {/* Dates Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FormField
                            label="Periodo Dal"
                            
                            type="date"
                            required
                            leftIcon={<CalendarIcon size={18} />}
                            error={errors.period_start?.message}
                            {...register('period_start', { required: 'Data inizio obbligatoria' })}
                        />

                        <FormField
                            label="Periodo Al"
                            
                            type="date"
                            required
                            leftIcon={<CalendarIcon size={18} />}
                            error={errors.period_end?.message}
                            {...register('period_end', {
                                required: 'Data fine obbligatoria',
                                validate: value =>
                                    !startDate || new Date(value) >= new Date(startDate) ||
                                    'La data fine deve essere successiva alla data inizio'
                            })}
                        />
                    </div>

                    {/* Notes */}
                    <FormField
                        label="Note"
                        
                        as="textarea"
                        placeholder="Note aggiuntive per l'approvatore..."
                        helperText="Opzionale"
                        {...register('employee_notes')}
                    />

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
                        <div className="p-4 bg-red-50 border border-red-100 rounded-lg flex items-start gap-3 text-red-700">
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
                    <div className="flex items-center justify-between pt-6 border-t border-slate-100">
                        <Button
                            type="button"
                            variant="ghost"
                            icon={<ArrowLeft size={18} />}
                            onClick={() => navigate(-1)}
                        >
                            Annulla
                        </Button>

                        <Button
                            type="submit"
                            variant="primary"
                            icon={<Save size={18} />}
                            isLoading={createMutation.isPending}
                        >
                            Crea e Aggiungi Voci
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default ExpenseFormPage;
