/**
 * KRONOS - Audit Service API
 */
import { auditApi } from './api';
import type {
    AuditLogListItem,
    AuditLogDetails,
    DataTableRequest,
    DataTableResponse
} from '../types';

const ENDPOINT = '/audit';

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
    }
};

export default auditService;
