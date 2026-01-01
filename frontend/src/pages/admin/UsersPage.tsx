/**
 * KRONOS - User Management Page
 * Premium Enterprise Administration
 */
import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { userService } from '../../services/userService';
import type { UserWithProfile } from '../../types';
import {
    Search,
    Filter,
    Plus,
    Loader,
    ShieldCheck,
    Briefcase,
    Building,
    Shield,
    Edit,
    Trash2,
} from 'lucide-react';

export function UsersPage() {
    const navigate = useNavigate();
    const { user: currentUser } = useAuth();
    const toast = useToast();
    const [users, setUsers] = useState<UserWithProfile[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedRole, setSelectedRole] = useState<string>('all');

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        try {
            const data = await userService.getUsers();
            setUsers(data as UserWithProfile[]);
        } catch (error) {
            console.error('Failed to load users:', error);
            toast.error('Errore nel caricamento degli utenti');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteUser = async (userId: string) => {
        if (!window.confirm('Sei sicuro di voler eliminare questo utente?')) return;

        try {
            await userService.deleteUser(userId);
            setUsers(users.filter(u => u.id !== userId));
            toast.success('Utente eliminato con successo');
        } catch (error) {
            console.error('Failed to delete user:', error);
            toast.error('Errore durante l\'eliminazione');
        }
    };

    const filteredUsers = users.filter(user => {
        const matchesSearch = (
            (user.first_name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
            (user.last_name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
            (user.email?.toLowerCase() || '').includes(searchTerm.toLowerCase())
        );
        const matchesRole = selectedRole === 'all' ||
            (selectedRole === 'admin' && user.is_superuser) ||
            (selectedRole === 'manager' && !user.is_superuser); // Simplified role logic for demo

        return matchesSearch && matchesRole;
    });

    const getInitials = (first: string, last: string) => {
        return `${first?.charAt(0) || ''}${last?.charAt(0) || ''}`.toUpperCase();
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <Loader size={40} className="text-indigo-600 animate-spin mb-4" />
                <p className="text-gray-500 font-medium">Caricamento utenti...</p>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-fadeIn pb-12">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 mb-1">Dipendenti</h1>
                    <p className="text-gray-500">Gestisci l'organico, i ruoli e i permessi.</p>
                </div>
                <Link
                    to="/admin/users/new"
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium shadow-sm transition-all hover:shadow-md hover:-translate-y-0.5"
                >
                    <Plus size={20} />
                    Nuovo Dipendente
                </Link>
            </div>

            {/* Filters Bar */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col md:flex-row gap-4 items-center justify-between">
                <div className="relative w-full md:w-96">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                    <input
                        type="text"
                        placeholder="Cerca per nome, email o ruolo..."
                        className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                <div className="flex items-center gap-3 w-full md:w-auto">
                    <div className="relative flex-1 md:flex-none">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <select
                            className="w-full pl-9 pr-8 py-2 bg-white border border-gray-200 rounded-lg appearance-none cursor-pointer hover:border-gray-300 focus:outline-none focus:border-indigo-500 transition-colors text-sm"
                            value={selectedRole}
                            onChange={(e) => setSelectedRole(e.target.value)}
                        >
                            <option value="all">Tutti i Ruoli</option>
                            <option value="admin">Amministratori</option>
                            <option value="manager">Manager</option>
                            <option value="employee">Dipendenti</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Grid View */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredUsers.map(user => (
                    <div key={user.id} className="group bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-1 overflow-hidden flex flex-col">
                        <div className="p-6 flex flex-col items-center border-b border-gray-50 bg-gradient-to-b from-gray-50/50 to-transparent">
                            <div className="relative mb-4">
                                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-xl font-bold text-white shadow-lg shadow-indigo-200">
                                    {getInitials(user.first_name, user.last_name)}
                                </div>
                                {user.is_superuser && (
                                    <div className="absolute -bottom-1 -right-1 bg-white p-1 rounded-full shadow-sm" title="Admin">
                                        <ShieldCheck size={16} className="text-indigo-600 shrink-0" />
                                    </div>
                                )}
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate w-full text-center">{user.first_name} {user.last_name}</h3>
                            <p className="text-sm text-gray-500 truncate w-full text-center">{user.email}</p>
                        </div>
                        <div className="p-6 pt-4 flex-1 flex flex-col justify-between">
                            <div className="space-y-2 text-sm text-gray-600 mb-4">
                                <div className="flex items-center gap-2">
                                    <Briefcase size={16} className="text-gray-400" />
                                    <span>{user.profile?.position || 'Nessuna posizione'}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Building size={16} className="text-gray-400" />
                                    <span>{user.profile?.department || 'Nessun dipartimento'}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Shield size={16} className="text-gray-400" />
                                    <span>{user.is_superuser ? 'Amministratore' : 'Dipendente'}</span>
                                </div>
                            </div>
                            <div className="flex gap-2 mt-auto">
                                <button
                                    onClick={(e) => { e.stopPropagation(); navigate(`/admin/users/${user.id}`); }}
                                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 rounded-lg font-medium transition-colors text-sm"
                                >
                                    <Edit size={16} /> Modifica
                                </button>
                                {currentUser?.id !== user.id && ( // Prevent user from deleting themselves
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleDeleteUser(user.id); }}
                                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg font-medium transition-colors text-sm"
                                    >
                                        <Trash2 size={16} /> Elimina
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
                {filteredUsers.length === 0 && (
                    <div className="col-span-full flex flex-col items-center justify-center p-12 bg-white rounded-xl border-2 border-dashed border-gray-200 text-gray-400">
                        <Search size={48} strokeWidth={1} />
                        <h3 className="text-lg font-bold mt-3 text-gray-600">Nessun utente trovato</h3>
                        <p className="text-sm">Prova a modificare i termini di ricerca.</p>
                    </div>
                )}
            </div >

            {/* Simple Info Footer */}
            < div className="p-4 bg-blue-50 border border-blue-100 rounded-lg flex gap-3 text-sm text-blue-800" >
                <ShieldCheck className="shrink-0 text-blue-600" size={20} />
                <div>
                    <p className="font-semibold">Nota sulla sicurezza</p>
                    <p className="opacity-80">Le modifiche ai ruoli amministrativi vengono registrate nel log di audit per conformità aziendale.</p>
                </div>
            </div >
        </div >
    );
}

export default UsersPage;
