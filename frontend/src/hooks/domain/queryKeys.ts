


export const queryKeys = {
    // Leaves
    leaveRequests: ['leave-requests'] as const,
    leaveRequest: (id: string) => ['leave-requests', id] as const,
    pendingApprovals: ['leave-requests', 'pending'] as const,
    leaveBalance: (year?: number) => ['leave-balance', year] as const,
    balanceSummary: ['balance-summary'] as const,
    calendarEvents: (start: string, end: string) => ['calendar', start, end] as const,

    // Expenses
    trips: ['trips'] as const,
    trip: (id: string) => ['trips', id] as const,
    pendingTrips: ['trips', 'pending'] as const,
    tripAllowances: (tripId: string) => ['trips', tripId, 'allowances'] as const,

    reports: ['expense-reports'] as const,
    report: (id: string) => ['expense-reports', id] as const,
    pendingReports: ['expense-reports', 'pending'] as const,

    // Users
    users: ['users'] as const,
    user: (id: string) => ['users', id] as const,

    // Configs
    configs: ['configs'] as const,
    contractTypes: ['contract-types'] as const,
};
