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
    HrDailySnapshot
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

    getTeamDashboard: async (teamId: string): Promise<any> => {
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

    getTodayStats: async (): Promise<any> => {
        const response = await hrApi.get(`${ENDPOINT_DASHBOARD}/stats/today`);
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Reports
    // ═══════════════════════════════════════════════════════════════════

    getMonthlyReport: async (year: number, month: number, departmentId?: string): Promise<MonthlyReportResponse> => {
        const params: any = { year, month };
        if (departmentId) params.department_id = departmentId;
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/monthly`, { params });
        return response.data;
    },

    getMonthlyReportsSummary: async (year: number): Promise<any> => {
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/monthly/${year}`);
        return response.data;
    },

    getComplianceReport: async (): Promise<ComplianceReportResponse> => {
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/compliance`);
        return response.data;
    },

    getBudgetReport: async (year?: number, month?: number): Promise<BudgetReportResponse> => {
        const params: any = {};
        if (year) params.year = year;
        if (month) params.month = month;
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/budget`, { params });
        return response.data;
    },

    exportLul: async (year: number, month: number): Promise<any> => {
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/export/lul/${year}/${month}`);
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Admin / Management
    // ═══════════════════════════════════════════════════════════════════

    createDailySnapshot: async (): Promise<HrDailySnapshot> => {
        const response = await hrApi.post(`${ENDPOINT_ADMIN}/snapshots/create-daily`);
        return response.data;
    },

    createAlert: async (data: any): Promise<HrAlert> => {
        const response = await hrApi.post(`${ENDPOINT_ADMIN}/alerts`, data);
        return response.data;
    },

    runComplianceCheck: async (): Promise<any> => {
        const response = await hrApi.post(`${ENDPOINT_ADMIN}/compliance/run-check`);
        return response.data;
    },

    calculateMonthlyStats: async (year: number, month: number): Promise<any> => {
        const response = await hrApi.post(`${ENDPOINT_ADMIN}/stats/calculate-monthly`, null, {
            params: { year, month }
        });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Training & Safety (D.Lgs. 81/08)
    // ═══════════════════════════════════════════════════════════════════

    getTrainingOverview: async (): Promise<any> => {
        const response = await hrApi.get('/hr/training/overview');
        return response.data;
    },

    getExpiringTrainings: async (days: number = 60): Promise<any[]> => {
        const response = await hrApi.get('/hr/training/expiring', { params: { days } });
        return response.data;
    },

    getEmployeeTrainings: async (employeeId: string): Promise<any[]> => {
        const response = await hrApi.get(`/hr/training/employee/${employeeId}`);
        return response.data;
    },

    createTrainingRecord: async (data: any): Promise<any> => {
        const response = await hrApi.post('/hr/training', data);
        return response.data;
    },

    updateTrainingRecord: async (id: string, data: any): Promise<any> => {
        const response = await hrApi.put(`/hr/training/${id}`, data);
        return response.data;
    },

    deleteTrainingRecord: async (id: string): Promise<void> => {
        await hrApi.delete(`/hr/training/${id}`);
    },

    getEmployeeMedicalRecords: async (employeeId: string): Promise<any[]> => {
        const response = await hrApi.get(`/hr/training/medical/${employeeId}`);
        return response.data;
    },

    createMedicalRecord: async (data: any): Promise<any> => {
        const response = await hrApi.post('/hr/training/medical', data);
        return response.data;
    },

    updateMedicalRecord: async (id: string, data: any): Promise<any> => {
        const response = await hrApi.put(`/hr/training/medical/${id}`, data);
        return response.data;
    },

    deleteMedicalRecord: async (id: string): Promise<void> => {
        await hrApi.delete(`/hr/training/medical/${id}`);
    },

    getEmployeeCompliance: async (employeeId: string): Promise<any> => {
        const response = await hrApi.get(`/hr/training/compliance/${employeeId}`);
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Attendance Reports
    // ═══════════════════════════════════════════════════════════════════

    getDailyAttendance: async (date: string, department?: string): Promise<any> => {
        const params: Record<string, string> = { target_date: date };
        if (department) params.department = department;
        const response = await hrApi.get(`${ENDPOINT_REPORTS}/attendance/daily`, { params });
        return response.data;
    },

    getAggregateAttendance: async (params: {
        start_date: string;
        end_date: string;
        department?: string;
    }): Promise<any> => {
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
    }): Promise<any> => {
        const response = await hrApi.get('/hr/management/leaves/datatable', { params });
        return response.data;
    },

    getLeaveDetail: async (id: string): Promise<any> => {
        const response = await hrApi.get(`/hr/management/leaves/${id}`);
        return response.data;
    },

    updateLeaveHR: async (id: string, data: Record<string, any>): Promise<any> => {
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
    }): Promise<any> => {
        const response = await hrApi.get('/hr/management/trips/datatable', { params });
        return response.data;
    },

    getTripDetail: async (id: string): Promise<any> => {
        const response = await hrApi.get(`/hr/management/trips/${id}`);
        return response.data;
    },

    updateTripHR: async (id: string, data: Record<string, any>): Promise<any> => {
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
    }): Promise<any> => {
        const response = await hrApi.get('/hr/management/expenses/datatable', { params });
        return response.data;
    },

    getExpenseDetail: async (id: string): Promise<any> => {
        const response = await hrApi.get(`/hr/management/expenses/${id}`);
        return response.data;
    },

    updateExpenseHR: async (id: string, data: Record<string, any>): Promise<any> => {
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
    }): Promise<any> => {
        const response = await hrApi.get('/hr/training/datatable', { params });
        return response.data;
    },
};

export default hrReportingService;

