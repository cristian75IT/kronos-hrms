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
    DailyAttendanceResponse,
    AggregateReportRequest,
    AggregateReportResponse,
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

    acceptCondition: async (id: string, accept: boolean): Promise<LeaveRequest> => {
        const response = await leavesApi.post(`${ENDPOINT}/${id}/accept-condition`, { accept });
        return response.data;
    },

    calculateDays: async (
        startDate: string,
        endDate: string,
        startHalfDay = false,
        endHalfDay = false,
        leaveTypeId?: string
    ): Promise<{ days: number; hours: number; message?: string }> => {
        const response = await leavesApi.post(`${ENDPOINT}/calculate-days`, {
            start_date: startDate,
            end_date: endDate,
            start_half_day: startHalfDay,
            end_half_day: endHalfDay,
            leave_type_id: leaveTypeId,
        });
        return response.data;
    },

    getExcludedDays: async (
        startDate: string,
        endDate: string
    ): Promise<{
        start_date: string;
        end_date: string;
        working_days: number;
        excluded_days: Array<{
            date: string;
            reason: 'weekend' | 'holiday' | 'closure';
            name: string;
        }>;
    }> => {
        const response = await leavesApi.get(`${ENDPOINT}/excluded-days`, {
            params: { start_date: startDate, end_date: endDate }
        });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Approver Read-Only Methods (kept for legacy compatibility)
    // ═══════════════════════════════════════════════════════════════════

    getPendingApprovals: async (): Promise<LeaveRequest[]> => {
        const response = await leavesApi.get(`${ENDPOINT}/pending`);
        return response.data;
    },

    getApprovalHistory: async (params?: { status?: string; year?: number; limit?: number }): Promise<LeaveRequest[]> => {
        const response = await leavesApi.get(`${ENDPOINT}/history`, { params });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Approval Actions - MIGRATED TO CENTRAL APPROVALS SERVICE
    // ═══════════════════════════════════════════════════════════════════
    // NOTE: approveRequest, rejectRequest, and approveConditional have been removed.
    // All approval actions must now go through approvalsService:
    //   - approvalsService.approveRequest(approvalRequestId, notes)
    //   - approvalsService.rejectRequest(approvalRequestId, reason)
    //   - approvalsService.approveRequestConditional(approvalRequestId, conditionType, conditionDetails)
    // ═══════════════════════════════════════════════════════════════════



    revokeApproval: async (id: string, reason: string): Promise<LeaveRequest> => {
        const response = await leavesApi.post(`${ENDPOINT}/${id}/revoke`, null, {
            params: { reason }
        });
        return response.data;
    },

    reopenRequest: async (id: string, notes?: string): Promise<LeaveRequest> => {
        const response = await leavesApi.post(`${ENDPOINT}/${id}/reopen`, null, {
            params: { notes }
        });
        return response.data;
    },

    recallRequest: async (id: string, reason: string, recallDate: string): Promise<LeaveRequest> => {
        const response = await leavesApi.post(`${ENDPOINT}/${id}/recall`, {
            reason,
            recall_date: recallDate,
        });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Balance
    // ═══════════════════════════════════════════════════════════════════

    getMyBalance: async (year?: number, userId?: string): Promise<LeaveBalance> => {
        const url = userId ? `/balances/${userId}` : '/balances/me';
        const params = year ? { year } : {};
        const response = await leavesApi.get(url, { params });
        return response.data;
    },

    getBalanceSummary: async (userId?: string): Promise<LeaveBalanceSummary> => {
        const url = userId ? `/balances/${userId}/summary` : '/balances/me/summary';
        const response = await leavesApi.get(url);
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
    ): Promise<{ events: CalendarEvent[]; holidays: CalendarEvent[]; closures: CalendarEvent[] }> => {
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

    recalculateAccruals: async (year?: number): Promise<void> => {
        const params = year ? { year } : {};
        // Note: endpoint is /balances/accrual/recalculate. BaseURL is /api/v1.
        await leavesApi.post('/balances/accrual/recalculate', null, { params });
    },

    recalculateUserAccruals: async (userId: string, year?: number): Promise<void> => {
        const params = year ? { year } : {};
        await leavesApi.post(`/balances/${userId}/accrual/recalculate`, null, { params });
    },

    getUserBalance: async (userId: string, year?: number): Promise<LeaveBalance> => {
        const params = year ? { year } : {};
        const response = await leavesApi.get(`/balances/${userId}`, { params });
        return response.data;
    },

    adjustBalance: async (userId: string, year: number, data: { balance_type: string, amount: number, reason: string, expiry_date?: string }): Promise<LeaveBalance> => {
        const response = await leavesApi.post(`/balances/${userId}/adjust`, data, { params: { year } });
        return response.data;
    },

    getTransactions: async (balanceId: string): Promise<any[]> => {
        const response = await leavesApi.get(`/balances/transactions/${balanceId}`);
        return response.data;
    },

    processAccruals: async (year: number, month: number): Promise<string> => {
        const response = await leavesApi.post('/balances/process-accruals', null, { params: { year, month } });
        return response.data.message;
    },

    processExpirations: async (): Promise<string> => {
        const response = await leavesApi.post('/balances/process-expirations');
        return response.data.message;
    },

    processRollover: async (year: number): Promise<string> => {
        const response = await leavesApi.post('/balances/process-rollover', null, { params: { year } });
        return response.data.message;
    },

    runReconciliation: async (): Promise<string> => {
        const response = await leavesApi.post('/balances/reconciliation/check');
        return response.data.message;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Preview & Selective Apply (Admin Tools)
    // ═══════════════════════════════════════════════════════════════════

    previewRecalculate: async (year?: number): Promise<{
        year: number;
        employees: Array<{
            user_id: string;
            name: string;
            current_vacation: number;
            new_vacation: number;
            current_rol: number;
            new_rol: number;
            current_permits: number;
            new_permits: number;
        }>;
        total_count: number;
    }> => {
        const params = year ? { year } : {};
        const response = await leavesApi.get('/balances/accrual/preview', { params });
        return response.data;
    },

    applyRecalculateSelected: async (userIds: string[], year?: number): Promise<string> => {
        const params = year ? { year } : {};
        const response = await leavesApi.post('/balances/accrual/apply-selected', { user_ids: userIds }, { params });
        return response.data.message;
    },

    previewRollover: async (year: number): Promise<{
        from_year: number;
        to_year: number;
        employees: Array<{
            user_id: string;
            name: string;
            current_vacation: number;
            new_vacation: number;
            current_rol: number;
            new_rol: number;
            current_permits: number;
            new_permits: number;
        }>;
        total_count: number;
    }> => {
        const response = await leavesApi.get('/balances/rollover/preview', { params: { year } });
        return response.data;
    },

    applyRolloverSelected: async (userIds: string[], year: number): Promise<string> => {
        const response = await leavesApi.post('/balances/rollover/apply-selected', { user_ids: userIds }, { params: { year } });
        return response.data.message;
    },

    // ═══════════════════════════════════════════════════════════════════
    // HR Reporting
    // ═══════════════════════════════════════════════════════════════════

    getDailyAttendance: async (date: string, department?: string): Promise<DailyAttendanceResponse> => {
        const response = await leavesApi.post('/leaves/daily-attendance', { date, department });
        return response.data;
    },

    getAggregateAttendance: async (request: AggregateReportRequest): Promise<AggregateReportResponse> => {
        const response = await leavesApi.post('/leaves/aggregate-attendance', request);
        return response.data;
    },

    importBalances: async (items: any[], mode: 'APPEND' | 'REPLACE' = 'APPEND'): Promise<string> => {
        const response = await leavesApi.post('/balances/import', { items, mode });
        return response.data.message;
    },
};

export default leavesService;
