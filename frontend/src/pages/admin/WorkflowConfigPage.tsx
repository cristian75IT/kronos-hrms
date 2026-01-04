/**
 * KRONOS - Workflow Configuration Page
 * 
 * Admin page for configuring approval workflows.
 */
import React, { useState, useEffect } from 'react';
import { useToast } from '../../context/ToastContext';
import {
    Settings,
    Plus,
    Pencil,
    Trash2,
    Clock,
    Users,
    CheckCircle,
    XCircle,
    AlertTriangle,
    ArrowUpCircle,
    Layers,
    ChevronDown,
    ChevronRight,
} from 'lucide-react';

import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { Modal } from '../../components/common/Modal';
import approvalsService from '../../services/approvals.service';
import type {
    WorkflowConfig,
    WorkflowConfigCreate,
    EntityTypeInfo,
    ApprovalModeInfo,
    ExpirationActionInfo,
} from '../../services/approvals.service';

// ═══════════════════════════════════════════════════════════
// Helper Components
// ═══════════════════════════════════════════════════════════

const ApprovalModeIcon: React.FC<{ mode: string }> = ({ mode }) => {
    switch (mode) {
        case 'ANY':
            return <CheckCircle className="h-4 w-4 text-green-500" />;
        case 'ALL':
            return <Users className="h-4 w-4 text-blue-500" />;
        case 'SEQUENTIAL':
            return <Layers className="h-4 w-4 text-purple-500" />;
        case 'MAJORITY':
            return <ArrowUpCircle className="h-4 w-4 text-orange-500" />;
        default:
            return null;
    }
};

const ExpirationActionBadge: React.FC<{ action: string }> = ({ action }) => {
    const configs: Record<string, { color: string; icon: React.ReactNode }> = {
        REJECT: { color: 'bg-red-100 text-red-700', icon: <XCircle className="h-3 w-3" /> },
        ESCALATE: { color: 'bg-yellow-100 text-yellow-700', icon: <ArrowUpCircle className="h-3 w-3" /> },
        AUTO_APPROVE: { color: 'bg-green-100 text-green-700', icon: <CheckCircle className="h-3 w-3" /> },
        NOTIFY_ONLY: { color: 'bg-blue-100 text-blue-700', icon: <AlertTriangle className="h-3 w-3" /> },
    };
    const config = configs[action] || configs.REJECT;

    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
            {config.icon}
            {action}
        </span>
    );
};

// ═══════════════════════════════════════════════════════════
// Workflow Form Modal
// ═══════════════════════════════════════════════════════════

interface WorkflowFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (data: WorkflowConfigCreate) => Promise<void>;
    workflow?: WorkflowConfig | null;
    entityTypes: EntityTypeInfo[];
    approvalModes: ApprovalModeInfo[];
    expirationActions: ExpirationActionInfo[];
}

const WorkflowFormModal: React.FC<WorkflowFormModalProps> = ({
    isOpen,
    onClose,
    onSave,
    workflow,
    entityTypes,
    approvalModes,
    expirationActions,
}) => {
    const [formData, setFormData] = useState<WorkflowConfigCreate>({
        entity_type: '',
        name: '',
        description: '',
        min_approvers: 1,
        max_approvers: undefined,
        approval_mode: 'ANY',
        approver_role_ids: [],
        auto_assign_approvers: false,
        allow_self_approval: false,
        expiration_hours: undefined,
        expiration_action: 'REJECT',
        send_reminders: true,
        reminder_hours_before: 24,
        priority: 100,
        is_active: true,
        is_default: false,
    });
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (workflow) {
            setFormData({
                entity_type: workflow.entity_type,
                name: workflow.name,
                description: workflow.description || '',
                min_approvers: workflow.min_approvers,
                max_approvers: workflow.max_approvers,
                approval_mode: workflow.approval_mode,
                approver_role_ids: workflow.approver_role_ids,
                auto_assign_approvers: workflow.auto_assign_approvers,
                allow_self_approval: workflow.allow_self_approval,
                expiration_hours: workflow.expiration_hours,
                expiration_action: workflow.expiration_action,
                send_reminders: workflow.send_reminders,
                reminder_hours_before: workflow.reminder_hours_before,
                priority: workflow.priority,
                is_active: workflow.is_active,
                is_default: workflow.is_default,
            });
        } else {
            setFormData({
                entity_type: '',
                name: '',
                description: '',
                min_approvers: 1,
                approval_mode: 'ANY',
                approver_role_ids: [],
                auto_assign_approvers: false,
                allow_self_approval: false,
                expiration_action: 'REJECT',
                send_reminders: true,
                reminder_hours_before: 24,
                priority: 100,
                is_active: true,
                is_default: false,
            });
        }
    }, [workflow, isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!formData.entity_type || !formData.name) {
            toast.error('Compila i campi obbligatori');
            return;
        }

        setIsSaving(true);
        try {
            await onSave(formData);
            onClose();
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={workflow ? 'Modifica Workflow' : 'Nuovo Workflow'}
            size="lg"
        >
            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Basic Info */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Tipo Entità *
                        </label>
                        <select
                            value={formData.entity_type}
                            onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
                            className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            disabled={!!workflow}
                        >
                            <option value="">Seleziona...</option>
                            {entityTypes.map((t) => (
                                <option key={t.code} value={t.code}>
                                    {t.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Nome Workflow *
                        </label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            placeholder="es. Approvazione Ferie Standard"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Descrizione
                    </label>
                    <textarea
                        value={formData.description || ''}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        rows={2}
                    />
                </div>

                {/* Approval Settings */}
                <div className="border-t pt-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-3">Impostazioni Approvazione</h4>

                    <div className="grid grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Modalità
                            </label>
                            <select
                                value={formData.approval_mode}
                                onChange={(e) => setFormData({ ...formData, approval_mode: e.target.value })}
                                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            >
                                {approvalModes.map((m) => (
                                    <option key={m.code} value={m.code}>
                                        {m.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Min. Approvatori
                            </label>
                            <input
                                type="number"
                                min={1}
                                max={10}
                                value={formData.min_approvers}
                                onChange={(e) => setFormData({ ...formData, min_approvers: parseInt(e.target.value) })}
                                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Max. Approvatori
                            </label>
                            <input
                                type="number"
                                min={1}
                                max={20}
                                value={formData.max_approvers || ''}
                                onChange={(e) => setFormData({ ...formData, max_approvers: e.target.value ? parseInt(e.target.value) : undefined })}
                                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                placeholder="Nessun limite"
                            />
                        </div>
                    </div>

                    <div className="mt-4 flex gap-6">
                        <label className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                checked={formData.auto_assign_approvers}
                                onChange={(e) => setFormData({ ...formData, auto_assign_approvers: e.target.checked })}
                                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                            />
                            <span className="text-sm text-gray-700">Assegna automaticamente</span>
                        </label>

                        <label className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                checked={formData.allow_self_approval}
                                onChange={(e) => setFormData({ ...formData, allow_self_approval: e.target.checked })}
                                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                            />
                            <span className="text-sm text-gray-700">Permetti auto-approvazione</span>
                        </label>
                    </div>
                </div>

                {/* Expiration Settings */}
                <div className="border-t pt-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-3">Scadenza</h4>

                    <div className="grid grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Ore alla Scadenza
                            </label>
                            <input
                                type="number"
                                min={1}
                                value={formData.expiration_hours || ''}
                                onChange={(e) => setFormData({ ...formData, expiration_hours: e.target.value ? parseInt(e.target.value) : undefined })}
                                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                placeholder="Nessuna scadenza"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Azione alla Scadenza
                            </label>
                            <select
                                value={formData.expiration_action}
                                onChange={(e) => setFormData({ ...formData, expiration_action: e.target.value })}
                                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            >
                                {expirationActions.map((a) => (
                                    <option key={a.code} value={a.code}>
                                        {a.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Promemoria (ore prima)
                            </label>
                            <input
                                type="number"
                                min={1}
                                value={formData.reminder_hours_before || ''}
                                onChange={(e) => setFormData({ ...formData, reminder_hours_before: e.target.value ? parseInt(e.target.value) : undefined })}
                                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                disabled={!formData.send_reminders}
                            />
                        </div>
                    </div>

                    <div className="mt-4">
                        <label className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                checked={formData.send_reminders}
                                onChange={(e) => setFormData({ ...formData, send_reminders: e.target.checked })}
                                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                            />
                            <span className="text-sm text-gray-700">Invia promemoria</span>
                        </label>
                    </div>
                </div>

                {/* Priority & Status */}
                <div className="border-t pt-4">
                    <div className="grid grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Priorità (1-1000)
                            </label>
                            <input
                                type="number"
                                min={1}
                                max={1000}
                                value={formData.priority}
                                onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                            <p className="text-xs text-gray-500 mt-1">Valori più bassi = priorità maggiore</p>
                        </div>

                        <div className="flex items-end gap-6">
                            <label className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={formData.is_active}
                                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                <span className="text-sm text-gray-700">Attivo</span>
                            </label>

                            <label className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={formData.is_default}
                                    onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                <span className="text-sm text-gray-700">Default</span>
                            </label>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-4 border-t">
                    <Button variant="secondary" onClick={onClose} disabled={isSaving}>
                        Annulla
                    </Button>
                    <Button type="submit" isLoading={isSaving}>
                        {workflow ? 'Salva Modifiche' : 'Crea Workflow'}
                    </Button>
                </div>
            </form>
        </Modal>
    );
};

// ═══════════════════════════════════════════════════════════
// Main Page Component
// ═══════════════════════════════════════════════════════════

const WorkflowConfigPage: React.FC = () => {
    const toast = useToast();

    const [workflows, setWorkflows] = useState<WorkflowConfig[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [entityTypes, setEntityTypes] = useState<EntityTypeInfo[]>([]);
    const [approvalModes, setApprovalModes] = useState<ApprovalModeInfo[]>([]);
    const [expirationActions, setExpirationActions] = useState<ExpirationActionInfo[]>([]);

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingWorkflow, setEditingWorkflow] = useState<WorkflowConfig | null>(null);
    const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set());

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setIsLoading(true);
        try {
            const [wfs, types, modes, actions] = await Promise.all([
                approvalsService.getWorkflowConfigs(undefined, false),
                approvalsService.getEntityTypes(),
                approvalsService.getApprovalModes(),
                approvalsService.getExpirationActions(),
            ]);
            setWorkflows(wfs);
            setEntityTypes(types);
            setApprovalModes(modes);
            setExpirationActions(actions);

            // Expand all types by default
            setExpandedTypes(new Set(types.map(t => t.code)));
        } catch (error) {
            console.error(error);
            toast.error('Errore nel caricamento dei workflow');
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreate = () => {
        setEditingWorkflow(null);
        setIsModalOpen(true);
    };

    const handleEdit = (workflow: WorkflowConfig) => {
        setEditingWorkflow(workflow);
        setIsModalOpen(true);
    };

    const handleSave = async (data: WorkflowConfigCreate) => {
        try {
            if (editingWorkflow) {
                await approvalsService.updateWorkflowConfig(editingWorkflow.id, data);
                toast.success('Workflow aggiornato');
            } else {
                await approvalsService.createWorkflowConfig(data);
                toast.success('Workflow creato');
            }
            loadData();
        } catch (error) {
            console.error(error);
            toast.error('Errore nel salvataggio');
            throw error;
        }
    };

    const handleDelete = async (workflow: WorkflowConfig) => {
        if (!confirm(`Sei sicuro di voler disattivare "${workflow.name}"?`)) return;

        try {
            await approvalsService.deleteWorkflowConfig(workflow.id);
            toast.success('Workflow disattivato');
            loadData();
        } catch (error) {
            console.error(error);
            toast.error('Errore nella disattivazione');
        }
    };

    const toggleType = (type: string) => {
        setExpandedTypes(prev => {
            const next = new Set(prev);
            if (next.has(type)) {
                next.delete(type);
            } else {
                next.add(type);
            }
            return next;
        });
    };

    // Group workflows by entity type
    const workflowsByType = workflows.reduce((acc, wf) => {
        if (!acc[wf.entity_type]) acc[wf.entity_type] = [];
        acc[wf.entity_type].push(wf);
        return acc;
    }, {} as Record<string, WorkflowConfig[]>);

    const getModeName = (code: string) => {
        return approvalModes.find(m => m.code === code)?.name || code;
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                        <Settings className="h-7 w-7 text-indigo-600" />
                        Configurazione Workflow Approvazioni
                    </h1>
                    <p className="text-gray-600 mt-1">
                        Gestisci i flussi autorizzativi per ferie, trasferte, note spese e altro
                    </p>
                </div>

                <Button onClick={handleCreate} className="flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    Nuovo Workflow
                </Button>
            </div>

            {/* Content */}
            {isLoading ? (
                <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
                </div>
            ) : (
                <div className="space-y-4">
                    {entityTypes.map((type) => (
                        <Card key={type.code} className="overflow-hidden">
                            {/* Type Header */}
                            <button
                                onClick={() => toggleType(type.code)}
                                className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    {expandedTypes.has(type.code) ? (
                                        <ChevronDown className="h-5 w-5 text-gray-400" />
                                    ) : (
                                        <ChevronRight className="h-5 w-5 text-gray-400" />
                                    )}
                                    <span className="font-semibold text-gray-900">{type.name}</span>
                                    <span className="text-sm text-gray-500">
                                        ({workflowsByType[type.code]?.length || 0} workflow)
                                    </span>
                                </div>
                            </button>

                            {/* Workflows List */}
                            {expandedTypes.has(type.code) && (
                                <div className="border-t">
                                    {workflowsByType[type.code]?.length ? (
                                        <table className="w-full">
                                            <thead className="bg-gray-50">
                                                <tr>
                                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Nome</th>
                                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Modalità</th>
                                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Approvatori</th>
                                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Scadenza</th>
                                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Azione Scadenza</th>
                                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Stato</th>
                                                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Azioni</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-200">
                                                {workflowsByType[type.code]
                                                    .sort((a, b) => a.priority - b.priority)
                                                    .map((wf) => (
                                                        <tr key={wf.id} className={!wf.is_active ? 'bg-gray-50 opacity-60' : ''}>
                                                            <td className="px-4 py-3">
                                                                <div className="flex items-center gap-2">
                                                                    <span className="font-medium text-gray-900">{wf.name}</span>
                                                                    {wf.is_default && (
                                                                        <span className="px-1.5 py-0.5 rounded text-xs bg-indigo-100 text-indigo-700">
                                                                            Default
                                                                        </span>
                                                                    )}
                                                                </div>
                                                                {wf.description && (
                                                                    <p className="text-xs text-gray-500 mt-0.5">{wf.description}</p>
                                                                )}
                                                            </td>
                                                            <td className="px-4 py-3">
                                                                <div className="flex items-center gap-1.5">
                                                                    <ApprovalModeIcon mode={wf.approval_mode} />
                                                                    <span className="text-sm">{getModeName(wf.approval_mode)}</span>
                                                                </div>
                                                            </td>
                                                            <td className="px-4 py-3">
                                                                <span className="text-sm">
                                                                    {wf.min_approvers}
                                                                    {wf.max_approvers && wf.max_approvers !== wf.min_approvers
                                                                        ? `-${wf.max_approvers}`
                                                                        : ''}
                                                                </span>
                                                            </td>
                                                            <td className="px-4 py-3">
                                                                {wf.expiration_hours ? (
                                                                    <div className="flex items-center gap-1 text-sm">
                                                                        <Clock className="h-3.5 w-3.5 text-gray-400" />
                                                                        {wf.expiration_hours}h
                                                                    </div>
                                                                ) : (
                                                                    <span className="text-sm text-gray-400">-</span>
                                                                )}
                                                            </td>
                                                            <td className="px-4 py-3">
                                                                <ExpirationActionBadge action={wf.expiration_action} />
                                                            </td>
                                                            <td className="px-4 py-3">
                                                                {wf.is_active ? (
                                                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                                                        <CheckCircle className="h-3 w-3" />
                                                                        Attivo
                                                                    </span>
                                                                ) : (
                                                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                                                                        Inattivo
                                                                    </span>
                                                                )}
                                                            </td>
                                                            <td className="px-4 py-3 text-right">
                                                                <div className="flex items-center justify-end gap-1">
                                                                    <button
                                                                        onClick={() => handleEdit(wf)}
                                                                        className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded"
                                                                        title="Modifica"
                                                                    >
                                                                        <Pencil className="h-4 w-4" />
                                                                    </button>
                                                                    <button
                                                                        onClick={() => handleDelete(wf)}
                                                                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                                                                        title="Disattiva"
                                                                    >
                                                                        <Trash2 className="h-4 w-4" />
                                                                    </button>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    ))}
                                            </tbody>
                                        </table>
                                    ) : (
                                        <div className="px-4 py-8 text-center text-gray-500">
                                            <p>Nessun workflow configurato per questo tipo</p>
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                className="mt-2"
                                                onClick={() => {
                                                    setEditingWorkflow(null);
                                                    setIsModalOpen(true);
                                                }}
                                            >
                                                <Plus className="h-4 w-4 mr-1" />
                                                Aggiungi
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </Card>
                    ))}
                </div>
            )}

            {/* Form Modal */}
            <WorkflowFormModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSave}
                workflow={editingWorkflow}
                entityTypes={entityTypes}
                approvalModes={approvalModes}
                expirationActions={expirationActions}
            />
        </div>
    );
};

export default WorkflowConfigPage;
