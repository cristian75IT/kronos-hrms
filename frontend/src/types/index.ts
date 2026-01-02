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
    is_active: boolean;
    is_superuser?: boolean; // Admin
    is_manager?: boolean;
    is_approver?: boolean;
    is_hr?: boolean;
    last_login?: string;
    created_at: string;
}

export interface UserProfile {
    id: string;
    user_id: string;
    phone?: string;
    department?: string;
    position?: string;
    hire_date?: string;
    contract_type?: string;
    weekly_hours?: number;
    manager_id?: string;
    employee_number?: string;
    location?: string;
    avatar_url?: string;
}

export interface UserWithProfile extends User {
    profile?: UserProfile;
    roles: string[];
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
    max_consecutive_days?: number;
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
    submitted_at?: string;
    created_at: string;
    updated_at: string;
}

export interface LeaveRequestCreate {
    leave_type_id: string;
    start_date: string;
    end_date: string;
    start_half_day?: boolean;
    end_half_day?: boolean;
    employee_notes?: string;
}

export interface LeaveRequestUpdate {
    start_date?: string;
    end_date?: string;
    start_half_day?: boolean;
    end_half_day?: boolean;
    employee_notes?: string;
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
    is_approved?: boolean;
    rejection_reason?: string;
}

// ═══════════════════════════════════════════════════════════════════
// Wallet Types (Leaves & Expensive)
// ═══════════════════════════════════════════════════════════════════

export interface TripWallet {
    id: string;
    trip_id: string;
    user_id: string;
    budget: number;
    spent: number;
    balance: number;
    total_taxable: number;
    total_non_taxable: number;
    currency: string;
    status: string;
    policy_violations_count: number;
    compliance_flags: Record<string, any>;
    last_transaction_at?: string;
}

export interface TripWalletTransaction {
    id: string;
    wallet_id: string;
    transaction_type: string;
    category: string;
    amount: number;
    tax_amount: number;
    tax_rate: number;
    is_reimbursable: boolean;
    is_taxable: boolean;
    has_receipt: boolean;
    reference_id?: string;
    description?: string;
    compliance_flags: Record<string, any>;
    policy_violations: string[];
    created_at: string;
    created_by?: string;
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
    channel: 'in_app' | 'email';
    is_read: boolean;
    read_at?: string;
    entity_type?: string;
    entity_id?: string;
    action_url?: string;
    priority: 'low' | 'normal' | 'high' | 'urgent';
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
    user_email?: string;
    action: string;
    resource_type: string;
    resource_id?: string;
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
}

export interface DailyAttendanceResponse {
    date: string;
    items: DailyAttendanceItem[];
    total_present: number;
    total_absent: number;
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
