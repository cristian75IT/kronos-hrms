/**
 * KRONOS - Wiki Security & RBAC Page
 */
import {
    Shield,
    Lock,
    Key,
    ArrowLeft,
    GitBranch
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/common';

export function WikiSecurity() {
    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1">
                        <Shield className="text-indigo-600" size={24} />
                        Sicurezza & RBAC
                    </h1>
                    <p className="text-sm text-gray-500">Gestione dei permessi e controllo degli accessi</p>
                </div>
                <Button as={Link} to="/wiki" variant="secondary" icon={<ArrowLeft size={18} />}>
                    Torna alla Wiki
                </Button>
            </div>

            {/* RBAC Overview */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center gap-3">
                    <Lock className="text-indigo-500" size={20} />
                    <h3 className="font-semibold text-gray-900">Dynamic Scoped RBAC</h3>
                </div>
                <div className="p-6 space-y-4">
                    <p className="text-gray-600">
                        KRONOS utilizza un sistema di <strong>Access Controllo Basato sui Ruoli (RBAC)</strong> dinamico e granulare. A differenza dei sistemi statici, ogni permesso è associato a uno <strong>Scope</strong> (Ambito) che definisce su quali risorse l'utente può agire.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                        <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-100">
                            <h4 className="font-bold text-indigo-900 text-sm mb-1 uppercase tracking-wider">GLOBAL</h4>
                            <p className="text-xs text-indigo-700">Accesso totale a tutte le risorse dell'azienda su tutte le sedi e aree.</p>
                        </div>
                        <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                            <h4 className="font-bold text-blue-900 text-sm mb-1 uppercase tracking-wider">AREA</h4>
                            <p className="text-xs text-blue-700">Accesso limitato ai dipendenti appartenenti alla propria Area o Dipartimento.</p>
                        </div>
                        <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-100">
                            <h4 className="font-bold text-emerald-900 text-sm mb-1 uppercase tracking-wider">OWN</h4>
                            <p className="text-xs text-emerald-700">Accesso limitato esclusivamente ai propri dati personali.</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Role Hierarchy */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center gap-3">
                    <GitBranch className="text-purple-500" size={20} />
                    <h3 className="font-semibold text-gray-900">Gerarchia dei Ruoli (Inheritance)</h3>
                </div>
                <div className="p-6 space-y-4">
                    <p className="text-gray-600 leading-relaxed">
                        I ruoli sono organizzati gerarchicamente. Un ruolo "Genitore" eredita automaticamente tutti i permessi dei ruoli "Figli".
                    </p>
                    <div className="flex flex-col space-y-2 border-l-2 border-indigo-200 ml-4 pl-6">
                        <div className="flex items-center gap-2">
                            <span className="p-1 px-3 bg-indigo-600 text-white rounded-full text-xs font-bold">Admin</span>
                            <span className="text-gray-400 text-xs">→ Eredita tutto (Superuser)</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="p-1 px-3 bg-blue-600 text-white rounded-full text-xs font-bold">Manager</span>
                            <span className="text-gray-400 text-xs">→ Eredita da Approver + Gestione Team</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="p-1 px-3 bg-teal-600 text-white rounded-full text-xs font-bold">Approver</span>
                            <span className="text-gray-400 text-xs">→ Approvazione ferie, spese e trasferte</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="p-1 px-3 bg-amber-600 text-white rounded-full text-xs font-bold">Employee</span>
                            <span className="text-gray-400 text-xs">→ Accesso standard ai propri servizi</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Keycloak Sync */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center gap-3">
                    <Key className="text-amber-500" size={20} />
                    <h3 className="font-semibold text-gray-900">Integrazione Keycloak</h3>
                </div>
                <div className="p-6 space-y-4">
                    <p className="text-gray-600 leading-relaxed">
                        L'autenticazione è gestita centralmente tramite <strong>Keycloak</strong>. Il sistema sincronizza automaticamente gli utenti e i loro ruoli realm al primo login.
                    </p>
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-100 flex items-start gap-3">
                        <Shield className="text-amber-500 shrink-0 mt-0.5" size={16} />
                        <div className="text-xs text-gray-500 space-y-1">
                            <p><strong>Note Operativa:</strong> Se un utente viene creato in Keycloak ma non ha un contratto in KRONOS, potrà accedere ma avrà funzionalità limitate (Basic User).</p>
                            <p>Le password non risiedono mai nel database di KRONOS.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default WikiSecurity;
