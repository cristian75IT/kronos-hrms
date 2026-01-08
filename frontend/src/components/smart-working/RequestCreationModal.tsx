import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useToast } from '../../context/ToastContext';
import { Modal } from '../../components/common/Modal';
import { Button } from '../../components/common/Button';
import { smartWorkingService } from '../../services/smartWorking.service';
import type { SWAgreement } from '../../services/smartWorking.service';

// Zod validation schema
const requestSchema = z.object({
    notes: z.string().optional(),
});

type FormData = z.infer<typeof requestSchema>;

interface RequestCreationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    selectedDate: Date | null;
    activeAgreement: SWAgreement | undefined;
}

export const RequestCreationModal: React.FC<RequestCreationModalProps> = ({
    isOpen,
    onClose,
    onSuccess,
    selectedDate,
    activeAgreement
}) => {
    const toast = useToast();
    const { register, handleSubmit, reset } = useForm<FormData>({
        resolver: zodResolver(requestSchema)
    });
    const [loading, setLoading] = useState(false);

    const onSubmit = async (data: FormData) => {
        if (!selectedDate || !activeAgreement) return;
        setLoading(true);
        try {
            // Format date as YYYY-MM-DD
            const dateStr = selectedDate.toISOString().split('T')[0];

            await smartWorkingService.submitRequest({
                agreement_id: activeAgreement.id,
                date: dateStr,
                notes: data.notes
            });
            toast.success('Richiesta inviata con successo');
            reset();
            onSuccess();
            onClose();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } };
            const msg = err.response?.data?.detail || 'Errore nell\'invio della richiesta';
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    if (!selectedDate) return null;

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={`Richiesta Smart Working: ${selectedDate.toLocaleDateString('it-IT')}`} size="sm">
            {!activeAgreement ? (
                <div className="text-center py-4">
                    <p className="text-red-500 font-medium">Nessun accordo attivo trovato.</p>
                    <p className="text-sm text-gray-500 mt-2">Devi avere un accordo attivo per inserire richieste.</p>
                    <div className="mt-4 flex justify-center">
                        <Button variant="secondary" onClick={onClose}>Chiudi</Button>
                    </div>
                </div>
            ) : (
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Note (Opzionale)</label>
                        <textarea
                            {...register('notes')}
                            rows={3}
                            className="w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                            placeholder="Es. Lavoro su progetto X"
                        />
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                        <Button variant="secondary" onClick={onClose} type="button">Annulla</Button>
                        <Button variant="primary" type="submit" disabled={loading}>
                            {loading ? 'Invio...' : 'Invia Richiesta'}
                        </Button>
                    </div>
                </form>
            )}
        </Modal>
    );
};
