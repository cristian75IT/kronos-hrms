/**
 * KRONOS - Main App Component with Routing
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { MainLayout } from './components/layout/MainLayout';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { LoginPage } from './pages/auth/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { LeavesPage } from './pages/leaves/LeavesPage';
import { LeaveRequestForm } from './pages/leaves/LeaveRequestForm';
import { LeaveDetailPage } from './pages/leaves/LeaveDetailPage';

import { TripsPage } from './pages/expenses/TripsPage';
import { TripFormPage } from './pages/expenses/TripFormPage';
import { TripDetailPage } from './pages/expenses/TripDetailPage';
import { ExpensesPage } from './pages/expenses/ExpensesPage';
import { ExpenseFormPage } from './pages/expenses/ExpenseFormPage';
import { ExpenseDetailPage } from './pages/expenses/ExpenseDetailPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { UsersPage } from './pages/admin/UsersPage';
import { UserFormPage } from './pages/admin/UserFormPage';
import { CompanyClosuresPage } from './pages/admin/CompanyClosuresPage';
import { ConfigPage } from './pages/admin/ConfigPage';

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Routes */}
            <Route element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }>
              <Route path="/" element={<DashboardPage />} />

              {/* Leaves */}
              <Route path="/leaves" element={<LeavesPage />} />
              <Route path="/leaves/new" element={<LeaveRequestForm />} />
              <Route path="/leaves/:id" element={<LeaveDetailPage />} />

              {/* Trips */}
              <Route path="/trips" element={<TripsPage />} />
              <Route path="/trips/new" element={<TripFormPage />} />
              <Route path="/trips/:id" element={<TripDetailPage />} />

              {/* Expenses */}
              <Route path="/expenses" element={<ExpensesPage />} />
              <Route path="/expenses/new" element={<ExpenseFormPage />} />
              <Route path="/expenses/:id" element={<ExpenseDetailPage />} />

              {/* Approvals */}
              <Route path="/approvals" element={<ApprovalsPage />} />

              {/* Admin */}
              <Route path="/admin/users" element={<ProtectedRoute roles={['admin', 'hr']}><UsersPage /></ProtectedRoute>} />
              <Route path="/admin/users/new" element={<ProtectedRoute roles={['admin', 'hr']}><UserFormPage /></ProtectedRoute>} />
              <Route path="/admin/users/:id" element={<ProtectedRoute roles={['admin', 'hr']}><PlaceholderPage title="Dettaglio Utente" /></ProtectedRoute>} />
              <Route path="/admin/closures" element={<ProtectedRoute roles={['admin', 'hr']}><CompanyClosuresPage /></ProtectedRoute>} />
              <Route path="/admin/config" element={<ProtectedRoute roles={['admin']}><ConfigPage /></ProtectedRoute>} />

            </Route>

            {/* Catch all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}

// Temporary placeholder for unimplemented pages
function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="placeholder-page">
      <div className="placeholder-content">
        <h1>{title}</h1>
        <p>Questa pagina è in fase di sviluppo</p>
      </div>
      <style>{`
        .placeholder-page {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 60vh;
        }
        .placeholder-content {
          text-align: center;
        }
        .placeholder-content h1 {
          font-size: var(--font-size-2xl);
          margin-bottom: var(--space-2);
        }
        .placeholder-content p {
          color: var(--color-text-muted);
        }
      `}</style>
    </div>
  );
}

export default App;

