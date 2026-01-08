import React, { useState } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import itLocale from '@fullcalendar/core/locales/it';
import { Card } from '../../components/common/Card';
import type { SWRequest, SWAgreement } from '../../services/smartWorking.service';
import { RequestCreationModal } from './RequestCreationModal';
import './RequestCalendar.css';

interface RequestCalendarProps {
    requests: SWRequest[];
    activeAgreement: SWAgreement | undefined;
    onRefresh: () => void;
}

export const RequestCalendar: React.FC<RequestCalendarProps> = ({ requests, activeAgreement, onRefresh }) => {
    const [creationModalOpen, setCreationModalOpen] = useState(false);
    const [selectedDate, setSelectedDate] = useState<Date | null>(null);

    const handleDateClick = (arg: { date: Date }) => {
        // Prevent selecting weekends
        const day = arg.date.getDay();
        if (day === 0 || day === 6) return;

        setSelectedDate(arg.date);
        setCreationModalOpen(true);
    };

    const events = requests.map(req => ({
        id: req.id,
        title: 'Smart Working',
        start: req.date,
        backgroundColor: getStatusColor(req.status),
        borderColor: getStatusColor(req.status),
        textColor: '#333',
        extendedProps: {
            status: req.status,
            notes: req.notes
        }
    }));

    function getStatusColor(status: string) {
        switch (status) {
            case 'APPROVED': return '#d1fae5'; // Emerald 100
            case 'PENDING': return '#fef3c7'; // Amber 100
            case 'REJECTED': return '#fee2e2'; // Red 100
            case 'CANCELLED': return '#f3f4f6'; // Gray 100
            default: return '#f3f4f6';
        }
    }

    return (
        <>
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
                    events={events}
                    dateClick={handleDateClick}
                    height="auto"
                    contentHeight="auto"
                    firstDay={1} // Monday
                />
            </Card>

            <RequestCreationModal
                isOpen={creationModalOpen}
                onClose={() => setCreationModalOpen(false)}
                onSuccess={onRefresh}
                selectedDate={selectedDate}
                activeAgreement={activeAgreement}
            />
        </>
    );
};
