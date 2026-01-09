/**
 * KRONOS - Leave Request Form Component
 * Refactored with FormField component and improved UX
 */
import { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Calendar as CalendarIcon, Save, AlertCircle, Laptop, ArrowLeft } from 'lucide-react';
import { useCreateLeaveRequest, useUpdateLeaveRequest, useLeaveRequest } from '../../hooks/domain/useLeaves';
import { configApi } from '../../services/api';
import type { LeaveType, LeaveRequestCreate } from '../../types';
import { formatApiError } from '../../utils/errorUtils';

import { leavesService } from '../../services/leaves.service';
import { smartWorkingService, type SWAgreement } from '../../services/smartWorking.service';

import { FormField, PageHeader, Button, Skeleton } from '../../components/common';

// Weekday names for display
const WEEKDAY_NAMES: Record<number, string> = {
    0: 'Lunedì',
    1: 'Martedì',
    2: 'Mercoledì',
    3: 'Giovedì',
    4: 'Venerdì',
};

export function LeaveRequestForm() {
    const navigate = useNavigate();
    const { id } = useParams<{ id: string }>();
    const isEditing = !!id;
    const [searchParams] = useSearchParams();

    const createMutation = useCreateLeaveRequest();
    const updateMutation = useUpdateLeaveRequest();

    // Fetch existing request if editing
    const { data: existingLeave, isLoading: isLoadingLeave } = useLeaveRequest(id || '');

    const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
    const [loadingTypes, setLoadingTypes] = useState(true);

    // Smart Working agreement state
    const [swAgreement, setSwAgreement] = useState<SWAgreement | null>(null);

    // Calculation state
    const [calculatedDays, setCalculatedDays] = useState<number | null>(null);
    const [isCalculating, setIsCalculating] = useState(false);

    // Pre-fill date from URL query param if present
    const initialDate = searchParams.get('date') || new Date().toISOString().split('T')[0];

    const { register, handleSubmit, watch, setValue, reset, formState: { errors } } = useForm<LeaveRequestCreate>({
        defaultValues: {
            start_date: initialDate,
            end_date: initialDate,
            start_half_day: false,
            end_half_day: false,
        }
    });

    // Populate form when data is loaded
    useEffect(() => {
        if (existingLeave) {
            reset({
                leave_type_id: existingLeave.leave_type_id,
                start_date: existingLeave.start_date,
                end_date: existingLeave.end_date,
                start_half_day: existingLeave.start_half_day,
                end_half_day: existingLeave.end_half_day,
                employee_notes: existingLeave.employee_notes || '',
                protocol_number: existingLeave.protocol_number || '',
            });
        }
    }, [existingLeave, reset]);

    const startDate = watch('start_date');
    const endDate = watch('end_date');
    const startHalfDay = watch('start_half_day');
    const endHalfDay = watch('end_half_day');
    const leaveTypeId = watch('leave_type_id');

    // Fetch leave types
    useEffect(() => {
        async function fetchLeaveTypes() {
            try {
                const response = await configApi.get('/leave-types');
                const types = response.data.items || [];
                const filteredTypes = types.filter((t: LeaveType) =>
                    !t.name.toLowerCase().includes('permess') &&
                    !t.name.toLowerCase().includes('ex-fest') &&
                    !t.name.toLowerCase().includes('rol')
                );
                setLeaveTypes(filteredTypes);
            } catch (error) {
                console.error('Failed to load leave types', error);
            } finally {
                setLoadingTypes(false);
            }
        }
        fetchLeaveTypes();
    }, [setValue, watch, isEditing]);

    // Fetch Smart Working agreement for conflict detection
    useEffect(() => {
        async function fetchSwAgreement() {
            try {
                const agreements = await smartWorkingService.getMyAgreements();
                const active = agreements.find(a => a.status === 'ACTIVE');
                setSwAgreement(active || null);
            } catch (error) {
                console.error('Failed to load SW agreement', error);
            }
        }
        fetchSwAgreement();
    }, []);

    // Detect SW conflicts
    const swConflictDays = useMemo(() => {
        if (!startDate || !endDate || !swAgreement?.allowed_weekdays?.length) {
            return [];
        }

        const conflicts: { date: Date; weekdayName: string }[] = [];
        const start = new Date(startDate);
        const end = new Date(endDate);

        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const jsWeekday = d.getDay();
            if (jsWeekday === 0 || jsWeekday === 6) continue;

            const agreementWeekday = jsWeekday - 1;

            if (swAgreement.allowed_weekdays.includes(agreementWeekday)) {
                conflicts.push({
                    date: new Date(d),
                    weekdayName: WEEKDAY_NAMES[agreementWeekday]
                });
            }
        }

        return conflicts;
    }, [startDate, endDate, swAgreement]);

    // Calculate days effect
    useEffect(() => {
        const calculate = async () => {
            if (!startDate || !endDate || !leaveTypeId) {
                setCalculatedDays(null);
                return;
            }

            if (new Date(endDate) < new Date(startDate)) {
                setCalculatedDays(null);
                return;
            }

            setIsCalculating(true);
            try {
                const result = await leavesService.calculateDays(
                    startDate,
                    endDate,
                    startHalfDay,
                    endHalfDay,
                    leaveTypeId
                );
                setCalculatedDays(result.days);
            } catch (error) {
                console.error("Calculation failed", error);
                setCalculatedDays(null);
            } finally {
                setIsCalculating(false);
            }
        };

        const timeoutId = setTimeout(calculate, 300);
        return () => clearTimeout(timeoutId);
    }, [startDate, endDate, startHalfDay, endHalfDay, leaveTypeId]);

    const selectedType = leaveTypes.find(t => t.id === leaveTypeId);
    const requiresProtocol = selectedType?.requires_protocol || false;

    const onSubmit = (data: LeaveRequestCreate) => {
        if (isEditing && id) {
            updateMutation.mutate({ id, data: data as any }, {
                onSuccess: () => navigate(`/leaves/${id}`)
            });
        } else {
            createMutation.mutate(data, {
                onSuccess: () => navigate('/leaves')
            });
        }
    };

    const isSubmitting = createMutation.isPending || updateMutation.isPending;

    // Loading state
    if (isLoadingLeave && isEditing) {
        return (
            <div className="max-w-2xl mx-auto py-8">
                <div className="space-y-4">
                    <Skeleton variant="title" />
                    <Skeleton variant="text" className="w-2/3" />
                    <div className="mt-8 space-y-6 bg-white p-6 rounded-xl border border-slate-200">
                        <Skeleton variant="button" className="w-full h-10" />
                        <div className="grid grid-cols-2 gap-4">
                            <Skeleton variant="button" className="w-full h-10" />
                            <Skeleton variant="button" className="w-full h-10" />
                        </div>
                        <Skeleton variant="card" className="h-24" />
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto animate-fadeIn py-8">
            {/* Page Header with Breadcrumb */}
            <PageHeader
                title={isEditing ? 'Modifica Richiesta' : 'Nuova Richiesta Assenza'}
                description={isEditing
                    ? 'Aggiorna i dettagli della tua richiesta di assenza.'
                    : 'Compila il modulo per richiedere ferie o permessi.'
                }
                breadcrumbs={[
                    { label: 'Assenze', path: '/leaves' },
                    { label: isEditing ? `Richiesta #${id?.slice(0, 8)}` : 'Nuova' }
                ]}
            />

            {/* Form Card */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                    {/* Leave Type Selection */}
                    {loadingTypes ? (
                        <Skeleton variant="button" className="w-full h-10" />
                    ) : (
                        <FormField
                            label="Tipo di Richiesta"
                            
                            as="select"
                            required
                            error={errors.leave_type_id?.message}
                            options={[
                                { value: '', label: '-- Seleziona tipo --' },
                                ...leaveTypes.map(type => ({
                                    value: type.id,
                                    label: `${type.name}${(type.max_single_request_days || type.max_consecutive_days) ? ` (Max ${type.max_single_request_days || type.max_consecutive_days} gg)` : ''}`
                                }))
                            ]}
                            {...register('leave_type_id', { required: 'Seleziona un tipo di assenza' })}
                        />
                    )}

                    {/* Date Selection Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FormField
                            label="Dal giorno"
                            
                            type="date"
                            required
                            leftIcon={<CalendarIcon size={18} />}
                            error={errors.start_date?.message}
                            {...register('start_date', {
                                required: 'Data inizio obbligatoria',
                                onChange: (e) => setValue('end_date', e.target.value)
                            })}
                        />

                        <FormField
                            label="Al giorno"
                            
                            type="date"
                            required
                            leftIcon={<CalendarIcon size={18} />}
                            error={errors.end_date?.message}
                            {...register('end_date', {
                                required: 'Data fine obbligatoria',
                                validate: value =>
                                    !startDate || new Date(value) >= new Date(startDate) ||
                                    'La data fine deve essere successiva alla data inizio'
                            })}
                        />
                    </div>

                    {/* Smart Working Conflict Alert */}
                    {swConflictDays.length > 0 && (
                        <div className="p-4 bg-teal-50 border border-teal-200 rounded-lg flex items-start gap-3 animate-fadeIn">
                            <Laptop size={20} className="text-teal-600 mt-0.5 shrink-0" />
                            <div className="text-sm">
                                <p className="font-semibold text-teal-800">Attenzione: Giorni Smart Working</p>
                                <p className="text-teal-700 mt-1">
                                    La tua richiesta include {swConflictDays.length === 1 ? 'un giorno' : `${swConflictDays.length} giorni`} normalmente
                                    destinat{swConflictDays.length === 1 ? 'o' : 'i'} al <strong>lavoro agile</strong>:
                                </p>
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {swConflictDays.map((c, idx) => (
                                        <span key={idx} className="px-2 py-1 bg-white border border-teal-300 rounded text-xs font-medium text-teal-700">
                                            {c.weekdayName} {c.date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })}
                                        </span>
                                    ))}
                                </div>
                                <p className="text-teal-600 text-xs mt-2">
                                    Puoi comunque procedere con la richiesta.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Duration Preview Card */}
                    <div className="bg-indigo-50 rounded-lg p-4 flex items-center gap-4 border border-indigo-100">
                        <div className="bg-white p-2.5 rounded-lg shadow-sm border border-indigo-100">
                            {isCalculating ? (
                                <div className="w-5 h-5 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
                            ) : (
                                <CalendarIcon className="text-indigo-600" size={20} />
                            )}
                        </div>
                        <div>
                            <div className="text-xs font-semibold text-indigo-800 uppercase tracking-wider mb-0.5">
                                Durata effettiva
                            </div>
                            <div className="flex items-baseline gap-2">
                                <span className={`text-2xl font-bold font-mono ${calculatedDays !== null ? 'text-indigo-900' : 'text-slate-400'}`}>
                                    {calculatedDays !== null ? calculatedDays : '-'}
                                </span>
                                <span className="text-sm font-medium text-indigo-700/70">
                                    giorni lavorativi
                                </span>
                            </div>
                            {calculatedDays !== null && (
                                <div className="text-xs text-indigo-600/80 mt-1">
                                    Escluse festività e weekend
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Protocol Number (INPS) - Only if required */}
                    {requiresProtocol && (
                        <FormField
                            label="Codice iNPS / Protocollo Telematico"
                            
                            required
                            error={errors.protocol_number?.message}
                            helperText="Inserisci il protocollo telematico fornito dal medico o dall'iNPS."
                            placeholder="Esempio: MAL12345678"
                            wrapperClassName="animate-fadeIn"
                            {...register('protocol_number', {
                                required: requiresProtocol ? 'Il codice iNPS è obbligatorio per la malattia' : false,
                                minLength: { value: 5, message: 'Il codice deve essere di almeno 5 caratteri' }
                            })}
                        />
                    )}

                    {/* Notes */}
                    <FormField
                        label="Note"
                        
                        as="textarea"
                        placeholder="Inserisci eventuali note per l'approvatore..."
                        helperText="Opzionale - aggiungi qualsiasi informazione utile per l'approvatore"
                        {...register('employee_notes')}
                    />

                    {/* Error Message */}
                    {(createMutation.isError || updateMutation.isError) && (
                        <div className="p-4 bg-red-50 border border-red-100 rounded-lg flex items-start gap-3 text-red-700">
                            <AlertCircle size={20} className="mt-0.5 flex-shrink-0" />
                            <div>
                                <div className="font-semibold text-sm">Errore durante l'invio</div>
                                <div className="text-sm opacity-90 mt-1">
                                    {formatApiError(createMutation.error || updateMutation.error)}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-6 border-t border-slate-100 mt-6">
                        <Button
                            type="button"
                            variant="ghost"
                            icon={<ArrowLeft size={18} />}
                            onClick={() => navigate(isEditing ? `/leaves/${id}` : '/leaves')}
                        >
                            Annulla
                        </Button>

                        <Button
                            type="submit"
                            variant="primary"
                            icon={<Save size={18} />}
                            isLoading={isSubmitting}
                        >
                            {isEditing ? 'Salva Modifiche' : 'Invia Richiesta'}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default LeaveRequestForm;
