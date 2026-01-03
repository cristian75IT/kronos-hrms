import { useState } from 'react';
import {
    Receipt,
    Search,
    CheckCircle,
    XCircle,
    Clock,
    User,
    Euro
} from 'lucide-react';
import ServerSideTable from '../../components/common/ServerSideTable';
import { Button } from '../../components/common';
import { createColumnHelper } from '@tanstack/react-table';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

// Types
interface HRExpenseItem {
    id: string;
    employee_id: string;
    employee_name: string;
    department: string | null;
    trip_id: string | null;
    trip_destination: string | null;
    total_amount: number;
    items_count: number;
    status: string;
    submitted_at: string;
}

const columnHelper = createColumnHelper<HRExpenseItem>();

export function HRExpensesManagement() {
    const [filters, setFilters] = useState({
        status: '',
    });

    const handleFilterChange = (key: string, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const columns = [
        columnHelper.accessor('employee_name', {
            header: 'Dipendente',
            cell: info => (
                <div className="flex items-center gap-2">
                    <div className="bg-green-50 p-1.5 rounded-full text-green-600">
                        <User size={14} />
                    </div>
                    <div>
                        <div className="font-bold text-gray-900">{info.getValue()}</div>
                        <div className="text-[10px] text-gray-500">{info.row.original.department || 'N/A'}</div>
                    </div>
                </div>
            )
        }),
        columnHelper.accessor('trip_destination', {
            header: 'Riferimento',
            cell: info => (
                info.getValue() ? (
                    <span className="text-sm text-gray-700">Missione: <strong>{info.getValue()}</strong></span>
                ) : <span className="text-gray-400 text-sm">Generico</span>
            )
        }),
        columnHelper.accessor('items_count', {
            header: 'Voci',
            cell: info => <span className="text-sm px-2 py-0.5 bg-gray-100 rounded text-gray-600">{info.getValue()}</span>
        }),
        columnHelper.accessor('total_amount', {
            header: 'Importo',
            cell: info => (
                <div className="flex items-center gap-1 font-bold text-gray-900">
                    <Euro size={12} className="text-gray-400" />
                    {info.getValue().toFixed(2)}
                </div>
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
                } else if (status === 'submitted') {
                    colorClass = 'bg-amber-100 text-amber-700';
                } else if (status === 'paid') {
                    colorClass = 'bg-blue-100 text-blue-700';
                    icon = <Euro size={12} />;
                }

                return (
                    <span className={`flex items-center gap-1.5 w-fit px-2.5 py-1 rounded-full text-xs font-bold capitalize ${colorClass}`}>
                        {icon}
                        {status === 'submitted' ? 'Inviata' : status === 'paid' ? 'Pagata' : status}
                    </span>
                );
            }
        }),
        columnHelper.accessor('submitted_at', {
            header: 'Inviata il',
            cell: info => info.getValue() ? <span className="text-gray-500 text-xs">{format(new Date(info.getValue()), 'd MMM HH:mm', { locale: it })}</span> : '-'
        }),
    ];

    return (
        <div className="space-y-6 animate-fadeIn pb-12">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Receipt className="text-indigo-600" />
                        Gestione Note Spese
                    </h1>
                    <p className="text-sm text-gray-500">Approvazione rimborsi e controllo costi</p>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-wrap gap-4 items-end">
                <div className="w-full md:w-auto flex-1 max-w-xs">
                    <label className="text-xs font-bold text-gray-500 uppercase mb-1 block">Stato Rimborso</label>
                    <select
                        className="w-full h-10 px-3 rounded-lg border border-gray-300 bg-gray-50 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                        value={filters.status}
                        onChange={(e) => handleFilterChange('status', e.target.value)}
                    >
                        <option value="">Tutti gli stati</option>
                        <option value="submitted">Inviate</option>
                        <option value="approved">Approvate</option>
                        <option value="paid">Pagate</option>
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
                        Elenco Note Spese
                    </h3>
                </div>
                <div className="p-4">
                    <ServerSideTable
                        apiEndpoint="/hr/management/expenses/datatable"
                        method="GET"
                        columns={columns}
                        extraData={{
                            status_filter: filters.status
                        }}
                        className="bg-white"
                    />
                </div>
            </div>
        </div>
    );
}

export default HRExpensesManagement;
