/**
 * KRONOS - Timesheet Service
 */
import { hrApi } from './api';
import type { MonthlyTimesheet } from '../types';

const ENDPOINT = '/hr/timesheets';

export const timesheetService = {
    /**
     * Get timesheet for a specific month
     */
    getMyTimesheet: async (year: number, month: number): Promise<MonthlyTimesheet> => {
        const response = await hrApi.get(`${ENDPOINT}/me/${year}/${month}`);
        return response.data;
    },

    /**
     * Confirm a timesheet
     */
    confirmMyTimesheet: async (year: number, month: number, notes?: string): Promise<MonthlyTimesheet> => {
        const response = await hrApi.post(`${ENDPOINT}/me/${year}/${month}/confirm`, { notes });
        return response.data;
    },

    /**
     * List recent timesheets
     */
    listMyTimesheets: async (): Promise<MonthlyTimesheet[]> => {
        const response = await hrApi.get(`${ENDPOINT}/me`);
        return response.data;
    }
};
