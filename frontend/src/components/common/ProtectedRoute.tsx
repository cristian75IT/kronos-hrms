/**
 * KRONOS - Protected Route Component
 */
import { useAuth } from '../../context/AuthContext';
import { Navigate, useLocation } from 'react-router-dom';
import { type ReactNode } from 'react';

interface ProtectedRouteProps {
    children: ReactNode;
    roles?: string[];
}

export function ProtectedRoute({ children, roles = [] }: ProtectedRouteProps) {
    const { isAuthenticated, isLoading, roles: userRoles } = useAuth();
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
        // Redirect to login page, saving the location they were trying to go to
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // Role check
    if (roles.length > 0) {
        const hasRole = roles.some((role) => userRoles.includes(role));

        if (!hasRole) {
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

    return children;
}
