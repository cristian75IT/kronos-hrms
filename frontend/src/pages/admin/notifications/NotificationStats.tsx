import React from 'react';
import { Card } from '../../../components/common/Card';
import { Send, CheckCircle2, AlertOctagon, TrendingUp } from 'lucide-react';
import type { Notification } from '../../../services/notification.service';

interface NotificationStatsProps {
    history: Notification[];
}

export const NotificationStats: React.FC<NotificationStatsProps> = ({ history }) => {
    // Calculators
    const totalSent = history.length;

    // For Read Rate (In-App only for now as email tracking is harder without pixel)
    const inAppNotifications = history.filter(n => n.channel === 'in_app');
    const readCount = inAppNotifications.filter(n => n.read_at).length;
    const readRate = inAppNotifications.length > 0
        ? Math.round((readCount / inAppNotifications.length) * 100)
        : 0;

    const failedCount = history.filter(n => n.status === 'failed').length;

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card className="stats-card border-l-4 border-l-blue-500">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">Totale Inviate</p>
                        <h3 className="text-3xl font-bold text-gray-900 mt-1">{totalSent}</h3>
                    </div>
                    <div className="p-3 bg-blue-50 rounded-full">
                        <Send className="text-blue-600" size={24} />
                    </div>
                </div>
                <div className="mt-4 flex items-center text-sm text-gray-600">
                    <TrendingUp size={14} className="mr-1 text-green-500" />
                    <span>Ultimi 30 giorni</span>
                </div>
            </Card>

            <Card className="stats-card border-l-4 border-l-green-500">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">Tasso di Lettura</p>
                        <h3 className="text-3xl font-bold text-gray-900 mt-1">{readRate}%</h3>
                    </div>
                    <div className="p-3 bg-green-50 rounded-full">
                        <CheckCircle2 className="text-green-600" size={24} />
                    </div>
                </div>
                <div className="mt-4 text-sm text-gray-500">
                    Su {inAppNotifications.length} notifiche In-App
                </div>
            </Card>

            <Card className="stats-card border-l-4 border-l-red-500">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">Invii Falliti</p>
                        <h3 className="text-3xl font-bold text-gray-900 mt-1">{failedCount}</h3>
                    </div>
                    <div className="p-3 bg-red-50 rounded-full">
                        <AlertOctagon className="text-red-600" size={24} />
                    </div>
                </div>
                <div className="mt-4 text-sm text-gray-500">
                    Errori di consegna
                </div>
            </Card>
        </div>
    );
};
