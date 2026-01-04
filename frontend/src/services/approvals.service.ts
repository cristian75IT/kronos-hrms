/**
 * KRONOS - Approval Service API Client
 * 
 * Client for interacting with the approval workflow engine.
 */
import api from './api';

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

export interface WorkflowCondition {
    min_amount?: number;
    max_amount?: number;
    min_days?: number;
    max_days?: number;
    entity_subtypes?: string[];
    departments?: string[];
    locations?: string[];
}

export interface WorkflowConfig {
    id: string;
    entity_type: string;
    name: string;
    description?: string;
    min_approvers: number;
    max_approvers?: number;
    approval_mode: 'ANY' | 'ALL' | 'SEQUENTIAL' | 'MAJORITY';
    approver_role_ids: string[];
    auto_assign_approvers: boolean;
    allow_self_approval: boolean;
    expiration_hours?: number;
    expiration_action: 'REJECT' | 'ESCALATE' | 'AUTO_APPROVE' | 'NOTIFY_ONLY';
    escalation_role_id?: string;
    reminder_hours_before?: number;
    send_reminders: boolean;
    conditions?: WorkflowCondition;
    priority: number;
    is_active: boolean;
    is_default: boolean;
    created_at: string;
    updated_at: string;
    created_by?: string;
}

export interface WorkflowConfigCreate {
    entity_type: string;
    name: string;
    description?: string;
    min_approvers?: number;
    max_approvers?: number;
    approval_mode?: string;
    approver_role_ids?: string[];
    auto_assign_approvers?: boolean;
    allow_self_approval?: boolean;
    expiration_hours?: number;
    expiration_action?: string;
    escalation_role_id?: string;
    reminder_hours_before?: number;
    send_reminders?: boolean;
    conditions?: WorkflowCondition;
    priority?: number;
    is_active?: boolean;
    is_default?: boolean;
}

export interface ApprovalDecision {
    id: string;
    approval_request_id: string;
    approver_id: string;
    approver_name?: string;
    approver_role?: string;
    approval_level: number;
    decision?: 'APPROVED' | 'REJECTED' | 'DELEGATED';
    decision_notes?: string;
    delegated_to_id?: string;
    delegated_to_name?: string;
    assigned_at: string;
    decided_at?: string;
}

export interface ApprovalRequest {
    id: string;
    entity_type: string;
    entity_id: string;
    entity_ref?: string;
    workflow_config_id?: string;
    requester_id: string;
    requester_name?: string;
    title: string;
    description?: string;
    metadata?: Record<string, unknown>;
    status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED' | 'CANCELLED' | 'ESCALATED';
    required_approvals: number;
    received_approvals: number;
    received_rejections: number;
    current_level: number;
    max_level: number;
    expires_at?: string;
    resolved_at?: string;
    resolution_notes?: string;
    created_at: string;
    updated_at: string;
    decisions?: ApprovalDecision[];
}

export interface PendingApprovalItem {
    request_id: string;
    entity_type: string;
    entity_id: string;
    entity_ref?: string;
    title: string;
    description?: string;
    requester_name?: string;
    approval_level: number;
    is_urgent: boolean;
    expires_at?: string;
    days_pending: number;
    created_at: string;
}

export interface PendingApprovalsResponse {
    total: number;
    urgent_count: number;
    items: PendingApprovalItem[];
}

export interface PendingCountResponse {
    total: number;
    urgent: number;
    by_type: Record<string, number>;
}

export interface EntityTypeInfo {
    code: string;
    name: string;
    description: string;
}

export interface ApprovalModeInfo {
    code: string;
    name: string;
    description: string;
}

export interface ExpirationActionInfo {
    code: string;
    name: string;
    description: string;
}

// ═══════════════════════════════════════════════════════════
// Service
// ═══════════════════════════════════════════════════════════

const BASE_URL = '/approvals';

export const approvalsService = {
    // ─────────────────────────────────────────────────────────────
    // Configuration (Admin)
    // ─────────────────────────────────────────────────────────────

    async getWorkflowConfigs(entityType?: string, activeOnly = true): Promise<WorkflowConfig[]> {
        const params = new URLSearchParams();
        if (entityType) params.append('entity_type', entityType);
        params.append('active_only', String(activeOnly));

        const response = await api.get(`${BASE_URL}/config/workflows?${params}`);
        return response.data;
    },

    async getWorkflowConfig(id: string): Promise<WorkflowConfig> {
        const response = await api.get(`${BASE_URL}/config/workflows/${id}`);
        return response.data;
    },

    async createWorkflowConfig(data: WorkflowConfigCreate): Promise<WorkflowConfig> {
        const response = await api.post(`${BASE_URL}/config/workflows`, data);
        return response.data;
    },

    async updateWorkflowConfig(id: string, data: Partial<WorkflowConfigCreate>): Promise<WorkflowConfig> {
        const response = await api.put(`${BASE_URL}/config/workflows/${id}`, data);
        return response.data;
    },

    async deleteWorkflowConfig(id: string): Promise<void> {
        await api.delete(`${BASE_URL}/config/workflows/${id}`);
    },

    async getEntityTypes(): Promise<EntityTypeInfo[]> {
        const response = await api.get(`${BASE_URL}/config/entity-types`);
        return response.data;
    },

    async getApprovalModes(): Promise<ApprovalModeInfo[]> {
        const response = await api.get(`${BASE_URL}/config/approval-modes`);
        return response.data;
    },

    async getExpirationActions(): Promise<ExpirationActionInfo[]> {
        const response = await api.get(`${BASE_URL}/config/expiration-actions`);
        return response.data;
    },

    // ─────────────────────────────────────────────────────────────
    // Pending Approvals (for approvers)
    // ─────────────────────────────────────────────────────────────

    async getPendingApprovals(entityType?: string): Promise<PendingApprovalsResponse> {
        const params = entityType ? `?entity_type=${entityType}` : '';
        const response = await api.get(`${BASE_URL}/decisions/pending${params}`);
        return response.data;
    },

    async getPendingCount(): Promise<PendingCountResponse> {
        const response = await api.get(`${BASE_URL}/decisions/pending/count`);
        return response.data;
    },

    // ─────────────────────────────────────────────────────────────
    // Decisions
    // ─────────────────────────────────────────────────────────────

    async approveRequest(requestId: string, notes?: string): Promise<ApprovalRequest> {
        const response = await api.post(`${BASE_URL}/decisions/${requestId}/approve`, { notes });
        return response.data;
    },

    async rejectRequest(requestId: string, notes: string): Promise<ApprovalRequest> {
        const response = await api.post(`${BASE_URL}/decisions/${requestId}/reject`, { notes });
        return response.data;
    },

    async delegateRequest(
        requestId: string,
        delegateToId: string,
        delegateToName?: string,
        notes?: string
    ): Promise<ApprovalRequest> {
        const response = await api.post(`${BASE_URL}/decisions/${requestId}/delegate`, {
            delegate_to_id: delegateToId,
            delegate_to_name: delegateToName,
            notes,
        });
        return response.data;
    },

    // ─────────────────────────────────────────────────────────────
    // Requests
    // ─────────────────────────────────────────────────────────────

    async getApprovalRequest(requestId: string, includeHistory = false): Promise<ApprovalRequest> {
        const params = includeHistory ? '?include_history=true' : '';
        const response = await api.get(`${BASE_URL}/requests/${requestId}${params}`);
        return response.data;
    },

    async getApprovalByEntity(entityType: string, entityId: string): Promise<ApprovalRequest | null> {
        try {
            const response = await api.get(`${BASE_URL}/requests/entity/${entityType}/${entityId}`);
            return response.data;
        } catch {
            return null;
        }
    },

    async cancelRequest(requestId: string, reason?: string): Promise<void> {
        await api.delete(`${BASE_URL}/requests/${requestId}`, { data: { reason } });
    },

    async resubmitRequest(requestId: string): Promise<ApprovalRequest> {
        const response = await api.post(`${BASE_URL}/requests/${requestId}/resubmit`);
        return response.data;
    },
};

export default approvalsService;
