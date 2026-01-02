/**
 * KRONOS - Enterprise Notification Center
 * 
 * Central hub for managing and dispatching notifications.
 * Features:
 * - Stats Dashboard
 * - Advanced History Log (Server-Side)
 * - Live Preview Composition
 */
import { useState, useEffect } from 'react';
import {
    Bell, Plus, History, LayoutDashboard
} from 'lucide-react';
import { userService } from '../../services/userService';
import notificationService from '../../services/notification.service';
import type { Notification, BulkNotificationRequest } from '../../services/notification.service';
import type { UserWithProfile } from '../../types';
import { useToast } from '../../context/ToastContext';
import { NotificationStats, NotificationHistory, NotificationCompose } from './notifications';

type Tab = 'dashboard' | 'compose';

interface Area {
    id: string;
    name: string;
    code: string;
}

export function NotificationCenterPage() {
    const toast = useToast();
    const [activeTab, setActiveTab] = useState<Tab>('dashboard');

    // Resource State
    const [users, setUsers] = useState<UserWithProfile[]>([]);
    const [areas, setAreas] = useState<Area[]>([]);


    // Stats State (fetched via history for now as per plan)
    const [recentHistory, setRecentHistory] = useState<Notification[]>([]);
    const [sending, setSending] = useState(false);

    useEffect(() => {
        loadResources();
        loadStats();
    }, []);

    // Refresh trigger for history
    const [refreshKey, setRefreshKey] = useState(0);

    const loadResources = async () => {

        try {
            const [usersData, areasData] = await Promise.all([
                userService.getUsers({ active_only: true }),
                userService.getAreas(true)
            ]);
            setUsers(usersData);
            setAreas(areasData);
        } catch (error) {
            console.error('Failed to load resources:', error);
            toast.error('Errore nel caricamento delle risorse');

        }
    };

    const loadStats = async () => {
        try {
            // Fetching last 100 for stats calculation
            const data = await notificationService.getHistory({ limit: 100 });
            setRecentHistory(data);
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    };

    const handleSend = async (request: BulkNotificationRequest) => {
        setSending(true);
        try {
            await notificationService.sendBulk(request);
            toast.success(`Notifica inviata con successo`);

            // Switch back to dashboard to see it in history
            setActiveTab('dashboard');
            loadStats(); // refresh stats
            setRefreshKey(prev => prev + 1); // Trigger history table refresh
        } catch (error) {
            console.error('Send failed:', error);
            toast.error('Errore durante l\'invio');
        } finally {
            setSending(false);
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Bell className="text-primary" /> Centro Notifiche
                    </h1>
                    <p className="text-gray-500 mt-1">Gestisci comunicazioni e monitora gli invii</p>
                </div>

                <div className="flex bg-white p-1 rounded-xl border shadow-sm">
                    <button
                        onClick={() => setActiveTab('dashboard')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all ${activeTab === 'dashboard'
                            ? 'bg-primary text-white shadow-md'
                            : 'text-gray-600 hover:bg-gray-50'
                            }`}
                    >
                        <LayoutDashboard size={18} />
                        Dashboard
                    </button>
                    <button
                        onClick={() => setActiveTab('compose')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all ${activeTab === 'compose'
                            ? 'bg-primary text-white shadow-md'
                            : 'text-gray-600 hover:bg-gray-50'
                            }`}
                    >
                        <Plus size={18} />
                        Nuova Notifica
                    </button>
                </div>
            </div>

            {/* Content Switch */}
            {/* Content Switch - Using hidden to prevent unmount crash with DataTables */}
            <div className={activeTab === 'dashboard' ? 'block animate-in fade-in duration-500' : 'hidden'}>
                <div className="space-y-8">
                    <NotificationStats history={recentHistory} />

                    <div>
                        <div className="flex items-center gap-2 mb-4">
                            <History className="text-gray-400" size={20} />
                            <h2 className="text-lg font-bold text-gray-800">Storico Attività</h2>
                        </div>
                        <NotificationHistory refreshTrigger={refreshKey} />
                    </div>
                </div>
            </div>

            <div className={activeTab === 'compose' ? 'block animate-in slide-in-from-right-8 duration-500' : 'hidden'}>
                <NotificationCompose
                    users={users}
                    areas={areas}
                    onSend={handleSend}
                    sending={sending}
                />
            </div>
        </div>
    );
}

export default NotificationCenterPage;
