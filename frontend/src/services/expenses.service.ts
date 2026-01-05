/**
 * KRONOS - Expenses Service API
 */
import { expensesApi } from './api';
import type {
    BusinessTrip,
    DailyAllowance,
    ExpenseReport,
    ExpenseItem,
    DataTableRequest,
    DataTableResponse,
} from '../types';

// ═══════════════════════════════════════════════════════════════════
// Business Trips
// ═══════════════════════════════════════════════════════════════════

export const tripsService = {
    getMyTrips: async (status?: string, year?: number): Promise<BusinessTrip[]> => {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (year) params.append('year', year.toString());

        const response = await expensesApi.get('/trips', { params });
        return response.data;
    },

    getTrip: async (id: string): Promise<BusinessTrip> => {
        const response = await expensesApi.get(`/trips/${id}`);
        return response.data;
    },

    createTrip: async (data: Partial<BusinessTrip>): Promise<BusinessTrip> => {
        const response = await expensesApi.post('/trips', data);
        return response.data;
    },

    updateTrip: async (id: string, data: Partial<BusinessTrip>): Promise<BusinessTrip> => {
        const response = await expensesApi.put(`/trips/${id}`, data);
        return response.data;
    },

    submitTrip: async (id: string): Promise<BusinessTrip> => {
        const response = await expensesApi.post(`/trips/${id}/submit`);
        return response.data;
    },

    completeTrip: async (id: string): Promise<BusinessTrip> => {
        const response = await expensesApi.post(`/trips/${id}/complete`);
        return response.data;
    },

    deleteTrip: async (id: string): Promise<void> => {
        await expensesApi.delete(`/trips/${id}`);
    },

    cancelTrip: async (id: string, reason: string): Promise<BusinessTrip> => {
        const response = await expensesApi.post(`/trips/${id}/cancel?reason=${encodeURIComponent(reason)}`);
        return response.data;
    },

    // Approver actions
    getPendingTrips: async (): Promise<BusinessTrip[]> => {
        const response = await expensesApi.get('/trips/pending');
        return response.data;
    },

    approveTrip: async (id: string, notes?: string): Promise<BusinessTrip> => {
        const response = await expensesApi.post(`/trips/${id}/approve`, { notes });
        return response.data;
    },

    rejectTrip: async (id: string, reason: string): Promise<BusinessTrip> => {
        const response = await expensesApi.post(`/trips/${id}/reject`, { reason });
        return response.data;
    },

    uploadAttachment: async (id: string, file: File): Promise<BusinessTrip> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await expensesApi.post(`/trips/${id}/attachment`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    // Daily Allowances
    getTripAllowances: async (tripId: string): Promise<DailyAllowance[]> => {
        const response = await expensesApi.get(`/trips/${tripId}/allowances`);
        return response.data;
    },

    updateAllowance: async (id: string, data: Partial<DailyAllowance>): Promise<DailyAllowance> => {
        const response = await expensesApi.put(`/allowances/${id}`, data);
        return response.data;
    },

    // DataTable
    getDataTable: async (request: DataTableRequest): Promise<DataTableResponse<BusinessTrip>> => {
        const response = await expensesApi.post('/trips/datatable', request);
        return response.data;
    },
};

// ═══════════════════════════════════════════════════════════════════
// Expense Reports
// ═══════════════════════════════════════════════════════════════════

export const reportsService = {
    getMyReports: async (status?: string): Promise<ExpenseReport[]> => {
        const params = status ? { status } : {};
        const response = await expensesApi.get('/expenses', { params });
        return response.data;
    },

    getStandaloneReports: async (status?: string): Promise<ExpenseReport[]> => {
        const params = status ? { status } : {};
        const response = await expensesApi.get('/expenses/standalone', { params });
        return response.data;
    },

    getReport: async (id: string): Promise<ExpenseReport> => {
        const response = await expensesApi.get(`/expenses/${id}`);
        return response.data;
    },

    createReport: async (data: Partial<ExpenseReport>): Promise<ExpenseReport> => {
        const response = await expensesApi.post('/expenses', data);
        return response.data;
    },

    submitReport: async (id: string): Promise<ExpenseReport> => {
        const response = await expensesApi.post(`/expenses/${id}/submit`);
        return response.data;
    },

    deleteReport: async (id: string): Promise<void> => {
        await expensesApi.delete(`/expenses/${id}`);
    },

    cancelReport: async (id: string, reason: string): Promise<ExpenseReport> => {
        const response = await expensesApi.post(`/expenses/${id}/cancel?reason=${encodeURIComponent(reason)}`);
        return response.data;
    },

    // Approver actions
    getPendingReports: async (): Promise<ExpenseReport[]> => {
        const response = await expensesApi.get('/expenses/pending');
        return response.data;
    },

    approveReport: async (
        id: string,
        approvedAmount?: number,
        notes?: string,
        itemApprovals?: Record<string, boolean>,
    ): Promise<ExpenseReport> => {
        const response = await expensesApi.post(`/expenses/${id}/approve`, {
            approved_amount: approvedAmount,
            notes,
            item_approvals: itemApprovals,
        });
        return response.data;
    },

    rejectReport: async (id: string, reason: string): Promise<ExpenseReport> => {
        const response = await expensesApi.post(`/expenses/${id}/reject`, { reason });
        return response.data;
    },

    markPaid: async (id: string, paymentReference: string): Promise<ExpenseReport> => {
        const response = await expensesApi.post(`/expenses/${id}/paid`, {
            payment_reference: paymentReference,
        });
        return response.data;
    },

    uploadAttachment: async (id: string, file: File): Promise<ExpenseReport> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await expensesApi.post(`/expenses/${id}/attachment`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    // Expense Items
    addItem: async (reportId: string, data: Partial<ExpenseItem>): Promise<ExpenseItem> => {
        const payload = { ...data, report_id: reportId };
        const response = await expensesApi.post('/expenses/items', payload);
        return response.data;
    },

    updateItem: async (itemId: string, data: Partial<ExpenseItem>): Promise<ExpenseItem> => {
        const response = await expensesApi.put(`/expenses/items/${itemId}`, data);
        return response.data;
    },

    deleteItem: async (itemId: string): Promise<void> => {
        await expensesApi.delete(`/expenses/items/${itemId}`);
    },

    uploadReceipt: async (itemId: string, file: File): Promise<{ path: string }> => {
        const formData = new FormData();
        formData.append('file', file);
        // Note: Backend endpoint for receipt upload missing in router, assuming pattern:
        const response = await expensesApi.post(`/expenses/items/${itemId}/receipt`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },
};

export default { trips: tripsService, reports: reportsService };
