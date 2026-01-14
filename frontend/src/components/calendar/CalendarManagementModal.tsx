import { useState } from 'react';
import { Settings, X, Plus, Tag, Edit3, Users, Calendar as CalendarIcon } from 'lucide-react';
import { Button } from '../common';
import { useToast } from '../../context/ToastContext';
import {
    useCreateUserCalendar,
    useDeleteUserCalendar,
    useUpdateUserCalendar,
    useShareUserCalendar,
    useUnshareUserCalendar,
    useUserCalendars
} from '../../hooks/domain/useCalendar';
import { useAuth } from '../../context/AuthContext';
import { useUsers } from '../../hooks/domain/useUsers';
import type { UserCalendar } from '../../services/calendar.service';

interface CalendarManagementModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function CalendarManagementModal({
    isOpen,
    onClose
}: CalendarManagementModalProps) {
    const toast = useToast();
    const { user: currentUser } = useAuth();
    const { data: users, isLoading: usersLoading } = useUsers();

    // Fetch calendars directly here
    const { data: userCalendarsData } = useUserCalendars();
    const userCalendars = (Array.isArray(userCalendarsData) ? userCalendarsData : []) as UserCalendar[];

    const createUserCalendar = useCreateUserCalendar();
    const deleteUserCalendar = useDeleteUserCalendar();
    const updateUserCalendar = useUpdateUserCalendar();
    const shareCalendarMut = useShareUserCalendar();
    const unshareCalendarMut = useUnshareUserCalendar();

    const [sharingCalendarId, setSharingCalendarId] = useState<string | null>(null);
    const [editingCalendarId, setEditingCalendarId] = useState<string | null>(null);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-scaleIn">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-indigo-50">
                    <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                        <Settings className="text-indigo-600" size={20} />
                        Gestione Calendari
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 space-y-6">
                    {/* Create New Calendar Form */}
                    <form
                        onSubmit={async (e) => {
                            e.preventDefault();
                            const formData = new FormData(e.currentTarget);
                            try {
                                await createUserCalendar.mutateAsync({
                                    name: formData.get('name') as string,
                                    color: formData.get('color') as string || '#4F46E5'
                                });
                                toast.success('Calendario creato');
                                (e.target as HTMLFormElement).reset();
                            } catch (err) {
                                toast.error('Errore durante la creazione');
                            }
                        }}
                        className="bg-gray-50 p-4 rounded-xl border border-gray-100"
                    >
                        <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                            <Plus size={14} className="text-indigo-600" />
                            Crea Nuovo Calendario
                        </h4>
                        <div className="flex gap-3">
                            <input
                                name="name"
                                required
                                placeholder="Nome calendario (es. Meeting, Sport...)"
                                className="flex-1 px-3 py-2 text-sm rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                            />
                            <input
                                type="color"
                                name="color"
                                defaultValue="#4F46E5"
                                className="w-10 h-9 rounded-lg border border-gray-200 cursor-pointer"
                            />
                            <Button type="submit" variant="primary" size="sm" isLoading={createUserCalendar.isPending}>
                                Aggiungi
                            </Button>
                        </div>
                    </form>

                    {/* Existing Calendars List */}
                    <div className="space-y-3">
                        <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                            <Tag size={14} className="text-indigo-600" />
                            I tuoi Calendari
                        </h4>
                        <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                            {userCalendars.map(cal => (
                                <div key={cal.id} className="space-y-2">
                                    {editingCalendarId === cal.id ? (
                                        /* Inline Edit Mode */
                                        <form
                                            onSubmit={async (e) => {
                                                e.preventDefault();
                                                const formData = new FormData(e.currentTarget);
                                                try {
                                                    await updateUserCalendar.mutateAsync({
                                                        id: cal.id,
                                                        data: {
                                                            name: formData.get('name') as string,
                                                            color: formData.get('color') as string
                                                        }
                                                    });
                                                    toast.success('Calendario aggiornato');
                                                    setEditingCalendarId(null);
                                                } catch (err) {
                                                    toast.error('Errore durante l\'aggiornamento');
                                                }
                                            }}
                                            className="flex items-center gap-3 p-3 rounded-xl border border-indigo-200 bg-indigo-50"
                                        >
                                            <input
                                                type="color"
                                                name="color"
                                                defaultValue={cal.color}
                                                className="w-8 h-8 rounded cursor-pointer border-none"
                                            />
                                            <input
                                                type="text"
                                                name="name"
                                                defaultValue={cal.name}
                                                required
                                                className="flex-1 px-2 py-1 text-sm rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                                            />
                                            <Button type="submit" variant="primary" size="sm" isLoading={updateUserCalendar.isPending}>
                                                Salva
                                            </Button>
                                            <button
                                                type="button"
                                                onClick={() => setEditingCalendarId(null)}
                                                className="text-gray-400 hover:text-gray-600 p-1"
                                            >
                                                <X size={16} />
                                            </button>
                                        </form>
                                    ) : (
                                        /* View Mode */
                                        <div className="flex items-center justify-between p-3 rounded-xl border border-gray-100 hover:bg-gray-50 transition-colors">
                                            <div className="flex items-center gap-3">
                                                <div className="w-4 h-4 rounded shadow-sm" style={{ backgroundColor: cal.color }} />
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-medium text-gray-700">{cal.name}</span>
                                                    {!cal.is_owner && (() => {
                                                        if (cal.type === 'SYSTEM') {
                                                            return <span className="text-[10px] text-gray-400">Calendario di Sistema</span>;
                                                        }
                                                        if (cal.type === 'LOCATION') {
                                                            return <span className="text-[10px] text-gray-400">Calendario Sede</span>;
                                                        }
                                                        const ownerId = cal.user_id || cal.owner_id;
                                                        const owner = (users || []).find((u: any) => u.id === ownerId);
                                                        const ownerName = owner?.full_name || `${owner?.first_name || ''} ${owner?.last_name || ''}`.trim() || 'un collega';
                                                        return (
                                                            <span className="text-[10px] text-gray-400">
                                                                Condiviso da {ownerName}
                                                            </span>
                                                        );
                                                    })()}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                {cal.is_owner && (
                                                    <>
                                                        <button
                                                            onClick={() => setEditingCalendarId(cal.id)}
                                                            className="p-1.5 rounded-lg transition-colors text-gray-400 hover:bg-gray-100 hover:text-amber-600"
                                                            title="Modifica"
                                                        >
                                                            <Edit3 size={16} />
                                                        </button>
                                                        <button
                                                            onClick={() => setSharingCalendarId(sharingCalendarId === cal.id ? null : cal.id)}
                                                            className={`p-1.5 rounded-lg transition-colors ${sharingCalendarId === cal.id ? 'bg-indigo-50 text-indigo-600' : 'text-gray-400 hover:bg-gray-100 hover:text-indigo-600'}`}
                                                            title="Condividi"
                                                        >
                                                            <Users size={16} />
                                                        </button>
                                                        <button
                                                            onClick={async () => {
                                                                if (confirm(`Sei sicuro di voler eliminare il calendario "${cal.name}"? Gli impegni associati perderanno il colore personalizzato.`)) {
                                                                    try {
                                                                        await deleteUserCalendar.mutateAsync(cal.id);
                                                                        toast.success('Calendario eliminato');
                                                                    } catch (err) {
                                                                        toast.error('Errore durante l\'eliminazione');
                                                                    }
                                                                }
                                                            }}
                                                            className="text-gray-400 hover:text-red-600 transition-colors p-1.5 hover:bg-red-50 rounded-lg"
                                                        >
                                                            <X size={16} />
                                                        </button>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* Sharing Section */}
                                    {sharingCalendarId === cal.id && cal.is_owner && (
                                        <div className="ml-7 p-3 bg-gray-50 rounded-xl border border-gray-200 space-y-3 animate-in fade-in slide-in-from-top-2">
                                            <div className="flex items-center justify-between">
                                                <h5 className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Gestisci Accessi</h5>
                                                <button onClick={() => setSharingCalendarId(null)} className="text-gray-400 hover:text-gray-600">
                                                    <X size={12} />
                                                </button>
                                            </div>

                                            {/* List of current shares */}
                                            <div className="space-y-2">
                                                {((cal as any).shares || cal.shared_with || []).map((share: any) => {
                                                    const shareUserId = share.user_id || share.shared_with_user_id;
                                                    const sharedUser = users?.find((u: any) => u.id === shareUserId);
                                                    const userName = sharedUser ? `${sharedUser.first_name || ''} ${sharedUser.last_name || ''}`.trim() : 'Utente';
                                                    const initials = userName.split(' ').map((n: string) => n[0]?.toUpperCase() || '').join('').slice(0, 2);
                                                    return (
                                                        <div key={share.id} className="flex items-center justify-between text-sm bg-white p-2 rounded-lg border border-gray-100">
                                                            <div className="flex items-center gap-2">
                                                                <div className="w-6 h-6 rounded-full bg-indigo-100 flex items-center justify-center text-[10px] font-bold text-indigo-600">
                                                                    {initials}
                                                                </div>
                                                                <span className="text-gray-600">{userName}</span>
                                                            </div>
                                                            <button
                                                                onClick={() => unshareCalendarMut.mutate({ calendarId: cal.id, sharedUserId: shareUserId })}
                                                                className="text-red-400 hover:text-red-600 p-1"
                                                            >
                                                                <X size={14} />
                                                            </button>
                                                        </div>
                                                    );
                                                })}
                                                {(!((cal as any).shares || cal.shared_with) || ((cal as any).shares || cal.shared_with || []).length === 0) && (
                                                    <p className="text-[11px] text-gray-400 italic">Nessuna condivisione attiva</p>
                                                )}
                                            </div>

                                            {/* Add share form */}
                                            <div className="pt-2 border-t border-gray-200">
                                                <select
                                                    className="w-full text-xs px-2 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none bg-white font-medium"
                                                    disabled={usersLoading}
                                                    onChange={(e) => {
                                                        if (e.target.value) {
                                                            shareCalendarMut.mutate({
                                                                calendarId: cal.id,
                                                                data: { user_id: e.target.value, permission: 'READ' }
                                                            });
                                                            e.target.value = "";
                                                        }
                                                    }}
                                                >
                                                    <option value="">{usersLoading ? 'Caricamento colleghi...' : 'Aggiungi collega...'}</option>
                                                    {(users || [])
                                                        .filter((u: any) => {
                                                            // Exclude current user (calendar owner)
                                                            const ownerId = cal.user_id || cal.owner_id || currentUser?.id;
                                                            if (u.id === ownerId) return false;
                                                            // Exclude already shared users - use 'shares' and 's.user_id'
                                                            const shares = (cal as any).shares || cal.shared_with || [];
                                                            if (shares.some((s: any) => s.user_id === u.id || s.shared_with_user_id === u.id)) return false;
                                                            return true;
                                                        })
                                                        .map((u: any) => (
                                                            <option key={u.id} value={u.id}>
                                                                {`${u.first_name || ''} ${u.last_name || ''}`.trim() || u.email}
                                                            </option>
                                                        ))}
                                                </select>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                            {(!userCalendars || userCalendars.length === 0) && (
                                <div className="text-center py-8 text-gray-400">
                                    <CalendarIcon size={32} className="mx-auto mb-2 opacity-20" />
                                    <p className="text-sm">Non hai ancora creato calendari personalizzati</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-end">
                    <Button onClick={onClose} variant="outline">
                        Chiudi
                    </Button>
                </div>
            </div>
        </div>
    );
}
