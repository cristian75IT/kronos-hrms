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
import { CalendarPage } from './pages/CalendarPage';

import { TripsPage } from './pages/expenses/TripsPage';
import { TripFormPage } from './pages/expenses/TripFormPage';
import { TripDetailPage } from './pages/expenses/TripDetailPage';
import { ExpensesPage } from './pages/expenses/ExpensesPage';
import { ExpenseFormPage } from './pages/expenses/ExpenseFormPage';
import { ExpenseDetailPage } from './pages/expenses/ExpenseDetailPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { UsersPage } from './pages/admin/UsersPage';
import { UserFormPage } from './pages/admin/UserFormPage';
import { AdminToolsPage } from './pages/admin/AdminToolsPage';
import { UserDetailPage } from './pages/admin/UserDetailPage';
import { NationalContractsPage } from './pages/admin/NationalContractsPage';
import { NationalContractDetailPage } from './pages/admin/NationalContractDetailPage';
import { SystemCalendarsPage } from './pages/admin/SystemCalendarsPage';
import { WikiIndex } from './pages/wiki/WikiIndex';
import { WikiCalculations } from './pages/wiki/WikiCalculations';
import { WikiManagement } from './pages/wiki/WikiManagement';
import { WikiConfig } from './pages/wiki/WikiConfig';
import { HRReportsPage } from './pages/hr/HRReportsPage';
import { AuditLogPage } from './pages/admin/AuditLogPage';

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
              <Route path="/leaves/:id/edit" element={<LeaveRequestForm />} />
              <Route path="/calendar" element={<CalendarPage />} />

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
              <Route path="/admin/users/:id" element={<ProtectedRoute roles={['admin', 'hr']}><UserDetailPage /></ProtectedRoute>} />
              <Route path="/admin/users/:id/edit" element={<ProtectedRoute roles={['admin', 'hr']}><UserFormPage /></ProtectedRoute>} />
              <Route path="/admin/system-calendars" element={<ProtectedRoute roles={['admin', 'hr']}><SystemCalendarsPage /></ProtectedRoute>} />
              <Route path="/admin/national-contracts" element={<ProtectedRoute roles={['admin', 'hr']}><NationalContractsPage /></ProtectedRoute>} />
              <Route path="/admin/national-contracts/:id" element={<ProtectedRoute roles={['admin', 'hr']}><NationalContractDetailPage /></ProtectedRoute>} />
              <Route path="/admin/tools" element={<ProtectedRoute roles={['admin']}><AdminToolsPage /></ProtectedRoute>} />
              <Route path="/admin/audit-logs" element={<ProtectedRoute roles={['admin']}><AuditLogPage /></ProtectedRoute>} />

              {/* HR */}
              <Route path="/hr/reports" element={<ProtectedRoute roles={['hr', 'admin']}><HRReportsPage /></ProtectedRoute>} />

              {/* Wiki & Knowledge Base */}
              <Route path="/wiki" element={<WikiIndex />} />
              <Route path="/wiki/calculations" element={<WikiCalculations />} />
              <Route path="/wiki/management" element={<WikiManagement />} />
              <Route path="/wiki/config" element={<WikiConfig />} />
              <Route path="/wiki/contracts" element={<WikiCalculations />} /> {/* Shared logic for now */}


            </Route>

            {/* Catch all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;
