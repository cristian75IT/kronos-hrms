import React, { useState } from 'react';
import { Card } from '../../../components/common/Card';
import {
    Users, Building, Mail, Smartphone, Monitor, Send,
    RefreshCw
} from 'lucide-react';
import { useToast } from '../../../context/ToastContext';
import type { UserWithProfile } from '../../../types';
import { NotificationChannel } from '../../../services/notification.service';
import type { BulkNotificationRequest } from '../../../services/notification.service';

interface NotificationComposeProps {
    users: UserWithProfile[];
    areas: any[];
    onSend: (request: BulkNotificationRequest) => Promise<void>;
    sending: boolean;
}

export const NotificationCompose: React.FC<NotificationComposeProps> = ({
    users, areas, onSend, sending
}) => {
    // Local state for form
    const toast = useToast();
    const [recipientMode, setRecipientMode] = useState<'user' | 'department'>('user');
    const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
    const [selectedArea, setSelectedArea] = useState<string>('');
    const [selectedChannels, setSelectedChannels] = useState<NotificationChannel[]>([NotificationChannel.IN_APP]);
    const [formData, setFormData] = useState({
        title: '',
        message: '',
        type: 'info' // Default type
    });

    const toggleChannel = (channel: NotificationChannel) => {
        setSelectedChannels(prev =>
            prev.includes(channel)
                ? prev.filter(c => c !== channel)
                : [...prev, channel]
        );
    };

    const handleSelectAllUsers = () => {
        if (selectedUsers.length === users.length) {
            setSelectedUsers([]);
        } else {
            setSelectedUsers(users.map(u => u.id));
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        let targetUserIds: string[] = [];
        if (recipientMode === 'user') {
            targetUserIds = selectedUsers;
        } else {
            if (activeAreaUsers.length > 0) {
                targetUserIds = activeAreaUsers.map(u => u.id);
            }
        }

        if (targetUserIds.length === 0) {
            toast.error('Seleziona almeno un destinatario o un dipartimento con utenti.');
            return;
        }

        if (!formData.title.trim() || !formData.message.trim()) {
            toast.error('Inserisci titolo e messaggio.');
            return;
        }

        if (selectedChannels.length === 0) {
            toast.error('Seleziona almeno un canale di invio.');
            return;
        }

        await onSend({
            notification_type: formData.type,
            title: formData.title,
            message: formData.message,
            user_ids: targetUserIds,
            channels: selectedChannels
        });
    };

    const activeAreaUsers = recipientMode === 'department' && selectedArea
        ? users.filter(u => (u as any).areas?.some((a: any) => a.id === selectedArea) || u.profile?.department === selectedArea)
        : [];

    return (
        <div className="max-w-4xl mx-auto">
            <Card title="Componi Notifica" className="h-full">
                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* 1. Recipients */}
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Destinatari</label>
                        <div className="flex gap-2 mb-3">
                            <button
                                type="button"
                                onClick={() => setRecipientMode('user')}
                                className={`flex-1 py-2 px-4 rounded-lg border flex items-center justify-center gap-2 transition-colors ${recipientMode === 'user'
                                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                                    }`}
                            >
                                <Users size={18} /> Singoli
                            </button>
                            <button
                                type="button"
                                onClick={() => setRecipientMode('department')}
                                className={`flex-1 py-2 px-4 rounded-lg border flex items-center justify-center gap-2 transition-colors ${recipientMode === 'department'
                                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                                    }`}
                            >
                                <Building size={18} /> Dipartimento
                            </button>
                        </div>

                        {recipientMode === 'user' ? (
                            <div className="space-y-2">
                                <div className="flex justify-end">
                                    <button
                                        type="button"
                                        onClick={handleSelectAllUsers}
                                        className="text-sm text-primary font-medium hover:underline"
                                    >
                                        {selectedUsers.length === users.length ? 'Deseleziona Tutti' : 'Seleziona Tutti'}
                                    </button>
                                </div>
                                <select
                                    multiple
                                    className="w-full h-48 p-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                                    value={selectedUsers}
                                    onChange={(e) => setSelectedUsers(Array.from(e.target.selectedOptions, o => o.value))}
                                >
                                    {users.map(u => (
                                        <option key={u.id} value={u.id}>
                                            {u.first_name} {u.last_name} ({u.email})
                                        </option>
                                    ))}
                                </select>
                                <p className="text-xs text-gray-500 text-right">
                                    {selectedUsers.length} utenti selezionati
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                <select
                                    className="w-full p-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    value={selectedArea}
                                    onChange={(e) => setSelectedArea(e.target.value)}
                                >
                                    <option value="">-- Seleziona Dipartimento --</option>
                                    {areas.map(a => (
                                        <option key={a.id} value={a.id}>{a.name}</option>
                                    ))}
                                </select>
                                {selectedArea && (
                                    <p className="text-xs text-gray-500">
                                        Verrà inviato a {activeAreaUsers.length} utenti in questo dipartimento.
                                    </p>
                                )}
                            </div>
                        )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* 2. Notification Type */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">Tipologia</label>
                            <select
                                value={formData.type}
                                onChange={e => setFormData({ ...formData, type: e.target.value })}
                                className="w-full p-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                            >
                                <option value="info">Info (Blu)</option>
                                <option value="warning">Avviso (Giallo)</option>
                                <option value="error">Urgente/Errore (Rosso)</option>
                                <option value="success">Successo (Verde)</option>
                                <option value="system_announcement">Annuncio di Sistema</option>
                            </select>
                        </div>

                        {/* 3. Channels */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">Canali</label>
                            <div className="grid grid-cols-3 gap-2">
                                {[
                                    { id: NotificationChannel.EMAIL, icon: Mail, label: 'Email' },
                                    { id: NotificationChannel.IN_APP, icon: Monitor, label: 'In-App' },
                                    { id: NotificationChannel.PUSH, icon: Smartphone, label: 'Push' }
                                ].map(channel => (
                                    <div
                                        key={channel.id}
                                        onClick={() => toggleChannel(channel.id)}
                                        className={`cursor-pointer p-3 rounded-xl border flex flex-col items-center gap-1 transition-all ${selectedChannels.includes(channel.id)
                                            ? 'bg-indigo-50 border-indigo-500 text-indigo-700 shadow-sm'
                                            : 'bg-white border-gray-200 text-gray-500 hover:border-indigo-200'
                                            }`}
                                    >
                                        <channel.icon size={20} />
                                        <span className="text-xs font-medium">{channel.label}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* 4. Content */}
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">Titolo</label>
                            <input
                                type="text"
                                value={formData.title}
                                onChange={e => setFormData({ ...formData, title: e.target.value })}
                                className="w-full p-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Titolo della notifica"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">Messaggio</label>
                            <textarea
                                value={formData.message}
                                onChange={e => setFormData({ ...formData, message: e.target.value })}
                                rows={5}
                                className="w-full p-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Scrivi il tuo messaggio..."
                            />
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="pt-4 border-t flex justify-end">
                        <button
                            type="submit"
                            disabled={sending}
                            className="bg-primary text-white px-8 py-3 rounded-lg font-medium flex items-center gap-2 hover:bg-primary-dark disabled:opacity-70 disabled:cursor-not-allowed transition-colors shadow-lg shadow-primary/30"
                        >
                            {sending ? <RefreshCw className="animate-spin" size={20} /> : <Send size={20} />}
                            {sending ? 'Invio in corso...' : 'Invia Notifica'}
                        </button>
                    </div>
                </form>
            </Card>
        </div>
    );
};
