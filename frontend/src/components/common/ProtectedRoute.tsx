/**
 * KRONOS - Protected Route Component with RBAC
 * 
 * Supports both role-based and permission-based access control.
 * Admin role always bypasses permission checks.
 */
import { useAuth } from '../../context/AuthContext';
import { Navigate, useLocation } from 'react-router-dom';
import { type ReactNode } from 'react';

interface ProtectedRouteProps {
    children: ReactNode;
    /** @deprecated Use permissions instead. Legacy role-based check. */
    roles?: string[];
    /** Required permissions (any match grants access) */
    permissions?: string[];
    /** Require ALL permissions (instead of any) */
    requireAll?: boolean;
}

export function ProtectedRoute({
    children,
    roles = [],
    permissions = [],
    requireAll = false
}: ProtectedRouteProps) {
    const {
        isAuthenticated,
        isLoading,
        isAdmin,
        hasRole,
        hasPermission
    } = useAuth();
    const location = useLocation();

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-bg-primary">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
                    <p className="text-text-secondary animate-pulse">Caricamento sicurezza...</p>
                </div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // Admin bypasses ALL permission checks
    if (isAdmin) {
        return <>{children}</>;
    }

    // Permission-based check (new RBAC system)
    if (permissions.length > 0) {
        const hasAccess = requireAll
            ? permissions.every(p => hasPermission(p))
            : permissions.some(p => hasPermission(p));

        if (!hasAccess) {
            return (
                <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
                    <div className="w-16 h-16 mb-4 rounded-full bg-red-100 flex items-center justify-center">
                        <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m0 0v2m0-2h2m-2 0H10m9.364-7.636A9 9 0 1112 3a9 9 0 017.364 7.364z" />
                        </svg>
                    </div>
                    <h1 className="text-2xl font-bold text-gray-800 mb-2">Accesso Negato</h1>
                    <p className="text-gray-600 mb-4">Non hai i permessi necessari per visualizzare questa pagina.</p>
                    <p className="text-sm text-gray-400 mb-6">
                        Permessi richiesti: {permissions.join(', ')}
                    </p>
                    <button
                        onClick={() => window.history.back()}
                        className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
                    >
                        Torna indietro
                    </button>
                </div>
            );
        }
    }

    // Legacy role check (fallback for backward compatibility)
    if (roles.length > 0) {
        const hasRoleAccess = roles.some(role => hasRole(role));

        if (!hasRoleAccess) {
            return (
                <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">Accesso Negato</h1>
                    <p className="text-gray-600 mb-6">Non hai i permessi necessari per visualizzare questa pagina.</p>
                    <button
                        onClick={() => window.history.back()}
                        className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
                    >
                        Torna indietro
                    </button>
                </div>
            );
        }
    }

    return <>{children}</>;
}
