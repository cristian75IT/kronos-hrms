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
import { ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown, AlertCircle, Loader2 } from 'lucide-react';
import api from '../../services/api';

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
        // Note: complex objects like 'order' and 'search' might need specific serialization 
        // compatible with what the backend expects (e.g. PHP/Laravel style or simple JSON)
        // For now, sending as query params, axios handles basic serialization.
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
      <div className="overflow-x-auto rounded-lg border border-base-200 bg-base-100 shadow-sm relative min-h-[300px]">

        {/* Loading Overlay */}
        {(isLoading || isFetching) && (
          <div className="absolute inset-0 bg-white/60 z-10 flex items-center justify-center backdrop-blur-[1px]">
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-lg border border-base-200">
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
              <span className="text-sm font-medium text-base-content/70">Caricamento...</span>
            </div>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/90">
            <div className="flex flex-col items-center text-center p-6 max-w-sm">
              <AlertCircle className="w-10 h-10 text-error mb-2" />
              <h3 className="font-bold text-lg text-error">Errore</h3>
              <p className="text-sm text-base-content/70 mb-4">
                {(error as Error)?.message || 'Impossibile caricare i dati'}
              </p>
              <button onClick={() => refetch()} className="btn btn-sm btn-outline btn-error">
                Riprova
              </button>
            </div>
          </div>
        )}

        <table className="table table-fixed w-full text-left bg-base-100">
          <thead className="bg-slate-50 text-slate-500 uppercase text-xs font-bold tracking-wider border-b border-slate-200">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => {
                  // Allow column definitions to pass styling via meta or simpler logic if needed
                  // For now, relies on column defs size/width handling by TanStack or custom classes in header
                  return (
                    <th
                      key={header.id}
                      className="px-4 py-3 whitespace-nowrap overflow-hidden text-ellipsis relative"
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
                  className={`hover:bg-slate-50 transition-colors ${onRowClick ? 'cursor-pointer active:bg-slate-100' : ''}`}
                  onClick={() => onRowClick && onRowClick(row.original)}
                >
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-4 py-3 text-sm text-slate-600 truncate">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              !isLoading && (
                <tr>
                  <td colSpan={columns.length} className="text-center py-16 text-slate-400 bg-slate-50/30">
                    <div className="flex flex-col items-center gap-2">
                      <AlertCircle size={24} className="opacity-20" />
                      <span>Nessun dato trovato</span>
                    </div>
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-2">
        <div className="text-sm text-base-content/60">
          Pagina <span className="font-medium text-base-content">{table.getState().pagination.pageIndex + 1}</span> di{' '}
          <span className="font-medium text-base-content">{table.getPageCount() > 0 ? table.getPageCount() : 1}</span>
          <span className="mx-2 hidden sm:inline">•</span>
          Totale: {data?.recordsFiltered || 0}
        </div>

        <div className="join">
          <button
            className="join-item btn btn-sm bg-base-100 hover:bg-white border-base-300"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronLeft size={16} />
          </button>

          <select
            value={table.getState().pagination.pageSize}
            onChange={e => {
              table.setPageSize(Number(e.target.value))
            }}
            className="join-item select select-sm select-bordered w-20 bg-base-100 font-normal focus:outline-none"
          >
            {[10, 20, 30, 50, 100].map(pageSize => (
              <option key={pageSize} value={pageSize}>
                {pageSize}
              </option>
            ))}
          </select>

          <button
            className="join-item btn btn-sm bg-base-100 hover:bg-white border-base-300"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default ServerSideTable;
