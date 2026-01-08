/**
 * KRONOS - Leave Request Form Component
 */
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Calendar as CalendarIcon, Save, X, AlertCircle, ChevronDown, Loader } from 'lucide-react';
import { useCreateLeaveRequest, useUpdateLeaveRequest, useLeaveRequest } from '../../hooks/domain/useLeaves';
import { configApi } from '../../services/api'; // Direct call for leave types since it's rarely updated
import type { LeaveType, LeaveRequestCreate } from '../../types';
import { formatApiError } from '../../utils/errorUtils';

import { leavesService } from '../../services/leaves.service';

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
                // Filter out Permessi and Ex-Festività as requested
                const filteredTypes = types.filter((t: LeaveType) =>
                    !t.name.toLowerCase().includes('permess') &&
                    !t.name.toLowerCase().includes('ex-fest') &&
                    !t.name.toLowerCase().includes('rol')
                );
                setLeaveTypes(filteredTypes);

                // Set default if not set and not editing
                const currentType = watch('leave_type_id');
                if (types.length > 0 && !currentType && !isEditing) {
                    setValue('leave_type_id', types[0].id);
                }
            } catch (error) {
                console.error('Failed to load leave types', error);
            } finally {
                setLoadingTypes(false);
            }
        }
        fetchLeaveTypes();
    }, [setValue, watch, isEditing]);

    // Calculate days effect
    useEffect(() => {
        const calculate = async () => {
            if (!startDate || !endDate) {
                setCalculatedDays(null);
                return;
            }

            // Check valid range
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

        const timeoutId = setTimeout(calculate, 300); // Simple debounce
        return () => clearTimeout(timeoutId);
    }, [startDate, endDate, startHalfDay, endHalfDay, leaveTypeId]);

    const selectedType = leaveTypes.find(t => t.id === leaveTypeId);
    const requiresProtocol = selectedType?.requires_protocol || false;

    const onSubmit = (data: LeaveRequestCreate) => {
        if (isEditing && id) {
            updateMutation.mutate({ id, data: data as any }, {
                onSuccess: () => {
                    navigate(`/leaves/${id}`);
                }
            });
        } else {
            createMutation.mutate(data, {
                onSuccess: () => {
                    navigate('/leaves');
                }
            });
        }
    };

    const onInvalid = (errors: any) => {
        console.error('Form validation failed:', errors);
    };

    if (isLoadingLeave && isEditing) {
        return (
            <div className="max-w-2xl mx-auto py-32 flex flex-col items-center justify-center animate-fadeIn">
                <Loader className="animate-spin text-indigo-600 mb-4" size={48} />
                <p className="text-gray-500 font-medium">Caricamento richiesta...</p>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto animate-fadeIn py-8">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">
                    {isEditing ? 'Modifica Richiesta' : 'Nuova Richiesta'}
                </h1>
                <p className="text-gray-500">
                    {isEditing ? 'Aggiorna i dettagli della tua richiesta di assenza.' : 'Compila il modulo per richiedere ferie o permessi.'}
                </p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                <form onSubmit={handleSubmit(onSubmit, onInvalid)} className="space-y-6">

                    {/* Leave Type Selection */}
                    <div>
                        <label htmlFor="leave_type_id" className="block text-sm font-medium text-gray-700 mb-1">Tipo di Richiesta</label>
                        {loadingTypes ? (
                            <div className="animate-pulse h-10 w-full bg-gray-100 rounded-lg" />
                        ) : (
                            <div className="relative">
                                <select
                                    id="leave_type_id"
                                    {...register('leave_type_id', { required: 'Seleziona un tipo' })}
                                    className={`block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm appearance-none pr-10 ${errors.leave_type_id ? 'border-red-300 focus:border-red-500 focus:ring-red-200' : ''}`}
                                >
                                    {leaveTypes.map((type) => (
                                        <option key={type.id} value={type.id}>
                                            {type.name}
                                            {(type.max_single_request_days || type.max_consecutive_days) ? ` (Max ${type.max_single_request_days || type.max_consecutive_days} gg)` : ''}
                                        </option>
                                    ))}
                                </select>
                                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
                                    <ChevronDown size={16} />
                                </div>
                            </div>
                        )}
                        {errors.leave_type_id && <span className="text-red-600 text-xs mt-1 flex items-center gap-1"><AlertCircle size={12} /> {errors.leave_type_id?.message || 'Seleziona un tipo'}</span>}
                    </div>

                    {/* Date Selection */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Dal giorno</label>
                            <div className="relative">
                                <CalendarIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="date"
                                    {...register('start_date', {
                                        required: 'Data inizio obbligatoria',
                                        onChange: (e) => {
                                            // Auto-update end date if it's empty or to help user
                                            setValue('end_date', e.target.value);
                                        }
                                    })}
                                    className={`block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm pl-10 ${errors.start_date ? 'border-red-300 focus:border-red-500 focus:ring-red-200' : ''}`}
                                />
                            </div>

                            {errors.start_date && <span className="text-red-600 text-xs mt-1 flex items-center gap-1"><AlertCircle size={12} /> {errors.start_date?.message}</span>}
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Al giorno</label>
                            <div className="relative">
                                <CalendarIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="date"
                                    {...register('end_date', {
                                        required: 'Data fine obbligatoria',
                                        validate: value =>
                                            !startDate || new Date(value) >= new Date(startDate) || 'La data fine deve essere successiva alla data inizio'
                                    })}
                                    className={`block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm pl-10 ${errors.end_date ? 'border-red-300 focus:border-red-500 focus:ring-red-200' : ''}`}
                                />
                            </div>

                            {errors.end_date && <span className="text-red-600 text-xs mt-1 flex items-center gap-1"><AlertCircle size={12} /> {errors.end_date?.message}</span>}
                        </div>
                    </div>

                    {/* Duration Preview */}
                    <div className="bg-indigo-50 rounded-lg p-4 flex items-center gap-4 border border-indigo-100">
                        <div className="bg-white p-2.5 rounded-lg shadow-sm border border-indigo-100">
                            {isCalculating ? (
                                <div className="w-5 h-5 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
                            ) : (
                                <CalendarIcon className="text-indigo-600" size={20} />
                            )}
                        </div>
                        <div>
                            <div className="text-xs font-semibold text-indigo-800 uppercase tracking-wider mb-0.5">Durata effettiva</div>
                            <div className="flex items-baseline gap-2">
                                <span className={`text-2xl font-bold font-mono ${calculatedDays !== null ? 'text-indigo-900' : 'text-gray-400'}`}>
                                    {calculatedDays !== null ? calculatedDays : '-'}
                                </span>
                                <span className="text-sm font-medium text-indigo-700/70">
                                    giorni lavorativi
                                </span>
                            </div>
                            {startDate && endDate && calculatedDays !== null && (
                                <div className="text-xs text-indigo-600/80 mt-1">
                                    Escluse festività e weekend
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Protocol Number (INPS) - Only if required */}
                    {requiresProtocol && (
                        <div className="animate-slideIn">
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Codice iNPS / Protocollo Telematico
                            </label>
                            <input
                                type="text"
                                {...register('protocol_number', {
                                    required: requiresProtocol ? 'Il codice iNPS è obbligatorio per la malattia' : false,
                                    minLength: { value: 5, message: 'Il codice deve essere di almeno 5 caratteri' }
                                })}
                                className={`block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${errors.protocol_number ? 'border-red-300 focus:border-red-500 focus:ring-red-200' : ''}`}
                                placeholder="Esempio: MAL12345678"
                            />
                            <p className="mt-1 text-xs text-gray-500">
                                Inserisci il protocollo telematico fornito dal medico o dall'iNPS.
                            </p>
                            {errors.protocol_number && <span className="text-red-600 text-xs mt-1 flex items-center gap-1"><AlertCircle size={12} /> {errors.protocol_number?.message}</span>}
                        </div>
                    )}

                    {/* Notes */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Note (Opzionale)</label>
                        <textarea
                            {...register('employee_notes')}
                            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm min-h-[100px] resize-y"
                            placeholder="Inserisci eventuali note per l'approvatore..."
                        />
                    </div>

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
                    <div className="flex items-center justify-end gap-3 pt-6 border-t border-gray-100 mt-6">
                        <button
                            type="button"
                            onClick={() => navigate(isEditing ? `/leaves/${id}` : '/leaves')}
                            className="btn btn-ghost text-gray-600 hover:text-gray-900"
                        >
                            <X size={18} />
                            Annulla
                        </button>
                        <button
                            type="submit"
                            disabled={createMutation.isPending || updateMutation.isPending}
                            className="btn btn-primary shadow-sm"
                        >
                            {(createMutation.isPending || updateMutation.isPending) ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                    Invio in corso...
                                </>
                            ) : (
                                <>
                                    <Save size={18} />
                                    {isEditing ? 'Salva Modifiche' : 'Invia Richiesta'}
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default LeaveRequestForm;
