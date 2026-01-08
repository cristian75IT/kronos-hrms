import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { X, Save, Loader } from 'lucide-react';
import { useAddExpenseItem } from '../../hooks/domain/useExpenses';
import { useExpenseTypes } from '../../hooks/domain/useConfigs';
import { useToast } from '../../context/ToastContext';

interface ExpenseItemModalProps {
    isOpen: boolean;
    onClose: () => void;
    reportId: string;
}

interface ExpenseItemFormValues {
    expense_type_id: string;
    date: string;
    description: string;
    amount: number;
    merchant_name?: string;
}

export function ExpenseItemModal({ isOpen, onClose, reportId }: ExpenseItemModalProps) {
    const { data: expenseTypes, isLoading: isLoadingTypes } = useExpenseTypes();
    const addMutation = useAddExpenseItem();
    const { success, error: showError } = useToast();

    const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<ExpenseItemFormValues>({
        defaultValues: {
            date: new Date().toISOString().split('T')[0]
        }
    });

    const currentTypeId = watch('expense_type_id');

    useEffect(() => {
        if (!isOpen) {
            reset();
        } else if (expenseTypes && expenseTypes.length > 0 && !currentTypeId) {
            // Set first type as default if none selected
            setValue('expense_type_id', expenseTypes[0].id);
        }
    }, [isOpen, reset, expenseTypes, currentTypeId, setValue]);

    const onSubmit = (data: ExpenseItemFormValues) => {
        addMutation.mutate({
            reportId,
            data: { ...data, amount: Number(data.amount) }
        }, {
            onSuccess: () => {
                success('Voce di spesa aggiunta');
                onClose();
            },
            onError: (err: any) => {
                showError(err.message || 'Errore durante il salvataggio');
            }
        });
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={onClose}>
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center p-4 border-b border-slate-100 bg-slate-50/50">
                    <h3 className="font-bold text-slate-900">Aggiungi Voce di Spesa</h3>
                    <button className="text-slate-400 hover:text-slate-600 p-1 rounded-full hover:bg-slate-100" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <label className="block text-sm font-semibold text-slate-700">Data <span className="text-red-500">*</span></label>
                            <input
                                type="date"
                                {...register('date', { required: 'La data è obbligatoria' })}
                                className="input w-full border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                            />
                            {errors.date && <span className="text-red-500 text-xs">{errors.date.message}</span>}
                        </div>
                        <div className="space-y-1.5">
                            <label className="block text-sm font-semibold text-slate-700">Tipologia <span className="text-red-500">*</span></label>
                            <select
                                {...register('expense_type_id', { required: 'Seleziona una tipologia' })}
                                className="input w-full border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                                disabled={isLoadingTypes}
                            >
                                <option value="">Seleziona...</option>
                                {expenseTypes?.map((t: any) => (
                                    <option key={t.id} value={t.id}>{t.name} ({t.code})</option>
                                ))}
                            </select>
                            {errors.expense_type_id && <span className="text-red-500 text-xs">{errors.expense_type_id.message}</span>}
                        </div>
                    </div>

                    <div className="space-y-1.5">
                        <label className="block text-sm font-semibold text-slate-700">Descrizione <span className="text-red-500">*</span></label>
                        <input
                            type="text"
                            {...register('description', { required: 'La descrizione è obbligatoria' })}
                            className="input w-full border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                            placeholder="Es. Pranzo con cliente"
                        />
                        {errors.description && <span className="text-red-500 text-xs">{errors.description.message}</span>}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <label className="block text-sm font-semibold text-slate-700">Importo (€) <span className="text-red-500">*</span></label>
                            <input
                                type="number"
                                step="0.01"
                                {...register('amount', {
                                    required: 'L\'importo è obbligatorio',
                                    min: { value: 0.01, message: 'L\'importo deve essere maggiore di 0' }
                                })}
                                className="input w-full border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                                placeholder="0.00"
                            />
                            {errors.amount && <span className="text-red-500 text-xs">{errors.amount.message}</span>}
                        </div>
                        <div className="space-y-1.5">
                            <label className="block text-sm font-semibold text-slate-700">Esercente (Opzionale)</label>
                            <input
                                type="text"
                                {...register('merchant_name')}
                                className="input w-full border-slate-300 focus:border-emerald-500 focus:ring-emerald-500"
                                placeholder="Es. Ristorante Da Mario"
                            />
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                        <button
                            type="button"
                            className="btn btn-ghost text-slate-600 hover:bg-slate-100"
                            onClick={onClose}
                        >
                            Annulla
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary bg-slate-900 hover:bg-slate-800 text-white border-none"
                            disabled={addMutation.isPending}
                        >
                            {addMutation.isPending ? <Loader size={18} className="animate-spin mr-2" /> : <Save size={18} className="mr-2" />}
                            Salva Voce
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
