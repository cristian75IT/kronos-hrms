/**
 * KRONOS - TypeScript Types & Interfaces
 */

// ═══════════════════════════════════════════════════════════════════
// Common Types
// ═══════════════════════════════════════════════════════════════════

export interface PaginatedResponse<T> {
    data: T[];
    total: number;
    page: number;
    limit: number;
    totalPages: number;
}

export interface ApiError {
    detail: string;
    code?: string;
    field?: string;
}

// ═══════════════════════════════════════════════════════════════════
// User & Auth Types
// ═══════════════════════════════════════════════════════════════════

export interface User {
    id: string;
    keycloak_id: string;
    email: string;
    username: string;
    first_name: string;
    last_name: string;
    full_name?: string;
    is_active: boolean;
    is_admin?: boolean;
    is_manager?: boolean;
    is_approver?: boolean;
    is_hr?: boolean;
    is_employee?: boolean;
    permissions?: string[];
    last_login?: string;
    created_at: string;

    // Organization
    department_id?: string;
    service_id?: string;
    executive_level_id?: string;
    department?: string; // flattened name
    service?: string; // flattened name
    executive_level?: string; // flattened name
}

export interface UserProfile {
    id: string;
    user_id: string;
    phone?: string;
    position?: string;
    hire_date?: string;
    termination_date?: string;
    contract_type?: string;
    weekly_hours?: number;
    manager_id?: string;
    employee_number?: string;
    location?: string;
    avatar_url?: string;

    // Organization
    department_id?: string | null;
    service_id?: string | null;
    executive_level_id?: string | null;

    // Relationships (Objects)
    department?: Department | null;
    service?: OrganizationalService | null;
    executive_level?: ExecutiveLevel | null;
}

export interface UserWithProfile extends User {
    profile?: UserProfile;
    roles: string[];
    permissions: string[];
}

export interface ContractType {
    id: string;
    code: string;
    name: string;
    description?: string;
    is_part_time: boolean;
    part_time_percentage: number;
    annual_vacation_days: number;
    annual_rol_hours: number;
    annual_permit_hours: number;
    is_active: boolean;
}

export interface EmployeeContract {
    id: string;
    user_id: string;
    contract_type_id: string;
    national_contract_id?: string;
    level_id?: string;
    start_date: string;
    end_date?: string;
    weekly_hours?: number;
    job_title?: string;
    department?: string;
    document_path?: string;
    created_at: string;
    updated_at: string;
    contract_type?: ContractType;
}

export interface EmployeeTraining {
    id: string;
    user_id: string;
    training_type: string;
    description?: string;
    issue_date: string;
    expiry_date?: string;
    certificate_id?: string;
    hours?: number;
    provider?: string;
    document_path?: string;
    created_at: string;
    updated_at: string;
}

export interface EmployeeTrainingCreate {
    user_id: string;
    training_type: string;
    description?: string;
    issue_date: string;
    expiry_date?: string;
    certificate_id?: string;
    hours?: number;
    provider?: string;
}

export interface EmployeeTrainingUpdate {
    training_type?: string;
    description?: string;
    issue_date?: string;
    expiry_date?: string;
    certificate_id?: string;
    hours?: number;
    provider?: string;
}


// ═══════════════════════════════════════════════════════════════════
// National Contracts (CCNL)
// ═══════════════════════════════════════════════════════════════════

export interface NationalContract {
    id: string;
    code: string;
    name: string;
    sector?: string;
    description?: string;
    source_url?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
    levels?: NationalContractLevel[];
}

export interface NationalContractTypeConfig {
    id: string;
    national_contract_version_id: string;
    contract_type_id: string;
    weekly_hours: number;
    annual_vacation_days: number;
    annual_rol_hours: number;
    annual_ex_festivita_hours: number;
    contract_type?: ContractType;
}

export interface CalculationMode {
    id: string;
    name: string;
    code: string;
    description?: string;
    function_name: string;
    default_parameters?: Record<string, any>;
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
}

export interface NationalContractVersion {
    id: string;
    national_contract_id: string;
    version_name: string;
    valid_from: string;
    valid_to?: string;

    weekly_hours_full_time: number;
    working_days_per_week: number;
    daily_hours: number;

    annual_vacation_days: number;
    vacation_accrual_method: string;
    vacation_carryover_months: number;

    annual_rol_hours: number;
    rol_accrual_method: string;
    rol_carryover_months: number;

    annual_ex_festivita_hours: number;

    sick_leave_carenza_days: number;
    sick_leave_max_days_year?: number;

    count_saturday_as_leave?: boolean;

    notes?: string;

    // Dynamic Calculation Modes
    vacation_calc_mode_id?: string;
    rol_calc_mode_id?: string;
    vacation_calc_params?: Record<string, any>;
    rol_calc_params?: Record<string, any>;

    vacation_calc_mode?: CalculationMode;
    rol_calc_mode?: CalculationMode;

    contract_type_configs?: NationalContractTypeConfig[];
    created_at: string;
}

export interface NationalContractLevel {
    id: string;
    national_contract_id: string;
    level_name: string;
    description?: string;
    sort_order: number;
}

export interface EmployeeContractCreate {
    contract_type_id: string;
    national_contract_id?: string;
    level_id?: string;
    start_date: string;
    end_date?: string;
    weekly_hours?: number;
    job_title?: string;
    department?: string;
    document_path?: string;
}

// ═══════════════════════════════════════════════════════════════════
// Calendar & Holidays
// ═══════════════════════════════════════════════════════════════════

export interface Holiday {
    id: string;
    date: string;
    name: string;
    location_id?: string;
    is_national: boolean;
    year: number;
    created_at: string;
}

export type ClosureType = 'total' | 'partial';

export interface CompanyClosure {
    id: string;
    name: string;
    description?: string;
    start_date: string;
    end_date: string;
    closure_type: ClosureType;
    affected_departments?: string[];
    affected_locations?: string[];
    is_paid: boolean;
    consumes_leave_balance: boolean;
    leave_type_id?: string;
    year: number;
    is_active: boolean;
    created_by?: string;
    created_at: string;
    updated_at: string;
}

export interface CompanyClosureCreate {
    name: string;
    description?: string;
    start_date: string;
    end_date: string;
    closure_type?: ClosureType;
    affected_departments?: string[];
    affected_locations?: string[];
    is_paid?: boolean;
    consumes_leave_balance?: boolean;
    leave_type_id?: string;
}

// ═══════════════════════════════════════════════════════════════════
// Leave Types

export type LeaveRequestStatus =
    | 'draft'
    | 'pending'
    | 'approved'
    | 'rejected'
    | 'cancelled'
    | 'approved_conditional'
    | 'recalled';

export type ConditionType = 'date_change' | 'partial_approval' | 'other';

export interface LeaveType {
    id: string;
    code: string;
    name: string;
    description?: string;
    color: string;
    icon?: string;
    scales_balance: boolean;
    balance_type?: 'vacation' | 'rol' | 'permits';
    requires_approval: boolean;
    requires_attachment: boolean;
    requires_protocol: boolean;
    max_consecutive_days?: number;
    max_single_request_days?: number;
    min_notice_days?: number;
    is_active: boolean;
}

export interface LeaveBalance {
    id: string;
    user_id: string;
    year: number;

    vacation_previous_year: number;
    vacation_current_year: number;
    vacation_accrued: number;
    vacation_used: number;
    vacation_available_ap: number;
    vacation_available_ac: number;
    vacation_available_total: number;

    rol_previous_year: number;
    rol_current_year: number;
    rol_accrued: number;
    rol_used: number;
    rol_available: number;

    permits_total: number;
    permits_used: number;
    permits_available: number;

    ap_expiry_date?: string;
    last_accrual_date?: string;
}

export interface LeaveBalanceSummary {
    vacation_available_ap: number;
    vacation_available_ac: number;
    vacation_total_available: number;
    rol_available: number;
    permits_available: number;
    ap_expiry_date?: string;
    days_until_ap_expiry?: number;
    // Pending reservations from ledger (days/hours in pending approval)
    pending_vacation?: number;
    pending_rol?: number;
    pending_permits?: number;
}

export interface LeaveRequest {
    id: string;
    user_id: string;
    user_name?: string;  // Full name of the requester
    leave_type_id: string;
    leave_type_code: string;
    status: LeaveRequestStatus;
    start_date: string;
    end_date: string;
    start_half_day: boolean;
    end_half_day: boolean;
    days_requested: number;
    employee_notes?: string;
    approver_notes?: string;
    approver_id?: string;
    approved_at?: string;
    condition_type?: ConditionType;
    condition_details?: string;
    condition_accepted?: boolean;
    protocol_number?: string;
    submitted_at?: string;
    created_at: string;
    updated_at: string;
    // Centralized approvals service integration
    approval_request_id?: string;
}

export interface LeaveRequestCreate {
    leave_type_id: string;
    start_date: string;
    end_date: string;
    start_half_day?: boolean;
    end_half_day?: boolean;
    employee_notes?: string;
    protocol_number?: string;
}

export interface LeaveRequestUpdate {
    start_date?: string;
    end_date?: string;
    start_half_day?: boolean;
    end_half_day?: boolean;
    employee_notes?: string;
    protocol_number?: string;
}

// ═══════════════════════════════════════════════════════════════════
// Expense Types
// ═══════════════════════════════════════════════════════════════════

export type TripStatus =
    | 'draft'
    | 'pending'
    | 'submitted'
    | 'approved'
    | 'rejected'
    | 'completed'
    | 'cancelled';

export type ExpenseReportStatus =
    | 'draft'
    | 'submitted'
    | 'approved'
    | 'rejected'
    | 'paid';

export type DestinationType = 'national' | 'eu' | 'extra_eu';

export interface ExpenseType {
    id: string;
    code: string;
    name: string;
    description?: string;
    category: string;
    requires_receipt: boolean;
    max_amount?: number;
    km_reimbursement_rate?: number;
    is_active: boolean;
}

export interface BusinessTrip {
    id: string;
    user_id: string;
    title: string;
    purpose?: string;
    destination: string;
    destination_type: DestinationType;
    start_date: string;
    end_date: string;
    status: TripStatus;
    project_code?: string;
    cost_center?: string;
    client_name?: string;
    attachment_path?: string;
    estimated_budget?: number;
    approver_id?: string;
    approved_at?: string;
    created_at: string;
}

export interface DailyAllowance {
    id: string;
    trip_id: string;
    date: string;
    is_full_day: boolean;
    breakfast_provided: boolean;
    lunch_provided: boolean;
    dinner_provided: boolean;
    base_amount: number;
    meals_deduction: number;
    final_amount: number;
    notes?: string;
}

export interface ExpenseReport {
    id: string;
    trip_id?: string;
    is_standalone: boolean;
    user_id: string;
    report_number: string;
    title: string;
    status: ExpenseReportStatus;
    period_start: string;
    period_end: string;
    total_amount: number;
    approved_amount?: number;
    employee_notes?: string;
    approver_notes?: string;
    created_at: string;
    items?: ExpenseItem[];
}

export interface ExpenseItem {
    id: string;
    report_id: string;
    expense_type_id: string;
    expense_type_code: string;
    date: string;
    description: string;
    amount: number;
    currency: string;
    exchange_rate: number;
    amount_eur: number;
    km_distance?: number;
    merchant_name?: string;
    receipt_number?: string;
    receipt_path?: string;
}



// ═══════════════════════════════════════════════════════════════════
// Calendar Types
// ═══════════════════════════════════════════════════════════════════

export interface CalendarEvent {
    id: string;
    title: string;
    start: string;
    end?: string;
    color?: string;
    allDay?: boolean;
    is_national?: boolean;
    userName?: string;
    extendedProps?: Record<string, unknown>;
}

export interface CalendarData {
    events: CalendarEvent[];
    holidays: CalendarEvent[];
    closures?: CalendarEvent[];
    teamEvents?: CalendarEvent[];
}
export interface Holiday {
    id: string;
    name: string;
    date: string;
    year: number;
    is_national: boolean;
}

// ═══════════════════════════════════════════════════════════════════
// Notification Types
// ═══════════════════════════════════════════════════════════════════

export interface Notification {
    id: string;
    user_id: string;
    notification_type: string;
    title: string;
    message: string;
    channel: 'in_app' | 'email' | 'push' | 'sms';
    status: 'pending' | 'sent' | 'delivered' | 'read' | 'failed';
    sent_at?: string;
    read_at?: string;
    recipient_name?: string;
    entity_type?: string;
    entity_id?: string;
    action_url?: string;
    created_at: string;
}

// ═══════════════════════════════════════════════════════════════════
// DataTable Types
// ═══════════════════════════════════════════════════════════════════

export interface DataTableRequest {
    draw: number;
    start: number;
    length: number;
    search_value?: string;
    order_column?: string;
    order_dir?: 'asc' | 'desc';
}

export interface DataTableResponse<T> {
    draw: number;
    recordsTotal: number;
    recordsFiltered: number;
    data: T[];
}

// ═══════════════════════════════════════════════════════════════════
// Audit Logs
// ═══════════════════════════════════════════════════════════════════

export interface AuditLogListItem {
    id: string;
    user_email: string | null;
    user_name?: string | null;
    action: string;
    resource_type: string;
    resource_id?: string;
    description?: string | null;
    status: 'SUCCESS' | 'FAILURE' | 'ERROR';
    service_name: string;
    created_at: string;
}

export interface AuditLogDetails extends AuditLogListItem {
    user_id?: string;
    description?: string;
    ip_address?: string;
    endpoint?: string;
    http_method?: string;
    error_message?: string;
    request_data?: any;
    response_data?: any;
}

// ═══════════════════════════════════════════════════════════════════
// HR Types
// ═══════════════════════════════════════════════════════════════════

export interface DailyAttendanceRequest {
    date: string;
    department?: string;
}

export interface DailyAttendanceItem {
    user_id: string;
    full_name: string;
    status: string;
    hours_worked?: number;
    leave_request_id?: string;
    leave_type_code?: string;
    leave_type?: string;     // Added to fix build
    department?: string;     // Added to fix build
    notes?: string;          // Added to fix build
}

export interface DailyAttendanceResponse {
    date: string;
    items: DailyAttendanceItem[];
    total_present: number;
    total_absent: number;
    total_employees?: number; // Added to fix build
}

// ═══════════════════════════════════════════════════════════════════
// HR Aggregate Reporting
// ═══════════════════════════════════════════════════════════════════

export interface AggregateReportRequest {
    start_date: string;
    end_date: string;
    department?: string;
}

export interface AggregateReportItem {
    user_id: string;
    full_name: string;
    total_days: number;
    worked_days: number;
    vacation_days: number;
    holiday_days: number;
    rol_hours: number;
    permit_hours: number;
    sick_days: number;
    other_absences: number;
}

export interface AggregateReportResponse {
    start_date: string;
    end_date: string;
    items: AggregateReportItem[];
}

// ═══════════════════════════════════════════════════════════════════
// HR Reporting & Dashboard Types
// ═══════════════════════════════════════════════════════════════════

export interface WorkforceStatus {
    total_employees: number;
    active_now: number;
    on_leave: number;
    on_trip: number;
    sick_leave: number;
    remote_working: number;
    absence_rate: number;
}

export interface HrPendingApprovals {
    total: number;
    leave_requests: number;
    expense_reports: number;
    trip_requests: number;
    // contracts: number; // Not currently provided by backend
    // other: number;
    // oldest_request_days: number; // Not currently provided by backend
}

export interface HrAlert {
    id: string;
    type: string;
    title: string;
    description: string;
    severity: 'info' | 'warning' | 'critical';
    employee_id?: string;
    employee_name?: string;
    department_id?: string;
    department_name?: string;
    created_at: string;
    action_required: boolean;
    action_deadline?: string;
    is_acknowledged: boolean;
    is_resolved: boolean;
}

export interface DashboardOverview {
    date: string;
    workforce: WorkforceStatus;
    pending_approvals: HrPendingApprovals;
    alerts: HrAlert[];
    quick_stats: {
        today_leaves: number;
        week_leaves: number;
        today_trips: number;
        week_trips: number;
    };
}

export interface HrDailySnapshot {
    id: string;
    created_at: string;
    snapshot_date: string;
    total_employees: number;
    on_leave: number;
    on_trip: number;
    sick_leave: number;
    remote_working: number;
    absence_rate: number;
    metrics: Record<string, any>;
}

export interface MonthlyReportResponse {
    id: string;
    year: number;
    month: number;
    generated_at: string;
    generated_by: string;
    status: string;
    employee_count: number;
    employees: any[]; // Detailed employee monthly data
    summary: Record<string, any>;
}

export interface ComplianceIssue {
    employee_id: string;
    employee_name: string;
    type: string;
    description: string;
    deadline?: string;
    days_missing?: number;
    severity: 'info' | 'warning' | 'critical' | string;
    resolved: boolean;
}

export interface ComplianceCheck {
    id: string;
    name: string;
    description: string;
    status: 'PASS' | 'WARN' | 'CRIT';
    result_value?: string;
    details?: string[];
}

export interface ComplianceStatistics {
    employees_compliant: number;
    employees_at_risk: number;
    employees_critical: number;
    compliance_rate: number;
}

export interface ComplianceReportResponse {
    period: string;
    compliance_status: 'OK' | 'WARNING' | 'CRITICAL' | string;
    issues: ComplianceIssue[];
    checks: ComplianceCheck[];
    statistics: ComplianceStatistics;
}

export interface BudgetReportResponse {
    year: number;
    generated_at: string;
    total_budget: number;
    spent_amount: number;
    remaining_amount: number;
    utilization_rate: number;
    breakdown_by_department: Record<string, number>;
    breakdown_by_category: Record<string, number>;
}

// ═══════════════════════════════════════════════════════════════════
// Enterprise Organization
// ═══════════════════════════════════════════════════════════════════

export interface ExecutiveLevel {
    id: string;
    code: string;
    title: string;
    hierarchy_level: number;
    escalates_to_id?: string;
    max_approval_amount?: number;
    can_override_workflow: boolean;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface ExecutiveLevelCreate {
    code: string;
    title: string;
    hierarchy_level: number;
    escalates_to_id?: string;
    max_approval_amount?: number;
    can_override_workflow?: boolean;
}

export interface ExecutiveLevelUpdate {
    title?: string;
    hierarchy_level?: number;
    escalates_to_id?: string;
    max_approval_amount?: number;
    can_override_workflow?: boolean;
    is_active?: boolean;
}

export interface Department {
    id: string;
    code: string;
    name: string;
    description?: string;
    parent_id?: string;
    manager_id?: string;
    deputy_manager_id?: string;
    cost_center_code?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;

    // Relations
    manager?: User;
    deputy_manager?: User;
    children?: Department[];
    services?: OrganizationalService[];
}

export interface DepartmentCreate {
    code: string;
    name: string;
    description?: string;
    parent_id?: string;
    manager_id?: string;
    deputy_manager_id?: string;
    cost_center_code?: string;
}

export interface DepartmentUpdate {
    name?: string;
    description?: string;
    parent_id?: string;
    manager_id?: string;
    deputy_manager_id?: string;
    cost_center_code?: string;
    is_active?: boolean;
}

export interface OrganizationalService {
    id: string;
    code: string;
    name: string;
    description?: string;
    department_id: string;
    coordinator_id?: string;
    deputy_coordinator_id?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;

    // Relations
    department_name?: string;
    coordinator?: User;
    deputy_coordinator?: User;
}

export interface OrganizationalServiceCreate {
    code: string;
    name: string;
    description?: string;
    department_id: string;
    coordinator_id?: string;
    deputy_coordinator_id?: string;
    is_active: boolean;
}

export interface OrganizationalServiceUpdate {
    name?: string;
    description?: string;
    department_id?: string;
    coordinator_id?: string;
    deputy_coordinator_id?: string;
    is_active?: boolean;
}
