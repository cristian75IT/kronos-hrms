/**
 * KRONOS - Main App Component with Routing
 * Refactored for Performance (Lazy Loading) and Robustness (Error Boundary)
 */
import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { NotificationProvider } from './context/NotificationContext';
import { MainLayout } from './components/layout/MainLayout';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { ErrorBoundary } from './components/common/ErrorBoundary';

// Lazy Loaded Pages - Named Exports
const LoginPage = lazy(() => import('./pages/auth/LoginPage').then(m => ({ default: m.LoginPage })));
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const ProfilePage = lazy(() => import('./pages/settings/ProfilePage').then(m => ({ default: m.ProfilePage })));

// Leaves
const LeavesPage = lazy(() => import('./pages/leaves/LeavesPage').then(m => ({ default: m.LeavesPage })));
const LeaveRequestForm = lazy(() => import('./pages/leaves/LeaveRequestForm').then(m => ({ default: m.LeaveRequestForm })));
const LeaveDetailPage = lazy(() => import('./pages/leaves/LeaveDetailPage').then(m => ({ default: m.LeaveDetailPage })));
const CalendarPage = lazy(() => import('./pages/CalendarPage').then(m => ({ default: m.CalendarPage })));
const NotificationsPage = lazy(() => import('./pages/NotificationsPage').then(m => ({ default: m.NotificationsPage })));

// Expenses & Trips
const TripsPage = lazy(() => import('./pages/expenses/TripsPage').then(m => ({ default: m.TripsPage })));
const TripFormPage = lazy(() => import('./pages/expenses/TripFormPage').then(m => ({ default: m.TripFormPage })));
const TripDetailPage = lazy(() => import('./pages/expenses/TripDetailPage').then(m => ({ default: m.TripDetailPage })));
const ExpensesPage = lazy(() => import('./pages/expenses/ExpensesPage').then(m => ({ default: m.ExpensesPage })));
const ExpenseFormPage = lazy(() => import('./pages/expenses/ExpenseFormPage').then(m => ({ default: m.ExpenseFormPage })));
const ExpenseDetailPage = lazy(() => import('./pages/expenses/ExpenseDetailPage').then(m => ({ default: m.ExpenseDetailPage })));

// Approvals
const ApprovalsPage = lazy(() => import('./pages/ApprovalsPage').then(m => ({ default: m.ApprovalsPage })));
const PendingApprovalsPage = lazy(() => import('./pages/approvals/PendingApprovalsPage')); // Default export

// Admin User Management
const UsersPage = lazy(() => import('./pages/admin/UsersPage').then(m => ({ default: m.UsersPage })));
const UserFormPage = lazy(() => import('./pages/admin/UserFormPage').then(m => ({ default: m.UserFormPage })));
const UserDetailPage = lazy(() => import('./pages/admin/UserDetailPage').then(m => ({ default: m.UserDetailPage })));
const RolesPage = lazy(() => import('./pages/admin/RolesPage')); // Default export
const OrganizationPage = lazy(() => import('./pages/admin/OrganizationPage')); // Default export

// Admin Tools & Config
const AdminToolsPage = lazy(() => import('./pages/admin/AdminToolsPage').then(m => ({ default: m.AdminToolsPage })));
const NationalContractsPage = lazy(() => import('./pages/admin/NationalContractsPage').then(m => ({ default: m.NationalContractsPage })));
const NationalContractDetailPage = lazy(() => import('./pages/admin/NationalContractDetailPage').then(m => ({ default: m.NationalContractDetailPage })));
const SystemCalendarsPage = lazy(() => import('./pages/admin/SystemCalendarsPage').then(m => ({ default: m.SystemCalendarsPage })));
const SystemInitializationPage = lazy(() => import('./pages/admin/SystemInitializationPage').then(m => ({ default: m.SystemInitializationPage })));
const AdminLeaveTypesPage = lazy(() => import('./pages/admin/AdminLeaveTypesPage')); // Default export
const WorkflowConfigPage = lazy(() => import('./pages/admin/WorkflowConfigPage')); // Default export
const NotificationCenterPage = lazy(() => import('./pages/admin/NotificationCenterPage').then(m => ({ default: m.NotificationCenterPage })));
const AuditLogPage = lazy(() => import('./pages/admin/AuditLogPage').then(m => ({ default: m.AuditLogPage })));
const AuditTrailPage = lazy(() => import('./pages/admin/AuditTrailPage').then(m => ({ default: m.AuditTrailPage })));
const EmailLogsPage = lazy(() => import('./pages/admin/EmailLogsPage').then(m => ({ default: m.EmailLogsPage })));

// Wiki
const WikiIndex = lazy(() => import('./pages/wiki/WikiIndex').then(m => ({ default: m.WikiIndex })));
const WikiCalculations = lazy(() => import('./pages/wiki/WikiCalculations').then(m => ({ default: m.WikiCalculations })));
const WikiManagement = lazy(() => import('./pages/wiki/WikiManagement').then(m => ({ default: m.WikiManagement })));
const WikiConfig = lazy(() => import('./pages/wiki/WikiConfig').then(m => ({ default: m.WikiConfig })));
const WikiSecurity = lazy(() => import('./pages/wiki/WikiSecurity').then(m => ({ default: m.WikiSecurity })));
const WikiHRReporting = lazy(() => import('./pages/wiki/WikiHRReporting').then(m => ({ default: m.WikiHRReporting })));

// HR Management
const HRReportsPage = lazy(() => import('./pages/hr/HRReportsPage').then(m => ({ default: m.HRReportsPage })));
const HRConsolePage = lazy(() => import('./pages/hr/HRConsolePage').then(m => ({ default: m.HRConsolePage })));
const HRTrainingPage = lazy(() => import('./pages/hr/HRTrainingPage').then(m => ({ default: m.HRTrainingPage })));
const HRLeavesManagement = lazy(() => import('./pages/hr/HRLeavesManagement').then(m => ({ default: m.HRLeavesManagement })));
const HRTripsManagement = lazy(() => import('./pages/hr/HRTripsManagement').then(m => ({ default: m.HRTripsManagement })));
const HRExpensesManagement = lazy(() => import('./pages/hr/HRExpensesManagement').then(m => ({ default: m.HRExpensesManagement })));
const SmartWorkingPage = lazy(() => import('./pages/smart-working/SmartWorkingPage').then(m => ({ default: m.SmartWorkingPage })));


function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <NotificationProvider>
            <BrowserRouter>
              <Suspense fallback={<LoadingSpinner />}>
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
                    <Route path="/approvals/pending" element={<PendingApprovalsPage />} />

                    {/* Admin - Users */}
                    <Route path="/admin/users" element={<ProtectedRoute permissions={['users:view']}><UsersPage /></ProtectedRoute>} />
                    <Route path="/admin/users/new" element={<ProtectedRoute permissions={['users:create']}><UserFormPage /></ProtectedRoute>} />
                    <Route path="/admin/users/:id" element={<ProtectedRoute permissions={['users:view']}><UserDetailPage /></ProtectedRoute>} />
                    <Route path="/admin/users/:id/edit" element={<ProtectedRoute permissions={['users:edit']}><UserFormPage /></ProtectedRoute>} />
                    <Route path="/admin/roles" element={<ProtectedRoute permissions={['roles:view']}><RolesPage /></ProtectedRoute>} />
                    <Route path="/admin/organization" element={<ProtectedRoute permissions={['settings:view']}><OrganizationPage /></ProtectedRoute>} />

                    {/* Admin - Global Tools */}
                    <Route path="/admin/tools" element={<ProtectedRoute permissions={['system:admin']}><AdminToolsPage /></ProtectedRoute>} />
                    <Route path="/admin/initialization" element={<ProtectedRoute permissions={['system:superadmin']}><SystemInitializationPage /></ProtectedRoute>} />
                    <Route path="/admin/notifications" element={<ProtectedRoute permissions={['notifications:manage']}><NotificationCenterPage /></ProtectedRoute>} />
                    <Route path="/admin/workflow-config" element={<ProtectedRoute permissions={['workflows:manage']}><WorkflowConfigPage /></ProtectedRoute>} />
                    <Route path="/admin/workflows" element={<ProtectedRoute permissions={['approvals:config']}><WorkflowConfigPage /></ProtectedRoute>} />

                    {/* Admin - Contracts & Leaves */}
                    <Route path="/admin/national-contracts" element={<ProtectedRoute permissions={['contracts:manage']}><NationalContractsPage /></ProtectedRoute>} />
                    <Route path="/admin/national-contracts/:id" element={<ProtectedRoute permissions={['contracts:manage']}><NationalContractDetailPage /></ProtectedRoute>} />
                    <Route path="/admin/leave-types" element={<ProtectedRoute permissions={['settings:manage']}><AdminLeaveTypesPage /></ProtectedRoute>} />
                    <Route path="/admin/system-calendars" element={<ProtectedRoute permissions={['calendars:manage']}><SystemCalendarsPage /></ProtectedRoute>} />

                    {/* Admin - Audit Link */}
                    <Route path="/admin/audit/logs" element={<ProtectedRoute permissions={['audit:view']}><AuditLogPage /></ProtectedRoute>} />
                    <Route path="/admin/audit/trail" element={<ProtectedRoute permissions={['audit:view']}><AuditTrailPage /></ProtectedRoute>} />
                    <Route path="/admin/audit/emails" element={<ProtectedRoute permissions={['audit:view']}><EmailLogsPage /></ProtectedRoute>} />

                    {/* HR Management - Console */}
                    <Route path="/hr/console" element={<ProtectedRoute permissions={['hr:view']}><HRConsolePage /></ProtectedRoute>} />
                    <Route path="/hr/reports" element={<ProtectedRoute permissions={['hr:reporting']}><HRReportsPage /></ProtectedRoute>} />
                    <Route path="/hr/training" element={<ProtectedRoute permissions={['hr:view']}><HRTrainingPage /></ProtectedRoute>} />
                    <Route path="/hr/leaves" element={<ProtectedRoute permissions={['hr:view']}><HRLeavesManagement /></ProtectedRoute>} />
                    <Route path="/hr/trips" element={<ProtectedRoute permissions={['hr:view']}><HRTripsManagement /></ProtectedRoute>} />
                    <Route path="/hr/expenses" element={<ProtectedRoute permissions={['hr:view']}><HRExpensesManagement /></ProtectedRoute>} />

                    {/* Smart Working */}
                    <Route path="/smart-working" element={<ProtectedRoute><SmartWorkingPage /></ProtectedRoute>} />

                    {/* Documentation / Wiki */}
                    <Route path="/wiki" element={<WikiIndex />} />
                    <Route path="/wiki/calculations" element={<WikiCalculations />} />
                    <Route path="/wiki/management" element={<WikiManagement />} />
                    <Route path="/wiki/config" element={<WikiConfig />} />
                    <Route path="/wiki/security" element={<WikiSecurity />} />
                    <Route path="/wiki/hr-reporting" element={<WikiHRReporting />} />
                  </Route>
                </Routes>
              </Suspense>
            </BrowserRouter>
          </NotificationProvider>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
