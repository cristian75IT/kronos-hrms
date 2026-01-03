/**
 * KRONOS - Enterprise Audit Service API
 */
import { auditApi } from './api';
import type {
    AuditLogListItem,
    AuditLogDetails,
    DataTableRequest,
    DataTableResponse
} from '../types';

const ENDPOINT = '/audit';

export interface AuditStatsSummary {
    period_days: number;
    total_events: number;
    by_status: Record<string, number>;
    unique_users: number;
    unique_services: number;
    success_rate: number;
}

export interface AuditServiceStats {
    service_name: string;
    total: number;
    success: number;
    failure: number;
    error: number;
    success_rate: number;
}

export interface AuditActionStats {
    action: string;
    resource_type: string;
    count: number;
}

export const auditService = {
    /**
     * Get audit logs for DataTable
     */
    getLogsDataTable: async (request: DataTableRequest, filters?: { resource_type?: string; service_name?: string }): Promise<DataTableResponse<AuditLogListItem>> => {
        const response = await auditApi.post(`${ENDPOINT}/logs/datatable`, request, { params: filters });
        return response.data;
    },

    /**
     * Get single log details
     */
    getLogDetails: async (id: string): Promise<AuditLogDetails> => {
        const response = await auditApi.get(`${ENDPOINT}/logs/${id}`);
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Audit Trail (Entity History)
    // ═══════════════════════════════════════════════════════════════════

    getEntityHistory: async (entityType: string, entityId: string): Promise<any[]> => {
        const response = await auditApi.get(`/trail/${entityType}/${entityId}/history`);
        return response.data;
    },

    getEntityVersion: async (entityType: string, entityId: string, version: number): Promise<any> => {
        const response = await auditApi.get(`/trail/${entityType}/${entityId}/version/${version}`);
        return response.data;
    },

    getUserChanges: async (userId: string, limit: number = 20): Promise<any[]> => {
        const response = await auditApi.get(`/trail/user/${userId}/changes`, { params: { limit } });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Enterprise Stats
    // ═══════════════════════════════════════════════════════════════════

    getStatsSummary: async (): Promise<any> => {
        const response = await auditApi.get('/enterprise/stats/summary');
        return response.data;
    },

    /**
     * Get stats grouped by service
     */
    getStatsByService: async (days: number = 7): Promise<AuditServiceStats[]> => {
        const response = await auditApi.get(`${ENDPOINT}/stats/by-service`, { params: { days } });
        return response.data;
    },

    /**
     * Get stats grouped by action
     */
    getStatsByAction: async (days: number = 7, serviceName?: string): Promise<AuditActionStats[]> => {
        const response = await auditApi.get(`${ENDPOINT}/stats/by-action`, {
            params: { days, service_name: serviceName }
        });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════
    // Export & Data Retention
    // ═══════════════════════════════════════════════════════════

    /**
     * Export audit logs
     */
    exportLogs: async (format: 'json' | 'csv' = 'json', options?: {
        start_date?: string;
        end_date?: string;
        service_name?: string;
        resource_type?: string;
        limit?: number;
    }): Promise<Blob> => {
        const response = await auditApi.get(`${ENDPOINT}/export`, {
            params: { format, ...options },
            responseType: 'blob'
        });
        return response.data;
    },

    /**
     * Archive old logs
     */
    archiveLogs: async (retentionDays: number = 90): Promise<{ archived_count: number; retention_days: number }> => {
        const response = await auditApi.post(`${ENDPOINT}/archive`, null, {
            params: { retention_days: retentionDays }
        });
        return response.data;
    },

    /**
     * Purge old archives
     */
    purgeArchives: async (archiveRetentionDays: number = 365): Promise<{ purged_count: number; archive_retention_days: number }> => {
        const response = await auditApi.post(`${ENDPOINT}/purge-archives`, null, {
            params: { archive_retention_days: archiveRetentionDays }
        });
        return response.data;
    },

    /**
     * Download export as file
     */
    downloadExport: async (format: 'json' | 'csv' = 'json', options?: {
        start_date?: string;
        end_date?: string;
        service_name?: string;
        resource_type?: string;
        limit?: number;
    }): Promise<void> => {
        const blob = await auditService.exportLogs(format, options);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit_export_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
};

export default auditService;

