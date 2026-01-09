import api from './api';

export interface SignatureTransaction {
    id: string;
    user_id: string;
    document_type: string;
    document_id: string;
    document_hash: string;
    signed_at: string;
    signature_method: string;
    is_valid: boolean;
    metadata?: {
        ip_address?: string;
    };
}

export const signatureService = {
    /**
     * Get all signatures performed by the current user
     */
    getMySignatures: async (): Promise<SignatureTransaction[]> => {
        const response = await api.get<{ data: SignatureTransaction[]; meta: any }>('/signatures/me/all');
        return response.data.data;
    },

    /**
     * Get details of a specific signature
     */
    getSignature: async (id: string): Promise<SignatureTransaction> => {
        const response = await api.get<SignatureTransaction>(`/signatures/${id}`);
        return response.data;
    }
};
