import React, { useState } from 'react';
import { MapPin, Clock, LogIn, LogOut, CheckCircle } from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { useToast } from '../../context/ToastContext';
import type { SWRequest } from '../../services/smartWorking.service';
import { smartWorkingService } from '../../services/smartWorking.service';

interface AttendanceWidgetProps {
    todayRequest: SWRequest | undefined;
    onStatusChange: () => void;
}

export const AttendanceWidget: React.FC<AttendanceWidgetProps> = ({ todayRequest, onStatusChange }) => {
    const toast = useToast();
    const [loading, setLoading] = useState(false);

    if (!todayRequest) {
        return (
            <Card className="p-4 border-l-4 border-l-slate-200">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-slate-100 rounded-full text-slate-400">
                        <MapPin size={24} />
                    </div>
                    <div>
                        <p className="text-sm text-slate-500 font-medium">Stato Odierno</p>
                        <h3 className="text-lg font-bold text-slate-900">In Sede</h3>
                        <p className="text-xs text-slate-500">Nessuna richiesta di Smart Working attiva</p>
                    </div>
                </div>
            </Card>
        );
    }

    if (todayRequest.status !== 'APPROVED') {
        return (
            <Card className="p-4 border-l-4 border-l-amber-200">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-amber-100 rounded-full text-amber-600">
                        <Clock size={24} />
                    </div>
                    <div>
                        <p className="text-sm text-slate-500 font-medium">Richiesta Odierna</p>
                        <h3 className="text-lg font-bold text-slate-900">{todayRequest.status}</h3>
                        <p className="text-xs text-slate-500">In attesa di approvazione</p>
                    </div>
                </div>
            </Card>
        );
    }

    const attendance = todayRequest.attendance;
    const isCheckedIn = !!attendance?.check_in;
    const isCheckedOut = !!attendance?.check_out;

    const handleCheckIn = async () => {
        setLoading(true);
        try {
            await smartWorkingService.checkIn({ request_id: todayRequest.id, location: 'Home' });
            toast.success('Check-in effettuato con successo');
            onStatusChange();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore durante il check-in');
        } finally {
            setLoading(false);
        }
    };

    const handleCheckOut = async () => {
        setLoading(true);
        try {
            await smartWorkingService.checkOut({ request_id: todayRequest.id });
            toast.success('Check-out effettuato con successo');
            onStatusChange();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || 'Errore durante il check-out');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className={`p-4 border-l-4 ${isCheckedIn && !isCheckedOut ? 'border-l-emerald-500' : 'border-l-blue-500'}`}>
            <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-full ${isCheckedIn ? 'bg-emerald-100 text-emerald-600' : 'bg-blue-100 text-blue-600'}`}>
                            <MapPin size={24} />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500 font-medium">Lavoro Agile</p>
                            <h3 className="text-lg font-bold text-slate-900">
                                {isCheckedOut ? 'Terminato' : isCheckedIn ? 'Al Lavoro' : 'Pronto'}
                            </h3>
                            <p className="text-xs text-slate-500">
                                {isCheckedIn
                                    ? `Iniziato alle ${new Date(attendance!.check_in!).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}`
                                    : 'Registra la tua presenza'}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="flex gap-2 mt-2">
                    {!isCheckedIn && !isCheckedOut && (
                        <Button
                            onClick={handleCheckIn}
                            disabled={loading}
                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                        >
                            <LogIn size={16} className="mr-2" /> Check-in
                        </Button>
                    )}

                    {isCheckedIn && !isCheckedOut && (
                        <Button
                            onClick={handleCheckOut}
                            disabled={loading}
                            className="w-full bg-slate-600 hover:bg-slate-700 text-white"
                        >
                            <LogOut size={16} className="mr-2" /> Check-out
                        </Button>
                    )}

                    {isCheckedOut && (
                        <div className="w-full py-2 flex items-center justify-center gap-2 text-sm text-slate-500 bg-slate-50 rounded border border-slate-100">
                            <CheckCircle size={16} className="text-emerald-500" />
                            Giornata completata alle {new Date(attendance!.check_out!).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}
                        </div>
                    )}
                </div>
            </div>
        </Card>
    );
};
