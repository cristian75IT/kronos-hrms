import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Modal, Button } from '../common';
import { useToast } from '../../context/ToastContext';
import { calendarService, type UserCalendar } from '../../services/calendar.service';
import { format } from 'date-fns';
import {
    Calendar,
    Clock,
    AlignLeft,
    Tag,
    Users,
    Bell,
    Palette,
    CheckCircle2,
    AlertCircle,
    CalendarPlus,
    MapPin,
    Video,
    Link as LinkIcon,
    Repeat
} from 'lucide-react';

interface NewEventModalProps {
    isOpen: boolean;
    onClose: () => void;
    onEventCreated: () => void;
    selectedDate?: string | null;
    userCalendars: UserCalendar[];
}

interface EventFormData {
    title: string;
    description?: string;
    start_date: string;
    end_date: string;
    start_time?: string;
    end_time?: string;
    is_all_day: boolean;
    event_type: string;
    visibility: string;
    calendar_id?: string;
    color: string;
    alert_before_minutes?: number;
    location?: string;
    is_virtual: boolean;
    meeting_url?: string;
    participant_ids?: string[];
    is_recurring: boolean;
    recurrence_rule?: string;
}

export function NewEventModal({ isOpen, onClose, onEventCreated, selectedDate, userCalendars }: NewEventModalProps) {
    const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<EventFormData>({
        defaultValues: {
            is_all_day: true,
            visibility: 'private',
            event_type: 'meeting',
            color: '#4F46E5',
            is_virtual: false,
            is_recurring: false,
        }
    });
    const [loading, setLoading] = useState(false);
    const toast = useToast();

    const isAllDay = watch('is_all_day');
    const isVirtual = watch('is_virtual');
    const isRecurring = watch('is_recurring');
    const selectedColor = watch('color');

    useEffect(() => {
        if (isOpen) {
            reset({
                is_all_day: true,
                visibility: 'private',
                event_type: 'meeting',
                color: '#4F46E5',
                is_virtual: false,
                is_recurring: false,
                start_date: selectedDate || format(new Date(), 'yyyy-MM-dd'),
                end_date: selectedDate || format(new Date(), 'yyyy-MM-dd'),
                start_time: '09:00',
                end_time: '10:00',
                alert_before_minutes: 2880,
            });
        }
    }, [isOpen, selectedDate, reset]);

    const onSubmit = async (data: EventFormData) => {
        setLoading(true);
        try {
            const payload = {
                ...data,
                start_time: data.is_all_day ? undefined : data.start_time,
                end_time: data.is_all_day ? undefined : data.end_time,
                calendar_id: data.calendar_id || undefined,
                meeting_url: data.is_virtual ? data.meeting_url : undefined,
                alert_before_minutes: data.alert_before_minutes ? Number(data.alert_before_minutes) : null,
                participant_ids: data.participant_ids?.filter(id => id) || undefined,
                is_recurring: data.is_recurring,
                recurrence_rule: data.is_recurring ? data.recurrence_rule : undefined,
            };

            await calendarService.createEvent(payload);
            toast.success('Impegno creato con successo');
            onEventCreated();
            onClose();
        } catch (error) {
            console.error(error);
            toast.error('Errore durante il salvataggio');
        } finally {
            setLoading(false);
        }
    };

    const InputLabel = ({ label, required, error, icon: Icon }: any) => (
        <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
            {Icon && <Icon size={16} className="text-slate-400" />}
            <span>
                {label} {required && <span className="text-indigo-600 ml-0.5">*</span>}
            </span>
            {error && <span className="text-red-500 text-xs font-normal ml-auto">{error.message}</span>}
        </label>
    );

    const inputClasses = (error: any) => `
        block w-full rounded-lg border-slate-200 bg-white shadow-sm
        focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 focus:outline-none
        transition-all duration-200 sm:text-sm py-2.5 px-3
        placeholder:text-slate-400
        ${error ? 'border-red-300 bg-red-50/10 focus:border-red-500 focus:ring-red-200' : 'hover:border-slate-300'}
    `;

    const colorOptions = [
        { value: '#4F46E5', name: 'Indigo' },
        { value: '#10B981', name: 'Verde' },
        { value: '#F59E0B', name: 'Ambra' },
        { value: '#EF4444', name: 'Rosso' },
        { value: '#EC4899', name: 'Rosa' },
        { value: '#8B5CF6', name: 'Viola' },
        { value: '#06B6D4', name: 'Ciano' },
        { value: '#64748B', name: 'Grigio' },
    ];

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Nuovo Impegno" size="3xl">
            <div className="space-y-8 pb-4">

                {/* Enterprise Header */}
                <div className="relative overflow-hidden rounded-2xl border border-white/40 bg-gradient-to-br from-indigo-50/80 to-white p-6 shadow-sm backdrop-blur-md">
                    <div className="flex items-start gap-5">
                        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-100/80 text-indigo-700 shadow-inner">
                            <CalendarPlus size={28} strokeWidth={1.5} />
                        </div>
                        <div className="space-y-1">
                            <h3 className="text-lg font-bold text-slate-900 tracking-tight">Crea Nuovo Impegno</h3>
                            <p className="text-sm text-slate-500 leading-relaxed max-w-lg">
                                Pianifica un nuovo appuntamento, riunione o promemoria.
                                Gli impegni saranno visibili nel tuo calendario personale.
                            </p>
                        </div>
                    </div>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">

                    {/* Main Content Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                        {/* Left Column: Core Info */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                                <AlignLeft className="text-indigo-500" size={18} />
                                <h4 className="font-semibold text-slate-800">Informazioni Principali</h4>
                            </div>

                            <div className="space-y-5">
                                <div className="space-y-1">
                                    <InputLabel label="Titolo" required error={errors.title} />
                                    <input
                                        type="text"
                                        placeholder="Es: Riunione con il team"
                                        {...register('title', { required: 'Il titolo è obbligatorio' })}
                                        className={inputClasses(errors.title)}
                                    />
                                </div>

                                <div className="space-y-1">
                                    <InputLabel label="Descrizione" icon={AlignLeft} />
                                    <textarea
                                        rows={3}
                                        placeholder="Aggiungi dettagli sull'impegno..."
                                        {...register('description')}
                                        className={inputClasses(null)}
                                    />
                                </div>

                                <div className="space-y-1">
                                    <InputLabel label="Tipologia" icon={Tag} />
                                    <select
                                        {...register('event_type')}
                                        className={inputClasses(null)}
                                    >
                                        <option value="meeting">📅 Riunione</option>
                                        <option value="task">✅ Attività</option>
                                        <option value="reminder">🔔 Promemoria</option>
                                        <option value="personal">👤 Personale</option>
                                        <option value="deadline">⏰ Scadenza</option>
                                        <option value="other">📌 Altro</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Right Column: Date & Time */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                                <Calendar className="text-indigo-500" size={18} />
                                <h4 className="font-semibold text-slate-800">Data e Orario</h4>
                            </div>

                            <div className="space-y-5">
                                {/* All Day Toggle */}
                                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
                                    <div className="flex items-center gap-2">
                                        <Clock className="text-slate-400" size={18} />
                                        <span className="text-sm font-medium text-slate-700">Tutto il giorno</span>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            {...register('is_all_day')}
                                            className="sr-only peer"
                                        />
                                        <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                                    </label>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1">
                                        <InputLabel label="Data Inizio" required error={errors.start_date} icon={Calendar} />
                                        <input
                                            type="date"
                                            {...register('start_date', { required: 'Data richiesta' })}
                                            className={inputClasses(errors.start_date)}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <InputLabel label="Data Fine" required error={errors.end_date} icon={Calendar} />
                                        <input
                                            type="date"
                                            {...register('end_date', { required: 'Data richiesta' })}
                                            className={inputClasses(errors.end_date)}
                                        />
                                    </div>
                                </div>

                                {/* Time Fields - Only shown when not all day */}
                                {!isAllDay && (
                                    <div className="grid grid-cols-2 gap-4 animate-fadeIn">
                                        <div className="space-y-1">
                                            <InputLabel label="Ora Inizio" icon={Clock} />
                                            <input
                                                type="time"
                                                {...register('start_time')}
                                                className={inputClasses(null)}
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <InputLabel label="Ora Fine" icon={Clock} />
                                            <input
                                                type="time"
                                                {...register('end_time')}
                                                className={inputClasses(null)}
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Full Width: Location & Settings Section */}
                    <div className="bg-slate-50 rounded-xl p-6 border border-slate-100 space-y-6">
                        <div className="flex items-center gap-2 pb-2 border-b border-slate-200/60">
                            <MapPin className="text-emerald-500" size={18} />
                            <h4 className="font-semibold text-slate-800">Luogo & Impostazioni</h4>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {/* Virtual Toggle */}
                            <div className="space-y-1">
                                <InputLabel label="Evento Virtuale" icon={Video} />
                                <div className="flex items-center gap-3 p-2.5 bg-white rounded-lg border border-slate-200">
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            {...register('is_virtual')}
                                            className="sr-only peer"
                                        />
                                        <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                                    </label>
                                    <span className="text-sm text-slate-600">{isVirtual ? 'Sì' : 'No'}</span>
                                </div>
                            </div>

                            {isVirtual ? (
                                <div className="space-y-1 md:col-span-2">
                                    <InputLabel label="Link Riunione" icon={LinkIcon} />
                                    <input
                                        type="url"
                                        placeholder="https://meet.google.com/..."
                                        {...register('meeting_url')}
                                        className={inputClasses(null)}
                                    />
                                </div>
                            ) : (
                                <div className="space-y-1 md:col-span-2">
                                    <InputLabel label="Luogo" icon={MapPin} />
                                    <input
                                        type="text"
                                        placeholder="Es: Sala Riunioni A"
                                        {...register('location')}
                                        className={inputClasses(null)}
                                    />
                                </div>
                            )}

                            <div className="space-y-1">
                                <InputLabel label="Calendario" icon={Calendar} />
                                <select
                                    {...register('calendar_id')}
                                    className={inputClasses(null)}
                                >
                                    <option value="">Calendario Predefinito</option>
                                    {userCalendars.map(cal => (
                                        <option key={cal.id} value={cal.id}>{cal.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="space-y-1">
                                <InputLabel label="Visibilità" icon={Users} />
                                <select
                                    {...register('visibility')}
                                    className={inputClasses(null)}
                                >
                                    <option value="private">🔒 Solo io</option>
                                    <option value="department">🏢 Il mio Dipartimento</option>
                                    <option value="service">🔧 Il mio Servizio</option>
                                    <option value="public">🌐 Tutti</option>
                                </select>
                            </div>

                            <div className="space-y-1">
                                <InputLabel label="Promemoria" icon={Bell} />
                                <select
                                    {...register('alert_before_minutes')}
                                    className={inputClasses(null)}
                                >
                                    <option value="">Nessun promemoria</option>
                                    <option value="15">15 minuti prima</option>
                                    <option value="30">30 minuti prima</option>
                                    <option value="60">1 ora prima</option>
                                    <option value="120">2 ore prima</option>
                                    <option value="1440">1 giorno prima</option>
                                    <option value="2880">2 giorni prima</option>
                                    <option value="10080">1 settimana prima</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Recurrence Section */}
                    <div className="bg-amber-50/50 rounded-xl p-6 border border-amber-100 space-y-4">
                        <div className="flex items-center gap-2 pb-2 border-b border-amber-200/60">
                            <Repeat className="text-amber-500" size={18} />
                            <h4 className="font-semibold text-slate-800">Ricorrenza</h4>
                        </div>

                        <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-slate-200">
                            <div className="flex items-center gap-2">
                                <Repeat className="text-slate-400" size={18} />
                                <span className="text-sm font-medium text-slate-700">Evento ricorrente</span>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    {...register('is_recurring')}
                                    className="sr-only peer"
                                />
                                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-amber-300/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
                            </label>
                        </div>

                        {isRecurring && (
                            <div className="space-y-1 animate-fadeIn">
                                <InputLabel label="Frequenza" icon={Repeat} />
                                <select
                                    {...register('recurrence_rule')}
                                    className={inputClasses(null)}
                                >
                                    <option value="FREQ=DAILY">Ogni giorno</option>
                                    <option value="FREQ=WEEKLY">Ogni settimana</option>
                                    <option value="FREQ=BIWEEKLY">Ogni 2 settimane</option>
                                    <option value="FREQ=MONTHLY">Ogni mese</option>
                                    <option value="FREQ=YEARLY">Ogni anno</option>
                                </select>
                            </div>
                        )}
                    </div>

                    {/* Participants Section (Placeholder - requires useUsers hook) */}
                    {/* 
                    <div className="bg-violet-50/50 rounded-xl p-6 border border-violet-100 space-y-4">
                        <div className="flex items-center gap-2 pb-2 border-b border-violet-200/60">
                            <UserPlus className="text-violet-500" size={18} />
                            <h4 className="font-semibold text-slate-800">Partecipanti</h4>
                        </div>
                        <p className="text-sm text-slate-500">
                            Seleziona gli utenti da invitare all'evento.
                        </p>
                    </div>
                    */}

                    {/* Color Picker Section */}
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <Palette className="text-slate-400" size={18} />
                            <span className="text-sm font-semibold text-slate-700">Colore Evento</span>
                        </div>
                        <div className="flex flex-wrap gap-3">
                            {colorOptions.map(({ value, name }) => (
                                <label key={value} className="relative cursor-pointer group">
                                    <input
                                        type="radio"
                                        value={value}
                                        {...register('color')}
                                        className="sr-only peer"
                                    />
                                    <div
                                        className={`
                                            w-10 h-10 rounded-xl shadow-sm transition-all duration-200
                                            group-hover:scale-110 group-hover:shadow-md
                                            ${selectedColor === value ? 'ring-2 ring-offset-2 ring-slate-400 scale-110' : ''}
                                        `}
                                        style={{ backgroundColor: value }}
                                        title={name}
                                    />
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-6 border-t border-slate-100">
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                            <AlertCircle size={14} />
                            <span>I campi con <span className="text-indigo-600 font-bold">*</span> sono obbligatori</span>
                        </div>

                        <div className="flex w-full sm:w-auto gap-3">
                            <Button variant="outline" type="button" onClick={onClose} disabled={loading} className="flex-1 sm:flex-none justify-center">
                                Annulla
                            </Button>
                            <Button
                                variant="primary"
                                type="submit"
                                disabled={loading}
                                className="flex-1 sm:flex-none justify-center min-w-[160px] shadow-lg shadow-indigo-500/20"
                            >
                                {loading ? (
                                    <><span className="loading loading-spinner loading-xs mr-2"></span> Creazione...</>
                                ) : (
                                    <><CheckCircle2 size={18} className="mr-2" /> Crea Impegno</>
                                )}
                            </Button>
                        </div>
                    </div>
                </form>
            </div>
        </Modal>
    );
}
