import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useToast } from '../../context/ToastContext';
import { Modal } from '../../components/common/Modal';
import { Button } from '../../components/common/Button';
import { smartWorkingService } from '../../services/smartWorking.service';
import { useAuth } from '../../context/AuthContext';

// Zod validation schema
const agreementSchema = z.object({
    start_date: z.string().min(1, 'Data inizio obbligatoria'),
    end_date: z.string().optional(),
    allowed_days_per_week: z.number().min(1, 'Minimo 1 giorno').max(5, 'Massimo 5 giorni'),
    notes: z.string().optional(),
});

type FormData = z.infer<typeof agreementSchema>;

interface AgreementRequestModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export const AgreementRequestModal: React.FC<AgreementRequestModalProps> = ({ isOpen, onClose, onSuccess }) => {
    const { user } = useAuth();
    const toast = useToast();
    const { register, handleSubmit, formState: { errors }, reset } = useForm<FormData>({
        resolver: zodResolver(agreementSchema),
        defaultValues: {
            allowed_days_per_week: 2
        }
    });
    const [loading, setLoading] = useState(false);

    const onSubmit = async (data: FormData) => {
        if (!user) return;
        setLoading(true);
        try {
            await smartWorkingService.createAgreement({
                user_id: user.id,
                start_date: data.start_date,
                end_date: data.end_date || null,
                allowed_days_per_week: data.allowed_days_per_week,
                notes: data.notes
            });
            toast.success('Accordo creato con successo');
            reset();
            onSuccess();
            onClose();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } };
            const msg = err.response?.data?.detail || 'Errore nella creazione dell\'accordo';
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Nuovo Accordo Smart Working" size="md">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Data Inizio <span className="text-red-500">*</span>
                    </label>
                    <input
                        type="date"
                        {...register('start_date')}
                        className="w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                    />
                    {errors.start_date && <span className="text-xs text-red-500">{errors.start_date.message}</span>}
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Data Fine (Opzionale)
                    </label>
                    <input
                        type="date"
                        {...register('end_date')}
                        className="w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Giorni a Settimana (Max 5) <span className="text-red-500">*</span>
                    </label>
                    <select
                        {...register('allowed_days_per_week')}
                        className="w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                    >
                        {[1, 2, 3, 4, 5].map(n => (
                            <option key={n} value={n}>{n} {n === 1 ? 'giorno' : 'giorni'}</option>
                        ))}
                    </select>
                    {errors.allowed_days_per_week && <span className="text-xs text-red-500">{errors.allowed_days_per_week.message}</span>}
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Note</label>
                    <textarea
                        {...register('notes')}
                        rows={3}
                        className="w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                        placeholder="Es. Richiesta standard"
                    />
                </div>

                <div className="flex justify-end gap-3 pt-4">
                    <Button variant="secondary" onClick={onClose} type="button">Annulla</Button>
                    <Button variant="primary" type="submit" disabled={loading}>
                        {loading ? 'Salvataggio...' : 'Crea Accordo'}
                    </Button>
                </div>
            </form>
        </Modal>
    );
};
