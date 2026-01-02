/**
 * KRONOS - Company Closures Management Page
 * Premium Admin page for managing company-wide closures
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
    ArrowLeft,
    Plus,
    Edit,
    Trash2,
    Calendar,
    Building,
    Users,
    Check,
    X,
    Loader,
    ChevronLeft,
    ChevronRight,
} from 'lucide-react';
import { format, parseISO, differenceInDays } from 'date-fns';
import { it } from 'date-fns/locale';
import { useToast } from '../../context/ToastContext';
import { ConfirmModal } from '../../components/common';
import { configApi } from '../../services/api';
import type { CompanyClosure, CompanyClosureCreate } from '../../types';

export function CompanyClosuresPage() {
    const toast = useToast();
    const [closures, setClosures] = useState<CompanyClosure[]>([]);
    const [loading, setLoading] = useState(true);
    const [year, setYear] = useState(new Date().getFullYear());
    const [showForm, setShowForm] = useState(false);
    const [editingClosure, setEditingClosure] = useState<CompanyClosure | null>(null);
    const [saving, setSaving] = useState(false);

    // Form state
    const [formData, setFormData] = useState<CompanyClosureCreate>({
        name: '',
        description: '',
        start_date: '',
        end_date: '',
        closure_type: 'total',
        is_paid: true,
        consumes_leave_balance: false,
    });
    const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

    useEffect(() => {
        loadClosures();
    }, [year]);

    const loadClosures = async () => {
        setLoading(true);
        try {
            const response = await configApi.get(`/closures?year=${year}`);
            setClosures(response.data.items || []);
        } catch (error: any) {
            toast.error('Impossibile sincronizzare le chiusure');
            setClosures([]);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        try {
            if (editingClosure) {
                await configApi.put(`/closures/${editingClosure.id}`, formData);
                toast.success('Chiusura aziendale aggiornata');
            } else {
                await configApi.post('/closures', formData);
                toast.success('Nuova chiusura pianificata con successo');
            }
            setShowForm(false);
            setEditingClosure(null);
            resetForm();
            loadClosures();
        } catch (error: any) {
            toast.error(error.message || 'Errore critico durante il salvataggio');
        } finally {
            setSaving(false);
        }
    };

    const onRequestDelete = (id: string) => {
        setDeleteConfirmId(id);
    };

    const confirmDelete = async () => {
        if (!deleteConfirmId) return;
        try {
            await configApi.delete(`/closures/${deleteConfirmId}`);
            toast.success('Pianificazione rimossa');
            loadClosures();
        } catch (error: any) {
            toast.error(error.message || "Errore durante l'eliminazione");
        } finally {
            setDeleteConfirmId(null);
        }
    };

    const handleEdit = (closure: CompanyClosure) => {
        setEditingClosure(closure);
        setFormData({
            name: closure.name,
            description: closure.description || '',
            start_date: closure.start_date,
            end_date: closure.end_date,
            closure_type: closure.closure_type,
            is_paid: closure.is_paid,
            consumes_leave_balance: closure.consumes_leave_balance,
        });
        setShowForm(true);
    };

    const resetForm = () => {
        setFormData({
            name: '',
            description: '',
            start_date: '',
            end_date: '',
            closure_type: 'total',
            is_paid: true,
            consumes_leave_balance: false,
        });
        setEditingClosure(null);
    };

    const getDuration = (start: string, end: string) => {
        const days = differenceInDays(parseISO(end), parseISO(start)) + 1;
        return days === 1 ? '1 giorno' : `${days} giorni lavorativi`;
    };

    return (
        <div className="space-y-8 animate-fadeIn max-w-[1400px] mx-auto pb-12 px-4 sm:px-6 lg:px-8">
            {/* Standard Enterprise Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pt-6">
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <Link to="/admin/config" className="text-sm font-medium text-gray-500 hover:text-gray-900 flex items-center gap-1 transition-colors">
                            <ArrowLeft size={14} />
                            Configurazione
                        </Link>
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Chiusure Aziendali</h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Configura i periodi di inattività collettiva, festività patronali e ferie di reparto.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center bg-white border border-gray-300 rounded-lg shadow-sm">
                        <button onClick={() => setYear(year - 1)} className="p-2 hover:bg-gray-50 text-gray-500 transition-colors border-r border-gray-100">
                            <ChevronLeft size={16} />
                        </button>
                        <span className="px-4 text-sm font-semibold text-gray-900 min-w-[4rem] text-center">{year}</span>
                        <button onClick={() => setYear(year + 1)} className="p-2 hover:bg-gray-50 text-gray-500 transition-colors border-l border-gray-100">
                            <ChevronRight size={16} />
                        </button>
                    </div>
                    <button
                        onClick={() => { resetForm(); setShowForm(true); }}
                        className="btn btn-primary flex items-center gap-2"
                    >
                        <Plus size={18} />
                        Pianifica Chiusura
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="space-y-6">
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-20">
                        <Loader size={32} className="animate-spin text-primary mb-3" />
                        <span className="text-sm text-gray-500 font-medium">Caricamento calendario...</span>
                    </div>
                ) : closures.length === 0 ? (
                    <div className="text-center py-20 bg-white rounded-lg border border-dashed border-gray-300">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-50 mb-4">
                            <Calendar size={32} className="text-gray-400" />
                        </div>
                        <h3 className="text-lg font-medium text-gray-900">Nessuna chiusura programmata</h3>
                        <p className="text-gray-500 max-w-sm mx-auto mt-1 mb-6">
                            Non sono presenti chiusure rilevate per l'anno {year}.
                        </p>
                        <button
                            className="btn btn-outline"
                            onClick={() => { resetForm(); setShowForm(true); }}
                        >
                            Aggiungi Ora
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {closures.map(closure => (
                            <div key={closure.id}
                                className={`bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all p-6 relative overflow-hidden ${!closure.is_active ? 'opacity-60 bg-gray-50' : ''}`}
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg ${closure.closure_type === 'total' ? 'bg-indigo-50 text-indigo-600' : 'bg-cyan-50 text-cyan-600'}`}>
                                            {closure.closure_type === 'total' ? <Building size={20} /> : <Users size={20} />}
                                        </div>
                                        <div>
                                            <h4 className="text-base font-semibold text-gray-900 leading-tight">{closure.name}</h4>
                                            <span className="text-xs text-gray-500 capitalize">
                                                {closure.closure_type === 'total' ? 'Chiusura Totale' : 'Parziale'}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex gap-1">
                                        <button onClick={() => handleEdit(closure)} className="p-1.5 text-gray-400 hover:text-primary hover:bg-gray-100 rounded-md transition-colors">
                                            <Edit size={16} />
                                        </button>
                                        <button onClick={() => onRequestDelete(closure.id)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors">
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </div>

                                {closure.description && (
                                    <p className="text-sm text-gray-500 mb-5 line-clamp-2">{closure.description}</p>
                                )}

                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    <div className="bg-gray-50 p-3 rounded-lg">
                                        <span className="block text-xs text-gray-400 uppercase font-semibold mb-1">Periodo</span>
                                        <span className="text-sm font-medium text-gray-900 block truncate">
                                            {format(parseISO(closure.start_date), 'dd MMM', { locale: it })} - {format(parseISO(closure.end_date), 'dd MMM', { locale: it })}
                                        </span>
                                    </div>
                                    <div className="bg-gray-50 p-3 rounded-lg">
                                        <span className="block text-xs text-gray-400 uppercase font-semibold mb-1">Durata</span>
                                        <span className="text-sm font-medium text-gray-900 block">
                                            {getDuration(closure.start_date, closure.end_date)}
                                        </span>
                                    </div>
                                </div>

                                <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100">
                                    {closure.is_paid && (
                                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-emerald-50 text-emerald-700">
                                            <Check size={10} className="mr-1" /> Retribuita
                                        </span>
                                    )}
                                    {closure.consumes_leave_balance && (
                                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-amber-50 text-amber-700">
                                            <Check size={10} className="mr-1" /> Scalo Saldo
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Modal Form */}
            {showForm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm" onClick={() => { setShowForm(false); resetForm(); }}>
                    <div className="relative w-full max-w-xl bg-white rounded-xl shadow-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
                        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">{editingClosure ? 'Modifica Chiusura' : 'Nuova Chiusura'}</h3>
                                <p className="text-xs text-gray-500">Pianifica un periodo di chiusura aziendale.</p>
                            </div>
                            <button className="text-gray-400 hover:text-gray-600 transition-colors" onClick={() => { setShowForm(false); resetForm(); }}>
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="p-6 space-y-6">
                            <div className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-1.5">
                                        <label className="block text-xs font-semibold text-gray-500 uppercase">Titolo</label>
                                        <input
                                            type="text"
                                            className="input w-full"
                                            placeholder="Es. Ferragosto"
                                            value={formData.name}
                                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                                            required
                                        />
                                    </div>

                                    <div className="space-y-1.5">
                                        <label className="block text-xs font-semibold text-gray-500 uppercase">Tipo</label>
                                        <div className="flex bg-gray-100 p-1 rounded-lg">
                                            <button
                                                type="button"
                                                className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${formData.closure_type === 'total' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                                                onClick={() => setFormData(prev => ({ ...prev, closure_type: 'total' }))}
                                            >
                                                Totale
                                            </button>
                                            <button
                                                type="button"
                                                className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${formData.closure_type === 'partial' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                                                onClick={() => setFormData(prev => ({ ...prev, closure_type: 'partial' }))}
                                            >
                                                Parziale
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-1.5">
                                        <label className="block text-xs font-semibold text-gray-500 uppercase">Da</label>
                                        <input
                                            type="date"
                                            className="input w-full"
                                            value={formData.start_date}
                                            onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="block text-xs font-semibold text-gray-500 uppercase">A</label>
                                        <input
                                            type="date"
                                            className="input w-full"
                                            value={formData.end_date}
                                            onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
                                            min={formData.start_date}
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-1.5">
                                    <label className="block text-xs font-semibold text-gray-500 uppercase">Descrizione (Opzionale)</label>
                                    <textarea
                                        className="input w-full min-h-[80px] py-2 resize-none"
                                        placeholder="Note aggiuntive..."
                                        value={formData.description}
                                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                                    />
                                </div>

                                <div className="pt-2 flex flex-col gap-3">
                                    <label className="flex items-center justify-between p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                                        <div>
                                            <span className="block text-sm font-medium text-gray-900">Chiurura Retribuita</span>
                                            <span className="block text-xs text-gray-500">L'azienda copre i costi della giornata</span>
                                        </div>
                                        <input
                                            type="checkbox"
                                            className="toggle toggle-primary toggle-sm"
                                            checked={formData.is_paid}
                                            onChange={() => setFormData(prev => ({ ...prev, is_paid: !prev.is_paid }))}
                                        />
                                    </label>

                                    <label className="flex items-center justify-between p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                                        <div>
                                            <span className="block text-sm font-medium text-gray-900">Scala dai permessi/ferie</span>
                                            <span className="block text-xs text-gray-500">Riduce il monte ore/giorni dei dipendenti</span>
                                        </div>
                                        <input
                                            type="checkbox"
                                            className="toggle toggle-warning toggle-sm"
                                            checked={formData.consumes_leave_balance}
                                            onChange={() => setFormData(prev => ({ ...prev, consumes_leave_balance: !prev.consumes_leave_balance }))}
                                        />
                                    </label>
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                                <button type="button" className="btn btn-ghost" onClick={() => { setShowForm(false); resetForm(); }}>
                                    Annulla
                                </button>
                                <button type="submit" className="btn btn-primary" disabled={saving}>
                                    {saving ? <Loader className="animate-spin mr-2" size={16} /> : null}
                                    {editingClosure ? 'Salva Modifiche' : 'Crea Chiusura'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <ConfirmModal
                isOpen={!!deleteConfirmId}
                onClose={() => setDeleteConfirmId(null)}
                onConfirm={confirmDelete}
                title="Elimina Chiusura"
                message="Questa azione rimuoverà la chiusura e potrebbe impattare i calendari dipendenti. Sei sicuro di voler procedere?"
                variant="danger"
                confirmLabel="Elimina"
            />
        </div>
    );
}

export default CompanyClosuresPage;
