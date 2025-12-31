/**
 * KRONOS - Contract History Component
 * Enterprise-grade contract management with timeline
 */
import { useState, useEffect } from 'react';
import { userService } from '../../services/userService';
import { leavesService } from '../../services/leaves.service';
import type { EmployeeContract, ContractType, EmployeeContractCreate } from '../../types';
import {
    Plus,
    X,
    Calendar,
    Briefcase,
    Clock,
    FileText,
    CheckCircle,
    AlertCircle,
    ChevronDown,
    ChevronUp,
    Edit,
} from 'lucide-react';

interface ContractHistoryProps {
    userId: string;
    userName?: string;
    onClose: () => void;
}

export function ContractHistory({ userId, userName, onClose }: ContractHistoryProps) {
    const [contracts, setContracts] = useState<EmployeeContract[]>([]);
    const [contractTypes, setContractTypes] = useState<ContractType[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Form state
    const [newContract, setNewContract] = useState<Partial<EmployeeContractCreate>>({
        weekly_hours: 40,
        start_date: new Date().toISOString().split('T')[0],
    });

    useEffect(() => {
        loadData();
    }, [userId]);

    const loadData = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const [contractsData, typesData] = await Promise.all([
                userService.getContracts(userId),
                userService.getContractTypes(),
            ]);
            setContracts(contractsData);
            setContractTypes(typesData);
        } catch (err: any) {
            setError('Errore nel caricamento dei contratti');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async () => {
        if (!newContract.contract_type_id || !newContract.start_date) {
            setError('Compila tutti i campi obbligatori');
            return;
        }

        try {
            await userService.addContract(userId, newContract as EmployeeContractCreate);

            // Integration: Recalculate leave accruals for this user immediately after contract change
            try {
                await leavesService.recalculateUserAccruals(userId);
            } catch (recalcErr) {
                console.error('Non-critical error: failed to auto-recalculate accruals', recalcErr);
                // We don't block the user, as the manual button is available in Config
            }

            setIsAdding(false);
            setNewContract({ weekly_hours: 40, start_date: new Date().toISOString().split('T')[0] });
            loadData();
        } catch (err: any) {
            setError(err.message || 'Errore durante il salvataggio');
        }
    };

    const getTypeName = (id: string) => contractTypes.find(t => t.id === id)?.name || id;
    const getTypeCode = (id: string) => contractTypes.find(t => t.id === id)?.code || '';

    const activeContract = contracts.find(c => !c.end_date);
    const pastContracts = contracts.filter(c => c.end_date);

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString('it-IT', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
        });
    };

    return (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
            <div className="modal-container animate-scaleIn">
                {/* Header */}
                <div className="modal-header">
                    <div className="modal-header-content">
                        <div className="modal-icon">
                            <Briefcase size={24} />
                        </div>
                        <div>
                            <h2>Gestione Contratti</h2>
                            {userName && <p className="modal-subtitle">{userName}</p>}
                        </div>
                    </div>
                    <button onClick={onClose} className="btn btn-ghost btn-icon">
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="modal-body">
                    {error && (
                        <div className="alert alert-error">
                            <AlertCircle size={16} />
                            <span>{error}</span>
                            <button onClick={() => setError(null)} className="btn btn-ghost btn-icon btn-sm">
                                <X size={14} />
                            </button>
                        </div>
                    )}

                    {/* Add Contract Button */}
                    {!isAdding && (
                        <button
                            className="btn btn-primary"
                            onClick={() => setIsAdding(true)}
                            style={{ marginBottom: 'var(--space-4)' }}
                        >
                            <Plus size={18} />
                            Nuovo Contratto
                        </button>
                    )}

                    {/* Add Contract Form */}
                    {isAdding && (
                        <div className="add-contract-form card animate-fadeInUp">
                            <div className="form-header">
                                <h3>
                                    <FileText size={18} />
                                    Nuovo Contratto
                                </h3>
                            </div>
                            <div className="form-body">
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="input-label input-label-required">Tipo Contratto</label>
                                        <select
                                            className="input"
                                            value={newContract.contract_type_id || ''}
                                            onChange={e => {
                                                const typeId = e.target.value;
                                                const type = contractTypes.find(t => t.id === typeId);
                                                // Default 40h base, adjusted by part-time percentage
                                                const defaultHours = type ? Math.round(40 * ((type.part_time_percentage || 100) / 100)) : 40;

                                                setNewContract({
                                                    ...newContract,
                                                    contract_type_id: typeId,
                                                    weekly_hours: defaultHours
                                                });
                                            }}
                                        >
                                            <option value="">Seleziona tipo...</option>
                                            {contractTypes.map(t => (
                                                <option key={t.id} value={t.id}>
                                                    {t.name} ({t.code})
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="input-label input-label-required">Ore Settimanali</label>
                                        <input
                                            type="number"
                                            className="input"
                                            value={newContract.weekly_hours}
                                            onChange={e => setNewContract({ ...newContract, weekly_hours: parseInt(e.target.value) })}
                                            min={1}
                                            max={48}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="input-label input-label-required">Data Inizio</label>
                                        <input
                                            type="date"
                                            className="input"
                                            value={newContract.start_date}
                                            onChange={e => setNewContract({ ...newContract, start_date: e.target.value })}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="input-label">Data Fine (opzionale)</label>
                                        <input
                                            type="date"
                                            className="input"
                                            value={newContract.end_date || ''}
                                            onChange={e => setNewContract({ ...newContract, end_date: e.target.value || undefined })}
                                        />
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label className="input-label">Mansione</label>
                                    <input
                                        type="text"
                                        className="input"
                                        value={newContract.job_title || ''}
                                        onChange={e => setNewContract({ ...newContract, job_title: e.target.value })}
                                        placeholder="es. Software Engineer Senior"
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="input-label">Livello / Inquadramento</label>
                                    <input
                                        type="text"
                                        className="input"
                                        value={newContract.level || ''}
                                        onChange={e => setNewContract({ ...newContract, level: e.target.value })}
                                        placeholder="es. Quadro, Impiegato III Livello"
                                    />
                                </div>

                                <div className="form-actions">
                                    <button className="btn btn-ghost" onClick={() => setIsAdding(false)}>
                                        Annulla
                                    </button>
                                    <button className="btn btn-primary" onClick={handleSave}>
                                        <CheckCircle size={16} />
                                        Salva Contratto
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Loading State */}
                    {isLoading && (
                        <div className="loading-state">
                            <div className="spinner" />
                            <p>Caricamento contratti...</p>
                        </div>
                    )}

                    {/* Contracts List */}
                    {!isLoading && (
                        <div className="contracts-list">
                            {/* Active Contract */}
                            {activeContract && (
                                <div className="contract-section">
                                    <h4 className="section-label">
                                        <CheckCircle size={14} />
                                        Contratto Attivo
                                    </h4>
                                    <div className="contract-card active">
                                        <div className="contract-header">
                                            <div className="contract-type-badge active">
                                                {getTypeCode(activeContract.contract_type_id)}
                                            </div>
                                            <div className="contract-main-info">
                                                <h4>{getTypeName(activeContract.contract_type_id)}</h4>
                                                {activeContract.job_title && (
                                                    <p className="contract-job-title">{activeContract.job_title}</p>
                                                )}
                                            </div>
                                            <button
                                                className="btn btn-ghost btn-icon btn-sm"
                                                onClick={() => setExpandedId(expandedId === activeContract.id ? null : activeContract.id)}
                                            >
                                                {expandedId === activeContract.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                            </button>
                                        </div>

                                        <div className="contract-meta">
                                            <span className="meta-item">
                                                <Calendar size={14} />
                                                Dal {formatDate(activeContract.start_date)}
                                            </span>
                                            <span className="meta-item">
                                                <Clock size={14} />
                                                {activeContract.weekly_hours}h/settimana
                                            </span>
                                        </div>

                                        {expandedId === activeContract.id && (
                                            <div className="contract-expanded animate-fadeInUp">
                                                <div className="expanded-grid">
                                                    {activeContract.level && (
                                                        <div className="expanded-item">
                                                            <span className="expanded-label">Livello</span>
                                                            <span className="expanded-value">{activeContract.level}</span>
                                                        </div>
                                                    )}
                                                    <div className="expanded-item">
                                                        <span className="expanded-label">Ore Settimanali</span>
                                                        <span className="expanded-value">{activeContract.weekly_hours}</span>
                                                    </div>
                                                </div>
                                                <div className="expanded-actions">
                                                    <button className="btn btn-secondary btn-sm">
                                                        <Edit size={14} />
                                                        Modifica
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Past Contracts */}
                            {pastContracts.length > 0 && (
                                <div className="contract-section">
                                    <h4 className="section-label">
                                        <Clock size={14} />
                                        Storico Contratti ({pastContracts.length})
                                    </h4>
                                    <div className="timeline">
                                        {pastContracts.map((contract, index) => (
                                            <div key={contract.id} className="contract-card past">
                                                <div className="timeline-connector">
                                                    <div className="timeline-dot" />
                                                    {index < pastContracts.length - 1 && <div className="timeline-line" />}
                                                </div>
                                                <div className="contract-content">
                                                    <div className="contract-header">
                                                        <div className="contract-type-badge">
                                                            {getTypeCode(contract.contract_type_id)}
                                                        </div>
                                                        <div className="contract-main-info">
                                                            <h4>{getTypeName(contract.contract_type_id)}</h4>
                                                            {contract.job_title && (
                                                                <p className="contract-job-title">{contract.job_title}</p>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <div className="contract-meta">
                                                        <span className="meta-item">
                                                            <Calendar size={14} />
                                                            {formatDate(contract.start_date)} - {formatDate(contract.end_date!)}
                                                        </span>
                                                        <span className="meta-item">
                                                            <Clock size={14} />
                                                            {contract.weekly_hours}h/settimana
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Empty State */}
                            {contracts.length === 0 && (
                                <div className="empty-state">
                                    <div className="empty-state-icon">
                                        <FileText size={32} />
                                    </div>
                                    <h3 className="empty-state-title">Nessun contratto</h3>
                                    <p className="empty-state-description">
                                        Non ci sono contratti registrati per questo dipendente.
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            <style>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(15, 23, 42, 0.6);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: var(--z-modal);
          backdrop-filter: blur(8px);
          padding: var(--space-4);
        }

        .modal-container {
          background: var(--color-bg-primary);
          width: 100%;
          max-width: 680px;
          max-height: 90vh;
          border-radius: var(--radius-2xl);
          box-shadow: var(--shadow-2xl);
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--space-5) var(--space-6);
          border-bottom: 1px solid var(--color-border-light);
          background: linear-gradient(135deg, rgba(var(--color-primary-rgb), 0.05) 0%, transparent 100%);
        }

        .modal-header-content {
          display: flex;
          align-items: center;
          gap: var(--space-4);
        }

        .modal-icon {
          width: 48px;
          height: 48px;
          background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
          border-radius: var(--radius-xl);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
        }

        .modal-header h2 {
          font-size: var(--font-size-xl);
          font-weight: var(--font-weight-bold);
          margin-bottom: var(--space-1);
        }

        .modal-subtitle {
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
        }

        .modal-body {
          flex: 1;
          padding: var(--space-6);
          overflow-y: auto;
        }

        .alert {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3) var(--space-4);
          border-radius: var(--radius-lg);
          margin-bottom: var(--space-4);
        }

        .alert-error {
          background: var(--color-danger-bg);
          color: var(--color-danger);
          border: 1px solid rgba(239, 68, 68, 0.2);
        }

        .alert span {
          flex: 1;
        }

        .add-contract-form {
          margin-bottom: var(--space-6);
          overflow: hidden;
        }

        .form-header {
          padding: var(--space-4) var(--space-5);
          background: var(--color-bg-tertiary);
          border-bottom: 1px solid var(--color-border-light);
        }

        .form-header h3 {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--font-size-md);
          font-weight: var(--font-weight-semibold);
          color: var(--color-primary);
        }

        .form-body {
          padding: var(--space-5);
        }

        .form-row {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: var(--space-4);
          margin-bottom: var(--space-4);
        }

        .form-group {
          margin-bottom: var(--space-4);
        }

        .form-group:last-child {
          margin-bottom: 0;
        }

        .form-actions {
          display: flex;
          justify-content: flex-end;
          gap: var(--space-3);
          margin-top: var(--space-4);
          padding-top: var(--space-4);
          border-top: 1px solid var(--color-border-light);
        }

        .loading-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-8);
          color: var(--color-text-muted);
        }

        .contracts-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-6);
        }

        .contract-section {
          display: flex;
          flex-direction: column;
          gap: var(--space-3);
        }

        .section-label {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--font-size-xs);
          font-weight: var(--font-weight-semibold);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--color-text-muted);
        }

        .contract-card {
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-xl);
          padding: var(--space-4);
          transition: all var(--transition-fast);
        }

        .contract-card.active {
          background: var(--color-bg-primary);
          border-color: var(--color-success);
          box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
        }

        .contract-card.past {
          background: transparent;
          border: none;
          padding: 0;
          display: flex;
          gap: var(--space-4);
        }

        .timeline-connector {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding-top: var(--space-2);
        }

        .timeline-dot {
          width: 12px;
          height: 12px;
          background: var(--color-border-strong);
          border-radius: var(--radius-full);
          flex-shrink: 0;
        }

        .timeline-line {
          width: 2px;
          flex: 1;
          background: var(--color-border);
          margin-top: var(--space-2);
        }

        .contract-content {
          flex: 1;
          padding: var(--space-4);
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border-light);
          border-radius: var(--radius-lg);
        }

        .contract-header {
          display: flex;
          align-items: flex-start;
          gap: var(--space-3);
          margin-bottom: var(--space-3);
        }

        .contract-type-badge {
          padding: var(--space-1-5) var(--space-2-5);
          background: var(--color-bg-tertiary);
          border-radius: var(--radius-md);
          font-size: var(--font-size-xs);
          font-weight: var(--font-weight-bold);
          color: var(--color-text-secondary);
          text-transform: uppercase;
        }

        .contract-type-badge.active {
          background: var(--color-success-bg);
          color: var(--color-success);
        }

        .contract-main-info {
          flex: 1;
        }

        .contract-main-info h4 {
          font-size: var(--font-size-md);
          font-weight: var(--font-weight-semibold);
          margin-bottom: var(--space-1);
        }

        .contract-job-title {
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
        }

        .contract-meta {
          display: flex;
          flex-wrap: wrap;
          gap: var(--space-4);
        }

        .meta-item {
          display: flex;
          align-items: center;
          gap: var(--space-1-5);
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
        }

        .meta-item svg {
          color: var(--color-text-muted);
        }

        .contract-expanded {
          margin-top: var(--space-4);
          padding-top: var(--space-4);
          border-top: 1px solid var(--color-border-light);
        }

        .expanded-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--space-4);
          margin-bottom: var(--space-4);
        }

        .expanded-item {
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
        }

        .expanded-label {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .expanded-value {
          font-weight: var(--font-weight-semibold);
          color: var(--color-text-primary);
        }

        .expanded-actions {
          display: flex;
          gap: var(--space-2);
        }
      `}</style>
        </div>
    );
}
