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
    Check,
    MessageSquare,
    Ban,

    ArrowRight
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { it } from 'date-fns/locale';

import { Button } from '../../components/common/Button';
import { Modal } from '../../components/common/Modal';
import approvalsService from '../../services/approvals.service';
import type {
    PendingApprovalItem,
    PendingApprovalsResponse,
    ArchivedApprovalItem,
    ArchivedApprovalsResponse,
} from '../../services/approvals.service';

// ═══════════════════════════════════════════════════════════
// Constants & Templates (Italian Labor Law Aligned)
// ═══════════════════════════════════════════════════════════

const CONDITION_SUGGESTIONS = {
    RECALL: [
        "Eccezionali ed indifferibili esigenze tecnico-produttive (CCNL).",
        "Sostituzione urgente personale assente non programmato.",
        "Picco di attività stagionale imprevisto richiedente presidio minimo."
    ],
    LOGISTIC: [
        "Garantire il servizio minimo garantito e continuità operativa.",
        "Mancato raggiungimento del numero minimo di operatori per turno.",
        "Coordinamento obbligatorio con scadenze di progetto improrogabili."
    ],
    TEMPORAL: [
        "Spostamento per coincidenza con attività di audit esterno.",
        "Revisione richiesta per sovrapposizione con formazione obbligatoria.",
        "Disponibilità limitata causa chiusura uffici programmata."
    ],
    PARTIAL: [
        "Approvazione parziale: garantita copertura solo per parte del periodo.",
        "Autorizzazione limitata ai giorni di basso carico operativo."
    ],
    OTHER: [
        "Accordo specifico individuale tra lavoratore e azienda.",
        "Compensazione ore o recupero flessibile concordato."
    ]
};

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
                    <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-${(item.entity_type === 'LEAVE' ? 3 : 2) + (showCancelOption ? 1 : 0)} gap-4`}>
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
                                    Approva con vincoli o richiami aziendali.
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

                        {/* Cancel Card */}
                        {showCancelOption && onCancel && (
                            <button
                                type="button"
                                onClick={() => setAction('cancel')}
                                className={`group relative flex flex-col items-center p-6 rounded-2xl border-2 transition-all duration-300 ${action === 'cancel'
                                    ? 'border-amber-500 bg-amber-50/50 shadow-lg shadow-amber-500/10'
                                    : 'border-white bg-white hover:border-amber-300 hover:shadow-md'
                                    } ring-1 ring-gray-100`}
                            >
                                <div className={`h-14 w-14 rounded-full flex items-center justify-center mb-4 transition-transform duration-500 ${action === 'cancel' ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/40 scale-110' : 'bg-amber-50 text-amber-500 group-hover:scale-110'
                                    }`}>
                                    <Ban className="h-8 w-8" />
                                </div>
                                <h5 className={`text-base font-bold mb-1 ${action === 'cancel' ? 'text-amber-900' : 'text-gray-900'}`}>
                                    Annulla
                                </h5>
                                <p className="text-xs text-center text-gray-500 leading-relaxed max-w-[140px]">
                                    Annulla la richiesta per motivi amministrativi.
                                </p>
                                {action === 'cancel' && (
                                    <div className="absolute -top-1.5 -right-1.5 h-6 w-6 bg-amber-500 rounded-full flex items-center justify-center text-white shadow-sm animate-in zoom-in duration-300">
                                        <Check className="h-4 w-4 stroke-[3]" />
                                    </div>
                                )}
                            </button>
                        )}
                    </div>
                </div>

                {/* Integrated Action Form */}
                <div className={`overflow-hidden transition-all duration-500 ease-in-out ${action ? 'max-h-[600px] opacity-100 mt-2' : 'max-h-0 opacity-0'}`}>
                    <div className="rounded-2xl bg-gray-50/80 p-6 border border-gray-100 ring-1 ring-white/50">
                        {action === 'approve_conditional' && (
                            <div className="space-y-6 animate-in slide-in-from-top-4 duration-500">
                                {/* Step 1: Condition Type Selector */}
                                <div className="space-y-3">
                                    <div className="flex items-center gap-3">
                                        <div className="h-7 w-7 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shadow-md">1</div>
                                        <h4 className="text-sm font-bold text-gray-900">Categoria della condizione</h4>
                                    </div>
                                    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 pl-10">
                                        {[
                                            { value: 'RECALL', label: 'Richiamo', icon: '⚠️', ccnl: true },
                                            { value: 'LOGISTIC', label: 'Operativa', icon: '⚙️', ccnl: true },
                                            { value: 'TEMPORAL', label: 'Temporale', icon: '📅', ccnl: false },
                                            { value: 'PARTIAL', label: 'Parziale', icon: '½', ccnl: false },
                                            { value: 'OTHER', label: 'Altro', icon: '✏️', ccnl: false },
                                        ].map((cat) => (
                                            <button
                                                key={cat.value}
                                                type="button"
                                                onClick={() => { setConditionType(cat.value); setConditionDetails(''); }}
                                                className={`relative flex flex-col items-center p-3 rounded-xl border-2 transition-all duration-200 ${conditionType === cat.value
                                                    ? 'border-blue-500 bg-blue-50 shadow-md shadow-blue-500/10'
                                                    : 'border-gray-100 bg-white hover:border-blue-200 hover:bg-blue-50/30'
                                                    }`}
                                            >
                                                <span className="text-xl mb-1">{cat.icon}</span>
                                                <span className={`text-xs font-semibold ${conditionType === cat.value ? 'text-blue-700' : 'text-gray-700'}`}>
                                                    {cat.label}
                                                </span>
                                                {cat.ccnl && (
                                                    <span className="absolute -top-1 -right-1 text-[8px] font-bold bg-emerald-500 text-white px-1.5 py-0.5 rounded-full shadow-sm">
                                                        CCNL
                                                    </span>
                                                )}
                                                {conditionType === cat.value && (
                                                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 h-2 w-2 bg-blue-500 rounded-full animate-pulse" />
                                                )}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Step 2: Template Selection */}
                                <div className="space-y-3">
                                    <div className="flex items-center gap-3">
                                        <div className="h-7 w-7 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold shadow-md">2</div>
                                        <h4 className="text-sm font-bold text-gray-900">Seleziona un template conforme</h4>
                                        <span className="text-[10px] text-gray-400 ml-auto italic">oppure scrivi manualmente sotto</span>
                                    </div>
                                    <div className="grid grid-cols-1 gap-2 pl-10">
                                        {CONDITION_SUGGESTIONS[conditionType as keyof typeof CONDITION_SUGGESTIONS]?.map((suggestion, idx) => {
                                            const isSelected = conditionDetails === suggestion;
                                            return (
                                                <button
                                                    key={idx}
                                                    type="button"
                                                    onClick={() => setConditionDetails(suggestion)}
                                                    className={`group relative flex items-start gap-3 p-3 rounded-xl border text-left transition-all duration-200 ${isSelected
                                                        ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-500/20'
                                                        : 'border-gray-100 bg-white hover:border-blue-200 hover:bg-gray-50'
                                                        }`}
                                                >
                                                    <div className={`flex-shrink-0 h-5 w-5 rounded-full border-2 flex items-center justify-center transition-all ${isSelected ? 'border-blue-500 bg-blue-500' : 'border-gray-300 group-hover:border-blue-400'
                                                        }`}>
                                                        {isSelected && <Check className="h-3 w-3 text-white stroke-[3]" />}
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <p className={`text-sm leading-relaxed ${isSelected ? 'text-blue-900 font-medium' : 'text-gray-700'}`}>
                                                            {suggestion}
                                                        </p>
                                                    </div>
                                                    {(conditionType === 'RECALL' || conditionType === 'LOGISTIC') && idx === 0 && (
                                                        <span className="flex-shrink-0 text-[9px] font-bold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-md ring-1 ring-emerald-200">
                                                            Consigliato
                                                        </span>
                                                    )}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>

                                {/* Step 3: Customization */}
                                <div className="space-y-3">
                                    <div className="flex items-center gap-3">
                                        <div className="h-7 w-7 rounded-full bg-gray-300 text-white flex items-center justify-center text-xs font-bold">3</div>
                                        <h4 className="text-sm font-bold text-gray-500">Personalizza o scrivi liberamente</h4>
                                    </div>
                                    <div className="pl-10">
                                        <textarea
                                            value={conditionDetails}
                                            onChange={(e) => setConditionDetails(e.target.value)}
                                            className="w-full text-sm rounded-xl border-gray-200 bg-white p-4 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all resize-none"
                                            rows={2}
                                            placeholder="Modifica il template selezionato o inserisci una condizione personalizzata..."
                                        />
                                        {conditionDetails && (
                                            <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                                                <Check className="h-3.5 w-3.5 text-emerald-500" />
                                                <span>Condizione definita: <span className="font-medium text-gray-700">{conditionDetails.substring(0, 50)}{conditionDetails.length > 50 ? '...' : ''}</span></span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className={`space-y-1.5 ${action === 'approve_conditional' ? 'mt-5' : ''}`}>
                            <label className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                                <MessageSquare className={`h-3.5 w-3.5 ${action === 'reject' ? 'text-rose-500' :
                                    action === 'approve' ? 'text-emerald-500' :
                                        action === 'cancel' ? 'text-amber-500' : 'text-blue-500'
                                    }`} />
                                {action === 'reject' ? 'Motivazione del Rifiuto *' :
                                    action === 'cancel' ? 'Motivazione Annullamento *' : 'Note Aggiuntive'}
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
                                        action === 'cancel' ? 'Indica il motivo per cui procedi con l\'annullamento...' :
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
                                            action === 'cancel' ? 'bg-amber-600 hover:bg-amber-700 shadow-amber-600/20' :
                                                'bg-blue-600 hover:bg-blue-700 shadow-blue-600/20'
                                        }`}
                                >
                                    {action === 'approve' ? 'Conferma Approvazione' :
                                        action === 'reject' ? 'Invia Rifiuto' :
                                            action === 'cancel' ? 'Conferma Annullamento' :
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
    const [archiveStatusFilter] = useState<string>('all');

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

    const getEntityUrl = (item: PendingApprovalItem | ArchivedApprovalItem) => {
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

    // Helper for table filtering tabs
    const filterTabs = [
        { id: '', label: 'Tutte', icon: FileText },
        { id: 'LEAVE', label: 'Ferie & Permessi', icon: Calendar },
        { id: 'TRIP', label: 'Trasferte', icon: Briefcase },
        { id: 'EXPENSE', label: 'Note Spese', icon: Receipt },
    ];

    if (isLoading && !data && !archivedData) {
        return (
            <div className="flex flex-col items-center justify-center p-32 gap-6">
                <div className="relative">
                    <div className="w-20 h-20 border-4 border-slate-200 border-t-indigo-600 rounded-full animate-spin" />
                    <CheckCircle className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-indigo-600" size={32} />
                </div>
                <p className="text-sm font-bold uppercase tracking-widest text-slate-400 animate-pulse">Caricamento Approvazioni...</p>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-fadeIn max-w-[1600px] mx-auto pb-12">
            {/* Enterprise Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-slate-200">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className={`p-2 rounded-lg ${viewMode === 'pending' ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-700'}`}>
                            {viewMode === 'pending' ? <CheckCircle size={24} /> : <FileSearch size={24} />}
                        </div>
                        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
                            {viewMode === 'pending' ? 'Approvazioni' : 'Archivio Decisioni'}
                        </h1>
                    </div>
                    <p className="text-slate-500 max-w-2xl">
                        {viewMode === 'pending'
                            ? 'Gestisci le richieste del tuo team con precisione e velocità. Verifica le priorità urgenti.'
                            : 'Consulta lo storico delle tue decisioni passate.'}
                    </p>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                    {viewMode === 'pending' && data && (
                        <div className="flex items-center gap-4 px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl">
                            <div className="text-right">
                                <div className="text-[10px] uppercase tracking-wider font-bold text-slate-400">Totali</div>
                                <div className="text-lg font-bold text-slate-900">{data.total}</div>
                            </div>
                            <div className="h-8 w-px bg-slate-200" />
                            <div className="text-right">
                                <div className="text-[10px] uppercase tracking-wider font-bold text-slate-400">Urgenti</div>
                                <div className={`text-lg font-bold ${data.urgent_count > 0 ? 'text-red-500 animate-pulse' : 'text-emerald-600'}`}>
                                    {data.urgent_count}
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="flex bg-slate-100 p-1 rounded-xl">
                        <button
                            onClick={() => setViewMode('pending')}
                            className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all ${viewMode === 'pending' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                        >
                            In Attesa
                        </button>
                        <button
                            onClick={() => setViewMode('archived')}
                            className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all ${viewMode === 'archived' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                        >
                            Archivio
                        </button>
                    </div>
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
                {filterTabs.map(filter => (
                    <button
                        key={filter.id}
                        onClick={() => setFilterType(filter.id)}
                        className={`
                            flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap
                            ${filterType === filter.id
                                ? 'bg-slate-900 text-white shadow-md'
                                : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200 hover:border-slate-300'}
                        `}
                    >
                        <filter.icon size={16} className={filterType === filter.id ? 'text-indigo-400' : 'text-slate-400'} />
                        {filter.label}
                    </button>
                ))}
            </div>

            {/* Data Table */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50 border-b border-slate-200">
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider w-[60px]">Stato</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider w-[300px]">Richiesta</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">Richiedente</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">Info & Scadenza</th>
                                <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Azioni</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {viewMode === 'pending' ? (
                                (data?.items?.length ?? 0) === 0 ? (
                                    <EmptyState />
                                ) : (
                                    data?.items.map((item) => (
                                        <tr
                                            key={item.request_id}
                                            onClick={() => openDecisionModal(item)}
                                            className="group hover:bg-slate-50/80 transition-colors cursor-pointer"
                                        >
                                            <td className="py-4 px-6 align-middle">
                                                {item.is_urgent ? (
                                                    <div className="h-8 w-8 rounded-full bg-red-100 text-red-600 flex items-center justify-center animate-pulse" title="Urgente">
                                                        <AlertTriangle size={16} />
                                                    </div>
                                                ) : (
                                                    <div className="h-8 w-8 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center">
                                                        <Clock size={16} />
                                                    </div>
                                                )}
                                            </td>

                                            <td className="py-4 px-6 align-top">
                                                <div className="flex items-start gap-3">
                                                    <div className={`mt-1 p-1.5 rounded-lg shrink-0 ${item.entity_type === 'LEAVE' ? 'bg-blue-50 text-blue-600' :
                                                        item.entity_type === 'TRIP' ? 'bg-purple-50 text-purple-600' :
                                                            'bg-emerald-50 text-emerald-600'
                                                        }`}>
                                                        <EntityIcon type={item.entity_type} className="h-4 w-4" />
                                                    </div>
                                                    <div>
                                                        <span className="font-bold text-slate-900 block group-hover:text-indigo-700 transition-colors line-clamp-1">
                                                            {item.title}
                                                        </span>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            <span className="text-xs text-slate-500 font-mono bg-slate-100 px-1.5 py-0.5 rounded">
                                                                #{item.entity_ref || item.request_id.slice(0, 8)}
                                                            </span>
                                                            <EntityTypeBadge type={item.entity_type} />
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>

                                            <td className="py-4 px-6 align-middle">
                                                <div className="flex items-center gap-3">
                                                    <div className="h-9 w-9 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-sm border border-indigo-100">
                                                        {item.requester_name?.charAt(0) || 'U'}
                                                    </div>
                                                    <div>
                                                        <div className="text-sm font-bold text-slate-700">{item.requester_name || 'Utente Sconosciuto'}</div>
                                                        <div className="text-xs text-slate-400">Richiedente</div>
                                                    </div>
                                                </div>
                                            </td>

                                            <td className="py-4 px-6 align-middle">
                                                <div className="space-y-1">
                                                    <div className="flex items-center gap-2 text-sm text-slate-600">
                                                        <Calendar size={14} className="text-slate-400" />
                                                        <span>{format(new Date(item.created_at), 'dd MMM yyyy', { locale: it })}</span>
                                                    </div>
                                                    {item.expires_at && (
                                                        <div className={`text-xs font-medium flex items-center gap-1 ${new Date(item.expires_at) < new Date(Date.now() + 86400000) ? 'text-red-500' : 'text-slate-400'
                                                            }`}>
                                                            <Clock size={12} />
                                                            Scade {formatDistanceToNow(new Date(item.expires_at), { addSuffix: true, locale: it })}
                                                        </div>
                                                    )}
                                                </div>
                                            </td>

                                            <td className="py-4 px-6 align-middle text-right">
                                                <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <Button size="sm" variant="secondary" className="bg-white hover:bg-emerald-50 hover:text-emerald-700 border-slate-200" onClick={(e) => {
                                                        e.stopPropagation();
                                                        openDecisionModal(item);
                                                    }}>
                                                        Valuta
                                                    </Button>
                                                    <button className="btn btn-ghost btn-sm btn-square text-slate-400 hover:text-indigo-600 hover:bg-indigo-50">
                                                        <ChevronRight size={18} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )
                            ) : (
                                (archivedData?.items?.length ?? 0) === 0 ? (
                                    <EmptyState type="archive" />
                                ) : (
                                    archivedData?.items.map((item) => (
                                        <tr
                                            key={item.request_id}
                                            onClick={() => {
                                                const url = getEntityUrl(item);
                                                if (url) navigate(url);
                                            }}
                                            className="group hover:bg-slate-50/80 transition-colors cursor-pointer"
                                        >
                                            <td className="py-4 px-6 align-middle">
                                                <div className={`h-8 w-8 rounded-full flex items-center justify-center ${item.decision === 'APPROVED' ? 'bg-emerald-100 text-emerald-600' :
                                                    item.decision === 'REJECTED' ? 'bg-red-100 text-red-600' :
                                                        'bg-slate-100 text-slate-600'
                                                    }`}>
                                                    {item.decision === 'APPROVED' ? <Check size={16} /> :
                                                        item.decision === 'REJECTED' ? <XCircle size={16} /> :
                                                            <ArrowRight size={16} />}
                                                </div>
                                            </td>
                                            <td className="py-4 px-6 align-top">
                                                <div className="flex items-start gap-3">
                                                    <div>
                                                        <span className="font-bold text-slate-900 block group-hover:text-indigo-700 transition-colors line-clamp-1">
                                                            {item.title}
                                                        </span>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            <EntityTypeBadge type={item.entity_type} />
                                                            <span className="text-xs text-slate-400">
                                                                {format(new Date(item.decided_at), 'dd MMM yyyy', { locale: it })}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="py-4 px-6 align-middle">
                                                <div className="text-sm font-medium text-slate-700">{item.requester_name}</div>
                                            </td>
                                            <td className="py-4 px-6 align-middle">
                                                <div className="text-sm text-slate-500 line-clamp-1 italic">
                                                    {item.decision_notes || 'Nessuna nota'}
                                                </div>
                                            </td>
                                            <td className="py-4 px-6 align-middle text-right">
                                                <button className="btn btn-ghost btn-sm btn-square text-slate-400 group-hover:text-indigo-600">
                                                    <ExternalLink size={16} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Footer Stats */}
                {((viewMode === 'pending' ? data?.items?.length : archivedData?.items?.length) ?? 0) > 0 && (
                    <div className="bg-slate-50 border-t border-slate-200 px-6 py-3 text-xs text-slate-500 flex justify-between items-center">
                        <span>
                            {viewMode === 'pending'
                                ? `Mostrati ${data?.items.length || 0} record in attesa`
                                : `Mostrati ${archivedData?.items.length || 0} record archiviati`}
                        </span>
                        <span className="flex items-center gap-1">
                            <ShieldCheck size={12} className="text-emerald-500" />
                            Secure Workflow
                        </span>
                    </div>
                )}
            </div>

            <DecisionModal
                isOpen={isDecisionModalOpen}
                onClose={() => setIsDecisionModalOpen(false)}
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

const EmptyState: React.FC<{ type?: 'pending' | 'archive' }> = ({ type = 'pending' }) => (
    <tr>
        <td colSpan={5} className="py-16 text-center">
            <div className="flex flex-col items-center justify-center">
                <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mb-4 ring-1 ring-slate-100">
                    {type === 'pending' ? <CheckCircle size={32} className="text-slate-300" /> : <FileSearch size={32} className="text-slate-300" />}
                </div>
                <h3 className="text-lg font-semibold text-slate-900">
                    {type === 'pending' ? 'Tutto in ordine!' : 'Nessuna decisione trovata'}
                </h3>
                <p className="text-slate-400 text-sm max-w-xs mx-auto mt-1">
                    {type === 'pending'
                        ? 'Non hai approvazioni in attesa al momento. Ottimo lavoro!'
                        : 'Non ci sono decisioni archiviate che corrispondono ai filtri selezionati.'}
                </p>
            </div>
        </td>
    </tr>
);

export default PendingApprovalsPage;
