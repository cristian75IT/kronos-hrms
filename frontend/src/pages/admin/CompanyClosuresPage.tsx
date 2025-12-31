/**
 * KRONOS - Company Closures Management Page
 * Admin page for managing company-wide closures (total or partial)
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
    AlertTriangle,
    Check,
    X,
    Clock,
    Loader,
} from 'lucide-react';
import { format, parseISO, differenceInDays } from 'date-fns';
import { it } from 'date-fns/locale';
import { useToast } from '../../context/ToastContext';
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

    // Load closures
    useEffect(() => {
        loadClosures();
    }, [year]);

    const loadClosures = async () => {
        setLoading(true);
        try {
            const response = await configApi.get(`/closures?year=${year}`);
            setClosures(response.data.items || []);
        } catch (error: any) {
            toast.error('Errore nel caricamento delle chiusure');
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
                toast.success('Chiusura aggiornata');
            } else {
                await configApi.post('/closures', formData);
                toast.success('Chiusura creata');
            }
            setShowForm(false);
            setEditingClosure(null);
            resetForm();
            loadClosures();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante il salvataggio');
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Sei sicuro di voler eliminare questa chiusura?')) return;
        try {
            await configApi.delete(`/closures/${id}`);
            toast.success('Chiusura eliminata');
            loadClosures();
        } catch (error: any) {
            toast.error(error.message || 'Errore durante l\'eliminazione');
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

    const getClosureIcon = (type: string) => {
        return type === 'total' ? <Building size={18} /> : <Users size={18} />;
    };

    const getDuration = (start: string, end: string) => {
        const days = differenceInDays(parseISO(end), parseISO(start)) + 1;
        return days === 1 ? '1 giorno' : `${days} giorni`;
    };

    return (
        <div className="closures-page animate-fadeIn">
            {/* Header */}
            <div className="page-header">
                <div className="header-left">
                    <Link to="/admin/config" className="btn btn-ghost btn-icon">
                        <ArrowLeft size={20} />
                    </Link>
                    <div>
                        <h1 className="page-title">Chiusure Aziendali</h1>
                        <p className="page-subtitle">Gestisci le chiusure aziendali totali o parziali</p>
                    </div>
                </div>
                <div className="header-actions">
                    <select
                        className="input input-sm"
                        value={year}
                        onChange={(e) => setYear(parseInt(e.target.value))}
                        style={{ width: '120px' }}
                    >
                        {[2024, 2025, 2026].map(y => (
                            <option key={y} value={y}>{y}</option>
                        ))}
                    </select>
                    <button
                        className="btn btn-primary"
                        onClick={() => { resetForm(); setShowForm(true); }}
                    >
                        <Plus size={18} />
                        Nuova Chiusura
                    </button>
                </div>
            </div>

            {/* Closures List */}
            <div className="card">
                {loading ? (
                    <div className="loading-state">
                        <Loader size={32} className="animate-spin" />
                        <p>Caricamento chiusure...</p>
                    </div>
                ) : closures.length === 0 ? (
                    <div className="empty-state">
                        <Calendar size={48} />
                        <h3>Nessuna chiusura per il {year}</h3>
                        <p>Non sono state configurate chiusure aziendali per quest'anno.</p>
                        <button
                            className="btn btn-primary"
                            onClick={() => { resetForm(); setShowForm(true); }}
                        >
                            <Plus size={18} />
                            Aggiungi Chiusura
                        </button>
                    </div>
                ) : (
                    <div className="closures-list">
                        {closures.map(closure => (
                            <div key={closure.id} className={`closure-item ${!closure.is_active ? 'inactive' : ''}`}>
                                <div className="closure-icon" style={{
                                    background: closure.closure_type === 'total'
                                        ? 'linear-gradient(135deg, #9333ea, #7c3aed)'
                                        : 'linear-gradient(135deg, #06b6d4, #0891b2)'
                                }}>
                                    {getClosureIcon(closure.closure_type)}
                                </div>
                                <div className="closure-info">
                                    <div className="closure-header">
                                        <h4 className="closure-name">{closure.name}</h4>
                                        <div className="closure-badges">
                                            <span className={`badge badge-${closure.closure_type === 'total' ? 'primary' : 'info'}`}>
                                                {closure.closure_type === 'total' ? 'Totale' : 'Parziale'}
                                            </span>
                                            {closure.is_paid && (
                                                <span className="badge badge-success">Retribuita</span>
                                            )}
                                            {closure.consumes_leave_balance && (
                                                <span className="badge badge-warning">Scala Ferie</span>
                                            )}
                                        </div>
                                    </div>
                                    {closure.description && (
                                        <p className="closure-description">{closure.description}</p>
                                    )}
                                    <div className="closure-meta">
                                        <span className="meta-item">
                                            <Calendar size={14} />
                                            {format(parseISO(closure.start_date), 'd MMMM yyyy', { locale: it })}
                                            {closure.start_date !== closure.end_date && (
                                                <> - {format(parseISO(closure.end_date), 'd MMMM yyyy', { locale: it })}</>
                                            )}
                                        </span>
                                        <span className="meta-item">
                                            <Clock size={14} />
                                            {getDuration(closure.start_date, closure.end_date)}
                                        </span>
                                    </div>
                                </div>
                                <div className="closure-actions">
                                    <button
                                        className="btn btn-ghost btn-icon btn-sm"
                                        onClick={() => handleEdit(closure)}
                                    >
                                        <Edit size={16} />
                                    </button>
                                    <button
                                        className="btn btn-ghost btn-icon btn-sm text-danger"
                                        onClick={() => handleDelete(closure.id)}
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Form Modal */}
            {showForm && (
                <div className="modal-overlay" onClick={() => { setShowForm(false); resetForm(); }}>
                    <div className="modal-container modal-lg animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>{editingClosure ? 'Modifica Chiusura' : 'Nuova Chiusura Aziendale'}</h3>
                            <button className="btn btn-ghost btn-icon" onClick={() => { setShowForm(false); resetForm(); }}>
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-grid">
                                    <div className="form-group">
                                        <label className="input-label input-label-required">Nome Chiusura</label>
                                        <input
                                            type="text"
                                            className="input"
                                            placeholder="es. Chiusura Natalizia, Ferie Collettive Agosto"
                                            value={formData.name}
                                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                                            required
                                        />
                                    </div>

                                    <div className="form-group">
                                        <label className="input-label">Tipo Chiusura</label>
                                        <div className="radio-group">
                                            <label className="radio-card">
                                                <input
                                                    type="radio"
                                                    name="closure_type"
                                                    checked={formData.closure_type === 'total'}
                                                    onChange={() => setFormData(prev => ({ ...prev, closure_type: 'total' }))}
                                                />
                                                <div className="radio-content">
                                                    <Building size={20} />
                                                    <span className="radio-label">Totale</span>
                                                    <span className="radio-desc">Tutta l'azienda</span>
                                                </div>
                                            </label>
                                            <label className="radio-card">
                                                <input
                                                    type="radio"
                                                    name="closure_type"
                                                    checked={formData.closure_type === 'partial'}
                                                    onChange={() => setFormData(prev => ({ ...prev, closure_type: 'partial' }))}
                                                />
                                                <div className="radio-content">
                                                    <Users size={20} />
                                                    <span className="radio-label">Parziale</span>
                                                    <span className="radio-desc">Solo alcuni reparti</span>
                                                </div>
                                            </label>
                                        </div>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label className="input-label">Descrizione (opzionale)</label>
                                    <textarea
                                        className="input"
                                        placeholder="Dettagli aggiuntivi sulla chiusura..."
                                        value={formData.description}
                                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                                        rows={3}
                                    />
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="input-label input-label-required">Data Inizio</label>
                                        <input
                                            type="date"
                                            className="input"
                                            value={formData.start_date}
                                            onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="input-label input-label-required">Data Fine</label>
                                        <input
                                            type="date"
                                            className="input"
                                            value={formData.end_date}
                                            onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
                                            min={formData.start_date}
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="form-section">
                                    <h4 className="section-title">Opzioni Retribuzione</h4>
                                    <div className="checkbox-group">
                                        <label className="checkbox-item">
                                            <input
                                                type="checkbox"
                                                checked={formData.is_paid}
                                                onChange={(e) => setFormData(prev => ({ ...prev, is_paid: e.target.checked }))}
                                            />
                                            <div className="checkbox-content">
                                                <span className="checkbox-label">Chiusura retribuita</span>
                                                <span className="checkbox-desc">I dipendenti riceveranno regolare retribuzione</span>
                                            </div>
                                        </label>
                                        <label className="checkbox-item">
                                            <input
                                                type="checkbox"
                                                checked={formData.consumes_leave_balance}
                                                onChange={(e) => setFormData(prev => ({ ...prev, consumes_leave_balance: e.target.checked }))}
                                            />
                                            <div className="checkbox-content">
                                                <span className="checkbox-label">Scala saldo ferie</span>
                                                <span className="checkbox-desc">I giorni verranno sottratti dal monte ferie</span>
                                            </div>
                                        </label>
                                    </div>
                                </div>

                                {!formData.is_paid && (
                                    <div className="alert alert-warning">
                                        <AlertTriangle size={18} />
                                        <span>Attenzione: una chiusura non retribuita potrebbe richiedere comunicazioni sindacali.</span>
                                    </div>
                                )}
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-ghost" onClick={() => { setShowForm(false); resetForm(); }}>
                                    Annulla
                                </button>
                                <button type="submit" className="btn btn-primary" disabled={saving}>
                                    {saving ? <Loader size={16} className="animate-spin" /> : <Check size={16} />}
                                    {editingClosure ? 'Aggiorna' : 'Crea Chiusura'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <style>{`
        .closures-page {
          display: flex;
          flex-direction: column;
          gap: var(--space-6);
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: var(--space-3);
        }

        .page-title {
          font-size: var(--font-size-2xl);
          font-weight: var(--font-weight-bold);
          margin-bottom: var(--space-1);
        }

        .page-subtitle {
          color: var(--color-text-muted);
          font-size: var(--font-size-sm);
        }

        .header-actions {
          display: flex;
          gap: var(--space-3);
        }

        .loading-state,
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: var(--space-12);
          text-align: center;
          color: var(--color-text-muted);
          gap: var(--space-4);
        }

        .empty-state h3 {
          color: var(--color-text-primary);
          margin: 0;
        }

        .closures-list {
          display: flex;
          flex-direction: column;
        }

        .closure-item {
          display: flex;
          align-items: flex-start;
          gap: var(--space-4);
          padding: var(--space-4);
          border-bottom: 1px solid var(--color-border-light);
          transition: all var(--transition-fast);
        }

        .closure-item:hover {
          background: var(--color-bg-hover);
        }

        .closure-item:last-child {
          border-bottom: none;
        }

        .closure-item.inactive {
          opacity: 0.5;
        }

        .closure-icon {
          width: 44px;
          height: 44px;
          border-radius: var(--radius-lg);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          flex-shrink: 0;
        }

        .closure-info {
          flex: 1;
          min-width: 0;
        }

        .closure-header {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          margin-bottom: var(--space-1);
          flex-wrap: wrap;
        }

        .closure-name {
          font-weight: var(--font-weight-semibold);
          margin: 0;
        }

        .closure-badges {
          display: flex;
          gap: var(--space-2);
        }

        .closure-description {
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
          margin: 0 0 var(--space-2) 0;
        }

        .closure-meta {
          display: flex;
          gap: var(--space-4);
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .meta-item {
          display: flex;
          align-items: center;
          gap: var(--space-1);
        }

        .closure-actions {
          display: flex;
          gap: var(--space-1);
        }

        /* Form Styles */
        .form-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: var(--space-4);
        }

        @media (max-width: 640px) {
          .form-grid {
            grid-template-columns: 1fr;
          }
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--space-4);
        }

        .radio-group {
          display: flex;
          gap: var(--space-3);
        }

        .radio-card {
          flex: 1;
          position: relative;
          cursor: pointer;
        }

        .radio-card input {
          position: absolute;
          opacity: 0;
        }

        .radio-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-4);
          border: 2px solid var(--color-border);
          border-radius: var(--radius-lg);
          transition: all var(--transition-fast);
          text-align: center;
        }

        .radio-card input:checked + .radio-content {
          border-color: var(--color-primary);
          background: var(--color-primary-bg);
        }

        .radio-label {
          font-weight: var(--font-weight-semibold);
        }

        .radio-desc {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .form-section {
          margin-top: var(--space-4);
          padding-top: var(--space-4);
          border-top: 1px solid var(--color-border-light);
        }

        .section-title {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-semibold);
          margin-bottom: var(--space-3);
        }

        .checkbox-group {
          display: flex;
          flex-direction: column;
          gap: var(--space-3);
        }

        .checkbox-item {
          display: flex;
          align-items: flex-start;
          gap: var(--space-3);
          cursor: pointer;
        }

        .checkbox-item input {
          margin-top: 4px;
          width: 18px;
          height: 18px;
          accent-color: var(--color-primary);
        }

        .checkbox-content {
          display: flex;
          flex-direction: column;
        }

        .checkbox-label {
          font-weight: var(--font-weight-medium);
        }

        .checkbox-desc {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .alert {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          border-radius: var(--radius-md);
          font-size: var(--font-size-sm);
          margin-top: var(--space-4);
        }

        .alert-warning {
          background: var(--color-warning-bg);
          color: var(--color-warning);
        }

        .modal-lg {
          max-width: 600px;
        }
      `}</style>
        </div>
    );
}

export default CompanyClosuresPage;
