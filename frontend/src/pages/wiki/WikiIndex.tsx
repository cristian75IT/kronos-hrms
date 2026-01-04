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
    Activity
} from 'lucide-react';
import { Link } from 'react-router-dom';

export function WikiIndex() {
    const wikiSections = [
        {
            title: 'Configuratore CCNL',
            description: 'Scopri come configurare i Contratti Collettivi Nazionali, i livelli e i parametri di maturazione.',
            icon: FileText,
            iconColor: 'bg-indigo-500',
            link: '/wiki/contracts',
            keywords: ['CCNL', 'Livelli', 'Inquadramento']
        },
        {
            title: 'Calcolo Ferie e ROL',
            description: 'Dettagli tecnici sulle modalità di calcolo, ratei mensili e differenze tra i vari modelli contrattuali.',
            icon: Calculator,
            iconColor: 'bg-emerald-500',
            link: '/wiki/calculations',
            keywords: ['Ratei', 'Ferie', 'ROL', 'Maturazione']
        },
        {
            title: 'Gestione Dipendenti',
            description: 'Guida alle azioni amministrative: assunzioni, variazioni contrattuali e gestione dei profili.',
            icon: Users,
            iconColor: 'bg-blue-500',
            link: '/wiki/management',
            keywords: ['Dipendenti', 'Azioni', 'Anagrafica']
        },
        {
            title: 'Impostazioni di Sistema',
            description: 'Configurazione globale delle festività, chiusure aziendali e parametri di sede.',
            icon: Settings,
            iconColor: 'bg-amber-500',
            link: '/wiki/config',
            keywords: ['Sedi', 'Aree', 'Festività']
        },
        {
            title: 'Sicurezza & RBAC',
            description: 'Approfondimento sul modello di permessi dinamici, gerarchie di ruoli e integrazione Keycloak.',
            icon: Shield,
            iconColor: 'bg-indigo-600',
            link: '/wiki/security',
            keywords: ['RBAC', 'Permessi', 'Scopes', 'Keycloak']
        },
        {
            title: 'Reporting HR & Compliance',
            description: 'Guida ai report di conformità (D.Lgs 81/08), dashboard workforce e snapshots giornalieri.',
            icon: Activity,
            iconColor: 'bg-rose-500',
            link: '/wiki/reporting',
            keywords: ['Reporting', 'Conformità', 'Snapshots', '81/08']
        }
    ];

    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1">
                        <Book className="text-indigo-600" size={24} />
                        Wiki & Documentazione
                    </h1>
                    <p className="text-sm text-gray-500">Centro risorse e guide operative per KRONOS</p>
                </div>
            </div>

            {/* Wiki Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {wikiSections.map((section, idx) => (
                    <Link
                        key={idx}
                        to={section.link}
                        className="group bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md hover:border-gray-300 transition-all"
                    >
                        <div className="flex items-start gap-4">
                            <div className={`flex items-center justify-center w-12 h-12 rounded-lg ${section.iconColor} text-white shadow-sm shrink-0`}>
                                <section.icon size={20} />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h3 className="font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors mb-1">
                                    {section.title}
                                </h3>
                                <p className="text-sm text-gray-500 leading-relaxed mb-3">
                                    {section.description}
                                </p>
                                <div className="flex flex-wrap gap-2">
                                    {section.keywords.map(kw => (
                                        <span key={kw} className="text-xs font-medium text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                                            #{kw}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <ChevronRight className="text-gray-300 group-hover:text-indigo-500 transition-colors shrink-0" size={20} />
                        </div>
                    </Link>
                ))}
            </div>

        </div>
    );
}

export default WikiIndex;
