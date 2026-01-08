
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { PageHeader } from '../../components/common/PageHeader';
import { Shield, Smartphone, Mail, User, Key } from 'lucide-react';
import { MfaSetupModal } from '../../components/auth/MfaSetupModal';

export function ProfilePage() {
    const { user } = useAuth();
    const [isMfaModalOpen, setIsMfaModalOpen] = useState(false);

    if (!user) return null;

    return (
        <div className="space-y-6">
            <PageHeader
                title="Il Mio Profilo"
                description="Gestisci le tue informazioni personali e la sicurezza dell'account"
                breadcrumbs={[{ label: 'Home', path: '/' }, { label: 'Profilo' }]}
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* User Info Card */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <User size={20} className="text-blue-600" />
                            Informazioni Personali
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-500 mb-1">Nome Completo</label>
                                <div className="text-gray-900 font-medium">{user.full_name}</div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-500 mb-1">Username</label>
                                <div className="text-gray-900 font-medium">{user.username}</div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-500 mb-1">Email</label>
                                <div className="text-gray-900 font-medium flex items-center gap-2">
                                    <Mail size={16} className="text-gray-400" />
                                    {user.email}
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-500 mb-1">Ruoli</label>
                                <div className="flex flex-wrap gap-2">
                                    {user.roles.map(role => (
                                        <span key={role} className="badge badge-sm badge-secondary">
                                            {role}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Security Card */}
                <div className="space-y-6">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <Shield size={20} className="text-indigo-600" />
                            Sicurezza Account
                        </h3>

                        <div className="space-y-6">
                            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                                <div className="flex items-start gap-3">
                                    <div className="shrink-0 p-2 bg-white rounded-lg border border-gray-100 shadow-sm text-indigo-600">
                                        <Smartphone size={20} />
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-gray-900">Autenticazione a Due Fattori</h4>
                                        <p className="text-sm text-gray-500 mt-1">
                                            Proteggi il tuo account con un livello di sicurezza extra.
                                        </p>
                                        <button
                                            onClick={() => setIsMfaModalOpen(true)}
                                            className="mt-3 btn btn-sm btn-outline btn-primary w-full"
                                        >
                                            <Key size={14} className="mr-2" />
                                            Configura 2FA
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <div className="text-xs text-gray-400 text-center">
                                Per cambiare la password, contatta l'amministratore di sistema o utilizza il portale Keycloak dedicato.
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <MfaSetupModal
                isOpen={isMfaModalOpen}
                onClose={() => setIsMfaModalOpen(false)}
            />
        </div>
    );
}
