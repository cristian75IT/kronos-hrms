import { useState, useEffect } from 'react';
import { userService } from '../../services/userService';
import type { EmployeeContract, ContractType, EmployeeContractCreate } from '../../types';
import { Plus, X, Calendar, Briefcase, Clock, FileText } from 'lucide-react';

interface ContractHistoryProps {
    userId: string;
    onClose: () => void;
}

export function ContractHistory({ userId, onClose }: ContractHistoryProps) {
    const [contracts, setContracts] = useState<EmployeeContract[]>([]);
    const [contractTypes, setContractTypes] = useState<ContractType[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);

    // Form state
    const [newContract, setNewContract] = useState<Partial<EmployeeContractCreate>>({
        weekly_hours: 40,
        start_date: new Date().toISOString().split('T')[0]
    });

    useEffect(() => {
        loadData();
    }, [userId]);

    const loadData = async () => {
        setIsLoading(true);
        try {
            const [contractsData, typesData] = await Promise.all([
                userService.getContracts(userId),
                userService.getContractTypes()
            ]);
            setContracts(contractsData);
            setContractTypes(typesData);
        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async () => {
        if (!newContract.contract_type_id || !newContract.start_date) return;

        try {
            await userService.addContract(userId, newContract as EmployeeContractCreate);
            setIsAdding(false);
            setNewContract({ weekly_hours: 40, start_date: new Date().toISOString().split('T')[0] });
            loadData();
        } catch (error) {
            console.error("Failed to save", error);
        }
    };

    // Helper per trovare nome tipo
    const getTypeName = (id: string) => contractTypes.find(t => t.id === id)?.name || id;

    return (
        <div className="contract-history-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
            <div className="contract-history-modal animate-slideUp">
                <div className="modal-header">
                    <h2>Storico Contratti</h2>
                    <button onClick={onClose} className="btn-icon"><X size={20} /></button>
                </div>

                <div className="modal-body">
                    {/* Toolbar */}
                    {!isAdding && (
                        <div className="mb-4">
                            <button className="btn btn-primary btn-sm" onClick={() => setIsAdding(true)}>
                                <Plus size={16} /> Nuovo Contratto
                            </button>
                        </div>
                    )}

                    {/* Add Form */}
                    {isAdding && (
                        <div className="add-form card p-4 mb-4 bg-base-100 border border-base-300">
                            <h3 className="text-sm font-bold mb-3">Nuovo Contratto</h3>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="form-group">
                                    <label>Tipo Contratto</label>
                                    <select
                                        className="input"
                                        value={newContract.contract_type_id || ''}
                                        onChange={e => setNewContract({ ...newContract, contract_type_id: e.target.value })}
                                    >
                                        <option value="">Seleziona...</option>
                                        {contractTypes.map(t => (
                                            <option key={t.id} value={t.id}>{t.name} ({t.code})</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Data Inizio</label>
                                    <input
                                        type="date"
                                        className="input"
                                        value={newContract.start_date}
                                        onChange={e => setNewContract({ ...newContract, start_date: e.target.value })}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Data Fine (Opzionale)</label>
                                    <input
                                        type="date"
                                        className="input"
                                        value={newContract.end_date || ''}
                                        onChange={e => setNewContract({ ...newContract, end_date: e.target.value })}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Ore Settimanali</label>
                                    <input
                                        type="number"
                                        className="input"
                                        value={newContract.weekly_hours}
                                        onChange={e => setNewContract({ ...newContract, weekly_hours: parseInt(e.target.value) })}
                                    />
                                </div>
                                <div className="form-group col-span-2">
                                    <label>Mansione (Job Title)</label>
                                    <input
                                        type="text"
                                        className="input"
                                        value={newContract.job_title || ''}
                                        onChange={e => setNewContract({ ...newContract, job_title: e.target.value })}
                                        placeholder="es. Software Engineer"
                                    />
                                </div>
                            </div>
                            <div className="flex justify-end gap-2 mt-4">
                                <button className="btn btn-ghost btn-sm" onClick={() => setIsAdding(false)}>Annulla</button>
                                <button className="btn btn-primary btn-sm" onClick={handleSave}>Salva</button>
                            </div>
                        </div>
                    )}

                    {/* List */}
                    {isLoading ? (
                        <div className="spinner-sm mx-auto my-4" />
                    ) : (
                        <div className="contracts-timeline">
                            {contracts.length === 0 ? (
                                <p className="text-center text-gray-500 py-4">Nessun contratto trovato.</p>
                            ) : (contracts.map((contract) => (
                                <div key={contract.id} className={`contract-card ${!contract.end_date ? 'active' : ''}`}>
                                    <div className="contract-icon">
                                        <Briefcase size={18} />
                                    </div>
                                    <div className="contract-details">
                                        <h4>{getTypeName(contract.contract_type_id)}</h4>
                                        <p className="contract-meta">
                                            <Calendar size={12} />
                                            {new Date(contract.start_date).toLocaleDateString()}
                                            {contract.end_date ? ` - ${new Date(contract.end_date).toLocaleDateString()}` : ' - Presente'}
                                        </p>
                                        <div className="flex gap-3 mt-1 text-xs text-secondary-500">
                                            {contract.weekly_hours && (
                                                <span className="flex items-center gap-1">
                                                    <Clock size={12} /> {contract.weekly_hours}h
                                                </span>
                                            )}
                                            {contract.job_title && (
                                                <span className="flex items-center gap-1">
                                                    <FileText size={12} /> {contract.job_title}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    {!contract.end_date && <span className="badge badge-success text-xs">Attivo</span>}
                                </div>
                            )))}
                        </div>
                    )}
                </div>
            </div>

            <style>{`
                .contract-history-overlay {
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    backdrop-filter: blur(4px);
                }
                .contract-history-modal {
                    background: var(--color-bg-primary);
                    width: 600px;
                    max-width: 90vw;
                    max-height: 85vh;
                    border-radius: var(--radius-xl);
                    box-shadow: 0 20px 40px rgba(0,0,0,0.2);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }
                .modal-header {
                    padding: var(--space-4);
                    border-bottom: 1px solid var(--color-border-light);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .modal-body {
                    padding: var(--space-4);
                    overflow-y: auto;
                }
                
                .contracts-timeline {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-3);
                    position: relative;
                }
                
                .contract-card {
                    display: flex;
                    align-items: flex-start;
                    gap: var(--space-3);
                    padding: var(--space-3);
                    border: 1px solid var(--color-border-light);
                    border-radius: var(--radius-lg);
                    background: var(--color-bg-secondary);
                }
                .contract-card.active {
                    border-color: var(--color-primary);
                    background: var(--color-bg-primary);
                }
                .contract-icon {
                    width: 36px;
                    height: 36px;
                    background: var(--color-bg-tertiary);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--color-text-primary);
                }
                .contract-card.active .contract-icon {
                    background: var(--color-primary-light);
                    color: var(--color-primary);
                }
                .contract-details {
                    flex: 1;
                }
                .contract-details h4 {
                    font-weight: 600;
                    margin-bottom: 2px;
                }
                .contract-meta {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 0.85rem;
                    color: var(--color-text-secondary);
                }
                
                .form-group label {
                    display: block;
                    font-size: 0.8rem;
                    margin-bottom: 4px;
                    color: var(--color-text-secondary);
                }
                .input {
                    width: 100%;
                    padding: 8px 12px;
                    border-radius: var(--radius-md);
                    border: 1px solid var(--color-border-light);
                    background: var(--color-bg-primary);
                }
            `}</style>
        </div>
    );
}
