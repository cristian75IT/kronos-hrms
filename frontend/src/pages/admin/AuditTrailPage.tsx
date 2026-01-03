import React, { useState } from 'react';
import {
    History,
    Search,
    User,
    Clock,
    FileDiff,
    Database,
    AlertCircle
} from 'lucide-react';
import { auditService } from '../../services/audit.service';
import { Button } from '../../components/common';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { useToast } from '../../context/ToastContext';

export function AuditTrailPage() {
    const [entityType, setEntityType] = useState('LeaveRequest');
    const [entityId, setEntityId] = useState('');
    const [history, setHistory] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [searched, setSearched] = useState(false);
    const toast = useToast();

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!entityId) {
            toast.error('Inserisci un ID valid');
            return;
        }

        setIsLoading(true);
        setSearched(true);
        try {
            const data = await auditService.getEntityHistory(entityType, entityId);
            setHistory(data);
        } catch (error) {
            console.error(error);
            toast.error('Errore nel recupero della storia');
            setHistory([]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="space-y-6 animate-fadeIn max-w-5xl mx-auto pb-12">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <History className="text-indigo-600" />
                        Audit Trail
                    </h1>
                    <p className="text-sm text-gray-500">Cronologia modifiche e versionamento entità</p>
                </div>
            </div>

            {/* Search Box */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4 items-end">
                    <div className="flex-1 w-full">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Entità</label>
                        <select
                            value={entityType}
                            onChange={(e) => setEntityType(e.target.value)}
                            className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        >
                            <option value="LeaveRequest">Richiesta Ferie</option>
                            <option value="BusinessTrip">Trasferta</option>
                            <option value="ExpenseReport">Nota Spese</option>
                            <option value="EmployeeContract">Contratto</option>
                            <option value="User">Utente</option>
                        </select>
                    </div>
                    <div className="flex-[2] w-full">
                        <label className="block text-sm font-medium text-gray-700 mb-1">ID Entità (UUID)</label>
                        <div className="relative">
                            <input
                                type="text"
                                value={entityId}
                                onChange={(e) => setEntityId(e.target.value)}
                                placeholder="es. 123e4567-e89b-12d3-a456-426614174000"
                                className="w-full pl-10 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 font-mono text-sm"
                            />
                            <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
                        </div>
                    </div>
                    <Button type="submit" variant="primary" isLoading={isLoading} disabled={!entityId}>
                        Cerca Storia
                    </Button>
                </form>
            </div>

            {/* Results */}
            {searched && (
                <div className="space-y-6">
                    {history.length === 0 ? (
                        <div className="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                            <Database className="mx-auto h-12 w-12 text-gray-300 mb-3" />
                            <h3 className="text-lg font-medium text-gray-900">Nessuna storia trovata</h3>
                            <p className="text-gray-500">Non ci sono modifiche registrate per questa entità.</p>
                        </div>
                    ) : (
                        <div className="relative border-l-2 border-indigo-200 ml-4 space-y-8 pl-8 py-2">
                            {history.map((change, index) => (
                                <div key={change.id || index} className="relative group">
                                    {/* Timeline Dot */}
                                    <div className="absolute -left-[41px] top-0 h-5 w-5 rounded-full border-4 border-white bg-indigo-600 shadow-sm group-hover:scale-125 transition-transform" />

                                    <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                                        <div className="flex justify-between items-start mb-3">
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-bold text-gray-900 text-lg">Versione {change.version}</span>
                                                    <span className="text-xs font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                                                        {change.id?.substring(0, 8)}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                                                    <Clock size={14} />
                                                    {format(new Date(change.changed_at), 'dd MMM yyyy, HH:mm:ss', { locale: it })}
                                                </p>
                                            </div>
                                            <div className="text-right">
                                                <div className="flex items-center gap-1.5 text-sm font-medium text-gray-900 justify-end">
                                                    <User size={14} className="text-indigo-600" />
                                                    {change.changed_by_name || 'Sistema'}
                                                </div>
                                                <p className="text-xs text-gray-400 mt-0.5 capitalize">{change.change_type}</p>
                                            </div>
                                        </div>

                                        {change.changes && Object.keys(change.changes).length > 0 ? (
                                            <div className="mt-4 bg-gray-50 rounded-lg p-4 border border-gray-100">
                                                <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                                                    <FileDiff size={14} /> Modifiche Rilevate
                                                </h4>
                                                <div className="space-y-3">
                                                    {Object.entries(change.changes).map(([field, diff]: [string, any]) => (
                                                        <div key={field} className="grid grid-cols-[120px,1fr] gap-4 text-sm border-b border-gray-200 last:border-0 pb-2 last:pb-0">
                                                            <div className="font-medium text-gray-700 font-mono truncate" title={field}>{field}</div>
                                                            <div className="grid grid-cols-2 gap-4">
                                                                <div className="text-red-600 bg-red-50 px-2 py-1 rounded break-all">
                                                                    <span className="text-[10px] text-red-400 font-bold uppercase block">Prima</span>
                                                                    {JSON.stringify(diff.old)}
                                                                </div>
                                                                <div className="text-green-600 bg-green-50 px-2 py-1 rounded break-all">
                                                                    <span className="text-[10px] text-green-400 font-bold uppercase block">Dopo</span>
                                                                    {JSON.stringify(diff.new)}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="mt-4 flex items-center gap-2 text-sm text-gray-500 italic bg-gray-50 p-3 rounded-lg">
                                                <AlertCircle size={16} /> Nessuna modifica field-level registrata
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default AuditTrailPage;
