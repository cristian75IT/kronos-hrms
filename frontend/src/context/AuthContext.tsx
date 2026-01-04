/**
 * KRONOS - Auth Context & Hooks (Custom Direct Grant Implementation)
 */
import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { UserWithProfile } from '../types';
import { authService } from '../services/authService';
import { tokenStorage } from '../utils/tokenStorage';
import { authApi } from '../services/api';

interface AuthContextType {
    user: UserWithProfile | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    roles: string[];
    hasRole: (role: string) => boolean;
    isAdmin: boolean;
    isApprover: boolean;
    isHR: boolean;
    isEmployee: boolean;
    login: (u: string, p: string) => Promise<void>;
    logout: () => void;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<UserWithProfile | null>(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const roles = user?.roles || [];
    const hasRole = (role: string): boolean =>
        roles.some(r => r.toLowerCase() === role.toLowerCase());

    const isAdmin = user?.is_admin || hasRole('admin');
    const isApprover = user?.is_approver || hasRole('approver');
    const isHR = user?.is_hr || hasRole('hr');
    const isEmployee = hasRole('employee') || hasRole('dipendente');

    const fetchUserProfile = async () => {
        try {
            // Get user info from backend
            const response = await authApi.get('/auth/me'); // Changed endpoint to match router (was /users/me but router has /auth/me)

            setUser({
                ...response.data,
            });
            setIsAuthenticated(true);
        } catch (error) {
            console.error('Failed to fetch user profile:', error);
            // Fallback to token decoding?
            const token = tokenStorage.getAccessToken();
            if (token) {
                const profile = authService.decodeToken(token);
                if (profile) {
                    setUser({
                        id: profile.id,
                        keycloak_id: profile.id,
                        email: profile.email,
                        username: profile.username,
                        first_name: profile.firstName,
                        last_name: profile.lastName,
                        full_name: `${profile.firstName} ${profile.lastName}`.trim(),
                        is_active: true,
                        created_at: new Date().toISOString(),
                        roles: profile.roles,
                        is_admin: profile.roles.includes('admin'),
                        is_manager: profile.roles.includes('manager'),
                        is_approver: profile.roles.includes('approver'),
                        is_hr: profile.roles.includes('hr'),
                    } as UserWithProfile);
                    setIsAuthenticated(true);
                } else {
                    handleLogout();
                }
            } else {
                handleLogout();
            }
        } finally {
            setIsLoading(false);
        }
    };

    const initAuth = async () => {
        const token = tokenStorage.getAccessToken();
        if (token) {
            // Validate token expiration could happen here
            await fetchUserProfile();
        } else {
            setIsLoading(false);
            setIsAuthenticated(false);
        }
    };

    useEffect(() => {
        initAuth();

        const handleAuthLogout = () => {
            handleLogout();
        };
        window.addEventListener('auth:logout', handleAuthLogout);
        return () => window.removeEventListener('auth:logout', handleAuthLogout);
    }, []);

    const login = async (u: string, p: string) => {
        setIsLoading(true);
        try {
            const tokens = await authService.login(u, p);
            tokenStorage.setTokens(tokens.access_token, tokens.refresh_token);
            await fetchUserProfile();
        } catch (e) {
            setIsLoading(false);
            throw e;
        }
    };

    const handleLogout = () => {
        tokenStorage.clear();
        setUser(null);
        setIsAuthenticated(false);
    };

    const logout = () => {
        handleLogout();
    };

    const refreshUser = async () => {
        await fetchUserProfile();
    };

    const value: AuthContextType = {
        user,
        isLoading,
        isAuthenticated,
        roles,
        hasRole,
        isAdmin,
        isApprover,
        isHR,
        isEmployee,
        login,
        logout,
        refreshUser,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

// Convenience hooks
export function useUser() {
    const { user } = useAuth();
    return user;
}

export function useIsAdmin() {
    const { isAdmin } = useAuth();
    return isAdmin;
}

export function useIsApprover() {
    const { isApprover, isAdmin, isHR } = useAuth();
    return isApprover || isAdmin || isHR;
}

export function useIsHR() {
    const { isHR, isAdmin } = useAuth();
    return isHR || isAdmin;
}

export function useIsEmployee() {
    const { isEmployee } = useAuth();
    return isEmployee;
}
