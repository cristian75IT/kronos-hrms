/**
 * KRONOS - Training Management Component
 * Management of safety training records and certifications (D.Lgs. 81/08)
 */
import { useState, useEffect } from 'react';
import { userService } from '../../services/userService';
import type { EmployeeTraining, EmployeeTrainingCreate, EmployeeTrainingUpdate } from '../../types';
import {
    Plus,
    X,
    GraduationCap,
    CheckCircle,
    AlertCircle,
    Edit,
    Trash2,
    Shield
} from 'lucide-react';

interface TrainingManagementProps {
    userId: string;
}

export function TrainingManagement({ userId }: TrainingManagementProps) {
    const [trainings, setTrainings] = useState<EmployeeTraining[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Form state
    const [formData, setFormData] = useState<Partial<EmployeeTrainingCreate>>({
        user_id: userId,
        training_type: '',
        description: '',
        issue_date: new Date().toISOString().split('T')[0],
        hours: 4,
    });

    useEffect(() => {
        loadData();
    }, [userId]);

    const loadData = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await userService.getTrainings(userId);
            setTrainings(data);
        } catch (err: any) {
            setError('Errore nel caricamento dei dati formativi');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async () => {
        if (!formData.training_type || !formData.issue_date) {
            setError('Compila i campi obbligatori (Tipo e Data Emissione)');
            return;
        }

        try {
            if (editingId) {
                await userService.updateTraining(editingId, formData as EmployeeTrainingUpdate);
            } else {
                await userService.createTraining(formData as EmployeeTrainingCreate);
            }
            setIsAdding(false);
            setEditingId(null);
            setFormData({
                user_id: userId,
                training_type: '',
                description: '',
                issue_date: new Date().toISOString().split('T')[0],
                hours: 4,
            });
            loadData();
        } catch (err: any) {
            setError(err.message || 'Errore durante il salvataggio');
        }
    };

    const handleEdit = (training: EmployeeTraining) => {
        setEditingId(training.id);
        setFormData({
            user_id: userId,
            training_type: training.training_type,
            description: training.description,
            issue_date: training.issue_date,
            expiry_date: training.expiry_date,
            certificate_id: training.certificate_id,
            hours: training.hours,
            provider: training.provider,
        });
        setIsAdding(true);
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm('Sei sicuro di voler eliminare questa registrazione?')) return;
        try {
            await userService.deleteTraining(id);
            loadData();
        } catch (err: any) {
            setError('Errore durante l\'eliminazione');
        }
    };

    const formatDate = (dateStr: string) => {
        try {
            const date = new Date(dateStr);
            if (isNaN(date.getTime())) return '-';
            return date.toLocaleDateString('it-IT', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
            });
        } catch (e) {
            return '-';
        }
    };

    return (
        <div className="animate-fadeIn space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="font-bold text-lg text-gray-900 flex items-center gap-2">
                    <Shield className="text-indigo-600" size={20} />
                    Formazione Sicurezza e Certificazioni
                </h3>
                {!isAdding && (
                    <button
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold flex items-center gap-2 shadow-sm transition-all"
                        onClick={() => {
                            setIsAdding(true);
                            setEditingId(null);
                            setFormData({
                                user_id: userId,
                                training_type: '',
                                description: '',
                                issue_date: new Date().toISOString().split('T')[0],
                                hours: 4,
                            });
                        }}
                    >
                        <Plus size={16} /> Aggiungi Corso
                    </button>
                )}
            </div>

            {error && (
                <div className="p-4 bg-red-50 text-red-700 border border-red-100 rounded-xl flex items-center gap-3">
                    <AlertCircle size={18} />
                    <span className="text-sm font-medium">{error}</span>
                </div>
            )}

            {isAdding && (
                <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm animate-fadeInUp">
                    <div className="flex justify-between items-center mb-6">
                        <h4 className="font-bold text-gray-900">{editingId ? 'Modifica Registrazione' : 'Nuova Registrazione Formativa'}</h4>
                        <button onClick={() => setIsAdding(false)} className="p-1 hover:bg-gray-100 rounded-full">
                            <X size={18} className="text-gray-400" />
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-gray-500 uppercase">Tipo Formazione *</label>
                            <select
                                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500/20 shadow-sm"
                                value={formData.training_type}
                                onChange={e => setFormData({ ...formData, training_type: e.target.value })}
                            >
                                <option value="">Seleziona...</option>
                                <option value="Generale">Formazione Generale (4h)</option>
                                <option value="Specifica Basso">Rischio Basso (4h)</option>
                                <option value="Specifica Medio">Rischio Medio (8h)</option>
                                <option value="Specifica Alto">Rischio Alto (12h)</option>
                                <option value="Aggiornamento">Aggiornamento Quinquennale (6h)</option>
                                <option value="Antincendio">Addetto Antincendio</option>
                                <option value="Primo Soccorso">Addetto Primo Soccorso</option>
                                <option value="RLS">RLS</option>
                                <option value="Altro">Altro / Specialistico</option>
                            </select>
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-gray-500 uppercase">Ore</label>
                            <input
                                type="number"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                value={formData.hours || ''}
                                onChange={e => setFormData({ ...formData, hours: parseInt(e.target.value) || 0 })}
                            />
                        </div>
                    </div>

                    <div className="space-y-1.5 mb-4">
                        <label className="text-xs font-bold text-gray-500 uppercase">Descrizione / Ente</label>
                        <input
                            type="text"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                            value={formData.description || ''}
                            onChange={e => setFormData({ ...formData, description: e.target.value })}
                            placeholder="es. Formazione Specifica - Rischio Basso (Ente Formatore)"
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-gray-500 uppercase">Data Emissione *</label>
                            <input
                                type="date"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                value={formData.issue_date}
                                onChange={e => setFormData({ ...formData, issue_date: e.target.value })}
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-gray-500 uppercase">Data Scadenza</label>
                            <input
                                type="date"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                value={formData.expiry_date || ''}
                                onChange={e => setFormData({ ...formData, expiry_date: e.target.value || undefined })}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-gray-500 uppercase">ID Certificato / Protocollo</label>
                            <input
                                type="text"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                value={formData.certificate_id || ''}
                                onChange={e => setFormData({ ...formData, certificate_id: e.target.value })}
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-gray-500 uppercase">Provider / Docente</label>
                            <input
                                type="text"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm"
                                value={formData.provider || ''}
                                onChange={e => setFormData({ ...formData, provider: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="flex justify-end gap-3">
                        <button onClick={() => setIsAdding(false)} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg">Annulla</button>
                        <button onClick={handleSave} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold flex items-center gap-2">
                            <CheckCircle size={16} /> Salva Registrazione
                        </button>
                    </div>
                </div>
            )}

            {isLoading ? (
                <div className="flex flex-col items-center py-12 gap-3">
                    <div className="w-10 h-10 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin" />
                    <p className="text-sm text-gray-400">Caricamento corsi...</p>
                </div>
            ) : trainings.length === 0 ? (
                <div className="bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl p-12 text-center">
                    <GraduationCap className="mx-auto text-gray-300 mb-4" size={48} />
                    <h4 className="text-gray-500 font-medium">Nessuna formazione registrata</h4>
                    <p className="text-sm text-gray-400 mt-2">I corsi obbligatori D.Lgs. 81/08 non sono ancora stati caricati.</p>
                </div>
            ) : (
                <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-50 border-b border-gray-100">
                                <th className="px-6 py-4 text-[0.65rem] font-black text-gray-400 uppercase tracking-widest">Corso / Certificazione</th>
                                <th className="px-6 py-4 text-[0.65rem] font-black text-gray-400 uppercase tracking-widest">Emissione</th>
                                <th className="px-6 py-4 text-[0.65rem] font-black text-gray-400 uppercase tracking-widest">Scadenza</th>
                                <th className="px-6 py-4 text-[0.65rem] font-black text-gray-400 uppercase tracking-widest text-center">Ore</th>
                                <th className="px-6 py-4 text-[0.65rem] font-black text-gray-400 uppercase tracking-widest text-right">Azioni</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {trainings.map(t => (
                                <tr key={t.id} className="hover:bg-gray-50/50 transition-colors group">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                                                <GraduationCap size={18} />
                                            </div>
                                            <div>
                                                <div className="font-bold text-gray-900">{t.training_type}</div>
                                                <div className="text-xs text-gray-500 truncate max-w-[200px]">{t.description || t.provider || '-'}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm font-medium text-gray-600 whitespace-nowrap">
                                        {formatDate(t.issue_date)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {t.expiry_date ? (
                                            <div className={`text-sm font-bold ${new Date(t.expiry_date) < new Date() ? 'text-red-600' : 'text-emerald-600'
                                                }`}>
                                                {formatDate(t.expiry_date)}
                                            </div>
                                        ) : (
                                            <span className="text-xs text-gray-400 italic">Senza scadenza</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-bold">
                                            {t.hours}h
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button onClick={() => handleEdit(t)} className="p-1.5 hover:bg-gray-100 rounded text-gray-500" title="Modifica">
                                                <Edit size={16} />
                                            </button>
                                            <button onClick={() => handleDelete(t.id)} className="p-1.5 hover:bg-red-50 rounded text-red-500" title="Elimina">
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
