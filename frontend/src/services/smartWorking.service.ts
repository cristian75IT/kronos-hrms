/**
 * KRONOS - Smart Working API Service
 */
import api from './api';

export interface SWAgreement {
    id: string;
    user_id: string;
    start_date: string;
    end_date: string | null;
    allowed_days_per_week: number;
    allowed_weekdays: number[] | null;
    allowed_weekdays_names: string[] | null;
    status: 'ACTIVE' | 'EXPIRED' | 'TERMINATED' | 'DRAFT' | 'PENDING';
    notes: string | null;
    created_at: string;
}

export interface SWRequest {
    id: string;
    user_id: string;
    agreement_id: string;
    date: string;
    status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
    notes: string | null;
    approval_request_id: string | null;
    approver_id: string | null;
    created_at: string;
    attendance?: SWAttendanceResponse | null;
}

export interface SWAttendanceResponse {
    id: string;
    request_id: string;
    check_in: string | null;
    check_out: string | null;
    location: string | null;
    created_at: string;
    updated_at: string;
}

export interface SWAttendance {
    id: string;
    request_id: string;
    check_in: string | null;
    check_out: string | null;
    location: string | null;
}

export interface SWAttendanceCheckIn {
    request_id: string;
    location?: string;
}

export interface SWAttendanceCheckOut {
    request_id: string;
}

export const smartWorkingService = {
    // Agreements
    getMyAgreements: async (): Promise<SWAgreement[]> => {
        const response = await api.get('/smart-working/agreements/me');
        return response.data;
    },

    createAgreement: async (data: Partial<SWAgreement>): Promise<SWAgreement> => {
        const response = await api.post('/smart-working/agreements', data);
        return response.data;
    },

    terminateAgreement: async (id: string): Promise<SWAgreement> => {
        const response = await api.put(`/smart-working/agreements/${id}/terminate`);
        return response.data;
    },

    // Requests
    getMyRequests: async (): Promise<SWRequest[]> => {
        const response = await api.get('/smart-working/requests/me');
        return response.data;
    },

    submitRequest: async (data: { agreement_id: string; date: string; notes?: string }): Promise<SWRequest> => {
        const response = await api.post('/smart-working/requests', data);
        return response.data;
    },

    cancelRequest: async (id: string): Promise<SWRequest> => {
        const response = await api.put(`/smart-working/requests/${id}/cancel`);
        return response.data;
    },

    convertToPresence: async (date: string): Promise<SWRequest> => {
        const response = await api.post('/smart-working/requests/presence', { date });
        return response.data;
    },

    signAgreement: async (id: string, otp_code: string): Promise<SWAgreement> => {
        const response = await api.post(`/smart-working/agreements/${id}/sign`, { otp_code });
        return response.data;
    },

    // Attendance
    checkIn: async (data: SWAttendanceCheckIn): Promise<SWAttendance> => {
        const response = await api.post('/smart-working/attendance/check-in', data);
        return response.data;
    },

    checkOut: async (data: SWAttendanceCheckOut): Promise<SWAttendance> => {
        const response = await api.post('/smart-working/attendance/check-out', data);
        return response.data;
    },

    // HR/Admin methods
    getUserAgreements: async (userId: string): Promise<SWAgreement[]> => {
        const response = await api.get(`/smart-working/agreements/user/${userId}`);
        return response.data;
    },

    getAllAgreements: async (): Promise<SWAgreement[]> => {
        const response = await api.get('/smart-working/agreements');
        return response.data;
    },

    updateAgreement: async (id: string, data: Partial<SWAgreement>): Promise<SWAgreement> => {
        const response = await api.put(`/smart-working/agreements/${id}`, data);
        return response.data;
    }
};
