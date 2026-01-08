/**
 * KRONOS - Auth Service
 * Handles direct authentication with Keycloak via REST API (Direct Access Grants)
 */

interface TokenResponse {
    access_token: string;
    expires_in: number;
    refresh_expires_in: number;
    refresh_token: string;
    token_type: string;
    not_before_policy: number;
    session_state: string;
    scope: string;
}

export interface UserProfile {
    id: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    roles: string[];
}

const KEYCLOAK_URL = import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080';
const REALM = import.meta.env.VITE_KEYCLOAK_REALM || 'kronos';
const CLIENT_ID = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'kronos-frontend';

const TOKEN_ENDPOINT = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`;

export const authService = {
    async login(username: string, password: string, totp?: string): Promise<TokenResponse> {
        const params = new URLSearchParams();
        params.append('client_id', CLIENT_ID);
        params.append('grant_type', 'password');
        params.append('username', username);
        params.append('password', password);
        if (totp) {
            params.append('totp', totp);
        }
        // public client, no client_secret

        const response = await fetch(TOKEN_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: params,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ error_description: 'Login failed' }));
            throw new Error(error.error_description || 'Authentication failed');
        }

        return response.json();
    },

    async refreshToken(refreshToken: string): Promise<TokenResponse> {
        const params = new URLSearchParams();
        params.append('client_id', CLIENT_ID);
        params.append('grant_type', 'refresh_token');
        params.append('refresh_token', refreshToken);

        const response = await fetch(TOKEN_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: params,
        });

        if (!response.ok) {
            throw new Error('Refresh failed');
        }

        return response.json();
    },

    decodeToken(token: string): UserProfile | null {
        try {
            const parts = token.split('.');
            if (parts.length !== 3) return null;

            const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));

            return {
                id: payload.sub,
                username: payload.preferred_username,
                email: payload.email,
                firstName: payload.given_name,
                lastName: payload.family_name,
                roles: payload.realm_access?.roles || [],
            };
        } catch (e) {
            console.error('Failed to decode token', e);
            return null;
        }
    },

    async setupMfa(token: string): Promise<{ secret: string; otp_url: string }> {
        // Needs token because this happens when user IS logged in but wants to enable MFA
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/auth/mfa/setup`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error("Failed to setup MFA");
        return response.json();
    },

    async enableMfa(token: string, secret: string, code: string): Promise<void> {
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/auth/mfa/enable`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ secret, code })
        });
        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || "Failed to verify MFA");
        }
    }
};
