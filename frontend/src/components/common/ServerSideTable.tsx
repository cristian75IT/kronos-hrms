import { useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
  type PaginationState,
  type SortingState,
} from '@tanstack/react-table';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown, AlertCircle, Loader2, Database } from 'lucide-react';
import api from '../../services/api';
import { EmptyState } from './EmptyState';

// Backend Response Structure (DataTables compatible)
interface DataTableResponse<T> {
  draw: number;
  recordsTotal: number;
  recordsFiltered: number;
  data: T[];
  error?: string;
}

export interface ServerSideTableProps<T extends object> {
  apiEndpoint: string;
  columns: ColumnDef<T, any>[];
  extraData?: Record<string, any>;
  pageLength?: number;
  onRowClick?: (row: T) => void;
  className?: string;
  showExport?: boolean; // Kept for interface compatibility
  refreshTrigger?: number; // Optional prop to trigger manual refetch
  method?: 'GET' | 'POST'; // Added method prop
  emptyState?: {
    title?: string;
    description?: string;
    icon?: React.ElementType;
    actionLabel?: string;
    onAction?: () => void;
  };
}

export function ServerSideTable<T extends object>({
  apiEndpoint,
  columns,
  extraData = {},
  pageLength = 10,
  onRowClick,
  className = '',
  refreshTrigger = 0,
  method = 'POST', // Default to POST
  emptyState
}: ServerSideTableProps<T>) {

  // -- State --
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: pageLength,
  });
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter] = useState('');

  // -- Data Fetching with React Query --
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery<DataTableResponse<T>>({
    queryKey: ['tableData', apiEndpoint, pagination, sorting, extraData, refreshTrigger],
    queryFn: async () => {

      // Map TanStack state to DataTables backend params
      const start = pagination.pageIndex * pagination.pageSize;
      const length = pagination.pageSize;

      const order = sorting.map((sort, index) => ({
        column: index, // Backend likely expects index-based sorting for now
        dir: sort.desc ? 'desc' : 'asc',
        name: sort.id
      }));

      const payload = {
        draw: Date.now(),
        start,
        length,
        search: { value: globalFilter, regex: false },
        order,
        ...extraData,
      };

      // api instance already handles Authorization header and baseURL
      let response;
      if (method === 'GET') {
        // Serialize payload for GET
        response = await api.get(apiEndpoint, { params: payload });
      } else {
        response = await api.post(apiEndpoint, payload);
      }

      return response.data;
    },
    placeholderData: (previousData) => previousData, // Keep previous data while fetching new
    staleTime: 5000,
  });

  // -- TanStack Table Instance --
  const table = useReactTable({
    data: data?.data ?? [],
    columns,
    pageCount: data?.recordsFiltered ? Math.ceil(data.recordsFiltered / pagination.pageSize) : -1,
    state: {
      pagination,
      sorting,
    },
    onPaginationChange: setPagination,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
    // debugTable: true,
  });

  // -- Render --
  return (
    <div className={`flex flex-col gap-4 w-full ${className}`}>

      {/* Table Container */}
      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm relative min-h-[300px]">

        {/* Loading Overlay */}
        {(isLoading || isFetching) && (
          <div className="absolute inset-0 bg-white/60 z-10 flex items-center justify-center backdrop-blur-[1px]">
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-lg border border-slate-200">
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
              <span className="text-sm font-medium text-slate-600">Caricamento...</span>
            </div>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/90">
            <EmptyState
              variant="small"
              title="Errore nel caricamento"
              description={(error as Error)?.message || 'Impossibile comunicare con il server'}
              icon={AlertCircle}
              actionLabel="Riprova"
              onAction={() => refetch()}
              className="text-red-600"
            />
          </div>
        )}

        <table className="table-auto w-full text-left bg-white border-collapse">
          <thead className="bg-slate-50 text-slate-500 uppercase text-xs font-bold tracking-wider border-b border-slate-200">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => {
                  return (
                    <th
                      key={header.id}
                      className="px-4 py-3 whitespace-nowrap overflow-hidden text-ellipsis relative font-semibold"
                      style={{ width: header.getSize() !== 150 ? header.getSize() : undefined }} // Use TanStack size if set explicity
                    >
                      {header.isPlaceholder ? null : (
                        <div
                          className={`flex items-center gap-2 cursor-pointer select-none ${header.column.getCanSort() ? 'hover:text-primary transition-colors' : ''
                            }`}
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {{
                            asc: <ArrowUp size={14} className="text-primary" />,
                            desc: <ArrowDown size={14} className="text-primary" />,
                          }[header.column.getIsSorted() as string] ?? (
                              header.column.getCanSort() ? <ArrowUpDown size={14} className="opacity-30 hover:opacity-100" /> : null
                            )}
                        </div>
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-slate-100">
            {table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map(row => (
                <tr
                  key={row.id}
                  className={`hover:bg-slate-50 transition-colors group ${onRowClick ? 'cursor-pointer active:bg-slate-100' : ''}`}
                  onClick={() => onRowClick && onRowClick(row.original)}
                >
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-4 py-3 text-sm text-slate-600 truncate group-hover:text-slate-900">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              !isLoading && (
                <tr>
                  <td colSpan={columns.length} className="p-0">
                    <EmptyState
                      title={emptyState?.title || "Nessun dato trovato"}
                      description={emptyState?.description || "Non ci sono record da mostrare in questa vista."}
                      icon={emptyState?.icon || Database}
                      actionLabel={emptyState?.actionLabel}
                      onAction={emptyState?.onAction}
                      variant="default"
                    />
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-2">
        <div className="text-sm text-slate-500">
          Pagina <span className="font-medium text-slate-900">{table.getState().pagination.pageIndex + 1}</span> di{' '}
          <span className="font-medium text-slate-900">{table.getPageCount() > 0 ? table.getPageCount() : 1}</span>
          <span className="mx-2 hidden sm:inline">•</span>
          Totale: {data?.recordsFiltered || 0}
        </div>

        <div className="flex items-center gap-2">
          <button
            className="p-1 px-2 rounded border border-slate-200 hover:bg-white hover:border-slate-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors bg-white shadow-sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronLeft size={16} className="text-slate-600" />
          </button>

          <select
            value={table.getState().pagination.pageSize}
            onChange={e => {
              table.setPageSize(Number(e.target.value))
            }}
            className="h-8 rounded border border-slate-200 bg-white text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary shadow-sm px-2 cursor-pointer"
          >
            {[10, 20, 30, 50, 100].map(pageSize => (
              <option key={pageSize} value={pageSize}>
                {pageSize}
              </option>
            ))}
          </select>

          <button
            className="p-1 px-2 rounded border border-slate-200 hover:bg-white hover:border-slate-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors bg-white shadow-sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <ChevronRight size={16} className="text-slate-600" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default ServerSideTable;
