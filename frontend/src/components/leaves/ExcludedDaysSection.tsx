/**
 * KRONOS - Excluded Days Section Component
 * 
 * Displays days excluded from leave calculation (weekends, holidays, closures).
 */
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { Ban, Sunrise, Building, Loader } from 'lucide-react';
import { leavesService } from '../../services/leaves.service';

interface ExcludedDay {
    date: string;
    reason: 'weekend' | 'holiday' | 'closure';
    name: string;
}

interface ExcludedDaysSectionProps {
    startDate: string;
    endDate: string;
}

export function ExcludedDaysSection({ startDate, endDate }: ExcludedDaysSectionProps) {
    const { data, isLoading, isError } = useQuery({
        queryKey: ['excluded-days', startDate, endDate],
        queryFn: () => leavesService.getExcludedDays(startDate, endDate),
        enabled: !!startDate && !!endDate,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });

    const excludedDays = data?.excluded_days || [];

    if (isLoading) {
        return (
            <div className="mt-6 pt-6 border-t border-gray-100">
                <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Loader size={14} className="animate-spin" />
                    Caricamento giorni esclusi...
                </div>
            </div>
        );
    }

    if (isError || excludedDays.length === 0) {
        return null;
    }

    const getReasonIcon = (reason: string) => {
        switch (reason) {
            case 'weekend':
                return <Ban size={14} className="text-gray-400" />;
            case 'holiday':
                return <Sunrise size={14} className="text-amber-500" />;
            case 'closure':
                return <Building size={14} className="text-blue-500" />;
            default:
                return <Ban size={14} className="text-gray-400" />;
        }
    };

    const getReasonLabel = (reason: string) => {
        switch (reason) {
            case 'weekend':
                return 'Weekend';
            case 'holiday':
                return 'Festività';
            case 'closure':
                return 'Chiusura';
            default:
                return reason;
        }
    };

    const getReasonBadgeClass = (reason: string) => {
        switch (reason) {
            case 'weekend':
                return 'bg-gray-200 text-gray-600';
            case 'holiday':
                return 'bg-amber-100 text-amber-700';
            case 'closure':
                return 'bg-blue-100 text-blue-700';
            default:
                return 'bg-gray-200 text-gray-600';
        }
    };

    return (
        <div className="mt-6 pt-6 border-t border-gray-100">
            <h4 className="text-xs uppercase font-semibold text-gray-400 mb-3 tracking-wide flex items-center gap-2">
                <Ban size={14} />
                Giorni non conteggiati ({excludedDays.length})
            </h4>
            <div className="space-y-2">
                {excludedDays.map((day: ExcludedDay, index: number) => (
                    <div
                        key={index}
                        className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg text-sm"
                    >
                        <div className="flex items-center gap-3">
                            {getReasonIcon(day.reason)}
                            <span className="text-gray-700 capitalize">
                                {format(new Date(day.date), 'EEEE d MMM', { locale: it })}
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-gray-500">{day.name}</span>
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getReasonBadgeClass(day.reason)}`}>
                                {getReasonLabel(day.reason)}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
