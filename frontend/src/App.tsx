/**
 * KRONOS - Main App Component with Routing
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { NotificationProvider } from './context/NotificationContext';
import { MainLayout } from './components/layout/MainLayout';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { LoginPage } from './pages/auth/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { LeavesPage } from './pages/leaves/LeavesPage';
import { LeaveRequestForm } from './pages/leaves/LeaveRequestForm';
import { LeaveDetailPage } from './pages/leaves/LeaveDetailPage';
import { CalendarPage } from './pages/CalendarPage';
import { NotificationsPage } from './pages/NotificationsPage';

import { TripsPage } from './pages/expenses/TripsPage';
import { TripFormPage } from './pages/expenses/TripFormPage';
import { TripDetailPage } from './pages/expenses/TripDetailPage';
import { ExpensesPage } from './pages/expenses/ExpensesPage';
import { ExpenseFormPage } from './pages/expenses/ExpenseFormPage';
import { ExpenseDetailPage } from './pages/expenses/ExpenseDetailPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { NotificationCenterPage } from './pages/admin/NotificationCenterPage';
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
import { WikiSecurity } from './pages/wiki/WikiSecurity';
import { WikiHRReporting } from './pages/wiki/WikiHRReporting';
import { HRReportsPage } from './pages/hr/HRReportsPage';
import { HRConsolePage } from './pages/hr/HRConsolePage';
import { AuditLogPage } from './pages/admin/AuditLogPage';
import { AuditTrailPage } from './pages/admin/AuditTrailPage';
import { EmailLogsPage } from './pages/admin/EmailLogsPage';
import { HRTrainingPage } from './pages/hr/HRTrainingPage';
import { HRLeavesManagement } from './pages/hr/HRLeavesManagement';
import { HRTripsManagement } from './pages/hr/HRTripsManagement';
import { HRExpensesManagement } from './pages/hr/HRExpensesManagement';
import WorkflowConfigPage from './pages/admin/WorkflowConfigPage';
import PendingApprovalsPage from './pages/approvals/PendingApprovalsPage';
import RolesPage from './pages/admin/RolesPage';
import OrganizationPage from './pages/admin/OrganizationPage';
import { SystemInitializationPage } from './pages/admin/SystemInitializationPage';
import { AdminLeaveTypesPage } from './pages/admin/AdminLeaveTypesPage';
import { ProfilePage } from './pages/settings/ProfilePage';

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <NotificationProvider>
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
                <Route path="/profile" element={<ProfilePage />} />

                {/* Leaves */}
                <Route path="/leaves" element={<LeavesPage />} />
                <Route path="/leaves/new" element={<LeaveRequestForm />} />
                <Route path="/leaves/:id" element={<LeaveDetailPage />} />
                <Route path="/leaves/:id/edit" element={<LeaveRequestForm />} />
                <Route path="/calendar" element={<CalendarPage />} />
                <Route path="/notifications" element={<NotificationsPage />} />

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

                {/* Admin - Users */}
                <Route path="/admin/users" element={<ProtectedRoute permissions={['users:view']}><UsersPage /></ProtectedRoute>} />
                <Route path="/admin/users/new" element={<ProtectedRoute permissions={['users:create']}><UserFormPage /></ProtectedRoute>} />
                <Route path="/admin/users/:id" element={<ProtectedRoute permissions={['users:view']}><UserDetailPage /></ProtectedRoute>} />
                <Route path="/admin/users/:id/edit" element={<ProtectedRoute permissions={['users:edit']}><UserFormPage /></ProtectedRoute>} />

                {/* Admin - Calendars & Contracts */}
                <Route path="/admin/system-calendars" element={<ProtectedRoute permissions={['calendar:manage']}><SystemCalendarsPage /></ProtectedRoute>} />
                <Route path="/admin/national-contracts" element={<ProtectedRoute permissions={['contracts:view']}><NationalContractsPage /></ProtectedRoute>} />
                <Route path="/admin/national-contracts/:id" element={<ProtectedRoute permissions={['contracts:view']}><NationalContractDetailPage /></ProtectedRoute>} />
                <Route path="/admin/leave-types" element={<ProtectedRoute permissions={['settings:edit']}><AdminLeaveTypesPage /></ProtectedRoute>} />

                {/* Admin - Notifications & Email */}
                <Route path="/admin/notifications" element={<ProtectedRoute permissions={['notifications:send']}><NotificationCenterPage /></ProtectedRoute>} />
                <Route path="/admin/email-logs" element={<ProtectedRoute permissions={['notifications:view']}><EmailLogsPage /></ProtectedRoute>} />
                <Route path="/admin/setup" element={<ProtectedRoute permissions={['settings:edit']}><SystemInitializationPage /></ProtectedRoute>} />

                {/* Admin - Tools & Audit */}
                <Route path="/admin/organization" element={<ProtectedRoute permissions={['settings:edit']}><OrganizationPage /></ProtectedRoute>} />
                <Route path="/admin/tools" element={<ProtectedRoute permissions={['settings:edit']}><AdminToolsPage /></ProtectedRoute>} />
                <Route path="/admin/audit-logs" element={<ProtectedRoute permissions={['audit:view']}><AuditLogPage /></ProtectedRoute>} />
                <Route path="/admin/audit-trail" element={<ProtectedRoute permissions={['audit:view']}><AuditTrailPage /></ProtectedRoute>} />
                <Route path="/admin/email-logs" element={<ProtectedRoute permissions={['notifications:view']}><EmailLogsPage /></ProtectedRoute>} />

                {/* Admin - Workflows & RBAC */}
                <Route path="/admin/workflows" element={<ProtectedRoute permissions={['approvals:config']}><WorkflowConfigPage /></ProtectedRoute>} />
                <Route path="/admin/roles" element={<ProtectedRoute permissions={['roles:view']}><RolesPage /></ProtectedRoute>} />

                {/* HR Routes */}
                <Route path="/hr/console" element={<ProtectedRoute permissions={['reports:view']}><HRConsolePage /></ProtectedRoute>} />
                <Route path="/hr/reports" element={<ProtectedRoute permissions={['reports:view']}><HRReportsPage /></ProtectedRoute>} />
                <Route path="/hr/training" element={<ProtectedRoute permissions={['training:view']}><HRTrainingPage /></ProtectedRoute>} />
                <Route path="/hr/leaves" element={<ProtectedRoute permissions={['leaves:manage']}><HRLeavesManagement /></ProtectedRoute>} />
                <Route path="/hr/trips" element={<ProtectedRoute permissions={['trips:manage']}><HRTripsManagement /></ProtectedRoute>} />
                <Route path="/hr/expenses" element={<ProtectedRoute permissions={['expenses:manage']}><HRExpensesManagement /></ProtectedRoute>} />

                {/* Wiki & Knowledge Base */}
                <Route path="/wiki" element={<ProtectedRoute permissions={['wiki:view']}><WikiIndex /></ProtectedRoute>} />
                <Route path="/wiki/calculations" element={<ProtectedRoute permissions={['wiki:view']}><WikiCalculations /></ProtectedRoute>} />
                <Route path="/wiki/management" element={<ProtectedRoute permissions={['wiki:view']}><WikiManagement /></ProtectedRoute>} />
                <Route path="/wiki/config" element={<ProtectedRoute permissions={['wiki:view']}><WikiConfig /></ProtectedRoute>} />
                <Route path="/wiki/security" element={<ProtectedRoute permissions={['wiki:view']}><WikiSecurity /></ProtectedRoute>} />
                <Route path="/wiki/reporting" element={<ProtectedRoute permissions={['wiki:view']}><WikiHRReporting /></ProtectedRoute>} />
                <Route path="/wiki/contracts" element={<ProtectedRoute permissions={['wiki:view']}><WikiCalculations /></ProtectedRoute>} />

                {/* Approvals */}
                <Route path="/approvals/pending" element={<ProtectedRoute permissions={['approvals:process']}><PendingApprovalsPage /></ProtectedRoute>} />
                <Route path="/approvals" element={<Navigate to="/approvals/pending" replace />} />


              </Route>

              {/* Catch all */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </NotificationProvider>
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;
