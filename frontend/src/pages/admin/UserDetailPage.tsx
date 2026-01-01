/**
 * KRONOS - User Detail Page
 * Enterprise-grade user detail view with tabs for info and contracts
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom';
import {
    ArrowLeft,
    User,
    Mail,
    Phone,
    Building,
    Briefcase,
    Calendar,
    FileText,
    Edit,
    CheckCircle,
    XCircle,
    Plus,
} from 'lucide-react';
import { userService } from '../../services/userService';
import { useToast } from '../../context/ToastContext';
import { ContractHistory } from '../../components/users/ContractHistory';
import type { UserWithProfile, EmployeeContract } from '../../types';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

export function UserDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const toast = useToast();
    const [user, setUser] = useState<UserWithProfile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'contracts'>((searchParams.get('tab') as 'overview' | 'contracts') || 'overview');
    const [showContractModal, setShowContractModal] = useState(false);
    const [contracts, setContracts] = useState<EmployeeContract[]>([]);

    useEffect(() => {
        if (id) {
            loadUser();
            loadContracts();
        }
    }, [id]);

    const loadUser = async () => {
        if (!id) return;
        setIsLoading(true);
        try {
            // Note: We might need a specific endpoint for single user with profile if getUsers doesn't support generic single get or if we want to reuse list cache. 
            // Assuming userService.getUser(id) exists or we use the list. 
            // Since useUsers hook is for generic list, let's see if we have a direct fetch.
            // If not, we might need to fetch the list and find, or implement getUser in service.
            // Looking at previous context, userService usually has basic CRUD. If not, I'll fallback to fetching user directly.

            // Checking userService usage in other files... ContractHistory used userService.getContracts(userId).
            // I'll assume userService.getUser(id) should exist or I'll implement it. 
            // For now, I'll try to use userService.getUser(id) if available, otherwise I'll need to double check service file. 
            // I will implement a fetch based on userService presence.
            const userData = await userService.getUser(id);
            setUser(userData);
        } catch (error) {
            console.error('Failed to load user', error);
            toast.error('Errore nel caricamento utente');
        } finally {
            setIsLoading(false);
        }
    };

    const loadContracts = async () => {
        if (!id) return;
        try {
            const data = await userService.getContracts(id);
            setContracts(data);
        } catch (error) {
            console.error('Failed to load contracts', error);
        }
    }

    const handleContractModalClose = () => {
        setShowContractModal(false);
        loadContracts(); // Reload to show updates
    };

    // Helper for safe date formatting
    const safeFormatDate = (dateString: string | undefined | null, formatStr: string = 'd MMM yyyy') => {
        if (!dateString) return '-';
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return '-';
            return format(date, formatStr, { locale: it });
        } catch (e) {
            return '-';
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="spinner-lg" />
            </div>
        );
    }

    if (!user) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen gap-4">
                <h2 className="text-2xl font-bold">Utente non trovato</h2>
                <Link to="/admin/users" className="btn btn-primary">Torna alla lista</Link>
            </div>
        );
    }

    const { profile } = user;
    const activeContract = contracts.find(c => !c.end_date);

    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate('/admin/users')} className="btn btn-ghost p-2 rounded-full hover:bg-gray-100">
                        <ArrowLeft size={20} className="text-gray-500" />
                    </button>
                    <div>
                        <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                            <Link to="/admin/users" className="hover:text-primary transition-colors">Gestione Utenti</Link>
                            <span>/</span>
                            <span>{user.first_name} {user.last_name}</span>
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                            {user.first_name} {user.last_name}
                            {!user.is_active && <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Non Attivo</span>}
                        </h1>
                    </div>
                </div>
                <div>
                    <button onClick={() => navigate(`/admin/users/${id}/edit`)} className="btn btn-white border border-gray-300 text-gray-700 hover:bg-gray-50 shadow-sm flex items-center gap-2">
                        <Edit size={16} />
                        Modifica
                    </button>
                </div>
            </header>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-[350px_1fr] gap-6 items-start">
                {/* Sidebar / Info Card */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-16 h-16 rounded-full bg-indigo-600 text-white flex items-center justify-center text-2xl font-bold shadow-md">
                                {user.first_name?.[0]}{user.last_name?.[0]}
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">{user.username}</h3>
                                <p className="text-gray-500 text-sm">{profile?.position || 'Nessuna posizione'}</p>
                            </div>
                        </div>

                        <div className="space-y-3 mb-6">
                            <div className="flex items-center gap-3 text-sm text-gray-600">
                                <Mail size={16} className="text-gray-400" />
                                <span className="truncate">{user.email}</span>
                            </div>
                            {profile?.phone && (
                                <div className="flex items-center gap-3 text-sm text-gray-600">
                                    <Phone size={16} className="text-gray-400" />
                                    <span>{profile.phone}</span>
                                </div>
                            )}
                            <div className="flex items-center gap-3 text-sm text-gray-600">
                                <Building size={16} className="text-gray-400" />
                                <span>{profile?.department || 'Nessun dipartimento'}</span>
                            </div>
                            {profile?.employee_number && (
                                <div className="flex items-center gap-3 text-sm text-gray-600">
                                    <User size={16} className="text-gray-400" />
                                    <span>ID: {profile.employee_number}</span>
                                </div>
                            )}
                        </div>

                        <div className="flex flex-wrap gap-2">
                            {user.roles?.map(role => (
                                <span key={role} className="px-2.5 py-0.5 rounded-md text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100 uppercase tracking-wide">
                                    {role}
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Quick Stats or Status */}
                    <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Stato Contratto</h3>
                        {activeContract ? (
                            <div className="flex items-start gap-3">
                                <CheckCircle size={20} className="text-emerald-500 mt-0.5" />
                                <div>
                                    <div className="font-bold text-emerald-700">Attivo</div>
                                    <div className="text-sm text-gray-900">{activeContract.weekly_hours}h / settimana</div>
                                    <div className="text-xs text-gray-500 mt-0.5">Dal {safeFormatDate(activeContract.start_date.toString())}</div>
                                </div>
                            </div>
                        ) : (
                            <div className="flex items-center gap-3">
                                <XCircle size={20} className="text-red-500" />
                                <span className="text-red-600 font-medium text-sm">Nessun contratto attivo</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Tabs & Content */}
                <div>
                    <div className="flex gap-1 border-b border-gray-200 mb-6">
                        <button
                            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'overview'
                                ? 'border-indigo-600 text-indigo-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                            onClick={() => setActiveTab('overview')}
                        >
                            <User size={16} /> Panoramica
                        </button>
                        <button
                            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'contracts'
                                ? 'border-indigo-600 text-indigo-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                            onClick={() => setActiveTab('contracts')}
                        >
                            <FileText size={16} /> Contratti
                        </button>
                    </div>

                    <div className="min-h-[400px]">
                        {activeTab === 'overview' && (
                            <div className="animate-fadeIn space-y-6">
                                {/* General Info Section */}
                                <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Informazioni Generali</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                        <div>
                                            <label className="block text-xs text-gray-500 uppercase mb-1">Data Assunzione</label>
                                            <div className="text-base font-medium text-gray-900">
                                                {profile?.hire_date ? safeFormatDate(profile.hire_date.toString(), 'd MMMM yyyy') : '-'}
                                            </div>
                                        </div>
                                        <div>
                                            <label className="block text-xs text-gray-500 uppercase mb-1">Sede di Lavoro</label>
                                            <div className="text-base font-medium text-gray-900">{profile?.location || '-'}</div>
                                        </div>
                                        <div>
                                            <label className="block text-xs text-gray-500 uppercase mb-1">Manager</label>
                                            <div className="text-base font-medium text-gray-900">{profile?.manager_id || '-'}</div>
                                        </div>
                                    </div>
                                </section>
                            </div>
                        )}

                        {activeTab === 'contracts' && (
                            <div className="animate-fadeIn">
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="font-bold text-lg text-gray-900">Storico Contratti</h3>
                                    <button onClick={() => setShowContractModal(true)} className="btn btn-primary btn-sm rounded-lg flex items-center gap-2">
                                        <Plus className="w-4 h-4" /> Gestisci Contratti
                                    </button>
                                </div>

                                {contracts.length === 0 ? (
                                    <div className="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                                        <FileText className="mx-auto text-gray-400 mb-2" size={32} />
                                        <p className="text-gray-500">Nessun contratto registrato</p>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {contracts.map(contract => (
                                            <div key={contract.id} className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:border-gray-300 transition-colors">
                                                <div className="flex items-start gap-3">
                                                    <div className={`p-2 rounded-lg ${!contract.end_date ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                                        <Briefcase size={20} />
                                                    </div>
                                                    <div>
                                                        <div className="font-bold text-gray-900 flex items-center gap-2">
                                                            {contract.contract_type?.name || 'Contratto'}
                                                            {!contract.end_date && <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-green-100 text-green-800">Attivo</span>}
                                                        </div>
                                                        <div className="text-sm text-gray-500 mt-1 flex items-center gap-1">
                                                            <Calendar size={12} />
                                                            {safeFormatDate(contract.start_date.toString())}
                                                            {contract.end_date ? ` - ${safeFormatDate(contract.end_date.toString())}` : ' - Presente'}
                                                        </div>
                                                        {contract.job_title && <div className="text-xs text-gray-400 mt-0.5">{contract.job_title}</div>}
                                                    </div>
                                                </div>
                                                <div className="text-right pl-12 md:pl-0">
                                                    <div className="font-mono font-bold text-gray-900">{contract.weekly_hours}h</div>
                                                    <div className="text-xs text-gray-500 uppercase tracking-wide">settimanali</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Contract Modal */}
            {showContractModal && id && (
                <ContractHistory
                    userId={id}
                    userName={`${user.first_name} ${user.last_name}`}
                    onClose={handleContractModalClose}
                />
            )}
        </div>
    );
}

export default UserDetailPage;
