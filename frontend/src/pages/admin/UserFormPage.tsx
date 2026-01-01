/**
 * KRONOS - User Create/Edit Form
 * Enterprise-grade user management form
 */
import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
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
    FileText,
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
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const toast = useToast();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const isEditing = !!id;

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<UserFormValues>({
        defaultValues: {
            is_admin: false,
            is_manager: false,
            is_approver: false,
        },
    });

    useEffect(() => {
        if (isEditing && id) {
            loadUser(id);
        }
    }, [isEditing, id]);

    const loadUser = async (userId: string) => {
        setIsLoading(true);
        try {
            const user = await userService.getUser(userId);

            // Map UserWithProfile to UserFormValues
            const formValues: UserFormValues = {
                username: user.username,
                email: user.email,
                first_name: user.first_name,
                last_name: user.last_name,

                // Profile fields
                phone: user.profile?.phone || '',
                hire_date: user.profile?.hire_date ? user.profile.hire_date.split('T')[0] : '', // Format YYYY-MM-DD
                department: user.profile?.department || '',
                position: user.profile?.position || '',
                employee_code: user.profile?.employee_number || '',

                // Roles -> booleans
                is_admin: (user.roles || []).includes('admin'),
                is_manager: (user.roles || []).includes('manager') || (user.roles || []).includes('hr'),
                is_approver: (user.roles || []).includes('approver'),
            };

            reset(formValues);
        } catch (error: any) {
            console.error('Failed to load user', error);
            toast.error('Impossibile caricare i dati utente');
            navigate('/admin/users');
        } finally {
            setIsLoading(false);
        }
    };

    const onSubmit = async (data: UserFormValues) => {
        setIsSubmitting(true);
        try {
            // Transform form data to API payload
            const roles: string[] = [];
            if (data.is_admin) roles.push('admin');
            if (data.is_manager) roles.push('manager');
            if (data.is_approver) roles.push('approver');
            // If user had other roles not managed here, careful not to lose them in a real app, 
            // but here we control roles strictly via UI.

            const payload: any = {
                username: data.username,
                email: data.email,
                first_name: data.first_name,
                last_name: data.last_name,
                role: roles[0] || 'employee', // Fallback for backend that might expect 'role' string field
                roles: roles,
                profile: {
                    phone: data.phone,
                    department: data.department,
                    position: data.position,
                    hire_date: data.hire_date || null,
                    employee_number: data.employee_code,
                }
            };

            if (isEditing && id) {
                await userService.updateUser(id, payload);
                toast.success('Utente aggiornato con successo');
            } else {
                await userService.createUser(payload);
                toast.success('Utente creato con successo');
            }
            navigate('/admin/users');
        } catch (error: any) {
            toast.error(error.message || `Errore durante ${isEditing ? 'l\'aggiornamento' : 'la creazione'} dell'utente`);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="spinner-lg" />
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate(-1)} className="btn btn-ghost p-2 rounded-full hover:bg-gray-100">
                        <ArrowLeft size={20} className="text-gray-500" />
                    </button>
                    <div>
                        <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                            <Link to="/admin/users" className="hover:text-primary transition-colors">Gestione Utenti</Link>
                            <span>/</span>
                            <span>{isEditing ? 'Modifica Utente' : 'Nuovo Utente'}</span>
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900">{isEditing ? `Modifica ${isEditing ? '' : 'Nuovo'} Utente` : 'Nuovo Utente'}</h1>
                    </div>
                </div>
            </header>

            <form onSubmit={handleSubmit(onSubmit)} className="w-full">
                <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6 items-start">
                    {/* Main Column */}
                    <div className="space-y-6">
                        {/* Personal Info */}
                        <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                            <div className="flex items-center gap-3 pb-4 mb-4 border-b border-gray-100 text-indigo-600">
                                <User size={20} />
                                <h2 className="text-lg font-semibold text-gray-900">Informazioni Personali</h2>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Nome <span className="text-red-500">*</span></label>
                                    <input
                                        type="text"
                                        className={`block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${errors.first_name ? 'border-red-300 focus:border-red-500 focus:ring-red-200' : ''}`}
                                        placeholder="Mario"
                                        {...register('first_name', { required: 'Nome richiesto' })}
                                    />
                                    {errors.first_name && (
                                        <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                            <AlertCircle size={12} />
                                            {errors.first_name?.message}
                                        </p>
                                    )}
                                </div>

                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Cognome <span className="text-red-500">*</span></label>
                                    <input
                                        type="text"
                                        className={`block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${errors.last_name ? 'border-red-300 focus:border-red-500 focus:ring-red-200' : ''}`}
                                        placeholder="Rossi"
                                        {...register('last_name', { required: 'Cognome richiesto' })}
                                    />
                                    {errors.last_name && (
                                        <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                            <AlertCircle size={12} />
                                            {errors.last_name?.message}
                                        </p>
                                    )}
                                </div>

                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Email <span className="text-red-500">*</span></label>
                                    <div className="relative rounded-md shadow-sm">
                                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                            <Mail size={16} className="text-gray-400" />
                                        </div>
                                        <input
                                            type="email"
                                            className={`block w-full rounded-lg border-gray-300 pl-10 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${errors.email ? 'border-red-300 focus:border-red-500 focus:ring-red-200' : ''}`}
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
                                        <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                            <AlertCircle size={12} />
                                            {errors.email?.message}
                                        </p>
                                    )}
                                </div>

                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Telefono</label>
                                    <div className="relative rounded-md shadow-sm">
                                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                            <Phone size={16} className="text-gray-400" />
                                        </div>
                                        <input
                                            type="tel"
                                            className="block w-full rounded-lg border-gray-300 pl-10 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                            placeholder="+39 123 456 7890"
                                            {...register('phone')}
                                        />
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* Work Info */}
                        <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                            <div className="flex items-center gap-3 pb-4 mb-4 border-b border-gray-100 text-indigo-600">
                                <Briefcase size={20} />
                                <h2 className="text-lg font-semibold text-gray-900">Informazioni Lavorative</h2>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Username <span className="text-red-500">*</span></label>
                                    <input
                                        type="text"
                                        className={`block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${errors.username ? 'border-red-300 focus:border-red-500 focus:ring-red-200' : ''}`}
                                        placeholder="mario.rossi"
                                        {...register('username', { required: 'Username richiesto' })}
                                    />
                                    {errors.username && (
                                        <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                            <AlertCircle size={12} />
                                            {errors.username?.message}
                                        </p>
                                    )}
                                </div>

                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Codice Dipendente</label>
                                    <input
                                        type="text"
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        placeholder="EMP001"
                                        {...register('employee_code')}
                                    />
                                </div>

                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Dipartimento</label>
                                    <div className="relative rounded-md shadow-sm">
                                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                            <Building size={16} className="text-gray-400" />
                                        </div>
                                        <input
                                            type="text"
                                            className="block w-full rounded-lg border-gray-300 pl-10 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                            placeholder="IT"
                                            {...register('department')}
                                        />
                                    </div>
                                </div>

                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Posizione</label>
                                    <input
                                        type="text"
                                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        placeholder="Software Developer"
                                        {...register('position')}
                                    />
                                </div>

                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Data Assunzione</label>
                                    <div className="relative rounded-md shadow-sm">
                                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                            <Calendar size={16} className="text-gray-400" />
                                        </div>
                                        <input
                                            type="date"
                                            className="block w-full rounded-lg border-gray-300 pl-10 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                            {...register('hire_date')}
                                        />
                                    </div>
                                </div>
                            </div>
                        </section>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* Contract Management Link - Only in Edit Mode */}
                        {isEditing && (
                            <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                                <div className="flex items-center gap-3 pb-4 mb-4 border-b border-gray-100 text-indigo-600">
                                    <FileText size={20} />
                                    <h2 className="text-lg font-semibold text-gray-900">Contratti</h2>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500 mb-4 leading-relaxed">
                                        Per gestire lo storico contratti, le promozioni e i livelli, accedi alla scheda contratto.
                                    </p>
                                    <button
                                        type="button"
                                        className="w-full btn btn-white border border-gray-300 text-gray-700 hover:bg-gray-50 flex items-center justify-center gap-2"
                                        onClick={() => navigate(`/admin/users/${id}?tab=contracts`)}
                                    >
                                        <Briefcase size={16} />
                                        Gestisci Contratti
                                    </button>
                                </div>
                            </section>
                        )}

                        {/* Permissions */}
                        <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                            <div className="flex items-center gap-3 pb-4 mb-4 border-b border-gray-100 text-indigo-600">
                                <Shield size={20} />
                                <h2 className="text-lg font-semibold text-gray-900">Permessi</h2>
                            </div>
                            <div className="space-y-3">
                                <label className="flex items-start gap-4 p-3 border border-gray-200 rounded-lg cursor-pointer hover:border-indigo-500 hover:bg-indigo-50/50 transition-all group">
                                    <input
                                        type="checkbox"
                                        className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                        {...register('is_admin')}
                                    />
                                    <div>
                                        <span className="block text-sm font-medium text-gray-900 group-hover:text-indigo-700">Amministratore</span>
                                        <span className="block text-xs text-gray-500 group-hover:text-indigo-600/70">Accesso completo al sistema</span>
                                    </div>
                                </label>

                                <label className="flex items-start gap-4 p-3 border border-gray-200 rounded-lg cursor-pointer hover:border-indigo-500 hover:bg-indigo-50/50 transition-all group">
                                    <input
                                        type="checkbox"
                                        className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                        {...register('is_manager')}
                                    />
                                    <div>
                                        <span className="block text-sm font-medium text-gray-900 group-hover:text-indigo-700">Manager</span>
                                        <span className="block text-xs text-gray-500 group-hover:text-indigo-600/70">Gestione team e report</span>
                                    </div>
                                </label>

                                <label className="flex items-start gap-4 p-3 border border-gray-200 rounded-lg cursor-pointer hover:border-indigo-500 hover:bg-indigo-50/50 transition-all group">
                                    <input
                                        type="checkbox"
                                        className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                        {...register('is_approver')}
                                    />
                                    <div>
                                        <span className="block text-sm font-medium text-gray-900 group-hover:text-indigo-700">Approvatore</span>
                                        <span className="block text-xs text-gray-500 group-hover:text-indigo-600/70">Approva ferie e richieste</span>
                                    </div>
                                </label>
                            </div>
                        </section>

                        {/* Actions */}
                        <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 shadow-inner flex flex-col gap-3">
                            <button
                                type="submit"
                                className="btn btn-primary w-full flex justify-center items-center gap-2 shadow-sm"
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? (
                                    <span className="spinner spinner-sm" />
                                ) : (
                                    <>
                                        <Save size={18} />
                                        {isEditing ? 'Salva Modifiche' : 'Crea Utente'}
                                    </>
                                )}
                            </button>
                            <button
                                type="button"
                                className="btn btn-ghost w-full text-gray-600 hover:bg-white hover:border-gray-300 border border-transparent"
                                onClick={() => navigate(-1)}
                            >
                                Annulla
                            </button>
                        </div>
                    </div>
                </div>
            </form>
        </div>
    );
}

export default UserFormPage;
