/**
 * KRONOS - Wallets Service API (Leaves & Expensive)
 */
import { walletsApi } from './api';
import type {
    TripWallet,
    TripWalletTransaction
} from '../types';

export const walletsService = {
    // ═══════════════════════════════════════════════════════════════════
    // Expensive Wallets (Business Trips)
    // ═══════════════════════════════════════════════════════════════════

    getTripWallet: async (tripId: string): Promise<TripWallet> => {
        const response = await walletsApi.get(`/expensive-wallets/${tripId}`);
        return response.data;
    },

    getTripTransactions: async (tripId: string): Promise<TripWalletTransaction[]> => {
        const response = await walletsApi.get(`/expensive-wallets/${tripId}/transactions`);
        return response.data;
    },

    initializeTripWallet: async (tripId: string, userId: string, budget: number): Promise<TripWallet> => {
        const response = await walletsApi.post(`/expensive-wallets/initialize/${tripId}`, null, {
            params: { user_id: userId, budget }
        });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Leaves Wallets (Ferie, ROL, Permessi)
    // ═══════════════════════════════════════════════════════════════════

    getLeavesWallet: async (userId: string, year?: number): Promise<any> => {
        const params = year ? { year } : {};
        const response = await walletsApi.get(`/leaves-wallets/${userId}`, { params });
        return response.data;
    },

    getLeavesTransactions: async (walletId: string): Promise<any[]> => {
        const response = await walletsApi.get(`/leaves-wallets/transactions/${walletId}`);
        return response.data;
    },

    // The shortcut for current user's leaves summary is still handled by leaves service
    // because it aggregates the pending local requests with the wallet data.
};

export default walletsService;
