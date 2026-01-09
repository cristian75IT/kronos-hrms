/**
 * KRONOS - HR Reporting Service API
 */
import { hrApi } from './api';
import type {
    DashboardOverview,
    HrAlert,
    MonthlyReportResponse,
    ComplianceReportResponse,
    BudgetReportResponse,
    Training,
    TrainingCreate,
    DataTableResponse,
    LeaveRequest,
    BusinessTrip,
    ExpenseReport,
    DailyAttendanceResponse,
    AggregateReportResponse,
    HrTodayStatsResponse,
    ComplianceCheckRunResult,
    MonthlyStatsCalculationResult,
    DailySnapshotCreateResult,
} from '../types';

const ENDPOINT_DASHBOARD = '/hr/dashboard';
const ENDPOINT_REPORTS = '/hr/reports';
const ENDPOINT_ADMIN = '/hr/admin';

export const hrReportingService = {
    // ═══════════════════════════════════════════════════════════════════
    // Dashboard
    // ═══════════════════════════════════════════════════════════════════

    getDashboardOverview: async (targetDate?: string): Promise<DashboardOverview> => {
        const params = targetDate ? { target_date: targetDate } : {};
        const response = await hrApi.get(`${ENDPOINT_DASHBOARD}/overview`, { params });
        return response.data;
    },

    getTeamDashboard: async (teamId: string): Promise<DashboardOverview> => {
        const response = await hrApi.get(`${ENDPOINT_DASHBOARD}/team/${teamId}`);
        return response.data;
    },

    getActiveAlerts: async (limit: number = 50): Promise<HrAlert[]> => {
        const response = await hrApi.get(`${ENDPOINT_DASHBOARD}/alerts`, { params: { limit } });
        return response.data;
    },

    acknowledgeAlert: async (alertId: string): Promise<void> => {
        await hrApi.post(`${ENDPOINT_DASHBOARD}/alerts/${alertId}/acknowledge`);
    },

    resolveAlert: async (alertId: string): Promise<void> => {
        await hrApi.post(`${ENDPOINT_DASHBOARD}/alerts/${alertId}/resolve`);
    },

    getTodayStats: async (): Promise<HrTodayStatsResponse> => {
        const response = await hrApi.get(`${ENDPOINT_DASHBOARD}/stats/today`);
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Reports
    // ═══════════════════════════════════════════════════════════════════

    getMonthlyReport: async (year: number, month: number, departmentId?: string): Promise<MonthlyReportResponse> => {
        const params: Record<string, unknown> = { year, month };
        if (departmentId) params.department_id = departmentId;
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/monthly`, { params });
        return response.data;
    },

    getMonthlyReportsSummary: async (year: number): Promise<MonthlyReportResponse[]> => {
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/monthly/${year}`);
        return response.data;
    },

    getComplianceReport: async (): Promise<ComplianceReportResponse> => {
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/compliance`);
        return response.data;
    },

    getBudgetReport: async (year?: number, month?: number): Promise<BudgetReportResponse> => {
        const params: Record<string, unknown> = {};
        if (year) params.year = year;
        if (month) params.month = month;
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/budget`, { params });
        return response.data;
    },

    exportLul: async (year: number, month: number): Promise<Blob> => {
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/export/lul/${year}/${month}`, { responseType: 'blob' });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Admin / Management
    // ═══════════════════════════════════════════════════════════════════

    createDailySnapshot: async (): Promise<DailySnapshotCreateResult> => {
        const response = await hrApi.post(`${ENDPOINT_ADMIN}/snapshots/create-daily`);
        return response.data;
    },

    createAlert: async (data: Partial<HrAlert>): Promise<HrAlert> => {
        const response = await hrApi.post(`${ENDPOINT_ADMIN}/alerts`, data);
        return response.data;
    },

    runComplianceCheck: async (): Promise<ComplianceCheckRunResult> => {
        const response = await hrApi.post(`${ENDPOINT_ADMIN}/compliance/run-check`);
        return response.data;
    },

    calculateMonthlyStats: async (year: number, month: number): Promise<MonthlyStatsCalculationResult> => {
        const response = await hrApi.post(`${ENDPOINT_ADMIN}/stats/calculate-monthly`, null, {
            params: { year, month }
        });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Training & Safety (D.Lgs. 81/08) - Using ServerSideTable pattern
    // ═══════════════════════════════════════════════════════════════════

    getTrainingOverview: async (): Promise<Record<string, unknown>> => {
        // NOTE: This endpoint may not exist in backend yet
        // Returns mock data or throws a friendly error
        try {
            const response = await hrApi.get('/hr/training/overview');
            return response.data;
        } catch {
            // Return empty overview if endpoint doesn't exist
            return {
                fully_compliant: 0,
                total_employees: 0,
                trainings_expiring_30_days: 0,
                trainings_expired: 0,
                non_compliant: 0,
                medical_visits_due: 0
            };
        }
    },

    createTrainingRecord: async (data: TrainingCreate): Promise<Training> => {
        const response = await hrApi.post('/hr/training', data);
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Attendance Reports
    // ═══════════════════════════════════════════════════════════════════

    getDailyAttendance: async (date: string, department?: string): Promise<DailyAttendanceResponse> => {
        const params: Record<string, string> = { target_date: date };
        if (department) params.department = department;
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/attendance/daily`, { params });
        return response.data;
    },

    getAggregateAttendance: async (params: {
        start_date: string;
        end_date: string;
        department?: string;
    }): Promise<AggregateReportResponse> => {
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/attendance/aggregate`, { params });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // HR Management - All Employees Data
    // ═══════════════════════════════════════════════════════════════════

    getAllLeavesDataTable: async (params: {
        draw?: number;
        start?: number;
        length?: number;
        search_value?: string;
        status_filter?: string;
        leave_type_filter?: string;
        date_from?: string;
        date_to?: string;
    }): Promise<DataTableResponse<LeaveRequest>> => {
        const response = await hrApi.get('/hr/management/leaves/datatable', { params });
        return response.data;
    },

    getLeaveDetail: async (id: string): Promise<LeaveRequest> => {
        const response = await hrApi.get(`/hr/management/leaves/${id}`);
        return response.data;
    },

    updateLeaveHR: async (id: string, data: Record<string, unknown>): Promise<LeaveRequest> => {
        const response = await hrApi.put(`/hr/management/leaves/${id}`, data);
        return response.data;
    },

    getAllTripsDataTable: async (params: {
        draw?: number;
        start?: number;
        length?: number;
        search_value?: string;
        status_filter?: string;
        date_from?: string;
        date_to?: string;
    }): Promise<DataTableResponse<BusinessTrip>> => {
        const response = await hrApi.get('/hr/management/trips/datatable', { params });
        return response.data;
    },

    getTripDetail: async (id: string): Promise<BusinessTrip> => {
        const response = await hrApi.get(`/hr/management/trips/${id}`);
        return response.data;
    },

    updateTripHR: async (id: string, data: Record<string, unknown>): Promise<BusinessTrip> => {
        const response = await hrApi.put(`/hr/management/trips/${id}`, data);
        return response.data;
    },

    getAllExpensesDataTable: async (params: {
        draw?: number;
        start?: number;
        length?: number;
        search_value?: string;
        status_filter?: string;
        date_from?: string;
        date_to?: string;
    }): Promise<DataTableResponse<ExpenseReport>> => {
        const response = await hrApi.get('/hr/management/expenses/datatable', { params });
        return response.data;
    },

    getExpenseDetail: async (id: string): Promise<ExpenseReport> => {
        const response = await hrApi.get(`/hr/management/expenses/${id}`);
        return response.data;
    },

    updateExpenseHR: async (id: string, data: Record<string, unknown>): Promise<ExpenseReport> => {
        const response = await hrApi.put(`/hr/management/expenses/${id}`, data);
        return response.data;
    },

    getTrainingDataTable: async (params: {
        draw?: number;
        start?: number;
        length?: number;
        search_value?: string;
        order_column?: string;
        order_dir?: string;
    }): Promise<DataTableResponse<Training>> => {
        const response = await hrApi.get('/hr/training/datatable', { params });
        return response.data;
    },
};

export default hrReportingService;

