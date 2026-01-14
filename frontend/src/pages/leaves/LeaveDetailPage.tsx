/**
 * KRONOS - Leave Detail Page (Refactored)
 * 
 * Displays detailed information about a leave request with actions.
 * Uses extracted hooks and components for better maintainability.
 */
import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
    ArrowLeft,
    Calendar,
    Clock,
    FileText,
    CheckCircle,
    XCircle,
    AlertCircle,
    Download,
    MessageSquare,
    History,
    Edit,
    Trash2,
    Send,
    Loader,
    Ban,
    Phone,
    Shield,
} from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { useQuery } from '@tanstack/react-query';

import { useLeaveRequest } from '../../hooks/domain/useLeaves';
import { useLeaveDetailActions } from '../../hooks/domain/useLeaveDetailActions';
import { useAuth, useIsApprover, useIsAdmin, useIsHR } from '../../context/AuthContext';
import approvalsService from '../../services/approvals.service';
import { ExcludedDaysSection, LeaveDetailModals } from '../../components/leaves';

// Constants
const LEAVE_TYPE_NAMES: Record<string, string> = {
    FER: 'Ferie',
    ROL: 'Riduzione Orario Lavoro',
    PAR: 'Ex-Festività / Altri',
    MAL: 'Malattia',
    MAT: 'Maternità/Paternità',
    LUT: 'Lutto',
    STU: 'Studio',
    DON: 'Donazione Sangue',
    L104: 'Legge 104',
    SW: 'Smart Working',
    NRT: 'Non Retribuito',
};

const CONDITION_TYPE_LABELS: Record<string, string> = {
    'ric': 'Riserva di Richiamo',
    'RIC': 'Riserva di Richiamo',
    'rep': 'Reperibilità',
    'REP': 'Reperibilità',
    'par': 'Approvazione Parziale',
    'PAR': 'Approvazione Parziale',
    'mod': 'Modifica Date',
    'MOD': 'Modifica Date',
    'alt': 'Altra Condizione',
    'ALT': 'Altra Condizione',
};

function getStatusConfig(status: string) {
    const configs: Record<string, { className: string; icon: React.ReactNode; label: string }> = {
        pending: {
            className: 'bg-amber-50 text-amber-700 border-amber-200',
            icon: <Clock size={16} />,
            label: 'In Attesa'
        },
        approved: {
            className: 'bg-emerald-50 text-emerald-700 border-emerald-200',
            icon: <CheckCircle size={16} />,
            label: 'Approvata'
        },
        rejected: {
            className: 'bg-red-50 text-red-700 border-red-200',
            icon: <XCircle size={16} />,
            label: 'Rifiutata'
        },
        draft: {
            className: 'bg-gray-100 text-gray-600 border-gray-200',
            icon: <FileText size={16} />,
            label: 'Bozza'
        },
        cancelled: {
            className: 'bg-gray-100 text-gray-500 border-gray-200',
            icon: <XCircle size={16} />,
            label: 'Annullata'
        },
    };
    return configs[status] || configs.pending;
}

export function LeaveDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const { user } = useAuth();
    const isApprover = useIsApprover();
    const isAdmin = useIsAdmin();
    const isHR = useIsHR();

    // Data fetching
    const { data: leave, isLoading, refetch } = useLeaveRequest(id || '');

    const { data: approvalRequest } = useQuery({
        queryKey: ['approval-request', leave?.approval_request_id],
        queryFn: () => approvalsService.getApprovalRequest(leave!.approval_request_id!),
        enabled: !!leave?.approval_request_id,
    });

    const { data: workflowConfig } = useQuery({
        queryKey: ['workflow-config', approvalRequest?.workflow_config_id],
        queryFn: () => approvalsService.getWorkflowConfig(approvalRequest!.workflow_config_id!),
        enabled: !!approvalRequest?.workflow_config_id,
    });

    // Actions hook
    const actions = useLeaveDetailActions({
        leaveId: id,
        approvalRequestId: leave?.approval_request_id,
        onRefetch: refetch,
    });

    // UI State
    const [activeTab, setActiveTab] = useState<'details' | 'history'>('details');

    // Derived state
    const isOwner = user?.id === leave?.user_id || user?.keycloak_id === leave?.user_id;
    const status = leave?.status?.toLowerCase() || 'draft';
    const statusConfig = getStatusConfig(status);

    // Loading state
    if (isLoading) {
        return (
            <div className="detail-page animate-fadeIn">
                <div className="detail-loading">
                    <div className="spinner-lg" />
                    <p>Caricamento richiesta...</p>
                </div>
            </div>
        );
    }

    // Not found state
    if (!leave) {
        return (
            <div className="detail-page animate-fadeIn">
                <div className="detail-empty">
                    <AlertCircle size={48} />
                    <h2>Richiesta non trovata</h2>
                    <p>La richiesta che stai cercando non esiste o è stata eliminata.</p>
                    <Link to="/leaves" className="btn btn-primary">
                        Torna alle Ferie
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto space-y-6 pb-8 animate-fadeIn px-4 sm:px-6 lg:px-8 pt-6">
            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start gap-4">
                <div className="flex items-start gap-4">
                    <button
                        onClick={() => navigate(-1)}
                        className="p-2 rounded-full hover:bg-gray-100 transition-colors text-gray-500 hover:text-gray-900"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                            <Link to="/leaves" className="hover:text-indigo-600 transition-colors">Ferie</Link>
                            <span>/</span>
                            <span>Dettaglio Richiesta</span>
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            {LEAVE_TYPE_NAMES[leave.leave_type_code] || leave.leave_type_code}
                        </h1>
                    </div>
                </div>
                <div className={`px-4 py-2 rounded-full border flex items-center gap-2 text-sm font-semibold ${statusConfig.className}`}>
                    {statusConfig.icon}
                    <span>{statusConfig.label}</span>
                </div>
            </header>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-8 items-start">
                {/* Left Column - Main Info */}
                <div>
                    {/* Tabs */}
                    <div className="flex p-1 space-x-1 bg-gray-100/80 rounded-xl mb-6 border border-gray-200">
                        <button
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${activeTab === 'details'
                                ? 'bg-white text-gray-900 shadow-sm ring-1 ring-black/5'
                                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200/50'
                                }`}
                            onClick={() => setActiveTab('details')}
                        >
                            <FileText size={16} />
                            Dettagli
                        </button>
                        <button
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${activeTab === 'history'
                                ? 'bg-white text-gray-900 shadow-sm ring-1 ring-black/5'
                                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200/50'
                                }`}
                            onClick={() => setActiveTab('history')}
                        >
                            <History size={16} />
                            Cronologia
                        </button>
                    </div>

                    {activeTab === 'details' && (
                        <DetailsTab leave={leave} />
                    )}

                    {activeTab === 'history' && (
                        <HistoryTab leave={leave} />
                    )}
                </div>

                {/* Right Column - Actions & Summary */}
                <div className="space-y-6">
                    {/* Workflow Info Card */}
                    {workflowConfig && (
                        <WorkflowInfoCard workflowConfig={workflowConfig} />
                    )}

                    {/* Actions Card */}
                    <ActionsCard
                        isOwner={isOwner}
                        isApprover={isApprover}
                        isAdmin={isAdmin}
                        isHR={isHR}
                        status={status}
                        leaveId={id || ''}
                        actionLoading={actions.actionLoading}
                        onSubmit={actions.handleSubmit}
                        onDelete={actions.onRequestDelete}
                        onShowCancelModal={() => actions.setShowCancelModal(true)}
                        onShowApproveModal={() => actions.setShowApproveModal(true)}
                        onShowRejectModal={() => actions.setShowRejectModal(true)}
                        onShowConditionalModal={() => actions.setShowConditionalModal(true)}
                        onShowRevokeModal={() => actions.setShowRevokeModal(true)}
                        onShowRecallModal={() => actions.setShowRecallModal(true)}
                        onShowReopenModal={() => actions.setShowReopenModal(true)}
                        onConditionResponse={actions.handleConditionResponse}
                    />

                    {/* Summary Card */}
                    <SummaryCard leave={leave} />
                </div>
            </div>

            {/* Modals */}
            <LeaveDetailModals
                {...actions}
                handleApprove={actions.handleApprove}
                handleReject={actions.handleReject}
                handleCancel={actions.handleCancel}
                handleConditionalApprove={actions.handleConditionalApprove}
                handleRevoke={actions.handleRevoke}
                handleReopen={actions.handleReopen}
                handleRecall={actions.handleRecall}
                confirmDelete={actions.confirmDelete}
            />
        </div>
    );
}

// ============================================================================
// Sub-components
// ============================================================================

interface LeaveData {
    start_date: string;
    end_date: string;
    start_half_day?: boolean;
    end_half_day?: boolean;
    days_requested: number;
    employee_notes?: string;
    approver_notes?: string;
    has_conditions?: boolean;
    condition_type?: string;
    condition_details?: string;
    condition_accepted?: boolean;
    condition_accepted_at?: string;
    attachment_path?: string;
    status: string;
    created_at: string;
    updated_at: string;
    approved_at?: string;
    leave_type_code: string;
}

function DetailsTab({ leave }: { leave: LeaveData }) {
    return (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm animate-fadeInUp">
            {/* Period Info */}
            <div className="p-6 border-b border-gray-100">
                <h3 className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider mb-6">
                    <Calendar size={18} />
                    Periodo Richiesto
                </h3>
                <div className="bg-gray-50/50 rounded-xl p-6 border border-gray-100">
                    <div className="flex flex-col gap-6">
                        {/* Start Date */}
                        <div>
                            <div className="text-xs uppercase font-semibold text-gray-400 mb-1 tracking-wide">Dal</div>
                            <div className="flex flex-wrap items-center gap-3">
                                <span className="text-lg font-semibold text-gray-900 capitalize">
                                    {format(new Date(leave.start_date), 'EEEE d MMMM yyyy', { locale: it })}
                                </span>
                                {leave.start_half_day && (
                                    <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                                        Solo pomeriggio
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Days connector */}
                        <div className="flex items-center gap-4">
                            <div className="h-px bg-gray-200 flex-1"></div>
                            <span className="px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-sm font-bold border border-indigo-100">
                                {leave.days_requested} giorni
                            </span>
                            <div className="h-px bg-gray-200 flex-1"></div>
                        </div>

                        {/* End Date */}
                        <div>
                            <div className="text-xs uppercase font-semibold text-gray-400 mb-1 tracking-wide">Al</div>
                            <div className="flex flex-wrap items-center gap-3">
                                <span className="text-lg font-semibold text-gray-900 capitalize">
                                    {format(new Date(leave.end_date), 'EEEE d MMMM yyyy', { locale: it })}
                                </span>
                                {leave.end_half_day && (
                                    <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                                        Solo mattina
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Excluded Days Section */}
                <ExcludedDaysSection startDate={leave.start_date} endDate={leave.end_date} />
            </div>

            {/* Employee Notes */}
            {leave.employee_notes && (
                <div className="p-6 border-b border-gray-100">
                    <h3 className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">
                        <MessageSquare size={18} />
                        Note del Dipendente
                    </h3>
                    <p className="text-gray-700 bg-yellow-50/50 p-4 rounded-lg border border-yellow-100 text-sm leading-relaxed">
                        {leave.employee_notes}
                    </p>
                </div>
            )}

            {/* Approver Notes */}
            {leave.approver_notes && (
                <div className="p-6 border-b border-gray-100">
                    <h3 className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">
                        <MessageSquare size={18} />
                        Note dell'Approvatore
                    </h3>
                    <p className="text-gray-700 bg-gray-50 p-4 rounded-lg border border-gray-100 text-sm leading-relaxed">
                        {leave.approver_notes}
                    </p>
                </div>
            )}

            {/* Condition Details */}
            {leave.has_conditions && leave.condition_details && (
                <div className="p-6 border-b border-gray-100">
                    <h3 className="flex items-center gap-2 text-sm font-bold text-amber-500 uppercase tracking-wider mb-4">
                        <AlertCircle size={18} />
                        Condizioni di Approvazione
                    </h3>
                    <div className="bg-amber-50 p-4 rounded-lg border border-amber-100 text-sm leading-relaxed">
                        <div className="flex flex-wrap items-center gap-2 mb-3 text-amber-800">
                            <span className="font-semibold">
                                {CONDITION_TYPE_LABELS[leave.condition_type || ''] || leave.condition_type}
                            </span>
                            {leave.status === 'approved' && leave.condition_accepted && (
                                <span className="bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded text-xs flex items-center gap-1">
                                    <CheckCircle size={10} /> Accettata dal dipendente
                                </span>
                            )}
                        </div>
                        <p className="text-gray-700 mb-3">{leave.condition_details}</p>

                        {leave.condition_accepted && leave.condition_accepted_at && (
                            <div className="mt-3 pt-3 border-t border-amber-200 text-xs text-gray-600 flex items-center gap-2">
                                <CheckCircle size={12} className="text-emerald-600" />
                                <span>
                                    Condizioni accettate il{' '}
                                    <strong>
                                        {format(new Date(leave.condition_accepted_at), "EEEE d MMMM yyyy 'alle' HH:mm", { locale: it })}
                                    </strong>
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Attachment */}
            {leave.attachment_path && (
                <div className="p-6">
                    <h3 className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">
                        <FileText size={18} />
                        Allegato
                    </h3>
                    <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                        <Download size={16} />
                        Scarica Allegato
                    </button>
                </div>
            )}
        </div>
    );
}

function HistoryTab({ leave }: { leave: LeaveData }) {
    return (
        <div className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm animate-fadeInUp">
            <div className="relative border-l-2 border-gray-100 ml-3 space-y-8">
                <div className="relative pl-8">
                    <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 border-white bg-indigo-500 shadow-sm" />
                    <div className="font-semibold text-gray-900">Richiesta Creata</div>
                    <div className="text-sm text-gray-500 mt-1">
                        {format(new Date(leave.created_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                    </div>
                </div>
                {leave.status !== 'draft' && (
                    <div className="relative pl-8">
                        <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 border-white bg-blue-500 shadow-sm" />
                        <div className="font-semibold text-gray-900">Richiesta Inviata</div>
                        <div className="text-sm text-gray-500 mt-1">
                            {format(new Date(leave.created_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                        </div>
                    </div>
                )}
                {leave.status === 'approved' && leave.approved_at && (
                    <div className="relative pl-8">
                        <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 border-white bg-emerald-500 shadow-sm" />
                        <div className="font-semibold text-gray-900">Richiesta Approvata</div>
                        <div className="text-sm text-gray-500 mt-1">
                            {format(new Date(leave.approved_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                        </div>
                    </div>
                )}
                {leave.status === 'rejected' && (
                    <div className="relative pl-8">
                        <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 border-white bg-red-500 shadow-sm" />
                        <div className="font-semibold text-gray-900">Richiesta Rifiutata</div>
                        <div className="text-sm text-gray-500 mt-1">
                            {format(new Date(leave.updated_at), 'd MMMM yyyy, HH:mm', { locale: it })}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

interface WorkflowConfig {
    name: string;
    min_approvers: number;
    approval_mode: string;
    target_role_ids?: string[];
    expiration_hours?: number;
}

function WorkflowInfoCard({ workflowConfig }: { workflowConfig: WorkflowConfig }) {
    return (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden animate-fadeInUp">
            <div className="p-4 bg-indigo-50 border-b border-indigo-100 flex items-center justify-between">
                <h3 className="text-sm font-bold text-indigo-900 uppercase tracking-wide flex items-center gap-2">
                    <Shield size={16} />
                    Regole Approvazione
                </h3>
                <div className="text-xs font-medium bg-white text-indigo-600 px-2 py-0.5 rounded border border-indigo-100">
                    {workflowConfig.min_approvers} {workflowConfig.min_approvers === 1 ? 'approvazione' : 'approvazioni'}
                </div>
            </div>
            <div className="p-4 space-y-3">
                <div className="text-sm">
                    <span className="text-gray-500 block text-xs uppercase font-semibold mb-1">Workflow</span>
                    <span className="font-medium text-gray-900">{workflowConfig.name}</span>
                </div>
                <div className="text-sm">
                    <span className="text-gray-500 block text-xs uppercase font-semibold mb-1">Dettagli</span>
                    <ul className="space-y-1 text-gray-700">
                        <li className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
                            {workflowConfig.min_approvers} {workflowConfig.min_approvers === 1 ? 'approvazione richiesta' : 'approvazioni richieste'}
                        </li>
                        {workflowConfig.approval_mode !== 'ANY' && (
                            <li className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
                                Modalità: {
                                    workflowConfig.approval_mode === 'ALL' ? 'Tutti gli approvatori' :
                                        workflowConfig.approval_mode === 'SEQUENTIAL' ? 'Sequenziale' :
                                            workflowConfig.approval_mode === 'MAJORITY' ? 'Maggioranza' : 'Qualsiasi'
                                }
                            </li>
                        )}
                        {workflowConfig.target_role_ids && workflowConfig.target_role_ids.length > 0 && (
                            <li className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
                                Specifico per {workflowConfig.target_role_ids.length} {workflowConfig.target_role_ids.length === 1 ? 'ruolo' : 'ruoli'}
                            </li>
                        )}
                        {workflowConfig.expiration_hours && (
                            <li className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
                                Scade dopo {workflowConfig.expiration_hours} ore
                            </li>
                        )}
                    </ul>
                </div>
            </div>
        </div>
    );
}

interface ActionsCardProps {
    isOwner: boolean;
    isApprover: boolean;
    isAdmin: boolean;
    isHR: boolean;
    status: string;
    leaveId: string;
    actionLoading: string | null;
    onSubmit: () => void;
    onDelete: () => void;
    onShowCancelModal: () => void;
    onShowApproveModal: () => void;
    onShowRejectModal: () => void;
    onShowConditionalModal: () => void;
    onShowRevokeModal: () => void;
    onShowRecallModal: () => void;
    onShowReopenModal: () => void;
    onConditionResponse: (accept: boolean) => void;
}

function ActionsCard({
    isOwner,
    isApprover,
    isAdmin,
    isHR,
    status,
    leaveId,
    actionLoading,
    onSubmit,
    onDelete,
    onShowCancelModal,
    onShowApproveModal,
    onShowRejectModal,
    onShowConditionalModal,
    onShowRevokeModal,
    onShowRecallModal,
    onShowReopenModal,
    onConditionResponse,
}: ActionsCardProps) {
    return (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 bg-gray-50 border-b border-gray-200">
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide">Azioni</h3>
            </div>

            {/* Employee Actions Section */}
            {isOwner && (
                <div className="p-4 border-b border-gray-100">
                    <div className="flex items-center gap-2 mb-3">
                        <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Dipendente</h4>
                    </div>
                    <div className="space-y-2">
                        {status === 'draft' && (
                            <>
                                <button
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                    onClick={onSubmit}
                                    disabled={actionLoading !== null}
                                >
                                    {actionLoading === 'submit' ? <Loader size={18} className="animate-spin" /> : <Send size={18} />}
                                    Invia Richiesta
                                </button>
                                <Link
                                    to={`/leaves/${leaveId}/edit`}
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-medium transition-colors"
                                >
                                    <Edit size={18} />
                                    Modifica
                                </Link>
                                <button
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-red-600 hover:bg-red-50 border border-red-200 rounded-lg font-medium transition-colors disabled:opacity-50"
                                    onClick={onDelete}
                                    disabled={actionLoading !== null}
                                >
                                    {actionLoading === 'delete' ? <Loader size={18} className="animate-spin" /> : <Trash2 size={18} />}
                                    Elimina Bozza
                                </button>
                            </>
                        )}
                        {(status === 'pending' || status === 'submitted') && (
                            <button
                                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white border border-red-200 text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors disabled:opacity-50"
                                onClick={onShowCancelModal}
                                disabled={actionLoading !== null}
                            >
                                <XCircle size={18} />
                                Annulla Richiesta
                            </button>
                        )}
                        {status === 'approved_conditional' && (
                            <>
                                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 mb-2">
                                    <strong>Attenzione:</strong> Questa richiesta è stata approvata con condizioni.
                                </div>
                                <button
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                    onClick={() => onConditionResponse(true)}
                                    disabled={actionLoading !== null}
                                >
                                    {actionLoading === 'accept_condition' ? <Loader size={18} className="animate-spin" /> : <CheckCircle size={18} />}
                                    Accetta Condizioni
                                </button>
                                <button
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                    onClick={() => onConditionResponse(false)}
                                    disabled={actionLoading !== null}
                                >
                                    {actionLoading === 'reject_condition' ? <Loader size={18} className="animate-spin" /> : <XCircle size={18} />}
                                    Rifiuta Condizioni
                                </button>
                            </>
                        )}
                        {['approved', 'rejected', 'cancelled'].includes(status) && !['approved_conditional'].includes(status) && (
                            <p className="text-center text-sm text-gray-400 italic py-2">
                                Nessuna azione disponibile
                            </p>
                        )}
                    </div>
                </div>
            )}

            {/* Approver Actions Section */}
            {isApprover && (!isOwner || isAdmin || isHR) && status !== 'draft' && (
                <div className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Approvatore</h4>
                    </div>
                    <div className="space-y-2">
                        {(status === 'pending' || status === 'submitted') && (
                            <>
                                <button
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                    onClick={onShowApproveModal}
                                    disabled={actionLoading !== null}
                                >
                                    <CheckCircle size={18} />
                                    Approva
                                </button>
                                <button
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                    onClick={onShowConditionalModal}
                                    disabled={actionLoading !== null}
                                >
                                    <AlertCircle size={18} />
                                    Approva con Condizioni
                                </button>
                                <button
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                    onClick={onShowRejectModal}
                                    disabled={actionLoading !== null}
                                >
                                    <XCircle size={18} />
                                    Rifiuta
                                </button>
                            </>
                        )}
                        {(status === 'approved' || status === 'approved_conditional') && (
                            <>
                                <button
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                    onClick={onShowRevokeModal}
                                    disabled={actionLoading !== null}
                                >
                                    <Ban size={18} />
                                    Revoca Approvazione
                                </button>
                                <button
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                    onClick={onShowRecallModal}
                                    disabled={actionLoading !== null}
                                >
                                    <Phone size={18} />
                                    Richiama in Servizio
                                </button>
                            </>
                        )}
                        {(status === 'rejected' || status === 'cancelled') && (
                            <button
                                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                onClick={onShowReopenModal}
                                disabled={actionLoading !== null}
                            >
                                <History size={18} />
                                Riapri Richiesta
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* No Actions Available */}
            {!isOwner && !isApprover && (
                <div className="p-4">
                    <p className="text-center text-sm text-gray-400 italic">
                        Nessuna azione disponibile per questa richiesta.
                    </p>
                </div>
            )}
        </div>
    );
}

function SummaryCard({ leave }: { leave: LeaveData }) {
    return (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide mb-4">Riepilogo</h3>
            <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-500">Tipo</span>
                    <span className="text-sm font-medium text-gray-900">{LEAVE_TYPE_NAMES[leave.leave_type_code] || leave.leave_type_code}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-500">Giorni</span>
                    <span className="text-sm font-bold text-gray-900">{leave.days_requested}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-sm text-gray-500">Creata il</span>
                    <span className="text-sm font-medium text-gray-900">
                        {format(new Date(leave.created_at), 'd MMM yyyy', { locale: it })}
                    </span>
                </div>
                {leave.approved_at && (
                    <div className="flex justify-between items-center py-2 border-b border-gray-100">
                        <span className="text-sm text-gray-500">Approvata il</span>
                        <span className="text-sm font-medium text-gray-900">
                            {format(new Date(leave.approved_at), 'd MMM yyyy', { locale: it })}
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}

export default LeaveDetailPage;
