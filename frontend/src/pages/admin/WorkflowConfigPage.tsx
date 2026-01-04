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
    ArrowUpCircle,
    Layers,
    Shield,
    FileText,
    Bell,
    Calendar,
    Search,
    Loader2
} from 'lucide-react';

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

const ApprovalModeBadge: React.FC<{ mode: string, name?: string }> = ({ mode, name }) => {
    const styles = {
        ANY: { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: <CheckCircle className="w-3 h-3" /> },
        ALL: { bg: 'bg-blue-50 text-blue-700 border-blue-200', icon: <Users className="w-3 h-3" /> },
        SEQUENTIAL: { bg: 'bg-purple-50 text-purple-700 border-purple-200', icon: <Layers className="w-3 h-3" /> },
        MAJORITY: { bg: 'bg-orange-50 text-orange-700 border-orange-200', icon: <ArrowUpCircle className="w-3 h-3" /> },
    };
    const style = styles[mode as keyof typeof styles] || styles.ANY;

    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${style.bg}`}>
            {style.icon}
            {name || mode}
        </span>
    );
};

const EntityTypeBadge: React.FC<{ type: string }> = ({ type }) => {
    switch (type) {
        case 'leave': return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700"><Calendar className="w-3 h-3" /> Ferie/Permessi</span>;
        case 'trip': return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-pink-50 text-pink-700"><MapPin className="w-3 h-3" /> Trasferte</span>;
        case 'expense': return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-teal-50 text-teal-700"><DollarSign className="w-3 h-3" /> Spese</span>;
        default: return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700"><FileText className="w-3 h-3" /> {type}</span>;
    }
};

import { MapPin, DollarSign } from 'lucide-react';

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
    const toast = useToast();
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
        target_role_ids: [],
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
                target_role_ids: workflow.target_role_ids || [],
            });
        } else {
            setFormData({
                entity_type: entityTypes.length > 0 ? entityTypes[0].code : '',
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
                target_role_ids: [],
            });
        }
    }, [workflow, isOpen, entityTypes]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!formData.entity_type || !formData.name) {
            toast.error('Compila i campi obbligatori (Nome e Tipo Entità)');
            return;
        }

        try {
            setIsSaving(true);
            await onSave(formData);
            onClose();
        } catch (error) {
            console.error(error);
            toast.error('Errore durante il salvataggio');
        } finally {
            setIsSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={onClose}>
            <div
                className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col animate-scaleIn"
                onClick={e => e.stopPropagation()}
            >
                {/* Modal Header */}
                <div className="flex justify-between items-center px-6 py-4 border-b border-gray-100 bg-gray-50/50">
                    <div className="flex items-center gap-3">
                        <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-2 rounded-lg text-white shadow-sm">
                            <Settings size={20} />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-gray-900">{workflow ? 'Modifica Workflow' : 'Nuovo Workflow'}</h3>
                            <p className="text-xs text-gray-500">Configura le regole di approvazione</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 hover:bg-gray-100 p-2 rounded-full transition-colors">
                        <XCircle size={20} />
                    </button>
                </div>

                {/* Modal Body */}
                <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Section 1: General Info */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
                                <FileText className="text-indigo-500" size={18} />
                                <h4 className="font-semibold text-gray-900">Informazioni Generali</h4>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Nome Workflow *</label>
                                    <input
                                        type="text"
                                        required
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                                        value={formData.name}
                                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                                        placeholder="es. Approvazione Ferie Manager"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Entità *</label>
                                        <select
                                            className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                                            value={formData.entity_type}
                                            onChange={e => setFormData({ ...formData, entity_type: e.target.value })}
                                        >
                                            <option value="" disabled>Seleziona tipo...</option>
                                            {entityTypes.map(t => (
                                                <option key={t.code} value={t.code}>{t.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Priorità</label>
                                        <input
                                            type="number"
                                            className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                                            value={formData.priority}
                                            onChange={e => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                                    <textarea
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm resize-none h-20"
                                        value={formData.description}
                                        onChange={e => setFormData({ ...formData, description: e.target.value })}
                                        placeholder="Descrivi lo scopo di questo workflow..."
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Section 2: Approval Rules */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
                                <Shield className="text-purple-500" size={18} />
                                <h4 className="font-semibold text-gray-900">Regole Approvazione</h4>
                            </div>

                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Modalità</label>
                                        <select
                                            className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                                            value={formData.approval_mode}
                                            onChange={e => setFormData({ ...formData, approval_mode: e.target.value })}
                                        >
                                            {approvalModes.map(m => (
                                                <option key={m.code} value={m.code}>{m.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Min. Approvatori</label>
                                        <input
                                            type="number"
                                            min="1"
                                            className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                                            value={formData.min_approvers}
                                            onChange={e => setFormData({ ...formData, min_approvers: parseInt(e.target.value) || 1 })}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-3 pt-2">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                            checked={formData.auto_assign_approvers}
                                            onChange={e => setFormData({ ...formData, auto_assign_approvers: e.target.checked })}
                                        />
                                        <span className="text-sm text-gray-700">Assegnazione Automatica Approvatori</span>
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                            checked={formData.allow_self_approval}
                                            onChange={e => setFormData({ ...formData, allow_self_approval: e.target.checked })}
                                        />
                                        <span className="text-sm text-gray-700">Consenti Auto-approvazione</span>
                                    </label>
                                </div>
                            </div>
                        </div>

                        {/* Section 3: Timeouts */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
                                <Clock className="text-orange-500" size={18} />
                                <h4 className="font-semibold text-gray-900">Scadenze</h4>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Scadenza (ore)</label>
                                    <input
                                        type="number"
                                        placeholder="Opzionale"
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                                        value={formData.expiration_hours || ''}
                                        onChange={e => setFormData({ ...formData, expiration_hours: e.target.value ? parseInt(e.target.value) : undefined })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Azione Scadenza</label>
                                    <select
                                        className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                                        value={formData.expiration_action}
                                        onChange={e => setFormData({ ...formData, expiration_action: e.target.value })}
                                    >
                                        {expirationActions.map(a => (
                                            <option key={a.code} value={a.code}>{a.name}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Section 4: Notifications */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
                                <Bell className="text-teal-500" size={18} />
                                <h4 className="font-semibold text-gray-900">Notifiche</h4>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-3">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                            checked={formData.send_reminders}
                                            onChange={e => setFormData({ ...formData, send_reminders: e.target.checked })}
                                        />
                                        <span className="text-sm text-gray-700">Invia Promemoria</span>
                                    </label>
                                </div>
                                {formData.send_reminders && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Ore prima per promemoria</label>
                                        <input
                                            type="number"
                                            className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                                            value={formData.reminder_hours_before}
                                            onChange={e => setFormData({ ...formData, reminder_hours_before: parseInt(e.target.value) || 0 })}
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </form>

                {/* Modal Footer */}
                <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 font-medium uppercase tracking-wide">Stato Iniziale:</span>
                        <div className="flex items-center gap-2">
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="sr-only peer"
                                    checked={formData.is_active}
                                    onChange={e => setFormData({ ...formData, is_active: e.target.checked })}
                                />
                                <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                                <span className="ml-2 text-sm font-medium text-gray-700">{formData.is_active ? 'Attivo' : 'Inattivo'}</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer ml-4">
                                <input
                                    type="checkbox"
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                    checked={formData.is_default}
                                    onChange={e => setFormData({ ...formData, is_default: e.target.checked })}
                                />
                                <span className="text-sm text-gray-700">Default</span>
                            </label>
                        </div>
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                            Annulla
                        </button>
                        <button
                            onClick={handleSubmit}
                            disabled={isSaving}
                            className="flex items-center gap-2 px-6 py-2 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-all disabled:opacity-50"
                        >
                            {isSaving && <Loader2 size={16} className="animate-spin" />}
                            Salva Configurazione
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// ═══════════════════════════════════════════════════════════
// Main Page
// ═══════════════════════════════════════════════════════════

const WorkflowConfigPage: React.FC = () => {
    const toast = useToast();
    const [workflows, setWorkflows] = useState<WorkflowConfig[]>([]);
    const [entityTypes, setEntityTypes] = useState<EntityTypeInfo[]>([]);
    const [approvalModes, setApprovalModes] = useState<ApprovalModeInfo[]>([]);
    const [expirationActions, setExpirationActions] = useState<ExpirationActionInfo[]>([]);

    const [isLoading, setIsLoading] = useState(false);

    // Modal state
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowConfig | null>(null);

    // Filters
    const [searchTerm, setSearchTerm] = useState('');
    const [entityFilter, setEntityFilter] = useState<string>('all');

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const [wf, et, am, ea] = await Promise.all([
                approvalsService.getWorkflowConfigs(undefined, false), // Fetch all, including inactive
                approvalsService.getEntityTypes(),
                approvalsService.getApprovalModes(),
                approvalsService.getExpirationActions()
            ]);
            setWorkflows(wf);
            setEntityTypes(et);
            setApprovalModes(am);
            setExpirationActions(ea);
        } catch (error) {
            console.error(error);
            toast.error('Errore durante il caricamento dei dati');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreateWrapper = async (data: WorkflowConfigCreate) => {
        await approvalsService.createWorkflowConfig(data);
        toast.success('Workflow creato con successo');
        fetchData();
    };

    const handleUpdateWrapper = async (data: WorkflowConfigCreate) => {
        if (!currentWorkflow) return;
        await approvalsService.updateWorkflowConfig(currentWorkflow.id, data);
        toast.success('Workflow aggiornato con successo');
        fetchData();
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Sei sicuro di voler eliminare questo workflow? Questa azione è irreversibile.')) return;
        try {
            await approvalsService.deleteWorkflowConfig(id);
            toast.success('Workflow eliminato');
            fetchData();
        } catch (error) {
            console.error(error);
            toast.error('Errore durante l\'eliminazione');
        }
    };

    const openCreateModal = () => {
        setCurrentWorkflow(null);
        setIsModalOpen(true);
    };

    const openEditModal = (wf: WorkflowConfig) => {
        setCurrentWorkflow(wf);
        setIsModalOpen(true);
    };

    const filteredWorkflows = workflows.filter(wf => {
        const matchesSearch = wf.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesEntity = entityFilter === 'all' || wf.entity_type === entityFilter;
        return matchesSearch && matchesEntity;
    });

    return (
        <div className="p-6 max-w-[1600px] mx-auto space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Gestione Workflow</h1>
                    <p className="text-gray-500 text-sm mt-1">Configura le regole di approvazione per i diversi processi aziendali</p>
                </div>
                <div>
                    <button
                        onClick={openCreateModal}
                        className="btn btn-primary flex items-center gap-2 px-5 py-2.5 rounded-lg shadow-sm hover:shadow-md transition-all"
                    >
                        <Plus size={18} />
                        Nuovo Workflow
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
                    <button
                        onClick={() => setEntityFilter('all')}
                        className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${entityFilter === 'all' ? 'bg-gray-900 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
                    >
                        Tutti
                    </button>
                    {entityTypes.map(t => (
                        <button
                            key={t.code}
                            onClick={() => setEntityFilter(t.code)}
                            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${entityFilter === t.code ? 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200' : 'text-gray-600 hover:bg-gray-100'}`}
                        >
                            {t.name}
                        </button>
                    ))}
                </div>

                <div className="relative w-full md:w-72">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                    <input
                        type="text"
                        placeholder="Cerca workflow..."
                        className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            {/* Workflow List (Table) */}
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                {isLoading ? (
                    <div className="p-12 flex flex-col items-center justify-center text-gray-400">
                        <Loader2 size={32} className="animate-spin mb-3 text-indigo-500" />
                        <p className="text-sm font-medium">Caricamento configurazioni...</p>
                    </div>
                ) : filteredWorkflows.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-gray-50/50 border-b border-gray-200">
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Workflow / Entità</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Regole Approvazione</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Priorità & Stato</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider text-right">Azioni</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {filteredWorkflows.map(wf => (
                                    <tr key={wf.id} className="hover:bg-gray-50/50 transition-colors group">
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1.5">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-semibold text-gray-900">{wf.name}</span>
                                                    {wf.is_default && (
                                                        <span className="text-[10px] font-bold bg-gray-900 text-white px-1.5 py-0.5 rounded">DEFAULT</span>
                                                    )}
                                                </div>
                                                <div className="mb-1">
                                                    <EntityTypeBadge type={wf.entity_type} />
                                                </div>
                                                <p className="text-xs text-gray-500 max-w-sm truncate">{wf.description || 'Nessuna descrizione'}</p>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="space-y-2">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-gray-500 w-16">Modalità:</span>
                                                    <ApprovalModeBadge mode={wf.approval_mode} name={approvalModes.find(m => m.code === wf.approval_mode)?.name} />
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-gray-500 w-16">Approvatori:</span>
                                                    <span className="text-sm font-medium text-gray-900">{wf.min_approvers} {wf.max_approvers ? `- ${wf.max_approvers}` : ''}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="space-y-2">
                                                <div className="flex items-center gap-2">
                                                    <div className={`w-2 h-2 rounded-full ${wf.is_active ? 'bg-emerald-500' : 'bg-gray-300'}`}></div>
                                                    <span className={`text-sm font-medium ${wf.is_active ? 'text-gray-900' : 'text-gray-500'}`}>{wf.is_active ? 'Attivo' : 'Inattivo'}</span>
                                                </div>
                                                <div className="text-xs text-gray-500">
                                                    Priorità: <span className="font-mono text-gray-700">{wf.priority}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => openEditModal(wf)}
                                                    className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
                                                    title="Modifica"
                                                >
                                                    <Pencil size={18} />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(wf.id)}
                                                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                                                    title="Elimina"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="py-20 text-center">
                        <div className="bg-gray-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-300">
                            <Layers size={40} />
                        </div>
                        <h3 className="text-lg font-medium text-gray-900">Nessun Workflow Configurato</h3>
                        <p className="text-gray-500 mt-2 max-w-sm mx-auto">Non ci sono workflow che corrispondono ai criteri di ricerca. Crea un nuovo workflow per iniziare.</p>
                        <button
                            onClick={openCreateModal}
                            className="mt-6 btn btn-white border border-gray-300 text-indigo-600 hover:bg-indigo-50"
                        >
                            Crea Workflow
                        </button>
                    </div>
                )}
            </div>

            {/* Modal */}
            <WorkflowFormModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={currentWorkflow ? handleUpdateWrapper : handleCreateWrapper}
                workflow={currentWorkflow}
                entityTypes={entityTypes}
                approvalModes={approvalModes}
                expirationActions={expirationActions}
            />
        </div>
    );
};

export default WorkflowConfigPage;
