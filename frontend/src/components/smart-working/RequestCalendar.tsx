import React, { useState, useMemo } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import itLocale from '@fullcalendar/core/locales/it';
import { Card } from '../../components/common/Card';
import { Laptop, Building, Info, X } from 'lucide-react';
import type { SWRequest, SWAgreement } from '../../services/smartWorking.service';
import { RequestCreationModal } from './RequestCreationModal';
import { format } from 'date-fns';
import './RequestCalendar.css';

interface RequestCalendarProps {
    requests: SWRequest[];
    activeAgreement: SWAgreement | undefined;
    onRefresh: () => void;
}

type ModalType = 'convert_to_office' | 'extra_request' | null;

export const RequestCalendar: React.FC<RequestCalendarProps> = ({ requests, activeAgreement, onRefresh }) => {
    const [modalType, setModalType] = useState<ModalType>(null);
    const [selectedDate, setSelectedDate] = useState<Date | null>(null);
    const [creationModalOpen, setCreationModalOpen] = useState(false);

    // Get allowed weekdays from active agreement (JS weekday: 0=Sun, 1=Mon, ...)
    // Agreement uses: 0=Mon, 1=Tue, ... so we need to convert: agreementDay + 1 (1=Mon in JS)
    const allowedJsWeekdays = activeAgreement?.allowed_weekdays?.map(d => d + 1) || [];

    // Check if a date already has a request
    const getRequestForDate = (dateStr: string) => {
        return requests.find(r => r.date === dateStr);
    };

    const handleDateClick = (arg: { date: Date }) => {
        const day = arg.date.getDay();
        // Prevent selecting weekends
        if (day === 0 || day === 6) return;

        const dateStr = format(arg.date, 'yyyy-MM-dd');
        const existingRequest = getRequestForDate(dateStr);

        // If there's already a request for this date, don't open any modal
        if (existingRequest) return;

        setSelectedDate(arg.date);

        // Determine modal type based on whether it's an allowed SW day or not
        if (allowedJsWeekdays.length > 0 && allowedJsWeekdays.includes(day)) {
            // This is an allowed SW day -> show "Convert to Office" modal
            setModalType('convert_to_office');
        } else {
            // This is a regular day -> show "Extra SW Request" modal
            setModalType('extra_request');
            setCreationModalOpen(true);
        }
    };

    const handleCloseConvertModal = () => {
        setModalType(null);
        setSelectedDate(null);
    };

    const handleConfirmConvert = async () => {
        // For now, just close the modal - in real implementation this would create
        // an "office day" entry or cancel the automatic SW for that day
        // This could be implemented by creating a special request type
        handleCloseConvertModal();
        // TODO: Implement backend API for converting SW day to office day
    };

    // Generate background events for all SW days in current view
    const generateSwDayEvents = useMemo(() => {
        if (!activeAgreement?.allowed_weekdays?.length) return [];

        const events: Array<{
            id: string;
            title: string;
            start: string;
            display: string;
            backgroundColor: string;
            borderColor: string;
            textColor: string;
            classNames: string[];
        }> = [];

        // Generate events for the next 3 months of SW days
        const today = new Date();
        const start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        const end = new Date(today.getFullYear(), today.getMonth() + 3, 0);

        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const jsWeekday = d.getDay();
            if (jsWeekday === 0 || jsWeekday === 6) continue;

            const agreementWeekday = jsWeekday - 1;
            if (activeAgreement.allowed_weekdays.includes(agreementWeekday)) {
                const dateStr = format(d, 'yyyy-MM-dd');

                // Don't show automatic SW if there's already a request for this date
                if (!getRequestForDate(dateStr)) {
                    events.push({
                        id: `sw-auto-${dateStr}`,
                        title: '🏠 Smart Working',
                        start: dateStr,
                        display: 'background',
                        backgroundColor: '#ccfbf1', // teal-100
                        borderColor: '#14b8a6',
                        textColor: '#0d9488',
                        classNames: ['sw-automatic-day']
                    });
                }
            }
        }

        return events;
    }, [activeAgreement, requests]);

    // Regular request events
    const requestEvents = requests.map(req => ({
        id: req.id,
        title: req.status === 'APPROVED' ? '✅ Smart Working' :
            req.status === 'PENDING' ? '⏳ In attesa' :
                req.status === 'REJECTED' ? '❌ Rifiutato' : 'Richiesta',
        start: req.date,
        backgroundColor: getStatusColor(req.status),
        borderColor: getStatusColor(req.status),
        textColor: '#333',
        extendedProps: {
            status: req.status,
            notes: req.notes
        }
    }));

    // Combine all events
    const allEvents = [...generateSwDayEvents, ...requestEvents];

    // Add CSS class to allowed weekday cells
    const dayCellClassNames = (arg: { date: Date }) => {
        const day = arg.date.getDay();
        const classes: string[] = [];

        if (day === 0 || day === 6) {
            classes.push('sw-weekend');
            return classes;
        }

        if (allowedJsWeekdays.length > 0) {
            if (allowedJsWeekdays.includes(day)) {
                classes.push('sw-allowed-day');
            } else {
                classes.push('sw-extra-request-day');
            }
        }

        return classes;
    };

    function getStatusColor(status: string) {
        switch (status) {
            case 'APPROVED': return '#d1fae5';
            case 'PENDING': return '#fef3c7';
            case 'REJECTED': return '#fee2e2';
            case 'CANCELLED': return '#f3f4f6';
            default: return '#f3f4f6';
        }
    }

    return (
        <>
            {/* Legend */}
            <div className="mb-4 flex flex-wrap items-center gap-4 text-sm bg-white p-4 rounded-lg border border-slate-200">
                <div className="flex items-center gap-2">
                    <span className="inline-block w-5 h-5 bg-teal-100 border-2 border-teal-400 rounded flex items-center justify-center">
                        <Laptop size={12} className="text-teal-600" />
                    </span>
                    <span className="text-slate-600">
                        Giorni SW automatici
                        {activeAgreement?.allowed_weekdays_names && (
                            <span className="font-medium text-teal-700 ml-1">
                                ({activeAgreement.allowed_weekdays_names.join(', ')})
                            </span>
                        )}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="inline-block w-5 h-5 bg-slate-100 border border-slate-300 rounded flex items-center justify-center">
                        <Building size={12} className="text-slate-500" />
                    </span>
                    <span className="text-slate-500">Giorni in ufficio (clicca per SW extra)</span>
                </div>
                <div className="flex items-center gap-2 ml-auto">
                    <Info size={14} className="text-slate-400" />
                    <span className="text-xs text-slate-400">Clicca su un giorno per modificare</span>
                </div>
            </div>

            <Card className="p-4 sw-calendar">
                <FullCalendar
                    plugins={[dayGridPlugin, interactionPlugin]}
                    initialView="dayGridMonth"
                    locale={itLocale}
                    headerToolbar={{
                        left: 'prev,next today',
                        center: 'title',
                        right: 'dayGridMonth'
                    }}
                    events={allEvents}
                    dateClick={handleDateClick}
                    dayCellClassNames={dayCellClassNames}
                    height="auto"
                    contentHeight="auto"
                    firstDay={1}
                />
            </Card>

            {/* Convert to Office Modal */}
            {modalType === 'convert_to_office' && selectedDate && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-fadeIn">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 animate-slideUp">
                        <div className="p-6">
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-3 bg-amber-100 rounded-xl">
                                        <Building size={24} className="text-amber-600" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-gray-900">Converti in Presenza</h3>
                                        <p className="text-sm text-gray-500">
                                            {selectedDate.toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long' })}
                                        </p>
                                    </div>
                                </div>
                                <button onClick={handleCloseConvertModal} className="text-gray-400 hover:text-gray-600">
                                    <X size={20} />
                                </button>
                            </div>

                            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                                <p className="text-sm text-amber-800">
                                    Questo giorno è normalmente destinato allo <strong>Smart Working</strong>
                                    secondo il tuo accordo. Vuoi lavorare in ufficio invece?
                                </p>
                            </div>

                            <div className="flex justify-end gap-3">
                                <button
                                    onClick={handleCloseConvertModal}
                                    className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg"
                                >
                                    Annulla
                                </button>
                                <button
                                    onClick={handleConfirmConvert}
                                    className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-bold flex items-center gap-2"
                                >
                                    <Building size={16} />
                                    Lavora in Ufficio
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Extra Request Modal */}
            <RequestCreationModal
                isOpen={creationModalOpen && modalType === 'extra_request'}
                onClose={() => {
                    setCreationModalOpen(false);
                    setModalType(null);
                }}
                onSuccess={onRefresh}
                selectedDate={selectedDate}
                activeAgreement={activeAgreement}
            />
        </>
    );
};
