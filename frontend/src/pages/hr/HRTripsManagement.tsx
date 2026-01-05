import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Plane,
    MapPin,
    Search,
    CheckCircle,
    XCircle,
    Clock,
    User,
    Eye
} from 'lucide-react';
import ServerSideTable from '../../components/common/ServerSideTable';
import { Button } from '../../components/common';
import { createColumnHelper } from '@tanstack/react-table';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

// Types
interface HRTripItem {
    id: string;
    user_id: string;
    user_name: string | null;
    department: string | null;
    destination: string;
    purpose: string | null;
    start_date: string;
    end_date: string;
    days_count: number;
    total_allowance: number;
    status: string;
    created_at: string;
}

const columnHelper = createColumnHelper<HRTripItem>();

export function HRTripsManagement() {
    const [filters, setFilters] = useState({
        status: '',
    });

    const handleFilterChange = (key: string, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const columns = [
        columnHelper.accessor('user_name', {
            header: 'Dipendente',
            cell: info => (
                <div className="flex items-center gap-2">
                    <div className="bg-purple-50 p-1.5 rounded-full text-purple-600">
                        <User size={14} />
                    </div>
                    <div>
                        <div className="font-bold text-gray-900">{info.getValue() || 'N/A'}</div>
                        <div className="text-[10px] text-gray-500">{info.row.original.department || 'N/A'}</div>
                    </div>
                </div>
            )
        }),
        columnHelper.accessor('destination', {
            header: 'Destinazione',
            cell: info => (
                <div className="flex items-center gap-2">
                    <MapPin size={14} className="text-gray-400" />
                    <span className="font-medium text-gray-900">{info.getValue()}</span>
                </div>
            )
        }),
        columnHelper.accessor('start_date', {
            header: 'Periodo',
            cell: info => (
                <div className="text-sm">
                    <span className="font-medium">{format(new Date(info.getValue()), 'd MMM', { locale: it })}</span>
                    <span className="text-gray-400 mx-1">➜</span>
                    <span className="font-medium">{format(new Date(info.row.original.end_date), 'd MMM yyyy', { locale: it })}</span>
                </div>
            )
        }),
        columnHelper.accessor('total_allowance', {
            header: 'Budget Est.',
            cell: info => (
                <span className="font-mono font-bold text-gray-700 bg-gray-50 px-2 py-1 rounded border border-gray-200">
                    € {info.getValue() ? Number(info.getValue()).toFixed(2) : '0.00'}
                </span>
            )
        }),
        columnHelper.accessor('status', {
            header: 'Stato',
            cell: info => {
                const status = info.getValue();
                let colorClass = 'bg-gray-100 text-gray-600';
                let icon = <Clock size={12} />;

                if (status === 'approved') {
                    colorClass = 'bg-emerald-100 text-emerald-700';
                    icon = <CheckCircle size={12} />;
                } else if (status === 'rejected') {
                    colorClass = 'bg-red-100 text-red-700';
                    icon = <XCircle size={12} />;
                } else if (status === 'pending') {
                    colorClass = 'bg-amber-100 text-amber-700';
                }

                return (
                    <span className={`flex items-center gap-1.5 w-fit px-2.5 py-1 rounded-full text-xs font-bold capitalize ${colorClass}`}>
                        {icon}
                        {status === 'pending' ? 'Richiesta' : status === 'approved' ? 'Approvata' : status === 'rejected' ? 'Rifiutata' : status}
                    </span>
                );
            }
        }),
        columnHelper.display({
            id: 'actions',
            header: 'Azioni',
            cell: info => (
                <Link
                    to={`/trips/${info.row.original.id}`}
                    className="flex items-center justify-center w-8 h-8 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-colors"
                    title="Vedi Dettagli"
                >
                    <Eye size={18} />
                </Link>
            )
        }),
    ];



    return (
        <div className="space-y-6 animate-fadeIn pb-12">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Plane className="text-indigo-600" />
                        Gestione Trasferte
                    </h1>
                    <p className="text-sm text-gray-500">Monitoraggio missioni e calcolo diarie</p>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-wrap gap-4 items-end">
                <div className="w-full md:w-auto flex-1 max-w-xs">
                    <label className="text-xs font-bold text-gray-500 uppercase mb-1 block">Stato Trasferta</label>
                    <select
                        className="w-full h-10 px-3 rounded-lg border border-gray-300 bg-gray-50 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                        value={filters.status}
                        onChange={(e) => handleFilterChange('status', e.target.value)}
                    >
                        <option value="">Tutti gli stati</option>
                        <option value="pending">In Attesa</option>
                        <option value="approved">Approvate</option>
                        <option value="rejected">Rifiutate</option>
                    </select>
                </div>

                <div className="w-full md:w-auto">
                    <Button variant="secondary" onClick={() => setFilters({ status: '' })}>
                        Reset Filtri
                    </Button>
                </div>
            </div>

            {/* Main DataTable */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                    <h3 className="font-bold text-gray-900 flex items-center gap-2">
                        <Search size={16} className="text-gray-400" />
                        Registro Missioni
                    </h3>
                </div>
                <div className="p-4">
                    <ServerSideTable
                        apiEndpoint="/trips/admin/datatable"
                        method="POST"
                        columns={columns}
                        extraData={{
                            status: filters.status
                        }}
                        className="bg-white"
                        onRowClick={(/* row */) => {
                            // Handler code
                        }}
                    />
                </div>
            </div>
        </div>
    );
}

export default HRTripsManagement;
