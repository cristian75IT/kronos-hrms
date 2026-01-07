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
    // Expensive Wallets (Business Trips) - Now under /expenses/wallet
    // ═══════════════════════════════════════════════════════════════════

    getTripWallet: async (tripId: string): Promise<TripWallet> => {
        const response = await walletsApi.get(`/expenses/wallet/${tripId}`);
        return response.data;
    },

    getTripTransactions: async (tripId: string): Promise<TripWalletTransaction[]> => {
        const response = await walletsApi.get(`/expenses/wallet/${tripId}/transactions`);
        return response.data;
    },

    getTripWalletSummary: async (tripId: string): Promise<any> => {
        const response = await walletsApi.get(`/expenses/wallet/${tripId}/summary`);
        return response.data;
    },

    initializeTripWallet: async (tripId: string, userId: string, budget: number): Promise<TripWallet> => {
        const response = await walletsApi.post(`/expenses/wallet/internal/initialize/${tripId}`, null, {
            params: { user_id: userId, budget }
        });
        return response.data;
    },

    // ═══════════════════════════════════════════════════════════════════
    // Leaves Wallets (Ferie, ROL, Permessi) - Now under /leaves/wallet
    // ═══════════════════════════════════════════════════════════════════

    getLeavesWallet: async (userId: string, year?: number): Promise<any> => {
        const params = year ? { year } : {};
        const response = await walletsApi.get(`/leaves/wallet/${userId}`, { params });
        return response.data;
    },

    getLeavesBalanceSummary: async (userId: string, year?: number): Promise<any> => {
        const params = year ? { year } : {};
        const response = await walletsApi.get(`/leaves/wallet/${userId}/summary`, { params });
        return response.data;
    },

    getLeavesAvailableBalance: async (userId: string, balanceType: string): Promise<number> => {
        const response = await walletsApi.get(`/leaves/wallet/${userId}/available/${balanceType}`);
        return response.data.available;
    },

    getLeavesTransactions: async (walletId: string): Promise<any[]> => {
        const response = await walletsApi.get(`/leaves/wallet/transactions/${walletId}`);
        return response.data;
    },

    // The shortcut for current user's leaves summary is still handled by leaves service
    // because it aggregates the pending local requests with the wallet data.
};

export default walletsService;
