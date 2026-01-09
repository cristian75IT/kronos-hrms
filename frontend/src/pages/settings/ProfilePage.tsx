/**
 * KRONOS - Profile Page
 * Enterprise user profile with security management
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import {
    Shield,
    Smartphone,
    Mail,
    User,
    Key,
    CheckCircle,
    AlertTriangle,
    Loader2,
    Lock,
    Building,
    Badge,
    Calendar,
    Briefcase,
    ChevronRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { MfaSetupModal } from '../../components/auth/MfaSetupModal';
import { authService } from '../../services/authService';
import { tokenStorage } from '../../utils/tokenStorage';

export function ProfilePage() {
    const { user, refreshUser } = useAuth();
    const toast = useToast();
    const [isMfaModalOpen, setIsMfaModalOpen] = useState(false);
    const [isDisabling2FA, setIsDisabling2FA] = useState(false);
    const [disableCode, setDisableCode] = useState('');
    const [showDisableForm, setShowDisableForm] = useState(false);

    // Password change state
    const [showPasswordForm, setShowPasswordForm] = useState(false);
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isChangingPassword, setIsChangingPassword] = useState(false);

    if (!user) return null;

    const handleDisable2FA = async () => {
        if (disableCode.length !== 6) return;
        setIsDisabling2FA(true);
        try {
            const token = tokenStorage.getAccessToken();
            if (!token) throw new Error("No session");
            await authService.disableMfa(token, disableCode);
            toast.success('Autenticazione a due fattori disattivata');
            setShowDisableForm(false);
            setDisableCode('');
            if (refreshUser) await refreshUser();
        } catch (error: unknown) {
            const err = error as { message?: string };
            toast.error(err.message || 'Errore disattivazione 2FA');
        } finally {
            setIsDisabling2FA(false);
        }
    };

    const handleChangePassword = async () => {
        if (newPassword !== confirmPassword) {
            toast.error('Le password non coincidono');
            return;
        }
        if (newPassword.length < 8) {
            toast.error('La password deve contenere almeno 8 caratteri');
            return;
        }
        setIsChangingPassword(true);
        try {
            const token = tokenStorage.getAccessToken();
            if (!token) throw new Error("No session");
            await authService.changePassword(token, currentPassword, newPassword, confirmPassword);
            toast.success('Password modificata con successo');
            setShowPasswordForm(false);
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch (error: unknown) {
            const err = error as { message?: string };
            toast.error(err.message || 'Errore cambio password');
        } finally {
            setIsChangingPassword(false);
        }
    };

    const handleMfaSetupComplete = async () => {
        setIsMfaModalOpen(false);
        if (refreshUser) await refreshUser();
    };

    const currentDate = new Date();

    // Profile info items
    const profileItems = [
        { icon: Mail, label: 'Email', value: user.email, color: 'text-blue-600', bg: 'bg-blue-50' },
        { icon: Badge, label: 'Username', value: user.username, color: 'text-indigo-600', bg: 'bg-indigo-50' },
        { icon: Building, label: 'Organizzazione', value: 'KRONOS Enterprise', color: 'text-purple-600', bg: 'bg-purple-50' },
        { icon: Briefcase, label: 'Ruoli', value: user.roles?.join(', ') || 'Employee', color: 'text-emerald-600', bg: 'bg-emerald-50' },
    ];

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto pb-8">
            {/* Enterprise Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-6">
                <div>
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                        <span className="uppercase tracking-wider text-xs font-bold">KRONOS</span>
                        <span>•</span>
                        <span>{format(currentDate, 'EEEE d MMMM', { locale: it })}</span>
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900">
                        Il Mio Profilo
                    </h1>
                    <p className="text-sm text-gray-500 mt-1">
                        Gestisci le tue informazioni personali e la sicurezza dell'account
                    </p>
                </div>

                {/* User Avatar Badge */}
                <div className="flex items-center gap-4 px-4 py-3 bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 rounded-lg">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                        {user.first_name?.charAt(0)}{user.last_name?.charAt(0)}
                    </div>
                    <div>
                        <div className="font-bold text-gray-900">{user.full_name}</div>
                        <div className="text-xs text-gray-500">{user.email}</div>
                    </div>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {profileItems.map((item, index) => (
                    <div
                        key={index}
                        className="p-4 bg-white rounded-lg border border-gray-200 hover:border-primary/50 hover:shadow-sm transition-all"
                    >
                        <div className="flex items-center gap-3 mb-2">
                            <div className={`p-2 rounded-md ${item.bg} ${item.color}`}>
                                <item.icon size={18} />
                            </div>
                            <div className="text-xs font-bold text-gray-500 uppercase tracking-wide">{item.label}</div>
                        </div>
                        <div className="text-sm font-semibold text-gray-900 truncate">{item.value}</div>
                    </div>
                ))}
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

                {/* Security Section - Left Column */}
                <div className="lg:col-span-2 space-y-4">
                    <h2 className="text-lg font-bold text-gray-900">Sicurezza Account</h2>

                    {/* 2FA Card */}
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <div className="p-4 border-b border-gray-100">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-md ${user.mfa_enabled ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'}`}>
                                    <Smartphone size={20} />
                                </div>
                                <div className="flex-1">
                                    <div className="font-semibold text-sm text-gray-900">Autenticazione 2FA</div>
                                    <div className={`inline-flex items-center gap-1.5 mt-1 px-2 py-0.5 rounded text-xs font-bold ${user.mfa_enabled
                                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                                        : 'bg-amber-50 text-amber-700 border border-amber-100'
                                        }`}>
                                        {user.mfa_enabled ? (
                                            <><CheckCircle size={12} /> Attivo</>
                                        ) : (
                                            <><AlertTriangle size={12} /> Non attivo</>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-4 bg-gray-50">
                            <p className="text-xs text-gray-500 mb-3">
                                {user.mfa_enabled
                                    ? 'Il tuo account è protetto con autenticazione a due fattori.'
                                    : 'Proteggi il tuo account con un secondo livello di verifica.'}
                            </p>

                            {user.mfa_enabled ? (
                                showDisableForm ? (
                                    <div className="space-y-3">
                                        <input
                                            type="text"
                                            value={disableCode}
                                            onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                            placeholder="Codice 6 cifre"
                                            className="w-full px-3 py-2 text-center text-lg tracking-[0.5em] font-mono border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                        />
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => { setShowDisableForm(false); setDisableCode(''); }}
                                                className="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                                            >
                                                Annulla
                                            </button>
                                            <button
                                                onClick={handleDisable2FA}
                                                disabled={isDisabling2FA || disableCode.length !== 6}
                                                className="flex-1 px-3 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                            >
                                                {isDisabling2FA ? <Loader2 size={14} className="animate-spin" /> : <Key size={14} />}
                                                Disattiva
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <button
                                        onClick={() => setShowDisableForm(true)}
                                        className="w-full px-3 py-2 text-sm font-medium text-red-700 bg-white border border-red-200 rounded-md hover:bg-red-50 flex items-center justify-center gap-2"
                                    >
                                        <Key size={14} />
                                        Disattiva 2FA
                                    </button>
                                )
                            ) : (
                                <button
                                    onClick={() => setIsMfaModalOpen(true)}
                                    className="w-full px-3 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 flex items-center justify-center gap-2"
                                >
                                    <Shield size={14} />
                                    Configura 2FA
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Password Card */}
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <div className="p-4 border-b border-gray-100">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-md bg-indigo-50 text-indigo-600">
                                    <Lock size={20} />
                                </div>
                                <div>
                                    <div className="font-semibold text-sm text-gray-900">Password</div>
                                    <div className="text-xs text-gray-500">Modifica la password del tuo account</div>
                                </div>
                            </div>
                        </div>

                        <div className="p-4 bg-gray-50">
                            {showPasswordForm ? (
                                <div className="space-y-3">
                                    <input
                                        type="password"
                                        value={currentPassword}
                                        onChange={(e) => setCurrentPassword(e.target.value)}
                                        placeholder="Password attuale"
                                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    <input
                                        type="password"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        placeholder="Nuova password (min 8 caratteri)"
                                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    <input
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        placeholder="Conferma nuova password"
                                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    />
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => {
                                                setShowPasswordForm(false);
                                                setCurrentPassword('');
                                                setNewPassword('');
                                                setConfirmPassword('');
                                            }}
                                            className="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                                        >
                                            Annulla
                                        </button>
                                        <button
                                            onClick={handleChangePassword}
                                            disabled={isChangingPassword || !currentPassword || !newPassword || !confirmPassword}
                                            className="flex-1 px-3 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                        >
                                            {isChangingPassword ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
                                            Salva
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <button
                                    onClick={() => setShowPasswordForm(true)}
                                    className="w-full px-3 py-2 text-sm font-medium text-indigo-700 bg-white border border-indigo-200 rounded-md hover:bg-indigo-50 flex items-center justify-center gap-2"
                                >
                                    <Lock size={14} />
                                    Cambia Password
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                {/* Account Details - Right Column */}
                <div className="lg:col-span-3 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-gray-900">Dettagli Account</h2>
                    </div>

                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        {/* Full Name */}
                        <div className="flex items-center gap-4 p-4 border-b border-gray-100">
                            <div className="p-2 bg-indigo-50 rounded-md text-indigo-600">
                                <User size={18} />
                            </div>
                            <div className="flex-1">
                                <div className="text-xs font-bold text-gray-500 uppercase tracking-wide">Nome Completo</div>
                                <div className="text-sm font-semibold text-gray-900 mt-0.5">{user.full_name}</div>
                            </div>
                        </div>

                        {/* Email */}
                        <div className="flex items-center gap-4 p-4 border-b border-gray-100">
                            <div className="p-2 bg-blue-50 rounded-md text-blue-600">
                                <Mail size={18} />
                            </div>
                            <div className="flex-1">
                                <div className="text-xs font-bold text-gray-500 uppercase tracking-wide">Email</div>
                                <div className="text-sm font-semibold text-gray-900 mt-0.5">{user.email}</div>
                            </div>
                        </div>

                        {/* Hire Date */}
                        {user.profile?.hire_date && (
                            <div className="flex items-center gap-4 p-4 border-b border-gray-100">
                                <div className="p-2 bg-emerald-50 rounded-md text-emerald-600">
                                    <Calendar size={18} />
                                </div>
                                <div className="flex-1">
                                    <div className="text-xs font-bold text-gray-500 uppercase tracking-wide">Data Assunzione</div>
                                    <div className="text-sm font-semibold text-gray-900 mt-0.5">
                                        {format(new Date(user.profile.hire_date), 'd MMMM yyyy', { locale: it })}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Roles */}
                        <div className="flex items-center gap-4 p-4 border-b border-gray-100">
                            <div className="p-2 bg-purple-50 rounded-md text-purple-600">
                                <Shield size={18} />
                            </div>
                            <div className="flex-1">
                                <div className="text-xs font-bold text-gray-500 uppercase tracking-wide">Ruoli Assegnati</div>
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {user.roles?.map((role: string) => (
                                        <span
                                            key={role}
                                            className="px-2 py-1 text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100 rounded-md"
                                        >
                                            {role}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Account Status */}
                        <div className="flex items-center gap-4 p-4">
                            <div className="p-2 bg-emerald-50 rounded-md text-emerald-600">
                                <CheckCircle size={18} />
                            </div>
                            <div className="flex-1">
                                <div className="text-xs font-bold text-gray-500 uppercase tracking-wide">Stato Account</div>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-100 rounded">
                                        <CheckCircle size={10} /> Attivo
                                    </span>
                                    <span className="text-xs text-gray-400">• Verificato</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <div className="p-4 border-b border-gray-100">
                            <div className="text-sm font-bold text-gray-900">Link Rapidi</div>
                        </div>
                        <div className="divide-y divide-gray-100">
                            <Link to="/leaves" className="flex items-center gap-3 p-4 hover:bg-gray-50 transition-colors group">
                                <div className="p-2 bg-emerald-50 rounded-md text-emerald-600">
                                    <Calendar size={16} />
                                </div>
                                <div className="flex-1 text-sm font-medium text-gray-900">Le Mie Ferie</div>
                                <ChevronRight size={16} className="text-gray-300 group-hover:text-gray-500" />
                            </Link>
                            <Link to="/trips" className="flex items-center gap-3 p-4 hover:bg-gray-50 transition-colors group">
                                <div className="p-2 bg-cyan-50 rounded-md text-cyan-600">
                                    <Briefcase size={16} />
                                </div>
                                <div className="flex-1 text-sm font-medium text-gray-900">Le Mie Trasferte</div>
                                <ChevronRight size={16} className="text-gray-300 group-hover:text-gray-500" />
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            <MfaSetupModal
                isOpen={isMfaModalOpen}
                onClose={handleMfaSetupComplete}
            />
        </div>
    );
}

export default ProfilePage;
