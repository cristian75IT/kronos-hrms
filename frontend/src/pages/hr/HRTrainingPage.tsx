import { useState, useEffect } from 'react';
import {
    GraduationCap,
    CheckCircle,
    AlertTriangle,
    Clock,
    Plus,
    FileText,
    Search,
    Download
} from 'lucide-react';
import { hrReportingService } from '../../services/hrReporting.service';
import ServerSideTable from '../../components/common/ServerSideTable';
import { Button } from '../../components/common';
import { AddTrainingModal } from '../../components/hr/AddTrainingModal';
import { createColumnHelper } from '@tanstack/react-table';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { useToast } from '../../context/ToastContext';

// Types (should be in types/index.ts but defining here for now if not exists)
interface TrainingRecord {
    id: string;
    employee_id: string;
    training_type: string;
    training_name: string;
    training_date: string;
    expiry_date: string | null;
    status: string;
    days_until_expiry: number | null;
    hours: number;
}

const columnHelper = createColumnHelper<TrainingRecord>();

export function HRTrainingPage() {
    const [overview, setOverview] = useState<any>(null);
    const [isLoadingOverview, setIsLoadingOverview] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [refreshKey, setRefreshKey] = useState(0);
    const toast = useToast();

    const columns = [
        columnHelper.accessor('employee_name' as any, {
            header: 'Dipendente',
            cell: info => <span className="font-bold text-gray-900">{info.getValue()}</span>
        }),
        columnHelper.accessor('training_name', {
            header: 'Corso',
            cell: info => <span className="font-medium text-gray-700">{info.getValue()}</span>
        }),
        columnHelper.accessor('training_type', {
            header: 'Tipo',
            cell: info => <span className="text-xs uppercase bg-gray-100 px-2 py-1 rounded text-gray-600">{info.getValue()}</span>
        }),
        columnHelper.accessor('training_date', {
            header: 'Data Corso',
            cell: info => format(new Date(info.getValue()), 'd MMM yyyy', { locale: it })
        }),
        columnHelper.accessor('expiry_date', {
            header: 'Scadenza',
            cell: info => {
                const dateVal = info.getValue();
                if (!dateVal) return <span className="text-gray-400">-</span>;
                return format(new Date(dateVal), 'd MMM yyyy', { locale: it });
            }
        }),
        columnHelper.accessor('status', {
            header: 'Stato',
            cell: info => {
                const status = info.getValue();
                const colors = {
                    valido: 'bg-emerald-100 text-emerald-700',
                    scaduto: 'bg-red-100 text-red-700',
                    in_scadenza: 'bg-amber-100 text-amber-700',
                    programmato: 'bg-blue-100 text-blue-700'
                };
                return (
                    <span className={`text-xs font-bold px-2 py-1 rounded-full ${colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-600'}`}>
                        {status.toUpperCase().replace('_', ' ')}
                    </span>
                );
            }
        }),
        columnHelper.accessor('days_until_expiry', {
            header: 'Giorni',
            cell: info => {
                const days = info.getValue();
                if (days === null) return null;
                if (days < 0) return <span className="text-red-600 font-bold">Scaduto</span>;
                if (days <= 60) return <span className="text-amber-600 font-bold">{days} gg</span>;
                return <span className="text-gray-500">{days} gg</span>;
            }
        }),
        // Actions column would go here
    ];

    useEffect(() => {
        loadOverview();
    }, [refreshKey]);

    const loadOverview = async () => {
        try {
            const data = await hrReportingService.getTrainingOverview();
            setOverview(data);
        } catch (error) {
            console.error(error);
            toast.error('Errore caricamento overview formazione');
        } finally {
            setIsLoadingOverview(false);
        }
    };

    return (
        <div className="space-y-6 animate-fadeIn pb-12">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <GraduationCap className="text-indigo-600" />
                        Formazione e Sicurezza
                    </h1>
                    <p className="text-sm text-gray-500">Gestione corsi, scadenze e sorveglianza sanitaria (D.Lgs. 81/08)</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => { }}>
                        <Download size={16} className="mr-2" /> Export
                    </Button>
                    <Button variant="primary" onClick={() => setIsModalOpen(true)}>
                        <Plus size={16} className="mr-2" /> Nuova Registrazione
                    </Button>
                </div>
            </div>

            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    title="Dipendenti Conformi"
                    value={overview?.fully_compliant ?? '-'}
                    total={overview?.total_employees}
                    icon={<CheckCircle className="text-emerald-600" />}
                    color="bg-emerald-50"
                    loading={isLoadingOverview}
                />
                <StatCard
                    title="In Scadenza (30gg)"
                    value={overview?.trainings_expiring_30_days ?? '-'}
                    icon={<Clock className="text-amber-600" />}
                    color="bg-amber-50"
                    loading={isLoadingOverview}
                />
                <StatCard
                    title="Scaduti / Non Conformi"
                    value={(overview?.trainings_expired ?? 0) + (overview?.non_compliant ?? 0)}
                    icon={<AlertTriangle className="text-red-600" />}
                    color="bg-red-50"
                    loading={isLoadingOverview}
                    warn={true}
                />
                <StatCard
                    title="Visite Mediche (Mese)"
                    value={overview?.medical_visits_due ?? '-'}
                    icon={<FileText className="text-blue-600" />}
                    color="bg-blue-50"
                    loading={isLoadingOverview}
                />
            </div>

            {/* Main DataTable */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                    <h3 className="font-bold text-gray-900 flex items-center gap-2">
                        <Search size={16} className="text-gray-400" />
                        Registro Formazione
                    </h3>
                </div>
                <div className="p-4">
                    <ServerSideTable
                        apiEndpoint="/hr/training/datatable"
                        method="GET"
                        columns={columns}
                        className="bg-white"
                        refreshTrigger={refreshKey}
                    />
                </div>
            </div>

            {/* Modals */}
            <AddTrainingModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onValuesSaved={() => {
                    setRefreshKey(prev => prev + 1); // Triggers loadOverview via useEffect and Table refresh via prop
                }}
            />
        </div>
    );
}

function StatCard({ title, value, total, icon, color, loading, warn }: any) {
    if (loading) return (
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 animate-pulse h-24"></div>
    );

    return (
        <div className={`bg-white p-5 rounded-xl shadow-sm border border-gray-200 flex items-start gap-4 hover:shadow-md transition-shadow ${warn && value > 0 ? 'border-red-200 bg-red-50/30' : ''}`}>
            <div className={`p-3 rounded-xl shrink-0 ${color}`}>
                {icon}
            </div>
            <div>
                <p className="text-xs font-bold text-gray-400 uppercase tracking-wide mb-1">{title}</p>
                <div className="flex items-baseline gap-1">
                    <h3 className={`text-2xl font-black leading-none mb-1 ${warn && value > 0 ? 'text-red-600' : 'text-gray-900'}`}>{value}</h3>
                    {total !== undefined && <span className="text-xs text-gray-500 font-medium">/ {total}</span>}
                </div>
            </div>
        </div>
    );
}

export default HRTrainingPage;
