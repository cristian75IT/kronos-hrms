/**
 * KRONOS - User Management Page
 * Enterprise-grade employee administration with integrated features
 */
import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { userService } from '../../services/userService';
import { leavesService } from '../../services/leaves.service';
import type { UserWithProfile, LeaveBalance } from '../../types';
import {
    Search,
    Filter,
    Plus,
    Loader,
    ShieldCheck,
    Briefcase,
    Building,
    Edit,
    Trash2,
    Zap,
    X,
    Users,
    Calendar,
    Wallet,
    RefreshCcw,
    Clock,
    FileText,
    LayoutGrid,
    List,
    Eye,
    TrendingUp,
    AlertCircle,
} from 'lucide-react';
import { Button, ConfirmModal } from '../../components/common';

interface UserWithBalance extends UserWithProfile {
    balance?: LeaveBalance | null;
}

export function UsersPage() {
    const navigate = useNavigate();
    const { user: currentUser } = useAuth();
    const toast = useToast();
    const [users, setUsers] = useState<UserWithBalance[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isLoadingBalances, setIsLoadingBalances] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedRole, setSelectedRole] = useState<string>('all');
    const [viewMode, setViewMode] = useState<'grid' | 'table'>('table');
    const [showBatchModal, setShowBatchModal] = useState(false);
    const [isProcessing, setIsProcessing] = useState<string | null>(null);
    const [userToDelete, setUserToDelete] = useState<string | null>(null);

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        try {
            setIsLoading(true);
            const data = await userService.getUsers();
            setUsers(data as UserWithBalance[]);
            loadBalances(data as UserWithBalance[]);
        } catch (error) {
            console.error('Failed to load users:', error);
            toast.error('Errore nel caricamento degli utenti');
        } finally {
            setIsLoading(false);
        }
    };

    const loadBalances = async (usersList: UserWithBalance[]) => {
        setIsLoadingBalances(true);
        const year = new Date().getFullYear();
        const updatedUsers = await Promise.all(
            usersList.map(async (user) => {
                try {
                    const balance = await leavesService.getUserBalance(user.id, year);
                    return { ...user, balance };
                } catch {
                    return { ...user, balance: null };
                }
            })
        );
        setUsers(updatedUsers);
        setIsLoadingBalances(false);
    };

    const handleDeleteClick = (userId: string) => {
        setUserToDelete(userId);
    };

    const confirmDeleteUser = async () => {
        if (!userToDelete) return;
        try {
            await userService.deleteUser(userToDelete);
            setUsers(prev => prev.filter(u => u.id !== userToDelete));
            toast.success('Utente eliminato con successo');
            setUserToDelete(null);
        } catch (error) {
            console.error('Failed to delete user:', error);
            toast.error('Errore durante l\'eliminazione');
        }
    };

    const handleBatchAction = async (action: string, apiCall: () => Promise<any>) => {
        setIsProcessing(action);
        try {
            await apiCall();
            toast.success('Operazione completata con successo');
            loadBalances(users);
        } catch (error) {
            toast.error('Errore durante l\'operazione');
        } finally {
            setIsProcessing(null);
        }
    };

    const filteredUsers = users.filter(user => {
        const matchesSearch = (
            (user.first_name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
            (user.last_name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
            (user.email?.toLowerCase() || '').includes(searchTerm.toLowerCase())
        );
        const matchesRole = selectedRole === 'all' ||
            (selectedRole === 'admin' && user.is_admin) ||
            (selectedRole === 'manager' && user.is_manager) ||
            (selectedRole === 'approver' && user.is_approver) ||
            (selectedRole === 'hr' && user.is_hr) ||
            (selectedRole === 'active' && user.is_active) ||
            (selectedRole === 'inactive' && !user.is_active);
        return matchesSearch && matchesRole;
    });

    const getInitials = (first: string, last: string) => {
        return `${first?.charAt(0) || ''}${last?.charAt(0) || ''}`.toUpperCase();
    };

    const totalUsers = users.length;
    const activeUsers = users.filter(u => u.is_active).length;
    const admins = users.filter(u => u.is_admin).length;

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <Loader size={40} className="text-indigo-600 animate-spin mb-4" />
                <p className="text-gray-500 font-medium">Caricamento dipendenti...</p>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1">
                        <Users className="text-indigo-600" size={24} />
                        Gestione Dipendenti
                    </h1>
                    <p className="text-sm text-gray-500">Gestisci l'organico, i contratti, i wallet e i permessi</p>
                </div>
                <div className="flex items-center gap-3">
                    <Button onClick={() => setShowBatchModal(true)} variant="secondary" icon={<Zap size={18} className="text-amber-500" />}>
                        Operazioni Massive
                    </Button>
                    <Link
                        to="/admin/users/new"
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium shadow-sm transition-all hover:shadow-md"
                    >
                        <Plus size={18} />
                        Nuovo Dipendente
                    </Link>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
                            <Users size={20} className="text-indigo-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-gray-900">{totalUsers}</div>
                            <div className="text-xs text-gray-500 uppercase font-medium">Totale Dipendenti</div>
                        </div>
                    </div>
                </div>
                <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                            <TrendingUp size={20} className="text-emerald-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-gray-900">{activeUsers}</div>
                            <div className="text-xs text-gray-500 uppercase font-medium">Attivi</div>
                        </div>
                    </div>
                </div>
                <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                            <ShieldCheck size={20} className="text-purple-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-gray-900">{admins}</div>
                            <div className="text-xs text-gray-500 uppercase font-medium">Amministratori</div>
                        </div>
                    </div>
                </div>
                <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                            <AlertCircle size={20} className="text-amber-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-gray-900">{totalUsers - activeUsers}</div>
                            <div className="text-xs text-gray-500 uppercase font-medium">Non Attivi</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Filters Bar */}
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
                <div className="relative w-full md:w-96">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                    <input
                        type="text"
                        placeholder="Cerca per nome, email..."
                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-3 w-full md:w-auto">
                    <div className="relative flex-1 md:flex-none">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <select
                            className="w-full pl-9 pr-8 py-2.5 bg-white border border-gray-200 rounded-lg appearance-none cursor-pointer hover:border-gray-300 focus:outline-none focus:border-indigo-500 transition-colors text-sm"
                            value={selectedRole}
                            onChange={(e) => setSelectedRole(e.target.value)}
                        >
                            <option value="all">Tutti</option>
                            <option value="admin">Amministratori</option>
                            <option value="manager">Manager</option>
                            <option value="approver">Approvatori</option>
                            <option value="hr">HR</option>
                            <option value="active">Attivi</option>
                            <option value="inactive">Non Attivi</option>
                        </select>
                    </div>
                    <div className="flex bg-gray-100 p-1 rounded-lg">
                        <button
                            onClick={() => setViewMode('table')}
                            className={`p-2 rounded-md transition-all ${viewMode === 'table' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            <List size={18} />
                        </button>
                        <button
                            onClick={() => setViewMode('grid')}
                            className={`p-2 rounded-md transition-all ${viewMode === 'grid' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            <LayoutGrid size={18} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Table View */}
            {viewMode === 'table' && (
                <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="bg-gray-50 border-b border-gray-200">
                                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Dipendente</th>
                                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Ruolo / Dipartimento</th>
                                    <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Ferie Disp.</th>
                                    <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">ROL Disp.</th>
                                    <th className="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Azioni</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {filteredUsers.map(user => (
                                    <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-sm font-bold text-white shadow-sm">
                                                    {getInitials(user.first_name, user.last_name)}
                                                </div>
                                                <div>
                                                    <div className="font-semibold text-gray-900 flex items-center gap-2">
                                                        {user.first_name} {user.last_name}
                                                        {user.is_admin && <ShieldCheck size={14} className="text-indigo-600" title="Amministratore" />}
                                                    </div>
                                                    <div className="text-sm text-gray-500">{user.email}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-wrap gap-1 mb-1">
                                                {user.is_admin && <span className="px-1.5 py-0.5 rounded text-[10px] bg-indigo-100 text-indigo-700 font-medium border border-indigo-200">Admin</span>}
                                                {user.is_manager && <span className="px-1.5 py-0.5 rounded text-[10px] bg-blue-100 text-blue-700 font-medium border border-blue-200">Manager</span>}
                                                {user.is_approver && <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-100 text-purple-700 font-medium border border-purple-200">Appr.</span>}
                                                {user.is_hr && <span className="px-1.5 py-0.5 rounded text-[10px] bg-pink-100 text-pink-700 font-medium border border-pink-200">HR</span>}
                                            </div>
                                            <div className="text-sm font-medium text-gray-900">{user.profile?.position || '-'}</div>
                                            <div className="text-xs text-gray-500">{user.profile?.department || '-'}</div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {isLoadingBalances ? (
                                                <Loader size={14} className="animate-spin text-gray-400 mx-auto" />
                                            ) : (
                                                <span className="font-bold text-gray-900">{user.balance?.vacation_available_total ?? '-'}</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {isLoadingBalances ? (
                                                <Loader size={14} className="animate-spin text-gray-400 mx-auto" />
                                            ) : (
                                                <span className="font-bold text-indigo-600">{user.balance?.rol_available ?? '-'}</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${user.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'}`}>
                                                {user.is_active ? 'Attivo' : 'Non Attivo'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center justify-end gap-1">
                                                <button onClick={() => navigate(`/admin/users/${user.id}`)} className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all" title="Visualizza">
                                                    <Eye size={16} />
                                                </button>
                                                <button onClick={() => navigate(`/admin/users/${user.id}?tab=contracts`)} className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-all" title="Contratti">
                                                    <FileText size={16} />
                                                </button>
                                                <button onClick={() => navigate(`/admin/users/${user.id}?tab=wallet`)} className="p-2 text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-all" title="Wallet">
                                                    <Wallet size={16} />
                                                </button>
                                                <button onClick={() => navigate(`/admin/users/${user.id}/edit`)} className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all" title="Modifica">
                                                    <Edit size={16} />
                                                </button>
                                                {currentUser?.id !== user.id && (
                                                    <button onClick={() => handleDeleteClick(user.id)} className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all" title="Elimina">
                                                        <Trash2 size={16} />
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {filteredUsers.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-12 text-center">
                                            <Search className="mx-auto text-gray-300 mb-3" size={40} />
                                            <p className="text-gray-500 font-medium">Nessun dipendente trovato</p>
                                            <p className="text-sm text-gray-400">Prova a modificare i termini di ricerca</p>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Grid View */}
            {viewMode === 'grid' && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {filteredUsers.map(user => (
                        <div key={user.id} className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all overflow-hidden">
                            <div className="p-5 border-b border-gray-100 bg-gradient-to-b from-gray-50/50">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-lg font-bold text-white shadow-lg">
                                        {getInitials(user.first_name, user.last_name)}
                                    </div>
                                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${user.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'}`}>
                                        {user.is_active ? 'Attivo' : 'Non Attivo'}
                                    </span>
                                </div>
                                <h3 className="font-bold text-gray-900 flex items-center gap-2">
                                    {user.first_name} {user.last_name}
                                    {user.is_admin && <ShieldCheck size={14} className="text-indigo-600" title="Amministratore" />}
                                </h3>
                                <p className="text-sm text-gray-500 truncate">{user.email}</p>
                            </div>
                            <div className="p-4 space-y-3">
                                <div className="flex items-center gap-2 text-sm">
                                    <Briefcase size={14} className="text-gray-400" />
                                    <span className="text-gray-600 truncate">{user.profile?.position || 'Nessuna posizione'}</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm">
                                    <Building size={14} className="text-gray-400" />
                                    <span className="text-gray-600 truncate">{user.profile?.department || 'Nessun dipartimento'}</span>
                                </div>
                                <div className="flex flex-wrap gap-1 pt-1">
                                    {user.is_admin && <span className="px-1.5 py-0.5 rounded text-[10px] bg-indigo-100 text-indigo-700 font-medium border border-indigo-200">Admin</span>}
                                    {user.is_manager && <span className="px-1.5 py-0.5 rounded text-[10px] bg-blue-100 text-blue-700 font-medium border border-blue-200">Manager</span>}
                                    {user.is_approver && <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-100 text-purple-700 font-medium border border-purple-200">Approver</span>}
                                    {user.is_hr && <span className="px-1.5 py-0.5 rounded text-[10px] bg-pink-100 text-pink-700 font-medium border border-pink-200">HR</span>}
                                </div>
                                <div className="flex gap-2 pt-2">
                                    <div className="flex-1 bg-amber-50 rounded-lg p-2 text-center">
                                        <div className="text-lg font-bold text-amber-700">
                                            {isLoadingBalances ? <Loader size={14} className="animate-spin mx-auto" /> : (user.balance?.vacation_available_total ?? '-')}
                                        </div>
                                        <div className="text-[10px] text-amber-600 uppercase font-medium">Ferie</div>
                                    </div>
                                    <div className="flex-1 bg-indigo-50 rounded-lg p-2 text-center">
                                        <div className="text-lg font-bold text-indigo-700">
                                            {isLoadingBalances ? <Loader size={14} className="animate-spin mx-auto" /> : (user.balance?.rol_available ?? '-')}
                                        </div>
                                        <div className="text-[10px] text-indigo-600 uppercase font-medium">ROL</div>
                                    </div>
                                </div>
                            </div>
                            <div className="p-3 border-t border-gray-100 bg-gray-50/50 flex gap-2">
                                <button onClick={() => navigate(`/admin/users/${user.id}`)} className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-all">
                                    <Eye size={14} /> Dettagli
                                </button>
                                <button onClick={() => navigate(`/admin/users/${user.id}?tab=wallet`)} className="flex items-center justify-center gap-1.5 px-3 py-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-lg text-sm font-medium transition-all">
                                    <Wallet size={14} />
                                </button>
                            </div>
                        </div>
                    ))}
                    {filteredUsers.length === 0 && (
                        <div className="col-span-full flex flex-col items-center justify-center p-12 bg-white rounded-xl border-2 border-dashed border-gray-200">
                            <Search className="text-gray-300 mb-3" size={48} />
                            <h3 className="text-lg font-bold text-gray-600">Nessun dipendente trovato</h3>
                            <p className="text-sm text-gray-400">Prova a modificare i termini di ricerca</p>
                        </div>
                    )}
                </div>
            )}

            {/* Batch Operations Modal */}
            {showBatchModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fadeIn" onClick={() => setShowBatchModal(false)}>
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden animate-scaleIn" onClick={e => e.stopPropagation()}>
                        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50/50">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                                    <Zap size={20} className="text-amber-600" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-gray-900">Operazioni Massive</h3>
                                    <p className="text-xs text-gray-500">Esegui operazioni su tutti i dipendenti</p>
                                </div>
                            </div>
                            <button onClick={() => setShowBatchModal(false)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                                <X size={20} className="text-gray-400" />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <button disabled={!!isProcessing} onClick={() => handleBatchAction('accruals', () => leavesService.processAccruals(new Date().getFullYear(), new Date().getMonth() + 1))} className="p-5 border border-gray-200 rounded-xl hover:border-indigo-300 hover:bg-indigo-50/50 text-left transition-all disabled:opacity-50">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
                                            {isProcessing === 'accruals' ? <Loader size={18} className="animate-spin text-indigo-600" /> : <Calendar size={18} className="text-indigo-600" />}
                                        </div>
                                        <h4 className="font-bold text-gray-900">Maturazione Mensile</h4>
                                    </div>
                                    <p className="text-xs text-gray-500 leading-relaxed">Genera i ratei ferie e ROL per il mese corrente su tutti i dipendenti attivi.</p>
                                </button>
                                <button disabled={!!isProcessing} onClick={() => handleBatchAction('expirations', () => leavesService.processExpirations())} className="p-5 border border-gray-200 rounded-xl hover:border-red-300 hover:bg-red-50/50 text-left transition-all disabled:opacity-50">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                                            {isProcessing === 'expirations' ? <Loader size={18} className="animate-spin text-red-600" /> : <Clock size={18} className="text-red-600" />}
                                        </div>
                                        <h4 className="font-bold text-gray-900">Scadenza Pacchetti</h4>
                                    </div>
                                    <p className="text-xs text-gray-500 leading-relaxed">Rimuove i saldi scaduti (ferie AP, ROL) dai wallet di tutti i dipendenti.</p>
                                </button>
                                <button disabled={!!isProcessing} onClick={() => handleBatchAction('recalc', () => leavesService.recalculateAccruals())} className="p-5 border border-gray-200 rounded-xl hover:border-purple-300 hover:bg-purple-50/50 text-left transition-all disabled:opacity-50">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                                            {isProcessing === 'recalc' ? <Loader size={18} className="animate-spin text-purple-600" /> : <RefreshCcw size={18} className="text-purple-600" />}
                                        </div>
                                        <h4 className="font-bold text-gray-900">Ricalcola Saldi</h4>
                                    </div>
                                    <p className="text-xs text-gray-500 leading-relaxed">Ricalcola tutti i saldi partendo dai contratti. Usare solo per correzioni.</p>
                                </button>
                                <button disabled={!!isProcessing} onClick={() => handleBatchAction('rollover', () => leavesService.processRollover(new Date().getFullYear() - 1))} className="p-5 border border-gray-200 rounded-xl hover:border-amber-300 hover:bg-amber-50/50 text-left transition-all disabled:opacity-50">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                                            {isProcessing === 'rollover' ? <Loader size={18} className="animate-spin text-amber-600" /> : <TrendingUp size={18} className="text-amber-600" />}
                                        </div>
                                        <h4 className="font-bold text-gray-900">Rollover Annuale</h4>
                                    </div>
                                    <p className="text-xs text-gray-500 leading-relaxed">Trasferisce i residui dell'anno precedente nei pacchetti AP del nuovo anno.</p>
                                </button>
                            </div>
                            <div className="p-4 bg-blue-50 border border-blue-100 rounded-lg flex gap-3">
                                <AlertCircle size={18} className="text-blue-600 shrink-0 mt-0.5" />
                                <div className="text-sm text-blue-800">
                                    <p className="font-medium">Nota importante</p>
                                    <p className="text-blue-700">Le operazioni massive vengono applicate a tutti i dipendenti attivi. Per controllo granulare, usa la funzione anteprima in Strumenti Admin.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Info Footer */}
            <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl flex gap-3 text-sm text-blue-800">
                <ShieldCheck className="shrink-0 text-blue-600" size={20} />
                <div>
                    <p className="font-semibold">Nota sulla sicurezza</p>
                    <p className="opacity-80">Le modifiche ai ruoli e ai wallet vengono registrate automaticamente per conformità e audit aziendale.</p>
                </div>
            </div>

            <ConfirmModal
                isOpen={!!userToDelete}
                onClose={() => setUserToDelete(null)}
                onConfirm={confirmDeleteUser}
                title="Elimina Dipendente"
                message="Sei sicuro di voler eliminare questo dipendente? Questa azione è irreversibile e rimuoverà anche lo storico contratti, il wallet e i dati sulle presenze."
                confirmLabel="Elimina"
                variant="danger"
            />
        </div>
    );
}

export default UsersPage;
