import { useState, useEffect } from 'react';
import { Laptop, Plus, Calendar, X, Save, AlertCircle, Check, Trash2, Edit, AlertTriangle } from 'lucide-react';
import { smartWorkingService, type SWAgreement } from '../../services/smartWorking.service';
import { useToast } from '../../context/ToastContext';
import { SignatureModal } from '../shared/SignatureModal';

interface SmartWorkingAgreementsProps {
    userId: string;
    userName?: string;
}

type AgreementFormData = {
    start_date: string;
    end_date: string | null;
    allowed_days_per_week: number;
    allowed_weekdays: number[];
    notes: string;
};

const WEEKDAY_NAMES: Record<number, string> = {
    0: 'Lunedì',
    1: 'Martedì',
    2: 'Mercoledì',
    3: 'Giovedì',
    4: 'Venerdì',
};

const defaultFormData: AgreementFormData = {
    start_date: new Date().toISOString().split('T')[0],
    end_date: null,
    allowed_days_per_week: 2,
    allowed_weekdays: [],
    notes: '',
};

export function SmartWorkingAgreements({ userId, userName }: SmartWorkingAgreementsProps) {
    const toast = useToast();
    const [agreements, setAgreements] = useState<SWAgreement[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [formData, setFormData] = useState<AgreementFormData>(defaultFormData);
    const [signingAgreement, setSigningAgreement] = useState<SWAgreement | null>(null);


    // Check if there's an active agreement (for warning)
    const hasActiveAgreement = agreements.some(a => a.status === 'ACTIVE');

    useEffect(() => {
        loadData();
    }, [userId]);

    const loadData = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await smartWorkingService.getUserAgreements(userId);
            setAgreements(data);
        } catch (err: unknown) {
            console.error('Error loading SW agreements:', err);
            setError('Errore nel caricamento degli accordi Smart Working');
        } finally {
            setIsLoading(false);
        }
    };

    const resetForm = () => {
        setFormData(defaultFormData);
        setEditingId(null);
        setIsAdding(false);
    };

    // Handle weekday toggle
    const toggleWeekday = (day: number) => {
        const newWeekdays = formData.allowed_weekdays.includes(day)
            ? formData.allowed_weekdays.filter(d => d !== day)
            : [...formData.allowed_weekdays, day].slice(0, formData.allowed_days_per_week);
        setFormData({ ...formData, allowed_weekdays: newWeekdays.sort((a, b) => a - b) });
    };

    // When days_per_week changes, trim weekdays if needed
    const handleDaysPerWeekChange = (days: number) => {
        const trimmedWeekdays = formData.allowed_weekdays.slice(0, days);
        setFormData({
            ...formData,
            allowed_days_per_week: days,
            allowed_weekdays: trimmedWeekdays
        });
    };

    const handleSave = async () => {
        // Validation
        if (!formData.start_date || formData.allowed_days_per_week < 1) {
            setError('Data inizio e giorni settimana obbligatori');
            return;
        }

        if (formData.allowed_weekdays.length !== formData.allowed_days_per_week) {
            setError(`Seleziona esattamente ${formData.allowed_days_per_week} giorni della settimana`);
            return;
        }

        try {
            const payload = {
                user_id: userId,
                start_date: formData.start_date,
                end_date: formData.end_date || null,
                allowed_days_per_week: formData.allowed_days_per_week,
                allowed_weekdays: formData.allowed_weekdays,
                notes: formData.notes || null,
            };

            if (editingId) {
                await smartWorkingService.updateAgreement(editingId, payload);
                toast.success('Accordo aggiornato');
            } else {
                await smartWorkingService.createAgreement(payload);
                toast.success(hasActiveAgreement
                    ? 'Accordo creato. L\'accordo precedente è stato archiviato.'
                    : 'Accordo creato'
                );
            }
            resetForm();
            loadData();
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Errore durante il salvataggio';
            setError(message);
            toast.error(message);
        }
    };

    const handleEdit = (agreement: SWAgreement) => {
        setEditingId(agreement.id);
        setFormData({
            start_date: agreement.start_date.split('T')[0],
            end_date: agreement.end_date?.split('T')[0] || null,
            allowed_days_per_week: agreement.allowed_days_per_week,
            allowed_weekdays: agreement.allowed_weekdays || [],
            notes: agreement.notes || '',
        });
        setIsAdding(true);
    };

    const handleTerminate = async (id: string) => {
        if (!window.confirm('Sei sicuro di voler terminare questo accordo?')) return;
        try {
            await smartWorkingService.terminateAgreement(id);
            toast.success('Accordo terminato');
            loadData();
        } catch (err: unknown) {
            toast.error('Errore durante la terminazione');
            console.error(err);
        }
    };

    const formatDate = (dateStr: string | null | undefined) => {
        if (!dateStr) return '-';
        try {
            return new Date(dateStr).toLocaleDateString('it-IT', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
            });
        } catch {
            return dateStr;
        }
    };

    const getStatusBadge = (status: SWAgreement['status']) => {
        const styles: Record<SWAgreement['status'], string> = {
            ACTIVE: 'bg-green-100 text-green-700',
            PENDING: 'bg-amber-100 text-amber-700',
            EXPIRED: 'bg-gray-100 text-gray-500',
            TERMINATED: 'bg-red-100 text-red-600',
            DRAFT: 'bg-yellow-100 text-yellow-700',
        };
        const labels: Record<SWAgreement['status'], string> = {
            ACTIVE: 'Attivo',
            PENDING: 'In Attesa di Firma',
            EXPIRED: 'Scaduto',
            TERMINATED: 'Terminato',
            DRAFT: 'Bozza',
        };
        return (
            <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${styles[status]} flex items-center gap-1`}>
                {status === 'ACTIVE' && <Check size={10} />}
                {labels[status]}
            </span>
        );
    };

    const handleSign = async (otp: string) => {
        if (!signingAgreement) return;
        try {
            await smartWorkingService.signAgreement(signingAgreement.id, otp);
            toast.success('Accordo firmato e attivato con successo');
            setSigningAgreement(null);
            loadData();
        } catch (err: unknown) {
            throw err;
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-lg shadow-teal-200">
                        <Laptop size={20} />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-gray-900">Accordi Smart Working</h3>
                        <p className="text-xs text-gray-500">Gestione lavoro agile per {userName || 'questo dipendente'}</p>
                    </div>
                </div>
                {!isAdding && (
                    <button
                        onClick={() => setIsAdding(true)}
                        className="btn btn-primary btn-sm flex items-center gap-2"
                    >
                        <Plus size={16} /> Nuovo Accordo
                    </button>
                )}
            </div>

            {error && (
                <div className="p-4 bg-red-50 text-red-700 border border-red-100 rounded-xl flex items-center gap-3">
                    <AlertCircle size={18} />
                    <span className="text-sm font-medium">{error}</span>
                    <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">
                        <X size={16} />
                    </button>
                </div>
            )}

            {/* Add/Edit Form */}
            {isAdding && (
                <div className="bg-gray-50 p-5 rounded-xl border border-gray-200 space-y-4 animate-fadeInUp">
                    <div className="flex justify-between items-center">
                        <h3 className="font-bold text-gray-900">
                            {editingId ? 'Modifica Accordo' : 'Nuovo Accordo Smart Working'}
                        </h3>
                        <button onClick={resetForm} className="text-gray-400 hover:text-gray-600">
                            <X size={18} />
                        </button>
                    </div>

                    {/* Warning when active agreement exists */}
                    {!editingId && hasActiveAgreement && (
                        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3">
                            <AlertTriangle size={18} className="text-amber-600 mt-0.5 shrink-0" />
                            <div className="text-sm">
                                <p className="font-bold text-amber-800">Attenzione: Accordo Attivo Esistente</p>
                                <p className="text-amber-700 mt-1">
                                    Creando un nuovo accordo, quello attualmente in vigore verrà automaticamente
                                    <strong> archiviato</strong> (stato: Scaduto) con data fine = giorno precedente alla nuova data inizio.
                                </p>
                            </div>
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-gray-500 uppercase">Data Inizio *</label>
                            <input
                                type="date"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                value={formData.start_date}
                                onChange={e => setFormData({ ...formData, start_date: e.target.value })}
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-gray-500 uppercase">Data Fine</label>
                            <input
                                type="date"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                value={formData.end_date || ''}
                                onChange={e => setFormData({ ...formData, end_date: e.target.value || null })}
                            />
                        </div>
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-xs font-bold text-gray-500 uppercase">Giorni Max / Settimana *</label>
                        <input
                            type="number"
                            min="1"
                            max="5"
                            className="w-24 px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                            value={formData.allowed_days_per_week}
                            onChange={e => handleDaysPerWeekChange(parseInt(e.target.value) || 1)}
                        />
                    </div>

                    {/* Weekday Selection */}
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-gray-500 uppercase">
                            Giorni Permessi * <span className="font-normal text-gray-400">(seleziona {formData.allowed_days_per_week})</span>
                        </label>
                        <div className="flex flex-wrap gap-2">
                            {[0, 1, 2, 3, 4].map(day => {
                                const isSelected = formData.allowed_weekdays.includes(day);
                                const isDisabled = !isSelected && formData.allowed_weekdays.length >= formData.allowed_days_per_week;
                                return (
                                    <button
                                        key={day}
                                        type="button"
                                        onClick={() => toggleWeekday(day)}
                                        disabled={isDisabled}
                                        className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${isSelected
                                            ? 'bg-teal-600 text-white shadow-md'
                                            : isDisabled
                                                ? 'bg-gray-100 text-gray-300 cursor-not-allowed'
                                                : 'bg-white border border-gray-300 text-gray-700 hover:border-teal-500'
                                            }`}
                                    >
                                        {WEEKDAY_NAMES[day]}
                                    </button>
                                );
                            })}
                        </div>
                        {formData.allowed_weekdays.length > 0 && formData.allowed_weekdays.length < formData.allowed_days_per_week && (
                            <p className="text-xs text-amber-600">
                                Seleziona altri {formData.allowed_days_per_week - formData.allowed_weekdays.length} giorn{formData.allowed_days_per_week - formData.allowed_weekdays.length === 1 ? 'o' : 'i'}
                            </p>
                        )}
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-xs font-bold text-gray-500 uppercase">Note</label>
                        <textarea
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm resize-none"
                            rows={2}
                            value={formData.notes}
                            onChange={e => setFormData({ ...formData, notes: e.target.value })}
                            placeholder="Note aggiuntive sull'accordo..."
                        />
                    </div>

                    <div className="flex justify-end gap-3 pt-2">
                        <button onClick={resetForm} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg">
                            Annulla
                        </button>
                        <button onClick={handleSave} className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-bold flex items-center gap-2">
                            <Save size={16} /> Salva
                        </button>
                    </div>
                </div>
            )}

            {/* Agreements List */}
            {isLoading ? (
                <div className="flex flex-col items-center py-12 gap-3">
                    <div className="w-10 h-10 border-4 border-teal-100 border-t-teal-600 rounded-full animate-spin" />
                    <p className="text-sm text-gray-400">Caricamento accordi...</p>
                </div>
            ) : agreements.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
                    <Laptop className="mx-auto text-gray-300 mb-3" size={40} />
                    <p className="text-gray-500 font-medium">Nessun accordo Smart Working</p>
                    <p className="text-sm text-gray-400 mt-1">Crea un accordo per abilitare il lavoro agile</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {agreements.map(agreement => (
                        <div
                            key={agreement.id}
                            className={`bg-white p-4 rounded-xl border shadow-sm transition-all group ${agreement.status === 'PENDING' ? 'border-amber-200 bg-amber-50/30' : 'border-gray-200 hover:border-gray-300'
                                }`}
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex items-start gap-3">
                                    <div className={`p-2.5 rounded-lg ${agreement.status === 'ACTIVE' ? 'bg-teal-100 text-teal-700' : agreement.status === 'PENDING' ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-500'}`}>
                                        <Laptop size={20} />
                                    </div>
                                    <div>
                                        <div className="font-bold text-gray-900 flex items-center gap-2">
                                            Accordo Smart Working
                                            {getStatusBadge(agreement.status)}
                                        </div>
                                        <div className="text-sm text-gray-500 mt-1 flex items-center gap-1">
                                            <Calendar size={12} />
                                            {formatDate(agreement.start_date)}
                                            {agreement.end_date ? ` → ${formatDate(agreement.end_date)}` : ' → In corso'}
                                        </div>
                                        <div className="flex flex-wrap gap-2 mt-2 text-xs">
                                            <span className="px-2 py-1 bg-teal-50 text-teal-700 rounded-full font-medium">
                                                {agreement.allowed_days_per_week} giorni/settimana
                                            </span>
                                            {agreement.allowed_weekdays_names && agreement.allowed_weekdays_names.length > 0 && (
                                                <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded-full">
                                                    {agreement.allowed_weekdays_names.join(', ')}
                                                </span>
                                            )}
                                        </div>
                                        {agreement.notes && (
                                            <div className="text-xs text-gray-400 mt-2 italic">{agreement.notes}</div>
                                        )}

                                        {/* SIGN BUTTON FOR PENDING */}
                                        {agreement.status === 'PENDING' && (
                                            <button
                                                onClick={() => setSigningAgreement(agreement)}
                                                className="mt-3 btn btn-sm bg-teal-600 hover:bg-teal-700 text-white shadow-md shadow-teal-200 animate-pulse"
                                            >
                                                <Edit size={14} className="mr-1.5" />
                                                Firma Digitale Richiesta
                                            </button>
                                        )}
                                    </div>
                                </div>
                                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    {agreement.status === 'ACTIVE' && (
                                        <button
                                            onClick={() => handleEdit(agreement)}
                                            className="p-2 hover:bg-gray-100 rounded-lg text-gray-500"
                                            title="Modifica"
                                        >
                                            <Edit size={16} />
                                        </button>
                                    )}
                                    {(agreement.status === 'ACTIVE' || agreement.status === 'PENDING') && (
                                        <button
                                            onClick={() => handleTerminate(agreement.id)}
                                            className="p-2 hover:bg-red-50 rounded-lg text-red-500"
                                            title="Termina"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <SignatureModal
                isOpen={!!signingAgreement}
                onClose={() => setSigningAgreement(null)}
                onSign={handleSign}
                documentTitle={`Accordo Smart Working - ${signingAgreement ? formatDate(signingAgreement.start_date) : ''}`}
            />
        </div>
    );
}
