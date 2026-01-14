/**
 * KRONOS - Wiki Index Page
 */
import {
    Book,
    Calculator,
    Settings,
    Users,
    FileText,
    ChevronRight,
    Shield,
    Bell,
    Database,
    Zap,
    Briefcase
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export function WikiIndex() {
    const { isAdmin, isHR } = useAuth();

    const checkAccess = (allowedRoles: string[]) => {
        if (isAdmin) return true;
        if (allowedRoles.includes('all')) return true;
        if (allowedRoles.includes('hr') && isHR) return true;
        return false;
    };

    const wikiSections = [
        {
            category: "HR & Organizzativo",
            items: [
                {
                    title: 'Gestione Dipendenti',
                    description: 'Assunzioni, variazioni contrattuali, anagrafiche e gestione dei profili utente.',
                    icon: Users,
                    link: '/wiki/management',
                    keywords: ['Dipendenti', 'Contratti', 'Anagrafica'],
                    allowedRoles: ['hr']
                },
                {
                    title: 'Configuratore CCNL',
                    description: 'Configurazione Contratti Collettivi Nazionali, livelli e parametri di maturazione.',
                    icon: FileText,
                    link: '/wiki/contracts',
                    keywords: ['CCNL', 'Livelli', 'Inquadramento'],
                    allowedRoles: ['hr']
                },
                {
                    title: 'Reporting HR & Compliance',
                    description: 'Report di conformità (D.Lgs 81/08), dashboard workforce e statistiche assenze.',
                    icon: Briefcase,
                    link: '/wiki/reporting',
                    keywords: ['Reporting', 'Conformità', '81/08'],
                    allowedRoles: ['hr']
                }
            ]
        },
        {
            category: "Amministrazione & Finanza",
            items: [
                {
                    title: 'Calcolo Ferie e ROL',
                    description: 'Logiche di maturazione, ratei mensili, arrotondamenti e differenze contrattuali.',
                    icon: Calculator,
                    link: '/wiki/calculations',
                    keywords: ['Ratei', 'Ferie', 'ROL', 'Maturazione'],
                    allowedRoles: ['all']
                },
                {
                    title: 'Riconciliazione Ledger',
                    description: 'Documentazione sul sistema di auto-fix e verifica congruenza saldo vs transazioni.',
                    icon: Zap,
                    link: '/wiki/reconciliation',
                    keywords: ['Ledger', 'Audit', 'Ricalcolo'],
                    allowedRoles: ['hr']
                }
            ]
        },
        {
            category: "Sistema & Sicurezza",
            items: [
                {
                    title: 'Impostazioni di Sistema',
                    description: 'Configurazione globale festività, chiusure e parametri di funzionamento.',
                    icon: Settings,
                    link: '/wiki/config',
                    keywords: ['Config', 'Sedi', 'Festività'],
                    allowedRoles: ['admin']
                },
                {
                    title: 'Sicurezza & RBAC',
                    description: 'Modello di permessi, ruoli utenti e Audit Trail delle operazioni sensibili.',
                    icon: Shield,
                    link: '/wiki/security',
                    keywords: ['RBAC', 'Permessi', 'Audit Log', 'GDPR'],
                    allowedRoles: ['admin']
                },
                {
                    title: 'Centro Notifiche',
                    description: 'Gestione flussi di comunicazione, template email e log di invio.',
                    icon: Bell,
                    link: '/wiki/notifications',
                    keywords: ['Email', 'Push', 'Template'],
                    allowedRoles: ['admin']
                },
                {
                    title: 'Manutenzione Dati',
                    description: 'Procedure di rollover annuale, pulizia cache e importazione massiva.',
                    icon: Database,
                    link: '/wiki/maintenance',
                    keywords: ['Rollover', 'Import', 'Cache'],
                    allowedRoles: ['admin']
                }
            ]
        }
    ];

    const visibleSections = wikiSections
        .map(section => ({
            ...section,
            items: section.items.filter(item => checkAccess(item.allowedRoles))
        }))
        .filter(section => section.items.length > 0);

    return (
        <div className="space-y-8 animate-fadeIn pb-12">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-slate-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
                        <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                            <Book size={28} />
                        </div>
                        Wiki & Documentazione
                    </h1>
                    <p className="text-sm text-slate-500 mt-2">Centro risorse, guide operative e riferimenti tecnici per KRONOS</p>
                </div>
            </div>

            {/* Wiki Sections */}
            <div className="space-y-10">
                {visibleSections.map((section, idx) => (
                    <div key={idx}>
                        <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 pl-1">
                            {section.category}
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {section.items.map((item, itemIdx) => (
                                <Link
                                    key={itemIdx}
                                    to={item.link}
                                    className="group bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all duration-200 flex flex-col h-full"
                                >
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg group-hover:bg-indigo-600 group-hover:text-white transition-colors duration-200">
                                            <item.icon size={20} />
                                        </div>
                                        <ChevronRight className="text-slate-300 group-hover:text-indigo-500 transition-colors" size={18} />
                                    </div>

                                    <h3 className="font-semibold text-slate-900 mb-2 group-hover:text-indigo-700 transition-colors">
                                        {item.title}
                                    </h3>

                                    <p className="text-sm text-slate-500 leading-relaxed mb-4 flex-grow">
                                        {item.description}
                                    </p>

                                    <div className="flex flex-wrap gap-2 mt-auto">
                                        {item.keywords.map(kw => (
                                            <span key={kw} className="text-[10px] font-medium text-slate-500 bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
                                                #{kw}
                                            </span>
                                        ))}
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {visibleSections.length === 0 && (
                <div className="text-center py-20 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                    <Book className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                    <h3 className="text-lg font-medium text-slate-900">Nessuna guida disponibile</h3>
                    <p className="text-slate-500">Non hai i permessi per visualizzare la documentazione.</p>
                </div>
            )}
        </div>
    );
}

export default WikiIndex;
