import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Modal, Button } from '../common';
import { useToast } from '../../context/ToastContext';
import { calendarService, type CalendarEvent, type UserCalendar } from '../../services/calendar.service';
import { format } from 'date-fns';
import {
    Calendar,
    Clock,
    AlignLeft,
    Tag,
    Users,
    Palette,
    AlertCircle,
    Edit3,
    Trash2,
    MapPin,
    Video,
    Eye,
    Save
} from 'lucide-react';

interface EventFormData {
    title: string;
    description: string;
    start_date: string;
    end_date: string;
    start_time: string;
    end_time: string;
    is_all_day: boolean;
    event_type: string;
    visibility: string;
    calendar_id: string;
    color: string;
    alert_before_minutes: number;
    location: string;
    is_virtual: boolean;
    meeting_url: string;
}

interface EventDetailModalProps {
    isOpen: boolean;
    onClose: () => void;
    event: CalendarEvent | null;
    onEventUpdated: () => void;
    onEventDeleted: () => void;
    userCalendars: UserCalendar[];
    currentUserId?: string;
    initialIsEditing?: boolean;
}

export function EventDetailModal({
    isOpen,
    onClose,
    event,
    onEventUpdated,
    onEventDeleted,
    userCalendars,
    currentUserId,
    initialIsEditing = false
}: EventDetailModalProps) {
    const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<EventFormData>();
    const [loading, setLoading] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const toast = useToast();

    const isAllDay = watch('is_all_day');
    const selectedColor = watch('color');

    // Check if current user can edit/delete this event
    const canModify = event?.user_id === currentUserId || event?.created_by === currentUserId;

    useEffect(() => {
        if (isOpen && event) {
            reset({
                title: event.title,
                description: event.description || '',
                start_date: event.start_date,
                end_date: event.end_date,
                start_time: event.start_time || '09:00',
                end_time: event.end_time || '10:00',
                is_all_day: event.is_all_day,
                event_type: event.event_type || 'meeting',
                visibility: event.visibility || 'private',
                calendar_id: event.calendar_id || '',
                color: event.color || '#4F46E5',
                alert_before_minutes: event.alert_before_minutes || 2880,
                location: event.location || '',
                is_virtual: event.is_virtual || false,
                meeting_url: event.meeting_url || '',
            });
            setIsEditing(initialIsEditing && canModify);
            setShowDeleteConfirm(false);
        }
    }, [isOpen, event, reset, initialIsEditing, canModify]);

    const onSubmit = async (data: EventFormData) => {
        if (!event) return;
        setLoading(true);
        try {
            const payload = {
                ...data,
                start_time: data.is_all_day ? undefined : data.start_time,
                end_time: data.is_all_day ? undefined : data.end_time,
                calendar_id: data.calendar_id || undefined,
                meeting_url: data.is_virtual ? data.meeting_url : undefined,
                alert_before_minutes: data.alert_before_minutes ? Number(data.alert_before_minutes) : undefined,
                visibility: data.visibility as 'private' | 'team' | 'public',
            };

            await calendarService.updateEvent(event.id, payload);
            toast.success('Impegno aggiornato con successo');
            onEventUpdated();
            onClose();
        } catch (error) {
            console.error(error);
            toast.error('Errore durante il salvataggio');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!event) return;
        setLoading(true);
        try {
            await calendarService.deleteEvent(event.id);
            toast.success('Impegno eliminato');
            onEventDeleted();
            onClose();
        } catch (error) {
            console.error(error);
            toast.error('Errore durante l\'eliminazione');
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

    const inputClasses = (error: any, disabled?: boolean) => `
        block w-full rounded-lg border-slate-200 bg-white shadow-sm
        focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 focus:outline-none
        transition-all duration-200 sm:text-sm py-2.5 px-3
        placeholder:text-slate-400
        ${error ? 'border-red-300 bg-red-50/10 focus:border-red-500 focus:ring-red-200' : 'hover:border-slate-300'}
        ${disabled ? 'bg-slate-50 cursor-not-allowed' : ''}
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

    if (!event) return null;

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={isEditing ? "Modifica Impegno" : "Dettagli Impegno"} size="3xl">
            <div className="space-y-6 pb-4">

                {/* Header with Event Color */}
                <div className="relative overflow-hidden rounded-2xl border border-white/40 p-6 shadow-sm backdrop-blur-md" style={{ background: `linear-gradient(135deg, ${event.color}15, white)` }}>
                    <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-4">
                            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl shadow-inner" style={{ backgroundColor: `${event.color}20`, color: event.color }}>
                                <Calendar size={28} strokeWidth={1.5} />
                            </div>
                            <div className="space-y-1">
                                <h3 className="text-lg font-bold text-slate-900 tracking-tight">{event.title}</h3>
                                <div className="flex items-center gap-3 text-sm text-slate-500">
                                    <span className="flex items-center gap-1">
                                        <Clock size={14} />
                                        {format(new Date(event.start_date), 'dd/MM/yyyy')}
                                        {event.end_date !== event.start_date && ` - ${format(new Date(event.end_date), 'dd/MM/yyyy')}`}
                                    </span>
                                    {!event.is_all_day && event.start_time && (
                                        <span className="flex items-center gap-1">
                                            {event.start_time} - {event.end_time}
                                        </span>
                                    )}
                                    {event.is_all_day && (
                                        <span className="px-2 py-0.5 bg-slate-100 rounded text-xs">Tutto il giorno</span>
                                    )}
                                </div>
                            </div>
                        </div>
                        {canModify && (
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setIsEditing(!isEditing)}
                                    className={`p-2 rounded-lg transition-colors ${isEditing ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                                    title={isEditing ? "Annulla modifica" : "Modifica"}
                                >
                                    {isEditing ? <Eye size={18} /> : <Edit3 size={18} />}
                                </button>
                                <button
                                    onClick={() => setShowDeleteConfirm(true)}
                                    className="p-2 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                                    title="Elimina"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Delete Confirmation */}
                {showDeleteConfirm && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <AlertCircle className="text-red-500" size={20} />
                            <span className="text-sm font-medium text-red-800">Sei sicuro di voler eliminare questo impegno?</span>
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={() => setShowDeleteConfirm(false)}>Annulla</Button>
                            <Button variant="primary" size="sm" onClick={handleDelete} disabled={loading} className="bg-red-600 hover:bg-red-700">
                                {loading ? 'Eliminazione...' : 'Elimina'}
                            </Button>
                        </div>
                    </div>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    {/* View Mode / Edit Mode */}
                    {!isEditing ? (
                        /* View Mode */
                        <div className="space-y-4">
                            {event.description && (
                                <div className="p-4 bg-slate-50 rounded-xl">
                                    <h4 className="text-xs font-bold text-slate-500 uppercase mb-2 flex items-center gap-2">
                                        <AlignLeft size={14} /> Descrizione
                                    </h4>
                                    <p className="text-sm text-slate-700">{event.description}</p>
                                </div>
                            )}

                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                {event.location && (
                                    <div className="p-3 bg-slate-50 rounded-lg">
                                        <span className="text-xs text-slate-500 flex items-center gap-1 mb-1"><MapPin size={12} /> Luogo</span>
                                        <span className="text-sm font-medium text-slate-700">{event.location}</span>
                                    </div>
                                )}
                                {event.is_virtual && event.meeting_url && (
                                    <div className="p-3 bg-slate-50 rounded-lg">
                                        <span className="text-xs text-slate-500 flex items-center gap-1 mb-1"><Video size={12} /> Riunione</span>
                                        <a href={event.meeting_url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-indigo-600 hover:underline truncate block">
                                            {event.meeting_url}
                                        </a>
                                    </div>
                                )}
                                <div className="p-3 bg-slate-50 rounded-lg">
                                    <span className="text-xs text-slate-500 flex items-center gap-1 mb-1"><Tag size={12} /> Tipo</span>
                                    <span className="text-sm font-medium text-slate-700 capitalize">{event.event_type}</span>
                                </div>
                                <div className="p-3 bg-slate-50 rounded-lg">
                                    <span className="text-xs text-slate-500 flex items-center gap-1 mb-1"><Users size={12} /> Visibilità</span>
                                    <span className="text-sm font-medium text-slate-700 capitalize">{event.visibility}</span>
                                </div>
                            </div>

                            {!canModify && (
                                <p className="text-xs text-center text-slate-400 italic py-2">
                                    Non hai i permessi per modificare questo impegno
                                </p>
                            )}
                        </div>
                    ) : (
                        /* Edit Mode */
                        <div className="space-y-6">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Left Column */}
                                <div className="space-y-4">
                                    <div className="space-y-1">
                                        <InputLabel label="Titolo" required error={errors.title} />
                                        <input
                                            type="text"
                                            {...register('title', { required: 'Il titolo è obbligatorio' })}
                                            className={inputClasses(errors.title)}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <InputLabel label="Descrizione" icon={AlignLeft} />
                                        <textarea rows={3} {...register('description')} className={inputClasses(null)} />
                                    </div>
                                    <div className="space-y-1">
                                        <InputLabel label="Tipologia" icon={Tag} />
                                        <select {...register('event_type')} className={inputClasses(null)}>
                                            <option value="meeting">📅 Riunione</option>
                                            <option value="task">✅ Attività</option>
                                            <option value="reminder">🔔 Promemoria</option>
                                            <option value="personal">👤 Personale</option>
                                            <option value="deadline">⏰ Scadenza</option>
                                            <option value="other">📌 Altro</option>
                                        </select>
                                    </div>
                                </div>

                                {/* Right Column */}
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
                                        <div className="flex items-center gap-2">
                                            <Clock className="text-slate-400" size={18} />
                                            <span className="text-sm font-medium text-slate-700">Tutto il giorno</span>
                                        </div>
                                        <label className="relative inline-flex items-center cursor-pointer">
                                            <input type="checkbox" {...register('is_all_day')} className="sr-only peer" />
                                            <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                                        </label>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <InputLabel label="Data Inizio" required icon={Calendar} />
                                            <input type="date" {...register('start_date', { required: 'Data richiesta' })} className={inputClasses(errors.start_date)} />
                                        </div>
                                        <div className="space-y-1">
                                            <InputLabel label="Data Fine" required icon={Calendar} />
                                            <input type="date" {...register('end_date', { required: 'Data richiesta' })} className={inputClasses(errors.end_date)} />
                                        </div>
                                    </div>

                                    {!isAllDay && (
                                        <div className="grid grid-cols-2 gap-4 animate-fadeIn">
                                            <div className="space-y-1">
                                                <InputLabel label="Ora Inizio" icon={Clock} />
                                                <input type="time" {...register('start_time')} className={inputClasses(null)} />
                                            </div>
                                            <div className="space-y-1">
                                                <InputLabel label="Ora Fine" icon={Clock} />
                                                <input type="time" {...register('end_time')} className={inputClasses(null)} />
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Location & Settings */}
                            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    <div className="space-y-1">
                                        <InputLabel label="Luogo" icon={MapPin} />
                                        <input type="text" {...register('location')} className={inputClasses(null)} placeholder="Es: Sala Riunioni A" />
                                    </div>
                                    <div className="space-y-1">
                                        <InputLabel label="Calendario" icon={Calendar} />
                                        <select {...register('calendar_id')} className={inputClasses(null)}>
                                            <option value="">Calendario Predefinito</option>
                                            {userCalendars.map(cal => (
                                                <option key={cal.id} value={cal.id}>{cal.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-1">
                                        <InputLabel label="Visibilità" icon={Users} />
                                        <select {...register('visibility')} className={inputClasses(null)}>
                                            <option value="private">🔒 Solo io</option>
                                            <option value="department">🏢 Il mio Dipartimento</option>
                                            <option value="service">🔧 Il mio Servizio</option>
                                            <option value="public">🌐 Tutti</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* Color Picker */}
                            <div className="space-y-2">
                                <div className="flex items-center gap-2">
                                    <Palette className="text-slate-400" size={16} />
                                    <span className="text-sm font-semibold text-slate-700">Colore</span>
                                </div>
                                <div className="flex flex-wrap gap-3">
                                    {colorOptions.map(({ value, name }) => (
                                        <label key={value} className="relative cursor-pointer group">
                                            <input type="radio" value={value} {...register('color')} className="sr-only peer" />
                                            <div
                                                className={`w-8 h-8 rounded-lg shadow-sm transition-all duration-200 group-hover:scale-110 ${selectedColor === value ? 'ring-2 ring-offset-2 ring-slate-400 scale-110' : ''}`}
                                                style={{ backgroundColor: value }}
                                                title={name}
                                            />
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Footer */}
                    <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                        <Button variant="outline" type="button" onClick={onClose} disabled={loading}>
                            {isEditing ? 'Annulla' : 'Chiudi'}
                        </Button>
                        {isEditing && (
                            <Button variant="primary" type="submit" disabled={loading} className="min-w-[140px] shadow-lg shadow-indigo-500/20">
                                {loading ? 'Salvataggio...' : <><Save size={16} className="mr-2" /> Salva Modifiche</>}
                            </Button>
                        )}
                    </div>
                </form>
            </div>
        </Modal>
    );
}
