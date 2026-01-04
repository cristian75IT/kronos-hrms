/**
 * KRONOS - User Create/Edit Form
 * Enterprise-grade user management with integrated contract creation
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
    CheckCircle,
    Clock,
    RefreshCw,
    BriefcaseBusiness
} from 'lucide-react';
import { userService } from '../../services/userService';
import { configService } from '../../services/config.service';
import { useToast } from '../../context/ToastContext';
import type { ContractType, EmployeeContractCreate } from '../../types';

interface UserFormValues {
    // User Info
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    phone?: string;

    // Profile Info
    hire_date?: string;
    department?: string;
    position?: string;
    employee_code?: string;

    // Roles
    is_admin: boolean;
    is_manager: boolean;
    is_approver: boolean;
    is_employee: boolean;
    is_hr: boolean;

    // First Contract (Only for creation)
    has_contract?: boolean;
    national_contract_id?: string;
    level_id?: string;
    contract_type_id?: string;
    weekly_hours?: number;
    contract_start_date?: string;
    job_title?: string;
}

export function UserFormPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const toast = useToast();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    // Contract Data dependencies
    const [contractTypes, setContractTypes] = useState<ContractType[]>([]);
    const [nationalContracts, setNationalContracts] = useState<any[]>([]);

    const isEditing = !!id;

    const {
        register,
        handleSubmit,
        reset,
        watch,
        setValue,
        formState: { errors },
    } = useForm<UserFormValues>({
        defaultValues: {
            is_admin: false,
            is_manager: false,
            is_approver: false,
            is_employee: true, // Default to Employee
            is_hr: false,
            has_contract: true, // Default checked for new users
            weekly_hours: 40,
            contract_start_date: new Date().toISOString().split('T')[0],
        },
    });

    const watchHasContract = watch('has_contract');
    const watchNationalContract = watch('national_contract_id');
    const watchContractType = watch('contract_type_id');

    useEffect(() => {
        loadDependencies();
        if (isEditing && id) {
            loadUser(id);
        }
    }, [isEditing, id]);

    // When contract type changes, auto-set hours
    useEffect(() => {
        if (watchContractType) {
            const type = contractTypes.find(t => t.id === watchContractType);
            if (type) {
                const defaultHours = Math.round(40 * ((type.part_time_percentage || 100) / 100));
                setValue('weekly_hours', defaultHours);
            }
        }
    }, [watchContractType, contractTypes, setValue]);

    const loadDependencies = async () => {
        try {
            const [types, ccnls] = await Promise.all([
                userService.getContractTypes(),
                configService.getNationalContracts()
            ]);
            setContractTypes(types);
            setNationalContracts(ccnls);
        } catch (error) {
            console.error('Failed to load form dependencies', error);
            toast.error('Errore caricamento dati contrattuali');
        }
    };

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
                is_admin: (user.roles || []).includes('admin') || !!user.is_admin,
                is_manager: (user.roles || []).includes('manager') || !!user.is_manager,
                is_approver: (user.roles || []).includes('approver') || !!user.is_approver,
                is_employee: (user.roles || []).includes('employee') || !!user.is_employee,
                is_hr: (user.roles || []).includes('hr') || !!user.is_hr,

                // Disable contract fields in edit mode (handled separately)
                has_contract: false
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
            // 1. Prepare User Payload
            const roles: string[] = [];
            if (data.is_admin) roles.push('admin');
            if (data.is_manager) roles.push('manager');
            if (data.is_approver) roles.push('approver');

            const payload: any = {
                username: data.username,
                email: data.email,
                first_name: data.first_name,
                last_name: data.last_name,
                role: roles[0] || 'employee',
                roles: roles,
                // Explicitly send boolean flags for backend update
                is_admin: data.is_admin,
                is_manager: data.is_manager,
                is_approver: data.is_approver,
                profile: {
                    phone: data.phone,
                    department: data.department,
                    position: data.has_contract ? data.job_title : data.position, // Use job title if contract set
                    hire_date: data.has_contract ? data.contract_start_date : (data.hire_date || null),
                    employee_number: data.employee_code,
                }
            };

            let userId = id;

            // 2. Create or Update User
            if (isEditing && id) {
                await userService.updateUser(id, payload);
                toast.success('Utente aggiornato con successo');
            } else {
                const newUser = await userService.createUser(payload);
                userId = newUser.id;
                toast.success('Utente creato con successo');
            }

            // 3. Create Contract (Only for new users with checked flag)
            if (!isEditing && data.has_contract && userId) {
                try {
                    const contractPayload: EmployeeContractCreate = {
                        contract_type_id: data.contract_type_id!,
                        national_contract_id: data.national_contract_id || undefined,
                        level_id: data.level_id || undefined,
                        start_date: data.contract_start_date!,
                        end_date: undefined,
                        weekly_hours: Number(data.weekly_hours),
                        job_title: data.job_title,
                    };

                    await userService.addContract(userId, contractPayload);
                    toast.success('Contratto associato correttamente');
                } catch (contractError: any) {
                    console.error('Failed to add contract', contractError);
                    toast.error('Utente creato, ma errore salvataggio contratto: ' + (contractError.response?.data?.detail || contractError.message));
                    // Navigate to user detail anyway so they can retry
                }
            }

            navigate('/admin/users');
        } catch (error: any) {
            console.error(error);
            toast.error(error.message || `Errore durante ${isEditing ? 'l\'aggiornamento' : 'la creazione'} dell'utente`);
        } finally {
            setIsSubmitting(false);
        }
    };

    const selectedCCNL = nationalContracts.find(c => c.id === watchNationalContract);

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
                        <h1 className="text-2xl font-bold text-gray-900">{isEditing ? `Modifica ${isEditing ? '' : 'Nuovo'} Utente` : 'Nuovo Dipendente'}</h1>
                    </div>
                </div>
            </header>

            {/* User Status Switch - Keycloak Sync */}
            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm mb-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                            <BriefcaseBusiness className="text-indigo-600" size={24} />
                            Stato e Ruolo Aziendale
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">
                            Definisce il tipo di contratto e l'accesso alle funzionalità HR.
                            <br /><span className="text-xs text-indigo-600 font-medium flex items-center gap-1 mt-1"><RefreshCw size={12} /> Sincronizzato con Keycloak (Ruolo 'employee')</span>
                        </p>
                    </div>

                    <div className="flex items-center gap-2 bg-gray-100 p-1.5 rounded-xl self-start md:self-center">
                        <button
                            type="button"
                            onClick={() => setValue('is_employee', false)}
                            className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all ${!watch('is_employee') ? 'bg-white shadow-md text-gray-900 ring-1 ring-black/5' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-200/50'}`}
                        >
                            Esterno / Consulente
                        </button>
                        <button
                            type="button"
                            onClick={() => setValue('is_employee', true)}
                            className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all ${watch('is_employee') ? 'bg-indigo-600 shadow-md text-white ring-1 ring-indigo-600' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-200/50'}`}
                        >
                            Dipendente
                        </button>
                    </div>
                </div>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="w-full">
                <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6 items-start">
                    {/* Main Column */}
                    <div className="space-y-6">
                        {/* Personal Info */}
                        <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm relative overflow-hidden group hover:shadow-md transition-shadow">
                            <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
                            <div className="flex items-center gap-3 pb-4 mb-4 border-b border-gray-100 text-indigo-600">
                                <User size={20} />
                                <h2 className="text-lg font-semibold text-gray-900">Identità Keycloak</h2>
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
                                        <p className="mt-1 text-sm text-red-600 flex items-center gap-1"><AlertCircle size={12} /> {errors.first_name?.message}</p>
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
                                        <p className="mt-1 text-sm text-red-600 flex items-center gap-1"><AlertCircle size={12} /> {errors.last_name?.message}</p>
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
                                            {...register('email', { required: 'Email richiesta', pattern: { value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i, message: 'Email non valida' } })}
                                        />
                                    </div>
                                    {errors.email && (
                                        <p className="mt-1 text-sm text-red-600 flex items-center gap-1"><AlertCircle size={12} /> {errors.email?.message}</p>
                                    )}
                                </div>
                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Telefono</label>
                                    <div className="relative rounded-md shadow-sm">
                                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                            <Phone size={16} className="text-gray-400" />
                                        </div>
                                        <input type="tel" className="block w-full rounded-lg border-gray-300 pl-10 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" placeholder="+39 123 456 7890" {...register('phone')} />
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* Work Info */}
                        <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm relative overflow-hidden">
                            <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
                            <div className="flex items-center gap-3 pb-4 mb-4 border-b border-gray-100 text-blue-600">
                                <Briefcase size={20} />
                                <h2 className="text-lg font-semibold text-gray-900">Informazioni Lavorative</h2>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Username <span className="text-red-500">*</span></label>
                                    <input
                                        type="text"
                                        disabled
                                        className="block w-full rounded-lg border-gray-300 shadow-sm bg-gray-100 text-gray-500 cursor-not-allowed sm:text-sm"
                                        placeholder="mario.rossi"
                                        {...register('username')}
                                    />
                                    {errors.username && (
                                        <p className="mt-1 text-sm text-red-600 flex items-center gap-1"><AlertCircle size={12} /> {errors.username?.message}</p>
                                    )}
                                </div>
                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Codice Dipendente</label>
                                    <input type="text" className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" placeholder="EMP001" {...register('employee_code')} />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="block text-sm font-medium text-gray-700">Dipartimento</label>
                                    <div className="relative rounded-md shadow-sm">
                                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                            <Building size={16} className="text-gray-400" />
                                        </div>
                                        <input type="text" className="block w-full rounded-lg border-gray-300 pl-10 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" placeholder="IT" {...register('department')} />
                                    </div>
                                </div>

                                {/* Visible only when NOT registering a contract (edit mode or manual opt-out) */}
                                {(!watchHasContract || isEditing) && (
                                    <>
                                        <div className="space-y-1.5">
                                            <label className="block text-sm font-medium text-gray-700">Posizione</label>
                                            <input type="text" className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" placeholder="Software Developer" {...register('position')} />
                                        </div>
                                        <div className="space-y-1.5">
                                            <label className="block text-sm font-medium text-gray-700">Data Assunzione</label>
                                            <div className="relative rounded-md shadow-sm">
                                                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                                    <Calendar size={16} className="text-gray-400" />
                                                </div>
                                                <input type="date" className="block w-full rounded-lg border-gray-300 pl-10 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" {...register('hire_date')} />
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>
                        </section>

                        {/* First Contract Section - ONLY FOR NEW EMPLOYEES */}
                        {!isEditing && watch('is_employee') && (
                            <section className={`bg-white p-6 rounded-xl border transition-all duration-300 ${watchHasContract ? 'border-emerald-200 shadow-md ring-1 ring-emerald-500/10' : 'border-gray-200'}`}>
                                <div className="flex items-center justify-between pb-4 mb-4 border-b border-gray-100">
                                    <div className="flex items-center gap-3 text-emerald-700">
                                        <FileText size={20} />
                                        <h2 className="text-lg font-semibold">Primo Contratto</h2>
                                    </div>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <span className="text-sm font-medium text-gray-600">Registra Contratto Iniziale</span>
                                        <div className="relative inline-flex items-center cursor-pointer">
                                            <input type="checkbox" className="sr-only peer" {...register('has_contract')} />
                                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-emerald-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                                        </div>
                                    </label>
                                </div>

                                {watchHasContract ? (
                                    <div className="space-y-5 animate-fadeIn">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="space-y-1.5">
                                                <label className="block text-sm font-medium text-gray-700">Tipo Contratto <span className="text-red-500">*</span></label>
                                                <select
                                                    className={`block w-full rounded-lg border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 sm:text-sm ${errors.contract_type_id ? 'border-red-300' : ''}`}
                                                    {...register('contract_type_id', { required: watchHasContract ? 'Tipo contratto richiesto' : false })}
                                                >
                                                    <option value="">Seleziona...</option>
                                                    {contractTypes.map(t => (
                                                        <option key={t.id} value={t.id}>{t.name} ({t.code})</option>
                                                    ))}
                                                </select>
                                                {errors.contract_type_id && <p className="text-xs text-red-500">{errors.contract_type_id.message}</p>}
                                            </div>

                                            <div className="space-y-1.5">
                                                <label className="block text-sm font-medium text-gray-700">CCNL di Riferimento</label>
                                                <select
                                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 sm:text-sm"
                                                    {...register('national_contract_id')}
                                                >
                                                    <option value="">Nessuno / Altro</option>
                                                    {nationalContracts.map(c => (
                                                        <option key={c.id} value={c.id}>{c.name}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="space-y-1.5">
                                                <label className="block text-sm font-medium text-gray-700">Qualifica / Livello</label>
                                                <select
                                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 sm:text-sm"
                                                    {...register('level_id')}
                                                    disabled={!watchNationalContract}
                                                >
                                                    <option value="">Seleziona livello...</option>
                                                    {selectedCCNL?.levels?.map((l: any) => (
                                                        <option key={l.id} value={l.id}>{l.level_name}</option>
                                                    ))}
                                                </select>
                                                {!watchNationalContract && <p className="text-xs text-gray-400">Seleziona prima un CCNL</p>}
                                            </div>
                                            <div className="space-y-1.5">
                                                <label className="block text-sm font-medium text-gray-700">Posizione / Mansione</label>
                                                <input
                                                    type="text"
                                                    className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 sm:text-sm"
                                                    placeholder="Software Engineer"
                                                    {...register('job_title', { required: watchHasContract ? 'Posizione richiesta' : false })}
                                                />
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="space-y-1.5">
                                                <label className="block text-sm font-medium text-gray-700">Data Inizio Contratto <span className="text-red-500">*</span></label>
                                                <input
                                                    type="date"
                                                    className={`block w-full rounded-lg border-gray-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 sm:text-sm ${errors.contract_start_date ? 'border-red-300' : ''}`}
                                                    {...register('contract_start_date', { required: watchHasContract ? 'Data inizio richiesta' : false })}
                                                />
                                            </div>
                                            <div className="space-y-1.5">
                                                <label className="block text-sm font-medium text-gray-700">Ore Settimanali <span className="text-red-500">*</span></label>
                                                <div className="relative rounded-md shadow-sm">
                                                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                                        <Clock size={16} className="text-gray-400" />
                                                    </div>
                                                    <input
                                                        type="number"
                                                        className="block w-full rounded-lg border-gray-300 pl-10 focus:border-emerald-500 focus:ring-emerald-500 sm:text-sm font-bold text-gray-900"
                                                        {...register('weekly_hours', { required: watchHasContract ? 'Ore richieste' : false, min: 1, max: 168 })}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="bg-gray-50 border border-gray-100 rounded-lg p-4 text-center">
                                        <p className="text-sm text-gray-500">I dati contrattuali potranno essere aggiunti successivamente dal profilo utente.</p>
                                    </div>
                                )}
                            </section>
                        )}

                        {/* HR Platform Section - ONLY FOR EXISTING EMPLOYEES */}
                        {isEditing && watch('is_employee') && (
                            <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-purple-500"></div>
                                <div className="flex items-center gap-3 pb-4 mb-4 border-b border-gray-100 text-purple-600">
                                    <BriefcaseBusiness size={20} />
                                    <h2 className="text-lg font-semibold text-gray-900">Piattaforma HR (Enterprise Link)</h2>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="p-5 bg-purple-50 rounded-lg border border-purple-100 hover:shadow-md transition-shadow cursor-pointer group">
                                        <div className="flex justify-between items-start">
                                            <h3 className="font-bold text-purple-900">Gestione Contratti</h3>
                                            <FileText size={18} className="text-purple-400 group-hover:text-purple-600" />
                                        </div>
                                        <p className="text-sm text-purple-700 mt-2 mb-3">Visualizza storico contratti, livelli e ore settimanali.</p>
                                        <Link to={`/admin/hr/contracts/${id}`} className="inline-flex items-center gap-1 text-sm font-bold text-purple-600 hover:text-purple-800">
                                            Gestisci Contratti <ArrowLeft className="rotate-180" size={14} />
                                        </Link>
                                    </div>

                                    <div className="p-5 bg-blue-50 rounded-lg border border-blue-100 hover:shadow-md transition-shadow cursor-pointer group">
                                        <div className="flex justify-between items-start">
                                            <h3 className="font-bold text-blue-900">Wallet Ferie & Permessi</h3>
                                            <Clock size={18} className="text-blue-400 group-hover:text-blue-600" />
                                        </div>
                                        <p className="text-sm text-blue-700 mt-2 mb-3">Bilancio ore, ratei maturati e residui anni precedenti.</p>
                                        <Link to={`/admin/hr/leaves/${id}`} className="inline-flex items-center gap-1 text-sm font-bold text-blue-600 hover:text-blue-800">
                                            Vedi Wallet <ArrowLeft className="rotate-180" size={14} />
                                        </Link>
                                    </div>

                                    <div className="p-5 bg-emerald-50 rounded-lg border border-emerald-100 hover:shadow-md transition-shadow cursor-pointer group">
                                        <div className="flex justify-between items-start">
                                            <h3 className="font-bold text-emerald-900">Formazione e Corsi</h3>
                                            <CheckCircle size={18} className="text-emerald-400 group-hover:text-emerald-600" />
                                        </div>
                                        <p className="text-sm text-emerald-700 mt-2 mb-3">Storico corsi sicurezza e certificazioni obbligatorie.</p>
                                        <Link to={`/admin/hr/training/${id}`} className="inline-flex items-center gap-1 text-sm font-bold text-emerald-600 hover:text-emerald-800">
                                            Piano Formativo <ArrowLeft className="rotate-180" size={14} />
                                        </Link>
                                    </div>
                                </div>
                            </section>
                        )}
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* Permissions */}
                        <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm relative overflow-hidden">
                            <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
                            <div className="flex items-center gap-3 pb-4 mb-4 border-b border-gray-100 text-indigo-600">
                                <Shield size={20} />
                                <h2 className="text-lg font-semibold text-gray-900">Ruoli & Permessi</h2>
                            </div>
                            <div className="space-y-3">
                                <label className="flex items-start gap-4 p-3 border border-gray-200 rounded-lg cursor-pointer hover:border-indigo-500 hover:bg-indigo-50/50 transition-all group">
                                    <input type="checkbox" className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" {...register('is_admin')} />
                                    <div>
                                        <span className="block text-sm font-medium text-gray-900 group-hover:text-indigo-700">Amministratore</span>
                                        <span className="block text-xs text-gray-500 group-hover:text-indigo-600/70">Accesso completo al sistema</span>
                                    </div>
                                </label>
                                <label className="flex items-start gap-4 p-3 border border-gray-200 rounded-lg cursor-pointer hover:border-indigo-500 hover:bg-indigo-50/50 transition-all group">
                                    <input type="checkbox" className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" {...register('is_manager')} />
                                    <div>
                                        <span className="block text-sm font-medium text-gray-900 group-hover:text-indigo-700">Manager</span>
                                        <span className="block text-xs text-gray-500 group-hover:text-indigo-600/70">Gestione team e report</span>
                                    </div>
                                </label>
                                <label className="flex items-start gap-4 p-3 border border-gray-200 rounded-lg cursor-pointer hover:border-indigo-500 hover:bg-indigo-50/50 transition-all group">
                                    <input type="checkbox" className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" {...register('is_approver')} />
                                    <div>
                                        <span className="block text-sm font-medium text-gray-900 group-hover:text-indigo-700">Approvatore</span>
                                        <span className="block text-xs text-gray-500 group-hover:text-indigo-600/70">Approva ferie e richieste</span>
                                    </div>
                                </label>
                                <label className="flex items-start gap-4 p-3 border border-gray-200 rounded-lg cursor-pointer hover:border-indigo-500 hover:bg-indigo-50/50 transition-all group">
                                    <input type="checkbox" className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" {...register('is_hr')} />
                                    <div>
                                        <span className="block text-sm font-medium text-gray-900 group-hover:text-indigo-700">HR Specialist</span>
                                        <span className="block text-xs text-gray-500 group-hover:text-indigo-600/70">Gestione dipendenti e report</span>
                                    </div>
                                </label>
                            </div>
                        </section>

                        {/* Actions */}
                        <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 shadow-inner flex flex-col gap-3">
                            <button
                                type="submit"
                                className="w-full flex justify-center items-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-lg shadow-indigo-200 transition-all hover:scale-[1.02] disabled:opacity-70 disabled:hover:scale-100"
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? (
                                    <span className="spinner spinner-sm" />
                                ) : (
                                    <>
                                        <Save size={18} />
                                        {isEditing ? 'Salva Modifiche' : (watchHasContract ? 'Crea Dipendente e Contratto' : 'Crea Utente')}
                                    </>
                                )}
                            </button>
                            <button
                                type="button"
                                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-xl font-medium transition-all"
                                onClick={() => navigate(-1)}
                            >
                                Annulla
                            </button>
                        </div>

                        {/* Helper Box */}
                        {!isEditing && watchHasContract && (
                            <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 flex gap-3">
                                <CheckCircle size={20} className="text-emerald-600 shrink-0 mt-0.5" />
                                <div className="text-sm text-emerald-800">
                                    <p className="font-bold mb-1">Tutto in uno step!</p>
                                    <p className="opacity-90">Verrà creato l'utente e automaticamente registrato il primo contratto attivo. Il wallet ferie sarà inizializzato a zero.</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </form>
        </div>
    );
}

export default UserFormPage;
