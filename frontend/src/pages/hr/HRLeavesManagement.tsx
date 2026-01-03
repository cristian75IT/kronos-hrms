import { useState } from 'react';
import {
    TreePalm,
    Search,
    CheckCircle,
    XCircle,
    Clock,
    User
} from 'lucide-react';
import ServerSideTable from '../../components/common/ServerSideTable';
import { Button } from '../../components/common';
import { createColumnHelper } from '@tanstack/react-table';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

// Types
interface HRLeaveItem {
    id: string;
    employee_id: string;
    employee_name: string;
    department: string | null;
    leave_type: string;
    leave_type_name: string;
    start_date: string;
    end_date: string;
    days_count: number;
    hours_count: number | null;
    status: string;
    created_at: string;
}

const columnHelper = createColumnHelper<HRLeaveItem>();

export function HRLeavesManagement() {
    const [filters, setFilters] = useState({
        status: '',
        leave_type: '',
        search: '' // handled by global filter usually but can be custom
    });

    // Function to handle filter changes could be added here
    const handleFilterChange = (key: string, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const columns = [
        columnHelper.accessor('employee_name', {
            header: 'Dipendente',
            cell: info => (
                <div className="flex items-center gap-2">
                    <div className="bg-indigo-50 p-1.5 rounded-full text-indigo-600">
                        <User size={14} />
                    </div>
                    <div>
                        <div className="font-bold text-gray-900">{info.getValue()}</div>
                        <div className="text-[10px] text-gray-500">{info.row.original.department || 'N/A'}</div>
                    </div>
                </div>
            )
        }),
        columnHelper.accessor('leave_type_name', {
            header: 'Tipo',
            cell: info => <span className="font-medium text-gray-700">{info.getValue()}</span>
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
        columnHelper.accessor('days_count', {
            header: 'Durata',
            cell: info => (
                <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-50 text-gray-700 text-xs font-medium border border-gray-200">
                    {info.getValue()} {info.getValue() === 1 ? 'giorno' : 'giorni'}
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
                        {status === 'pending' ? 'In Attesa' : status === 'approved' ? 'Approvata' : 'Rifiutata'}
                    </span>
                );
            }
        }),
        columnHelper.accessor('created_at', {
            header: 'Richiesta il',
            cell: info => <span className="text-gray-500 text-xs">{format(new Date(info.getValue()), 'd MMM HH:mm', { locale: it })}</span>
        }),
    ];

    return (
        <div className="space-y-6 animate-fadeIn pb-12">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <TreePalm className="text-indigo-600" />
                        Gestione Ferie e Permessi
                    </h1>
                    <p className="text-sm text-gray-500">Supervisione globale delle richieste di assenza</p>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-wrap gap-4 items-end">
                <div className="w-full md:w-auto flex-1 max-w-xs">
                    <label className="text-xs font-bold text-gray-500 uppercase mb-1 block">Stato Richiesta</label>
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

                <div className="w-full md:w-auto flex-1 max-w-xs">
                    <label className="text-xs font-bold text-gray-500 uppercase mb-1 block">Tipo Assenza</label>
                    <select
                        className="w-full h-10 px-3 rounded-lg border border-gray-300 bg-gray-50 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                        value={filters.leave_type}
                        onChange={(e) => handleFilterChange('leave_type', e.target.value)}
                    >
                        <option value="">Tutti i tipi</option>
                        <option value="ferie">Ferie</option>
                        <option value="permesso">Permesso</option>
                        <option value="malattia">Malattia</option>
                    </select>
                </div>

                <div className="w-full md:w-auto">
                    <Button variant="secondary" onClick={() => setFilters({ status: '', leave_type: '', search: '' })}>
                        Reset Filtri
                    </Button>
                </div>
            </div>

            {/* Main DataTable */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                    <h3 className="font-bold text-gray-900 flex items-center gap-2">
                        <Search size={16} className="text-gray-400" />
                        Elenco Richieste
                    </h3>
                </div>
                <div className="p-4">
                    <ServerSideTable
                        apiEndpoint="/hr/management/leaves/datatable"
                        method="GET"
                        columns={columns}
                        extraData={{
                            status_filter: filters.status,
                            leave_type_filter: filters.leave_type
                        }}
                        className="bg-white"
                        onRowClick={(/* row */) => {
                            // Navigate to detail or open modal
                            // window.location.href = `/leaves/${row.id}`; 
                            // Since we are HR, we might want a special HR detail view or reuse the existing one
                        }}
                    />
                </div>
            </div>
        </div>
    );
}

export default HRLeavesManagement;
