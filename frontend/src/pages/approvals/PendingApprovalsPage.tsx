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
    Calendar,
    Briefcase,
    Receipt,
    FileText,
    ChevronRight,
    ExternalLink,
    MessageSquare,
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
    onCancel?: (reason?: string) => Promise<void>;
    showCancelOption?: boolean;
}

const DecisionModal: React.FC<DecisionModalProps> = ({
    isOpen,
    onClose,
    item,
    onApprove,
    onReject,
    onCancel,
    showCancelOption = false,
}) => {
    const toast = useToast();
    const [notes, setNotes] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [action, setAction] = useState<'approve' | 'reject' | 'cancel' | null>(null);

    const handleSubmit = async () => {
        if (action === 'reject' && !notes.trim()) {
            toast.error('Inserisci una motivazione per il rifiuto');
            return;
        }

        setIsSubmitting(true);
        try {
            if (action === 'approve') {
                await onApprove(notes.trim() || undefined);
            } else if (action === 'reject') {
                await onReject(notes.trim());
            } else if (action === 'cancel' && onCancel) {
                await onCancel(notes.trim() || undefined);
            }
            onClose();
            setNotes('');
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
            title="Decisione Approvazione"
            size="md"
        >
            <div className="space-y-4">
                {/* Request Info */}
                <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <EntityIcon type={item.entity_type} className="h-10 w-10" />
                        <div className="flex-1">
                            <h3 className="font-semibold text-gray-900">{item.title}</h3>
                            {item.description && (
                                <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                            )}
                            <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                                <div className="flex items-center gap-1">
                                    <User className="h-4 w-4" />
                                    {item.requester_name || 'Utente'}
                                </div>
                                <span>•</span>
                                <span>{format(new Date(item.created_at), 'dd MMM yyyy', { locale: it })}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Decision Buttons */}
                <div className={`grid gap-4 ${showCancelOption ? 'grid-cols-3' : 'grid-cols-2'}`}>
                    <button
                        onClick={() => setAction('approve')}
                        className={`p-4 rounded-lg border-2 transition-all ${action === 'approve'
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 hover:border-green-300 hover:bg-green-50/50'
                            }`}
                    >
                        <CheckCircle className={`h-8 w-8 mx-auto mb-2 ${action === 'approve' ? 'text-green-500' : 'text-gray-400'
                            }`} />
                        <span className={`font-medium ${action === 'approve' ? 'text-green-700' : 'text-gray-700'
                            }`}>
                            Approva
                        </span>
                    </button>

                    <button
                        onClick={() => setAction('reject')}
                        className={`p-4 rounded-lg border-2 transition-all ${action === 'reject'
                            ? 'border-red-500 bg-red-50'
                            : 'border-gray-200 hover:border-red-300 hover:bg-red-50/50'
                            }`}
                    >
                        <XCircle className={`h-8 w-8 mx-auto mb-2 ${action === 'reject' ? 'text-red-500' : 'text-gray-400'
                            }`} />
                        <span className={`font-medium ${action === 'reject' ? 'text-red-700' : 'text-gray-700'
                            }`}>
                            Rifiuta
                        </span>
                    </button>

                    {showCancelOption && onCancel && (
                        <button
                            onClick={() => setAction('cancel')}
                            className={`p-4 rounded-lg border-2 transition-all ${action === 'cancel'
                                ? 'border-orange-500 bg-orange-50'
                                : 'border-gray-200 hover:border-orange-300 hover:bg-orange-50/50'
                                }`}
                        >
                            <Ban className={`h-8 w-8 mx-auto mb-2 ${action === 'cancel' ? 'text-orange-500' : 'text-gray-400'
                                }`} />
                            <span className={`font-medium ${action === 'cancel' ? 'text-orange-700' : 'text-gray-700'
                                }`}>
                                Annulla
                            </span>
                        </button>
                    )}
                </div>

                {/* Notes */}
                {action && (
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            {action === 'reject' ? 'Motivazione *' : action === 'cancel' ? 'Motivazione annullamento (opzionale)' : 'Note (opzionale)'}
                        </label>
                        <textarea
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            rows={3}
                            placeholder={action === 'reject'
                                ? 'Inserisci la motivazione del rifiuto...'
                                : action === 'cancel'
                                    ? 'Motivo dell\'annullamento...'
                                    : 'Aggiungi una nota (opzionale)...'
                            }
                        />
                    </div>
                )}

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-4 border-t">
                    <Button variant="secondary" onClick={onClose} disabled={isSubmitting}>
                        Chiudi
                    </Button>
                    <Button
                        onClick={handleSubmit}
                        disabled={!action || isSubmitting}
                        isLoading={isSubmitting}
                        className={
                            action === 'approve' ? 'bg-green-600 hover:bg-green-700' :
                                action === 'reject' ? 'bg-red-600 hover:bg-red-700' :
                                    action === 'cancel' ? 'bg-orange-600 hover:bg-orange-700' : ''
                        }
                    >
                        {action === 'approve' ? 'Conferma Approvazione' :
                            action === 'reject' ? 'Conferma Rifiuto' :
                                action === 'cancel' ? 'Conferma Annullamento' : 'Seleziona Azione'}
                    </Button>
                </div>
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

    const [data, setData] = useState<PendingApprovalsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedItem, setSelectedItem] = useState<PendingApprovalItem | null>(null);
    const [isDecisionModalOpen, setIsDecisionModalOpen] = useState(false);
    const [filterType, setFilterType] = useState<string>('');

    useEffect(() => {
        loadData();
    }, [filterType]);

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
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                        <Clock className="h-7 w-7 text-indigo-600" />
                        Approvazioni in Attesa
                    </h1>
                    <p className="text-gray-600 mt-1">
                        Richieste che richiedono la tua approvazione
                    </p>
                </div>

                {/* Filter */}
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

            {/* Stats */}
            {data && (
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
                onCancel={handleCancel}
                showCancelOption={true}
            />
        </div>
    );
};

export default PendingApprovalsPage;
