import React from 'react';
import { ServerSideTable } from '../../../components/common/ServerSideTable';
import type { ColumnDef } from '@tanstack/react-table';

interface NotificationHistoryProps {
    refreshTrigger?: number;
}

export const NotificationHistory: React.FC<NotificationHistoryProps> = ({ refreshTrigger = 0 }) => {

    // Determine the API endpoint
    // NOTE: ServerSideTable uses POST by default. Our endpoint is GET /notifications/history.
    // If we want to use ServerSideTable without modifying it, we need an adapter or a new endpoint.
    // However, looking at ServerSideTable, it uses `ajaxConfig` with `type: 'POST'`. 
    // Changing the component just for this might be risky if used elsewhere.
    // Strategy: Since I cannot easily change the backend to POST right now without context (User is waiting),
    // I will use a local wrapper or create a specialized table?
    // Alternative: Use ServerSideTable but pass a custom ajax config if possible? 
    // It doesn't seem to expose ajax config override, just `apiEndpoint`.
    //
    // WAIT: I am the agent. I can modify `ServerSideTable` to accept an optional `method` prop!
    // That is the "Enterprise" way to make it flexible.

    const columns: ColumnDef<any>[] = React.useMemo(() => [
        {
            accessorKey: 'created_at',
            header: 'DATA',
            cell: (info) => new Date(info.getValue() as string).toLocaleString()
        },
        {
            accessorKey: 'title',
            header: 'TITOLO'
        },
        {
            accessorKey: 'notification_type',
            header: 'TIPO',
            cell: (info) => (
                <span className="px-2 py-1 rounded-full bg-slate-100 text-xs font-medium text-slate-600">
                    {info.getValue() as string}
                </span>
            )
        },
        {
            accessorKey: 'channel',
            header: 'CANALE',
            cell: (info) => (
                <span className="uppercase text-xs font-bold tracking-wider text-slate-500">
                    {info.getValue() as string}
                </span>
            )
        },
        {
            accessorKey: 'status',
            header: 'STATO',
            cell: ({ row }) => {
                const data = row.original;
                if (data.read_at) {
                    return (
                        <div className="flex items-center gap-1 text-green-600 font-medium">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6L9 17l-5-5" /></svg>
                            Letto
                        </div>
                    );
                }
                if (data.status === 'failed') {
                    return (
                        <div className="flex items-center gap-1 text-red-600 font-medium">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
                            Fallito
                        </div>
                    );
                }
                return (
                    <div className="flex items-center gap-1 text-blue-600 font-medium">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                        Inviato
                    </div>
                );
            }
        }
    ], []);

    // Important: We need to modify ServerSideTable to support GET or add a POST endpoint.
    // Since I'm creating this file, I assume I'll mod ServerSideTable next.
    return (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
                <h3 className="font-semibold text-slate-700">Registro Attività</h3>
                {/* Export buttons are handled by ServerSideTable if showExport is true */}
            </div>
            <ServerSideTable
                apiEndpoint="/notifications/history/datatable"
                method="POST"
                columns={columns}
                pageLength={10}
                showExport={true}
                className="kronos-table-clean"
                refreshTrigger={refreshTrigger}
            />
        </div>
    );
};
