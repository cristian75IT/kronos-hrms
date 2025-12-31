/**
 * KRONOS - Main App Component with Routing
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { MainLayout } from './components/layout/MainLayout';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { LoginPage } from './pages/auth/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { LeavesPage } from './pages/leaves/LeavesPage';
import { LeaveRequestForm } from './pages/leaves/LeaveRequestForm';

import { TripsPage } from './pages/expenses/TripsPage';
import { ExpensesPage } from './pages/expenses/ExpensesPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { UsersPage } from './pages/admin/UsersPage';
import { TripFormPage } from './pages/expenses/TripFormPage';
import { ConfigPage } from './pages/admin/ConfigPage';
import { ExpenseFormPage } from './pages/expenses/ExpenseFormPage';

// Lazy load other pages
// const TripsPage = lazy(() => import('./pages/expenses/TripsPage'));

function App() {
  return (
    <AuthProvider>
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
            <Route path="/leaves/:id" element={<PlaceholderPage title="Dettaglio Richiesta" />} />

            {/* Trips */}
            <Route path="/trips" element={<TripsPage />} />
            <Route path="/trips/new" element={<TripFormPage />} />
            <Route path="/trips/:id" element={<PlaceholderPage title="Dettaglio Trasferta" />} />

            {/* Expenses */}
            <Route path="/expenses" element={<ExpensesPage />} />
            <Route path="/expenses/new" element={<ExpenseFormPage />} />
            <Route path="/expenses/:id" element={<PlaceholderPage title="Dettaglio Nota Spese" />} />

            {/* Approvals */}
            <Route path="/approvals" element={<ApprovalsPage />} />


            {/* Admin */}
            <Route path="/admin/users" element={<ProtectedRoute roles={['admin', 'hr']}><UsersPage /></ProtectedRoute>} />
            <Route path="/admin/config" element={<ProtectedRoute roles={['admin']}><ConfigPage /></ProtectedRoute>} />

          </Route>

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
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
