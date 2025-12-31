/**
 * KRONOS - User Create/Edit Form
 * Enterprise-grade user management form
 */
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import {
    ArrowLeft,
    User,
    Mail,
    Phone,
    Building,
    Briefcase,
    Calendar,
    Shield,
    Save,
    AlertCircle,
} from 'lucide-react';
import { userService } from '../../services/userService';
import { useToast } from '../../context/ToastContext';

interface UserFormValues {
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    phone?: string;
    hire_date?: string;
    department?: string;
    position?: string;
    employee_code?: string;
    is_admin: boolean;
    is_manager: boolean;
    is_approver: boolean;
}

export function UserFormPage() {
    const navigate = useNavigate();
    const toast = useToast();
    const [isSubmitting, setIsSubmitting] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<UserFormValues>({
        defaultValues: {
            is_admin: false,
            is_manager: false,
            is_approver: false,
        },
    });

    const onSubmit = async (data: UserFormValues) => {
        setIsSubmitting(true);
        try {
            // Call user creation API
            await userService.createUser(data);
            toast.success('Utente creato con successo');
            navigate('/admin/users');
        } catch (error: any) {
            toast.error(error.message || 'Errore durante la creazione dell\'utente');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="user-form-page animate-fadeIn">
            {/* Header */}
            <header className="page-header">
                <div className="header-left">
                    <button onClick={() => navigate(-1)} className="btn btn-ghost btn-icon">
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <div className="breadcrumb">
                            <Link to="/admin/users">Gestione Utenti</Link>
                            <span>/</span>
                            <span>Nuovo Utente</span>
                        </div>
                        <h1>Nuovo Utente</h1>
                    </div>
                </div>
            </header>

            <form onSubmit={handleSubmit(onSubmit)} className="user-form">
                <div className="form-layout">
                    {/* Main Column */}
                    <div className="form-main">
                        {/* Personal Info */}
                        <section className="form-section card">
                            <div className="section-header">
                                <User size={20} />
                                <h2>Informazioni Personali</h2>
                            </div>
                            <div className="section-content">
                                <div className="form-grid">
                                    <div className="form-group">
                                        <label className="input-label input-label-required">Nome</label>
                                        <input
                                            type="text"
                                            className={`input ${errors.first_name ? 'input-error' : ''}`}
                                            placeholder="Mario"
                                            {...register('first_name', { required: 'Nome richiesto' })}
                                        />
                                        {errors.first_name && (
                                            <span className="input-error-text">
                                                <AlertCircle size={12} />
                                                {errors.first_name.message}
                                            </span>
                                        )}
                                    </div>

                                    <div className="form-group">
                                        <label className="input-label input-label-required">Cognome</label>
                                        <input
                                            type="text"
                                            className={`input ${errors.last_name ? 'input-error' : ''}`}
                                            placeholder="Rossi"
                                            {...register('last_name', { required: 'Cognome richiesto' })}
                                        />
                                        {errors.last_name && (
                                            <span className="input-error-text">
                                                <AlertCircle size={12} />
                                                {errors.last_name.message}
                                            </span>
                                        )}
                                    </div>

                                    <div className="form-group">
                                        <label className="input-label input-label-required">Email</label>
                                        <div className="input-with-icon">
                                            <Mail size={18} />
                                            <input
                                                type="email"
                                                className={`input ${errors.email ? 'input-error' : ''}`}
                                                placeholder="mario.rossi@azienda.it"
                                                {...register('email', {
                                                    required: 'Email richiesta',
                                                    pattern: {
                                                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                                                        message: 'Email non valida',
                                                    },
                                                })}
                                            />
                                        </div>
                                        {errors.email && (
                                            <span className="input-error-text">
                                                <AlertCircle size={12} />
                                                {errors.email.message}
                                            </span>
                                        )}
                                    </div>

                                    <div className="form-group">
                                        <label className="input-label">Telefono</label>
                                        <div className="input-with-icon">
                                            <Phone size={18} />
                                            <input
                                                type="tel"
                                                className="input"
                                                placeholder="+39 123 456 7890"
                                                {...register('phone')}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* Work Info */}
                        <section className="form-section card">
                            <div className="section-header">
                                <Briefcase size={20} />
                                <h2>Informazioni Lavorative</h2>
                            </div>
                            <div className="section-content">
                                <div className="form-grid">
                                    <div className="form-group">
                                        <label className="input-label input-label-required">Username</label>
                                        <input
                                            type="text"
                                            className={`input ${errors.username ? 'input-error' : ''}`}
                                            placeholder="mario.rossi"
                                            {...register('username', { required: 'Username richiesto' })}
                                        />
                                        {errors.username && (
                                            <span className="input-error-text">
                                                <AlertCircle size={12} />
                                                {errors.username.message}
                                            </span>
                                        )}
                                    </div>

                                    <div className="form-group">
                                        <label className="input-label">Codice Dipendente</label>
                                        <input
                                            type="text"
                                            className="input"
                                            placeholder="EMP001"
                                            {...register('employee_code')}
                                        />
                                    </div>

                                    <div className="form-group">
                                        <label className="input-label">Dipartimento</label>
                                        <div className="input-with-icon">
                                            <Building size={18} />
                                            <input
                                                type="text"
                                                className="input"
                                                placeholder="IT"
                                                {...register('department')}
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group">
                                        <label className="input-label">Posizione</label>
                                        <input
                                            type="text"
                                            className="input"
                                            placeholder="Software Developer"
                                            {...register('position')}
                                        />
                                    </div>

                                    <div className="form-group">
                                        <label className="input-label">Data Assunzione</label>
                                        <div className="input-with-icon">
                                            <Calendar size={18} />
                                            <input
                                                type="date"
                                                className="input"
                                                {...register('hire_date')}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </section>
                    </div>

                    {/* Sidebar */}
                    <div className="form-sidebar">
                        {/* Permissions */}
                        <section className="form-section card">
                            <div className="section-header">
                                <Shield size={20} />
                                <h2>Permessi</h2>
                            </div>
                            <div className="section-content">
                                <div className="permissions-list">
                                    <label className="permission-item">
                                        <input
                                            type="checkbox"
                                            {...register('is_admin')}
                                        />
                                        <div className="permission-info">
                                            <span className="permission-name">Amministratore</span>
                                            <span className="permission-desc">Accesso completo al sistema</span>
                                        </div>
                                    </label>

                                    <label className="permission-item">
                                        <input
                                            type="checkbox"
                                            {...register('is_manager')}
                                        />
                                        <div className="permission-info">
                                            <span className="permission-name">Manager</span>
                                            <span className="permission-desc">Gestione team e report</span>
                                        </div>
                                    </label>

                                    <label className="permission-item">
                                        <input
                                            type="checkbox"
                                            {...register('is_approver')}
                                        />
                                        <div className="permission-info">
                                            <span className="permission-name">Approvatore</span>
                                            <span className="permission-desc">Approva ferie e richieste</span>
                                        </div>
                                    </label>
                                </div>
                            </div>
                        </section>

                        {/* Actions */}
                        <div className="form-actions">
                            <button
                                type="submit"
                                className="btn btn-primary btn-lg"
                                disabled={isSubmitting}
                                style={{ width: '100%' }}
                            >
                                {isSubmitting ? (
                                    <span className="spinner spinner-sm" />
                                ) : (
                                    <>
                                        <Save size={18} />
                                        Crea Utente
                                    </>
                                )}
                            </button>
                            <button
                                type="button"
                                className="btn btn-ghost"
                                onClick={() => navigate(-1)}
                                style={{ width: '100%' }}
                            >
                                Annulla
                            </button>
                        </div>
                    </div>
                </div>
            </form>

            <style>{`
        .user-form-page {
          display: flex;
          flex-direction: column;
          gap: var(--space-6);
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
        }

        .header-left {
          display: flex;
          align-items: flex-start;
          gap: var(--space-4);
        }

        .breadcrumb {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
          margin-bottom: var(--space-1);
        }

        .breadcrumb a:hover {
          color: var(--color-primary);
        }

        .page-header h1 {
          font-size: var(--font-size-2xl);
          font-weight: var(--font-weight-bold);
        }

        .form-layout {
          display: grid;
          grid-template-columns: 1fr 340px;
          gap: var(--space-6);
        }

        @media (max-width: 1024px) {
          .form-layout {
            grid-template-columns: 1fr;
          }
        }

        .form-main {
          display: flex;
          flex-direction: column;
          gap: var(--space-6);
        }

        .form-sidebar {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }

        .form-section {
          padding: var(--space-6);
        }

        .section-header {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding-bottom: var(--space-4);
          margin-bottom: var(--space-4);
          border-bottom: 1px solid var(--color-border-light);
          color: var(--color-primary);
        }

        .section-header h2 {
          font-size: var(--font-size-lg);
          font-weight: var(--font-weight-semibold);
          color: var(--color-text-primary);
        }

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

        .input-with-icon {
          position: relative;
          display: flex;
          align-items: center;
        }

        .input-with-icon svg {
          position: absolute;
          left: var(--space-3);
          color: var(--color-text-muted);
          pointer-events: none;
        }

        .input-with-icon .input {
          padding-left: var(--space-10);
        }

        .permissions-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-3);
        }

        .permission-item {
          display: flex;
          align-items: flex-start;
          gap: var(--space-3);
          padding: var(--space-3);
          border: 1px solid var(--color-border-light);
          border-radius: var(--radius-lg);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .permission-item:hover {
          border-color: var(--color-primary);
          background: var(--color-bg-hover);
        }

        .permission-item input[type="checkbox"] {
          width: 20px;
          height: 20px;
          margin-top: 2px;
          accent-color: var(--color-primary);
        }

        .permission-info {
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
        }

        .permission-name {
          font-weight: var(--font-weight-medium);
          color: var(--color-text-primary);
        }

        .permission-desc {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .form-actions {
          display: flex;
          flex-direction: column;
          gap: var(--space-3);
          padding: var(--space-4);
          background: var(--glass-bg);
          border: 1px solid var(--glass-border);
          border-radius: var(--radius-xl);
        }
      `}</style>
        </div>
    );
}

export default UserFormPage;
