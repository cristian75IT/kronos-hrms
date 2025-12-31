/**
 * KRONOS - Leaves Service API
 */
import { leavesApi } from './api';
import type {
    LeaveRequest,
    LeaveRequestCreate,
    LeaveRequestUpdate,
    LeaveBalance,
    LeaveBalanceSummary,
    CalendarEvent,
    DataTableRequest,
    DataTableResponse,
} from '../types';

const ENDPOINT = '/leaves';

export const leavesService = {
    // ═══════════════════════════════════════════════════════════════════
    // Leave Requests
    // ═══════════════════════════════════════════════════════════════════

    getMyRequests: async (year?: number, status?: string): Promise<LeaveRequest[]> => {
        const params = new URLSearchParams();
        if (year) params.append('year', year.toString());
        if (status) params.append('status', status);

        const response = await leavesApi.get(ENDPOINT, { params });
        return response.data;
    },

    getRequest: async (id: string): Promise<LeaveRequest> => {
        const response = await leavesApi.get(`${ENDPOINT}/${id}`);
        return response.data;
    },

    createRequest: async (data: LeaveRequestCreate): Promise<LeaveRequest> => {
        const response = await leavesApi.post(ENDPOINT, data);
        return response.data;
    },

    updateRequest: async (id: string, data: LeaveRequestUpdate): Promise<LeaveRequest> => {
        const response = await leavesApi.put(`${ENDPOINT}/${id}`, data);
        return response.data;
    },

    submitRequest: async (id: string): Promise<LeaveRequest> => {
        const response = await leavesApi.post(`${ENDPOINT}/${id}/submit`);
        return response.data;
    },

    cancelRequest: async (id: string, reason: string): Promise<LeaveRequest> => {
        const response = await leavesApi.post(`${ENDPOINT}/${id}/cancel`, { reason });
        return response.data;
    },

    deleteRequest: async (id: string): Promise<void> => {
        await leavesApi.delete(`${ENDPOINT}/${id}`);
    },

    acceptCondition: async (id: string): Promise<LeaveRequest> => {
        const response = await leavesApi.post(`${ENDPOINT}/${id}/accept-condition`);
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Approver Actions
    // ═══════════════════════════════════════════════════════════════════

    getPendingApprovals: async (): Promise<LeaveRequest[]> => {
        const response = await leavesApi.get(`${ENDPOINT}/pending`);
        return response.data;
    },

    approveRequest: async (id: string, notes?: string): Promise<LeaveRequest> => {
        const response = await leavesApi.post(`${ENDPOINT}/${id}/approve`, { notes });
        return response.data;
    },

    rejectRequest: async (id: string, reason: string): Promise<LeaveRequest> => {
        const response = await leavesApi.post(`${ENDPOINT}/${id}/reject`, { reason });
        return response.data;
    },

    approveConditional: async (
        id: string,
        conditionType: string,
        conditionDetails: string
    ): Promise<LeaveRequest> => {
        const response = await leavesApi.post(`${ENDPOINT}/${id}/approve-conditional`, {
            condition_type: conditionType,
            condition_details: conditionDetails,
        });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Balance
    // ═══════════════════════════════════════════════════════════════════

    getMyBalance: async (year?: number): Promise<LeaveBalance> => {
        const params = year ? { year } : {};
        const response = await leavesApi.get('/balances/me', { params });
        return response.data;
    },

    getBalanceSummary: async (): Promise<LeaveBalanceSummary> => {
        const response = await leavesApi.get('/balances/me/summary');
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Calendar
    // ═══════════════════════════════════════════════════════════════════

    getCalendarEvents: async (
        startDate: string,
        endDate: string,
        includeTeam?: boolean,
        includeHolidays?: boolean,
    ): Promise<{ events: CalendarEvent[]; holidays: CalendarEvent[] }> => {
        const response = await leavesApi.post('/leaves/calendar', {
            start_date: startDate,
            end_date: endDate,
            include_team: includeTeam,
            include_holidays: includeHolidays,
        });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // DataTable (Server-side)
    // ═══════════════════════════════════════════════════════════════════

    getDataTable: async (request: DataTableRequest): Promise<DataTableResponse<LeaveRequest>> => {
        const response = await leavesApi.post(`${ENDPOINT}/datatable`, request);
        return response.data;
    },
};

export default leavesService;
