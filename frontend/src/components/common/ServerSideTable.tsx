/**
 * KRONOS - Enterprise Server-Side DataTable Component
 * Implements DataTables.net with server-side processing as per tech-stack.md
 */
import DataTable from 'datatables.net-react';
import DT from 'datatables.net-dt';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { useState, useRef, useCallback } from 'react';
import { tokenStorage } from '../../utils/tokenStorage';

// Initialize DataTables
DataTable.use(DT);

export interface ColumnDef {
    data: string;
    title: string;
    orderable?: boolean;
    searchable?: boolean;
    render?: (data: any, type: string, row: any) => string;
    className?: string;
    width?: string;
}

export interface ServerSideTableProps {
    /** API endpoint for server-side processing (POST) */
    apiEndpoint: string;
    /** Column definitions */
    columns: ColumnDef[];
    /** Optional: Additional request data to send with each request */
    extraData?: Record<string, any>;
    /** Optional: Default page length */
    pageLength?: number;
    /** Optional: Row click handler */
    onRowClick?: (rowData: any) => void;
    /** Optional: Custom class for the table container */
    className?: string;
    /** Optional: Show export buttons */
    showExport?: boolean;
    /** Optional: Table ID for external control */
    tableId?: string;
}

/**
 * Enterprise Server-Side DataTable
 * 
 * Features:
 * - Server-side pagination, filtering, and sorting
 * - JWT token injection via Authorization header
 * - Italian localization
 * - Responsive design
 * - Export capabilities (Excel, PDF, CSV)
 * - Premium styling aligned with KRONOS design system
 */
export function ServerSideTable({
    apiEndpoint,
    columns,
    extraData = {},
    pageLength = 25,
    onRowClick,
    className = '',
    showExport = false,
    tableId,
}: ServerSideTableProps) {
    const [error, setError] = useState<string | null>(null);
    const tableRef = useRef<any>(null);

    // Get token from storage
    const token = tokenStorage.getAccessToken();

    // Build the AJAX configuration with JWT token
    const ajaxConfig = {
        url: apiEndpoint,
        type: 'POST',
        contentType: 'application/json',
        headers: {
            Authorization: `Bearer ${token}`,
        },
        data: (d: any) => {
            const requestData = {
                ...d,
                ...extraData,
            };
            return JSON.stringify(requestData);
        },
        dataSrc: (json: any) => {
            setError(null);
            return json.data || [];
        },
        error: (_xhr: any, _error: string, _thrown: string) => {
            setError('Errore durante il caricamento dei dati');
        },
    };

    // DataTables options
    const options: any = {
        serverSide: true,
        processing: true,
        responsive: true,
        pageLength,
        lengthMenu: [10, 25, 50, 100],
        order: [[0, 'desc'] as [number, string]],
        language: {
            url: '//cdn.datatables.net/plug-ins/2.0.0/i18n/it-IT.json',
            processing: '<div class="dt-loading"><div class="dt-spinner"></div><span>Caricamento...</span></div>',
            emptyTable: 'Nessun dato disponibile',
            zeroRecords: 'Nessun risultato trovato',
        },
        dom: showExport
            ? '<"dt-header"<"dt-length"l><"dt-search"f><"dt-buttons"B>>rt<"dt-footer"<"dt-info"i><"dt-pagination"p>>'
            : '<"dt-header"<"dt-length"l><"dt-search"f>>rt<"dt-footer"<"dt-info"i><"dt-pagination"p>>',
        buttons: showExport ? ['excel', 'pdf', 'csv'] : [],
        drawCallback: () => {
            // Add row click handlers after each draw
            if (onRowClick && tableRef.current) {
                const tableElement = tableRef.current;
                const rows = tableElement.querySelectorAll('tbody tr');
                rows.forEach((row: HTMLElement) => {
                    row.style.cursor = 'pointer';
                    row.onclick = () => {
                        const table = (window as any).$(tableElement).DataTable();
                        const rowData = table.row(row).data();
                        if (rowData) {
                            onRowClick(rowData);
                        }
                    };
                });
            }
        },
    };

    // Refresh function for external use
    const refresh = useCallback(() => {
        if (tableRef.current) {
            const table = (window as any).$(tableRef.current).DataTable();
            table.ajax.reload(null, false);
        }
    }, []);

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center p-12 bg-error/5 rounded-2xl border border-error/20">
                <AlertCircle size={48} className="text-error mb-4" />
                <h3 className="text-lg font-bold text-error mb-2">Errore di Caricamento</h3>
                <p className="text-sm text-base-content/60 mb-4">{error}</p>
                <button
                    onClick={refresh}
                    className="btn btn-primary btn-sm rounded-xl"
                >
                    <RefreshCw size={16} /> Riprova
                </button>
            </div>
        );
    }

    return (
        <div className={`kronos-datatable ${className}`}>
            <DataTable
                ref={tableRef}
                id={tableId}
                ajax={ajaxConfig}
                columns={columns}
                options={options}
                className="display responsive nowrap w-full"
            />

            <style>{`
        .kronos-datatable {
          --dt-row-hover: rgba(99, 102, 241, 0.04);
          --dt-row-stripe: rgba(0, 0, 0, 0.02);
          --dt-border-color: var(--color-border-light, #f1f5f9);
          --dt-primary: var(--color-primary, #5046e5);
        }

        .kronos-datatable table.dataTable {
          border-collapse: collapse;
          width: 100% !important;
          font-size: 0.875rem;
        }

        .kronos-datatable table.dataTable thead th {
          background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
          color: #475569;
          font-size: 0.65rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          padding: 1rem 1.25rem;
          border-bottom: 2px solid var(--dt-border-color);
          white-space: nowrap;
        }

        .kronos-datatable table.dataTable tbody td {
          padding: 1rem 1.25rem;
          border-bottom: 1px solid var(--dt-border-color);
          vertical-align: middle;
        }

        .kronos-datatable table.dataTable tbody tr:hover {
          background: var(--dt-row-hover) !important;
        }

        .kronos-datatable table.dataTable tbody tr.odd {
          background: var(--dt-row-stripe);
        }

        /* Header controls */
        .kronos-datatable .dt-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 1rem;
          padding: 1rem 0;
          flex-wrap: wrap;
        }

        .kronos-datatable .dt-search input {
          padding: 0.75rem 1rem;
          border: 1px solid var(--dt-border-color);
          border-radius: 0.75rem;
          font-size: 0.875rem;
          min-width: 250px;
          transition: all 0.2s;
        }

        .kronos-datatable .dt-search input:focus {
          outline: none;
          border-color: var(--dt-primary);
          box-shadow: 0 0 0 3px rgba(80, 70, 229, 0.1);
        }

        .kronos-datatable .dt-search label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: 500;
          color: #64748b;
        }

        .kronos-datatable .dt-length select {
          padding: 0.5rem 2rem 0.5rem 0.75rem;
          border: 1px solid var(--dt-border-color);
          border-radius: 0.5rem;
          font-size: 0.875rem;
          background: white;
        }

        /* Footer */
        .kronos-datatable .dt-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem 0;
          flex-wrap: wrap;
          gap: 1rem;
        }

        .kronos-datatable .dt-info {
          font-size: 0.875rem;
          color: #64748b;
        }

        /* Pagination */
        .kronos-datatable .dt-pagination .dt-paging-button {
          padding: 0.5rem 0.75rem;
          border: 1px solid var(--dt-border-color);
          border-radius: 0.5rem;
          margin: 0 0.125rem;
          font-size: 0.875rem;
          transition: all 0.15s;
          background: white;
        }

        .kronos-datatable .dt-pagination .dt-paging-button:hover:not(.disabled) {
          background: var(--dt-row-hover);
          border-color: var(--dt-primary);
        }

        .kronos-datatable .dt-pagination .dt-paging-button.current {
          background: var(--dt-primary);
          color: white;
          border-color: var(--dt-primary);
        }

        .kronos-datatable .dt-pagination .dt-paging-button.disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        /* Loading state */
        .kronos-datatable .dt-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          padding: 2rem;
          color: #64748b;
          font-weight: 500;
        }

        .kronos-datatable .dt-spinner {
          width: 24px;
          height: 24px;
          border: 3px solid var(--dt-border-color);
          border-top-color: var(--dt-primary);
          border-radius: 50%;
          animation: dt-spin 0.8s linear infinite;
        }

        @keyframes dt-spin {
          to { transform: rotate(360deg); }
        }

        /* Processing overlay */
        .kronos-datatable .dataTables_processing {
          background: rgba(255, 255, 255, 0.9) !important;
          border: none !important;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
          border-radius: 1rem;
          padding: 1.5rem 2rem;
        }

        /* Responsive */
        @media (max-width: 768px) {
          .kronos-datatable .dt-header,
          .kronos-datatable .dt-footer {
            flex-direction: column;
            align-items: stretch;
          }

          .kronos-datatable .dt-search input {
            min-width: 100%;
          }
        }

        /* Export buttons */
        .kronos-datatable .dt-buttons .dt-button {
          padding: 0.5rem 1rem;
          border: 1px solid var(--dt-border-color);
          border-radius: 0.5rem;
          font-size: 0.75rem;
          font-weight: 600;
          background: white;
          margin-right: 0.25rem;
          transition: all 0.15s;
        }

        .kronos-datatable .dt-buttons .dt-button:hover {
          background: var(--dt-row-hover);
          border-color: var(--dt-primary);
        }
      `}</style>
        </div>
    );
}

export default ServerSideTable;
