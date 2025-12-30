/**
 * KRONOS - Leave Request Form Component
 */
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Calendar as CalendarIcon, Save, X, AlertCircle } from 'lucide-react';
import { useCreateLeaveRequest } from '../../hooks/useApi';
import { configApi } from '../../services/api'; // Direct call for leave types since it's rarely updated
import type { LeaveType, LeaveRequestCreate } from '../../types';

export function LeaveRequestForm() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const createMutation = useCreateLeaveRequest();
    const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
    const [loadingTypes, setLoadingTypes] = useState(true);

    // Pre-fill date from URL query param if present
    const initialDate = searchParams.get('date') || new Date().toISOString().split('T')[0];

    const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<LeaveRequestCreate>({
        defaultValues: {
            start_date: initialDate,
            end_date: initialDate,
            start_half_day: false,
            end_half_day: false,
        }
    });

    const startDate = watch('start_date');
    const endDate = watch('end_date');

    // Fetch leave types
    useEffect(() => {
        async function fetchLeaveTypes() {
            try {
                const response = await configApi.get('/leave-types');
                setLeaveTypes(response.data);
                if (response.data.length > 0) {
                    setValue('leave_type_id', response.data[0].id);
                }
            } catch (error) {
                console.error('Failed to load leave types', error);
            } finally {
                setLoadingTypes(false);
            }
        }
        fetchLeaveTypes();
    }, [setValue]);

    const onSubmit = (data: LeaveRequestCreate) => {
        createMutation.mutate(data, {
            onSuccess: () => {
                navigate('/leaves');
            },
        });
    };

    // Simple days calculation for preview (logic mirrored from backend for instant feedback)
    const calculateDaysPreview = () => {
        if (!startDate || !endDate) return 0;
        const start = new Date(startDate);
        const end = new Date(endDate);
        const diffTime = Math.abs(end.getTime() - start.getTime());
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
        return diffDays;
    };

    return (
        <div className="max-w-2xl mx-auto animate-fadeIn">
            <div className="mb-6">
                <h1 className="text-2xl font-bold mb-1">Nuova Richiesta</h1>
                <p className="text-secondary">Compila il modulo per richiedere ferie o permessi.</p>
            </div>

            <div className="card">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                    {/* Leave Type Selection */}
                    <div className="form-group">
                        <label className="input-label block mb-2">Tipo di Richiesta</label>
                        {loadingTypes ? (
                            <div className="skeleton h-10 w-full" />
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {leaveTypes.map((type) => (
                                    <label
                                        key={type.id}
                                        className={`
                      type-selector p-3 border rounded-lg cursor-pointer transition-all
                      ${watch('leave_type_id') === type.id ? 'border-primary bg-primary/5 ring-1 ring-primary' : 'border-border hover:border-primary/50'}
                    `}
                                    >
                                        <div className="flex items-center gap-3">
                                            <input
                                                type="radio"
                                                value={type.id}
                                                {...register('leave_type_id', { required: true })}
                                                className="hidden"
                                            />
                                            <div
                                                className="w-3 h-3 rounded-full flex-shrink-0"
                                                style={{ backgroundColor: type.color }}
                                            />
                                            <div>
                                                <div className="font-semibold text-sm">{type.name}</div>
                                                {type.max_consecutive_days && (
                                                    <div className="text-xs text-secondary mt-0.5">Max {type.max_consecutive_days} gg</div>
                                                )}
                                            </div>
                                        </div>
                                    </label>
                                ))}
                            </div>
                        )}
                        {errors.leave_type_id && <span className="text-danger text-xs mt-1">Seleziona un tipo</span>}
                    </div>

                    {/* Date Selection */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="form-group">
                            <label className="input-label block mb-2">Dal giorno</label>
                            <div className="relative">
                                <CalendarIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                                <input
                                    type="date"
                                    {...register('start_date', { required: 'Data inizio obbligatoria' })}
                                    className="input w-full pl-10"
                                />
                            </div>
                            <div className="mt-2 flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    id="start_half_day"
                                    {...register('start_half_day')}
                                    className="rounded border-gray-300 text-primary focus:ring-primary"
                                />
                                <label htmlFor="start_half_day" className="text-sm text-secondary">
                                    Mezza giornata (Pomeriggio)
                                </label>
                            </div>
                            {errors.start_date && <span className="text-danger text-xs">{errors.start_date.message}</span>}
                        </div>

                        <div className="form-group">
                            <label className="input-label block mb-2">Al giorno</label>
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
                            <div className="mt-2 flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    id="end_half_day"
                                    {...register('end_half_day')}
                                    className="rounded border-gray-300 text-primary focus:ring-primary"
                                />
                                <label htmlFor="end_half_day" className="text-sm text-secondary">
                                    Mezza giornata (Mattina)
                                </label>
                            </div>
                            {errors.end_date && <span className="text-danger text-xs">{errors.end_date.message}</span>}
                        </div>
                    </div>

                    {/* Duration Preview */}
                    <div className="bg-bg-tertiary rounded-lg p-4 flex items-center gap-3">
                        <CalendarIcon className="text-primary" size={20} />
                        <div>
                            <div className="text-sm font-medium">Durata stimata</div>
                            <div className="text-2xl font-bold font-mono">
                                {calculateDaysPreview()} <span className="text-sm font-normal text-secondary">giorni</span>
                            </div>
                        </div>
                    </div>

                    {/* Notes */}
                    <div className="form-group">
                        <label className="input-label block mb-2">Note (Opzionale)</label>
                        <textarea
                            {...register('employee_notes')}
                            className="input w-full min-h-[100px] resize-y"
                            placeholder="Inserisci eventuali note per l'approvatore..."
                        />
                    </div>

                    {/* Error Message */}
                    {createMutation.isError && (
                        <div className="p-4 bg-danger/10 border border-danger/20 rounded-lg flex items-start gap-3 text-danger">
                            <AlertCircle size={20} className="mt-0.5 flex-shrink-0" />
                            <div>
                                <div className="font-semibold text-sm">Errore durante l'invio</div>
                                <div className="text-sm opacity-90">
                                    {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                                    {(createMutation.error as any)?.response?.data?.detail || 'Si è verificato un errore inatteso.'}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center justify-end gap-3 pt-4 border-t border-border">
                        <button
                            type="button"
                            onClick={() => navigate('/leaves')}
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
                                    Invio in corso...
                                </>
                            ) : (
                                <>
                                    <Save size={18} />
                                    Invia Richiesta
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>

            {/* Tailwind Utility Helper Styles for this form - inline for simplicity in this artifact */}
            <style>{`
        .grid { display: grid; }
        .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
        .gap-3 { gap: 0.75rem; }
        .gap-6 { gap: 1.5rem; }
        .mb-1 { margin-bottom: 0.25rem; }
        .mb-2 { margin-bottom: 0.5rem; }
        .mb-6 { margin-bottom: 1.5rem; }
        .mt-1 { margin-top: 0.25rem; }
        .mt-2 { margin-top: 0.5rem; }
        .mt-0.5 { margin-top: 0.125rem; }
        .p-3 { padding: 0.75rem; }
        .p-4 { padding: 1rem; }
        .pt-4 { padding-top: 1rem; }
        .pl-10 { padding-left: 2.5rem; }
        .w-full { width: 100%; }
        .w-3 { width: 0.75rem; }
        .h-3 { height: 0.75rem; }
        .h-10 { height: 2.5rem; }
        .rounded-lg { border-radius: var(--radius-lg); }
        .rounded-full { border-radius: 9999px; }
        .border { border-width: 1px; }
        .border-t { border-top-width: 1px; }
        .border-border { border-color: var(--color-border); }
        .border-primary { border-color: var(--color-primary); }
        .bg-primary\\/5 { background-color: rgba(var(--color-primary-rgb), 0.05); }
        .bg-danger\\/10 { background-color: rgba(239, 68, 68, 0.1); }
        .bg-bg-tertiary { background-color: var(--color-bg-tertiary); }
        .text-sm { font-size: var(--font-size-sm); }
        .text-xs { font-size: var(--font-size-xs); }
        .text-2xl { font-size: var(--font-size-2xl); }
        .text-secondary { color: var(--color-text-secondary); }
        .text-danger { color: var(--color-danger); }
        .text-primary { color: var(--color-primary); }
        .font-bold { font-weight: 700; }
        .font-semibold { font-weight: 600; }
        .font-medium { font-weight: 500; }
        .font-mono { font-family: var(--font-family-mono); }
        .block { display: block; }
        .hidden { display: none; }
        .flex { display: flex; }
        .items-center { align-items: center; }
        .items-start { align-items: flex-start; }
        .justify-end { justify-content: flex-end; }
        .flex-shrink-0 { flex-shrink: 0; }
        .relative { position: relative; }
        .absolute { position: absolute; }
        .left-3 { left: 0.75rem; }
        .top-1\\/2 { top: 50%; }
        .-translate-y-1\\/2 { transform: translateY(-50%); }
        .cursor-pointer { cursor: pointer; }
        .resize-y { resize: vertical; }
        .space-y-6 > * + * { margin-top: 1.5rem; }
        
        @media (min-width: 640px) {
          .sm\\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        @media (min-width: 768px) {
          .md\\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
      `}</style>
        </div>
    );
}

export default LeaveRequestForm;
