/**
 * KRONOS - Pending Approvals Page
 * 
 * Page for approvers to view and act on pending approval requests.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../../context/ToastContext';
import {
    CheckCircle,
    XCircle,
    Clock,
    AlertTriangle,
    User,
    Briefcase,
    Receipt,
    FileText,
    ChevronRight,
    ExternalLink,
    Calendar,
    FileSearch,
    ShieldCheck,
    AlertCircle,
    Check,
    Info,
    MessageSquare,
    Search,
    LayoutGrid,
    Ban,
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { it } from 'date-fns/locale';

import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { Modal } from '../../components/common/Modal';
import approvalsService from '../../services/approvals.service';
import type {
    PendingApprovalItem,
    PendingApprovalsResponse,
    ArchivedApprovalItem,
    ArchivedApprovalsResponse,
} from '../../services/approvals.service';

// ═══════════════════════════════════════════════════════════
// Helper Components
// ═══════════════════════════════════════════════════════════

const EntityIcon: React.FC<{ type: string; className?: string }> = ({ type, className = "h-5 w-5" }) => {
    switch (type) {
        case 'LEAVE':
            return <Calendar className={`${className} text-blue-500`} />;
        case 'TRIP':
            return <Briefcase className={`${className} text-purple-500`} />;
        case 'EXPENSE':
            return <Receipt className={`${className} text-green-500`} />;
        default:
            return <FileText className={`${className} text-gray-500`} />;
    }
};

const EntityTypeBadge: React.FC<{ type: string }> = ({ type }) => {
    const configs: Record<string, { color: string; label: string }> = {
        LEAVE: { color: 'bg-blue-100 text-blue-700', label: 'Ferie' },
        TRIP: { color: 'bg-purple-100 text-purple-700', label: 'Trasferta' },
        EXPENSE: { color: 'bg-green-100 text-green-700', label: 'Nota Spese' },
        DOCUMENT: { color: 'bg-gray-100 text-gray-700', label: 'Documento' },
        CONTRACT: { color: 'bg-orange-100 text-orange-700', label: 'Contratto' },
        OVERTIME: { color: 'bg-red-100 text-red-700', label: 'Straordinario' },
    };
    const config = configs[type] || { color: 'bg-gray-100 text-gray-700', label: type };

    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
            {config.label}
        </span>
    );
};

const UrgencyIndicator: React.FC<{ item: PendingApprovalItem }> = ({ item }) => {
    if (item.is_urgent) {
        return (
            <div className="flex items-center gap-1 text-red-600 animate-pulse">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-xs font-medium">Urgente</span>
            </div>
        );
    }

    if (item.expires_at) {
        const expiresDate = new Date(item.expires_at);
        const hoursRemaining = (expiresDate.getTime() - Date.now()) / (1000 * 60 * 60);

        if (hoursRemaining < 48) {
            return (
                <div className="flex items-center gap-1 text-orange-500">
                    <Clock className="h-4 w-4" />
                    <span className="text-xs">
                        Scade {formatDistanceToNow(expiresDate, { addSuffix: true, locale: it })}
                    </span>
                </div>
            );
        }
    }

    return null;
};

// ═══════════════════════════════════════════════════════════
// Decision Modal
// ═══════════════════════════════════════════════════════════

interface DecisionModalProps {
    isOpen: boolean;
    onClose: () => void;
    item: PendingApprovalItem | null;
    onApprove: (notes?: string) => Promise<void>;
    onReject: (notes: string) => Promise<void>;
    onApproveConditional?: (type: string, details: string, notes?: string) => Promise<void>;
    onCancel?: (reason?: string) => Promise<void>;
    showCancelOption?: boolean;
}

const DecisionModal: React.FC<DecisionModalProps> = ({
    isOpen,
    onClose,
    item,
    onApprove,
    onReject,
    onApproveConditional,
    onCancel,
    showCancelOption = false,
}) => {
    const toast = useToast();
    const navigate = useNavigate();
    const [notes, setNotes] = useState('');
    const [conditionType, setConditionType] = useState('LOGISTIC');
    const [conditionDetails, setConditionDetails] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [action, setAction] = useState<'approve' | 'reject' | 'cancel' | 'approve_conditional' | null>(null);

    const getEntityUrl = (item: any) => {
        switch (item.entity_type) {
            case 'LEAVE': return `/leaves/${item.entity_id}`;
            case 'TRIP': return `/trips/${item.entity_id}`;
            case 'EXPENSE': return `/expenses/${item.entity_id}`;
            default: return null;
        }
    };

    const handleSubmit = async () => {
        if (action === 'reject' && !notes.trim()) {
            toast.error('Inserisci una motivazione per il rifiuto');
            return;
        }

        if (action === 'approve_conditional' && (!conditionType || !conditionDetails.trim())) {
            toast.error('Inserisci i dettagli della condizione');
            return;
        }

        setIsSubmitting(true);
        try {
            if (action === 'approve') {
                await onApprove(notes.trim() || undefined);
            } else if (action === 'reject') {
                await onReject(notes.trim());
            } else if (action === 'approve_conditional' && onApproveConditional) {
                await onApproveConditional(conditionType, conditionDetails.trim(), notes.trim() || undefined);
            } else if (action === 'cancel' && onCancel) {
                await onCancel(notes.trim() || undefined);
            }
            onClose();
            setNotes('');
            setConditionDetails('');
            setAction(null);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!item) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Gestione Approvazione"
            size="2xl"
            hideFooter
        >
            <div className="space-y-6 pb-2">
                {/* Enterprise Header - Glassmorphism Style */}
                <div className="relative overflow-hidden rounded-2xl border border-white/40 bg-white/40 p-5 shadow-sm backdrop-blur-md">
                    <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-indigo-500/10 blur-3xl"></div>
                    <div className="absolute -left-12 -bottom-12 h-40 w-40 rounded-full bg-blue-500/5 blur-3xl"></div>

                    <div className="relative flex items-center gap-5">
                        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-gray-100">
                            <EntityIcon type={item.entity_type} className="h-10 w-10" />
                        </div>

                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-50 text-indigo-700 ring-1 ring-inset ring-indigo-700/10">
                                    {item.entity_type === 'LEAVE' ? 'Richiesta Ferie' :
                                        item.entity_type === 'TRIP' ? 'Trasferta' :
                                            item.entity_type === 'EXPENSE' ? 'Nota Spese' : item.entity_type}
                                </span>
                                {item.entity_ref && (
                                    <span className="text-xs font-mono text-gray-500">#{item.entity_ref}</span>
                                )}
                            </div>
                            <h3 className="text-lg font-bold text-gray-900 truncate">
                                {item.title}
                            </h3>
                            <div className="flex items-center gap-4 mt-2">
                                <div className="flex items-center gap-1.5 text-sm text-gray-600">
                                    <div className="h-6 w-6 rounded-full bg-indigo-100 flex items-center justify-center">
                                        <User className="h-3.5 w-3.5 text-indigo-600" />
                                    </div>
                                    <span className="font-medium underline decoration-indigo-200 underline-offset-4 decoration-2">
                                        {item.requester_name || 'Utente'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-1.5 text-sm text-gray-500">
                                    <Calendar className="h-4 w-4 text-gray-400" />
                                    {format(new Date(item.created_at), 'dd MMMM yyyy', { locale: it })}
                                </div>
                            </div>
                        </div>

                        {getEntityUrl(item) && (
                            <Button
                                variant="secondary"
                                size="md"
                                onClick={() => navigate(getEntityUrl(item)!)}
                                className="bg-white/80 hover:bg-white shadow-sm ring-1 ring-gray-200 border-none group"
                            >
                                <FileSearch className="h-4 w-4 mr-2 text-indigo-600 transition-transform group-hover:scale-110" />
                                <span className="text-gray-700 font-semibold">Vedi Dettaglio Completo</span>
                            </Button>
                        )}
                    </div>
                </div>

                {/* Decision Cards Section */}
                <div>
                    <h4 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4 ml-1">
                        Scegli una decisione
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Approve Card */}
                        <button
                            type="button"
                            onClick={() => setAction('approve')}
                            className={`group relative flex flex-col items-center p-6 rounded-2xl border-2 transition-all duration-300 ${action === 'approve'
                                ? 'border-emerald-500 bg-emerald-50/50 shadow-lg shadow-emerald-500/10'
                                : 'border-white bg-white hover:border-emerald-300 hover:shadow-md'
                                } ring-1 ring-gray-100`}
                        >
                            <div className={`h-14 w-14 rounded-full flex items-center justify-center mb-4 transition-transform duration-500 ${action === 'approve' ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/40 scale-110' : 'bg-emerald-50 text-emerald-500 group-hover:scale-110'
                                }`}>
                                <CheckCircle className="h-8 w-8" />
                            </div>
                            <h5 className={`text-base font-bold mb-1 ${action === 'approve' ? 'text-emerald-900' : 'text-gray-900'}`}>
                                Approva
                            </h5>
                            <p className="text-xs text-center text-gray-500 leading-relaxed max-w-[140px]">
                                Conferma la validità e autorizza la richiesta.
                            </p>
                            {action === 'approve' && (
                                <div className="absolute -top-1.5 -right-1.5 h-6 w-6 bg-emerald-500 rounded-full flex items-center justify-center text-white shadow-sm animate-in zoom-in duration-300">
                                    <Check className="h-4 w-4 stroke-[3]" />
                                </div>
                            )}
                        </button>

                        {/* Conditional Card (LEAVE Only) */}
                        {item.entity_type === 'LEAVE' && (
                            <button
                                type="button"
                                onClick={() => setAction('approve_conditional')}
                                className={`group relative flex flex-col items-center p-4 py-6 rounded-2xl border-2 transition-all duration-300 ${action === 'approve_conditional'
                                    ? 'border-blue-500 bg-blue-50/50 shadow-lg shadow-blue-500/10'
                                    : 'border-white bg-white hover:border-blue-300 hover:shadow-md'
                                    } ring-1 ring-gray-100`}
                            >
                                <div className={`h-14 w-14 rounded-full flex items-center justify-center mb-4 transition-transform duration-500 ${action === 'approve_conditional' ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/40 scale-110' : 'bg-blue-50 text-blue-500 group-hover:scale-110'
                                    }`}>
                                    <ShieldCheck className="h-8 w-8" />
                                </div>
                                <h5 className={`text-base font-bold mb-1 ${action === 'approve_conditional' ? 'text-blue-900' : 'text-gray-900'}`}>
                                    Condizionato
                                </h5>
                                <p className="text-xs text-center text-gray-500 leading-relaxed max-w-[140px]">
                                    Approva con vincoli o periodi alternativi.
                                </p>
                                {action === 'approve_conditional' && (
                                    <div className="absolute -top-1.5 -right-1.5 h-6 w-6 bg-blue-500 rounded-full flex items-center justify-center text-white shadow-sm animate-in zoom-in duration-300">
                                        <Check className="h-4 w-4 stroke-[3]" />
                                    </div>
                                )}
                            </button>
                        )}

                        {/* Reject Card */}
                        <button
                            type="button"
                            onClick={() => setAction('reject')}
                            className={`group relative flex flex-col items-center p-6 rounded-2xl border-2 transition-all duration-300 ${action === 'reject'
                                ? 'border-rose-500 bg-rose-50/50 shadow-lg shadow-rose-500/10'
                                : 'border-white bg-white hover:border-rose-300 hover:shadow-md'
                                } ring-1 ring-gray-100`}
                        >
                            <div className={`h-14 w-14 rounded-full flex items-center justify-center mb-4 transition-transform duration-500 ${action === 'reject' ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/40 scale-110' : 'bg-rose-50 text-rose-500 group-hover:scale-110'
                                }`}>
                                <XCircle className="h-8 w-8" />
                            </div>
                            <h5 className={`text-base font-bold mb-1 ${action === 'reject' ? 'text-rose-900' : 'text-gray-900'}`}>
                                Rifiuta
                            </h5>
                            <p className="text-xs text-center text-gray-500 leading-relaxed max-w-[140px]">
                                Respingi la richiesta indicando la motivazione.
                            </p>
                            {action === 'reject' && (
                                <div className="absolute -top-1.5 -right-1.5 h-6 w-6 bg-rose-500 rounded-full flex items-center justify-center text-white shadow-sm animate-in zoom-in duration-300">
                                    <Check className="h-4 w-4 stroke-[3]" />
                                </div>
                            )}
                        </button>
                    </div>
                </div>

                {/* Integrated Action Form */}
                <div className={`overflow-hidden transition-all duration-500 ease-in-out ${action ? 'max-h-[600px] opacity-100 mt-2' : 'max-h-0 opacity-0'}`}>
                    <div className="rounded-2xl bg-gray-50/80 p-6 border border-gray-100 ring-1 ring-white/50">
                        {action === 'approve_conditional' && (
                            <div className="space-y-5 animate-in slide-in-from-top-4 duration-500">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-1.5">
                                        <label className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                                            <Info className="h-3.5 w-3.5 text-blue-500" />
                                            Tipo di Condizione
                                        </label>
                                        <select
                                            value={conditionType}
                                            onChange={(e) => setConditionType(e.target.value)}
                                            className="w-full text-sm rounded-xl border-gray-200 bg-white px-4 py-2.5 shadow-sm focus:border-blue-500 focus:ring-blue-500 transition-colors"
                                        >
                                            <option value="LOGISTIC">Logistica / Operativa</option>
                                            <option value="TEMPORAL">Temporale (date sugerite)</option>
                                            <option value="PARTIAL">Approvazione Parziale</option>
                                            <option value="OTHER">Altro</option>
                                        </select>
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                                            Dettagli della Condizione *
                                        </label>
                                        <input
                                            type="text"
                                            value={conditionDetails}
                                            onChange={(e) => setConditionDetails(e.target.value)}
                                            className="w-full text-sm rounded-xl border-gray-200 bg-white px-4 py-2.5 shadow-sm focus:border-blue-500 focus:ring-blue-500 transition-colors"
                                            placeholder="Specifica le condizioni richieste..."
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className={`space-y-1.5 ${action === 'approve_conditional' ? 'mt-5' : ''}`}>
                            <label className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                                <MessageSquare className={`h-3.5 w-3.5 ${action === 'reject' ? 'text-rose-500' : action === 'approve' ? 'text-emerald-500' : 'text-blue-500'}`} />
                                {action === 'reject' ? 'Motivazione del Rifiuto *' : 'Note Aggiuntive'}
                            </label>
                            <textarea
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                className={`w-full text-sm rounded-xl border-gray-200 bg-white p-4 shadow-sm transition-all focus:ring-4 ${action === 'reject' ? 'focus:border-rose-400 focus:ring-rose-500/5' :
                                    action === 'approve' ? 'focus:border-emerald-400 focus:ring-emerald-500/5' :
                                        'focus:border-blue-400 focus:ring-blue-500/5'
                                    }`}
                                rows={3}
                                placeholder={
                                    action === 'reject' ? 'Spiega il motivo per cui la richiesta è stata declinata...' :
                                        'Aggiungi commenti per il collaboratore (opzionale)...'
                                }
                            />
                        </div>

                        {/* Submit Action Block */}
                        <div className="flex items-center justify-between mt-8">
                            <button
                                onClick={() => setAction(null)}
                                className="text-sm font-semibold text-gray-500 hover:text-gray-700 transition-colors"
                            >
                                Annulla Selezione
                            </button>
                            <div className="flex gap-3">
                                <Button
                                    variant="secondary"
                                    onClick={onClose}
                                    disabled={isSubmitting}
                                    className="rounded-xl px-5 hover:bg-gray-100"
                                >
                                    Esci
                                </Button>
                                <Button
                                    onClick={handleSubmit}
                                    disabled={!action || isSubmitting}
                                    isLoading={isSubmitting}
                                    className={`rounded-xl px-8 font-bold shadow-lg transition-all active:scale-95 ${action === 'approve' ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/20' :
                                        action === 'reject' ? 'bg-rose-600 hover:bg-rose-700 shadow-rose-600/20' :
                                            'bg-blue-600 hover:bg-blue-700 shadow-blue-600/20'
                                        }`}
                                >
                                    {action === 'approve' ? 'Conferma Approvazione' :
                                        action === 'reject' ? 'Invia Rifiuto' :
                                            'Conferma con Condizioni'}
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Default Close Action if no action selected */}
                {!action && (
                    <div className="flex justify-end pt-4 border-t border-gray-100">
                        <Button
                            variant="secondary"
                            onClick={onClose}
                            className="rounded-xl px-6"
                        >
                            Annulla
                        </Button>
                    </div>
                )}
            </div>
        </Modal>
    );
};

// ═══════════════════════════════════════════════════════════
// Main Page Component
// ═══════════════════════════════════════════════════════════

const PendingApprovalsPage: React.FC = () => {
    const navigate = useNavigate();
    const toast = useToast();

    // View mode: 'pending' or 'archived'
    const [viewMode, setViewMode] = useState<'pending' | 'archived'>('pending');

    const [data, setData] = useState<PendingApprovalsResponse | null>(null);
    const [archivedData, setArchivedData] = useState<ArchivedApprovalsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedItem, setSelectedItem] = useState<PendingApprovalItem | null>(null);
    const [isDecisionModalOpen, setIsDecisionModalOpen] = useState(false);
    const [filterType, setFilterType] = useState<string>('');
    const [archiveStatusFilter, setArchiveStatusFilter] = useState<string>('all');

    useEffect(() => {
        if (viewMode === 'pending') {
            loadData();
        } else {
            loadArchivedData();
        }
    }, [filterType, viewMode, archiveStatusFilter]);

    const loadData = async () => {
        setIsLoading(true);
        try {
            const response = await approvalsService.getPendingApprovals(filterType || undefined);
            setData(response);
        } catch (error) {
            console.error(error);
            toast.error('Errore nel caricamento delle approvazioni');
        } finally {
            setIsLoading(false);
        }
    };

    const loadArchivedData = async () => {
        setIsLoading(true);
        try {
            const response = await approvalsService.getArchivedApprovals(
                archiveStatusFilter === 'all' ? undefined : archiveStatusFilter,
                filterType || undefined
            );
            setArchivedData(response);
        } catch (error) {
            console.error(error);
            toast.error('Errore nel caricamento dell\'archivio');
        } finally {
            setIsLoading(false);
        }
    };

    const handleApprove = async (notes?: string) => {
        if (!selectedItem) return;

        try {
            await approvalsService.approveRequest(selectedItem.request_id, notes);
            toast.success('Richiesta approvata');
            loadData();
        } catch (error) {
            console.error(error);
            toast.error('Errore nell\'approvazione');
            throw error;
        }
    };

    const handleReject = async (notes: string) => {
        if (!selectedItem) return;

        try {
            await approvalsService.rejectRequest(selectedItem.request_id, notes);
            toast.success('Richiesta rifiutata');
            loadData();
        } catch (error) {
            console.error(error);
            toast.error('Errore nel rifiuto');
            throw error;
        }
    };

    const handleApproveConditional = async (type: string, details: string, notes?: string) => {
        if (!selectedItem) return;

        try {
            await approvalsService.approveRequestConditional(selectedItem.request_id, type, details, notes);
            toast.success('Richiesta approvata con condizioni');
            loadData();
        } catch (error) {
            console.error(error);
            toast.error('Errore nell\'approvazione condizionata');
            throw error;
        }
    };

    const handleCancel = async (reason?: string) => {
        if (!selectedItem) return;

        try {
            await approvalsService.cancelRequest(selectedItem.request_id, reason);
            toast.success('Richiesta annullata');
            loadData();
        } catch (error) {
            console.error(error);
            toast.error('Errore nell\'annullamento');
            throw error;
        }
    };

    const openDecisionModal = (item: PendingApprovalItem) => {
        setSelectedItem(item);
        setIsDecisionModalOpen(true);
    };

    const getEntityUrl = (item: PendingApprovalItem) => {
        switch (item.entity_type) {
            case 'LEAVE':
                return `/leaves/${item.entity_id}`;
            case 'TRIP':
                return `/trips/${item.entity_id}`;
            case 'EXPENSE':
                return `/expenses/${item.entity_id}`;
            default:
                return null;
        }
    };

    return (
        <div className="p-6 max-w-5xl mx-auto">
            {/* View Mode Tabs */}
            <div className="flex mb-6 p-1 bg-gray-100 rounded-lg self-start w-fit">
                <button
                    onClick={() => setViewMode('pending')}
                    className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-all ${viewMode === 'pending'
                        ? 'bg-white text-indigo-700 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    <Clock className="h-4 w-4" />
                    In Attesa
                    {data?.total ? (
                        <span className="ml-1 px-1.5 py-0.5 text-xs font-bold bg-indigo-100 text-indigo-700 rounded">
                            {data.total}
                        </span>
                    ) : null}
                </button>
                <button
                    onClick={() => setViewMode('archived')}
                    className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-all ${viewMode === 'archived'
                        ? 'bg-white text-indigo-700 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    <CheckCircle className="h-4 w-4" />
                    Archivio
                    {archivedData?.total ? (
                        <span className="ml-1 px-1.5 py-0.5 text-xs font-bold bg-gray-200 text-gray-700 rounded">
                            {archivedData.total}
                        </span>
                    ) : null}
                </button>
            </div>

            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                        {viewMode === 'pending' ? (
                            <>
                                <Clock className="h-7 w-7 text-indigo-600" />
                                Approvazioni in Attesa
                            </>
                        ) : (
                            <>
                                <CheckCircle className="h-7 w-7 text-green-600" />
                                Archivio Approvazioni
                            </>
                        )}
                    </h1>
                    <p className="text-gray-600 mt-1">
                        {viewMode === 'pending'
                            ? 'Richieste che richiedono la tua approvazione'
                            : 'Storico delle tue decisioni'}
                    </p>
                </div>

                {/* Filters */}
                <div className="flex gap-3">
                    {viewMode === 'archived' && (
                        <select
                            value={archiveStatusFilter}
                            onChange={(e) => setArchiveStatusFilter(e.target.value)}
                            className="rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        >
                            <option value="all">Tutte le decisioni</option>
                            <option value="approved">Approvate</option>
                            <option value="rejected">Rifiutate</option>
                        </select>
                    )}
                    <select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        className="rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    >
                        <option value="">Tutti i tipi</option>
                        <option value="LEAVE">Ferie</option>
                        <option value="TRIP">Trasferte</option>
                        <option value="EXPENSE">Note Spese</option>
                    </select>
                </div>
            </div>

            {/* Stats - Only for pending */}
            {viewMode === 'pending' && data && (
                <div className="grid grid-cols-3 gap-4 mb-6">
                    <Card className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-indigo-100 rounded-lg">
                                <Clock className="h-6 w-6 text-indigo-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-gray-900">{data.total}</p>
                                <p className="text-sm text-gray-500">Totale in attesa</p>
                            </div>
                        </div>
                    </Card>

                    <Card className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-red-100 rounded-lg">
                                <AlertTriangle className="h-6 w-6 text-red-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-red-600">{data.urgent_count}</p>
                                <p className="text-sm text-gray-500">Urgenti</p>
                            </div>
                        </div>
                    </Card>

                    <Card className="p-4 flex items-center gap-2 text-sm text-gray-500">
                        <MessageSquare className="h-5 w-5" />
                        Clicca su una richiesta per approvarla o rifiutarla
                    </Card>
                </div>
            )}

            {/* Content */}
            {isLoading ? (
                <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
                </div>
            ) : viewMode === 'archived' ? (
                /* ARCHIVED VIEW */
                archivedData?.items.length === 0 ? (
                    <Card className="p-12 text-center">
                        <CheckCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            Nessuna decisione in archivio
                        </h3>
                        <p className="text-gray-500">
                            Non hai ancora preso decisioni su nessuna richiesta
                        </p>
                    </Card>
                ) : (
                    <div className="space-y-3">
                        {archivedData?.items.map((item: ArchivedApprovalItem) => {
                            const decisionConfig = {
                                APPROVED: { color: 'bg-green-100 text-green-700 border-green-200', icon: CheckCircle, label: 'Approvata' },
                                REJECTED: { color: 'bg-red-100 text-red-700 border-red-200', icon: XCircle, label: 'Rifiutata' },
                                DELEGATED: { color: 'bg-orange-100 text-orange-700 border-orange-200', icon: User, label: 'Delegata' },
                            }[item.decision] || { color: 'bg-gray-100 text-gray-700', icon: FileText, label: item.decision };

                            const DecisionIcon = decisionConfig.icon;

                            return (
                                <Card key={item.request_id} className="p-4 hover:shadow-md transition-shadow">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <EntityIcon type={item.entity_type} className="h-8 w-8" />
                                            <div>
                                                <h3 className="font-medium text-gray-900">{item.title}</h3>
                                                <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                                                    <User className="h-4 w-4" />
                                                    <span>{item.requester_name || 'N/D'}</span>
                                                    <span>•</span>
                                                    <span>{format(new Date(item.created_at), 'dd MMM yyyy', { locale: it })}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <EntityTypeBadge type={item.entity_type} />
                                            <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium ${decisionConfig.color}`}>
                                                <DecisionIcon className="h-4 w-4" />
                                                {decisionConfig.label}
                                            </div>
                                            <div className="text-right text-sm text-gray-500">
                                                <p>Deciso il</p>
                                                <p className="font-medium">{format(new Date(item.decided_at), 'dd/MM/yyyy HH:mm', { locale: it })}</p>
                                            </div>
                                        </div>
                                    </div>
                                    {item.decision_notes && (
                                        <div className="mt-3 p-2 bg-gray-50 rounded text-sm text-gray-600">
                                            <span className="font-medium">Note: </span>{item.decision_notes}
                                        </div>
                                    )}
                                </Card>
                            );
                        })}
                    </div>
                )
            ) : data?.items.length === 0 ? (
                <Card className="p-12 text-center">
                    <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        Nessuna approvazione in attesa
                    </h3>
                    <p className="text-gray-500">
                        Sei in pari con tutte le approvazioni!
                    </p>
                </Card>
            ) : (
                <div className="space-y-3">
                    {data?.items.map((item) => {
                        const entityUrl = getEntityUrl(item);

                        return (
                            <div
                                key={item.request_id}
                                onClick={() => openDecisionModal(item)}
                                className="cursor-pointer"
                            >
                                <Card
                                    className={`p-4 hover:shadow-md transition-shadow ${item.is_urgent ? 'border-l-4 border-l-red-500' : ''
                                        }`}
                                >
                                    <div className="flex items-center gap-4">
                                        {/* Icon */}
                                        <EntityIcon type={item.entity_type} className="h-10 w-10" />

                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <EntityTypeBadge type={item.entity_type} />
                                                {item.entity_ref && (
                                                    <span className="text-xs text-gray-500 font-mono">
                                                        {item.entity_ref}
                                                    </span>
                                                )}
                                                <UrgencyIndicator item={item} />
                                            </div>

                                            <h3 className="font-semibold text-gray-900 truncate">
                                                {item.title}
                                            </h3>

                                            {item.description && (
                                                <p className="text-sm text-gray-600 truncate mt-0.5">
                                                    {item.description}
                                                </p>
                                            )}

                                            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                                                <div className="flex items-center gap-1">
                                                    <User className="h-4 w-4" />
                                                    {item.requester_name || 'Utente'}
                                                </div>
                                                <span>•</span>
                                                <span>
                                                    {item.days_pending === 0
                                                        ? 'Oggi'
                                                        : item.days_pending === 1
                                                            ? 'Ieri'
                                                            : `${item.days_pending} giorni fa`
                                                    }
                                                </span>
                                                {item.approval_level > 1 && (
                                                    <>
                                                        <span>•</span>
                                                        <span className="text-indigo-600">
                                                            Livello {item.approval_level}
                                                        </span>
                                                    </>
                                                )}
                                            </div>
                                        </div>

                                        {/* Actions */}
                                        <div className="flex items-center gap-2">
                                            {entityUrl && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        navigate(entityUrl);
                                                    }}
                                                    className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg"
                                                    title="Visualizza dettagli"
                                                >
                                                    <ExternalLink className="h-5 w-5" />
                                                </button>
                                            )}

                                            <ChevronRight className="h-5 w-5 text-gray-400" />
                                        </div>
                                    </div>
                                </Card>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Decision Modal */}
            <DecisionModal
                isOpen={isDecisionModalOpen}
                onClose={() => {
                    setIsDecisionModalOpen(false);
                    setSelectedItem(null);
                }}
                item={selectedItem}
                onApprove={handleApprove}
                onReject={handleReject}
                onApproveConditional={handleApproveConditional}
                onCancel={handleCancel}
                showCancelOption={true}
            />
        </div>
    );
};

export default PendingApprovalsPage;
