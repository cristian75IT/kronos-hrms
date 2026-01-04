/**
 * KRONOS - Wiki Management Page
 */
import {
    Users,
    UserPlus,
    UserMinus,
    FileText,
    ShieldCheck,
    Zap,
    ArrowLeft
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/common';

export function WikiManagement() {
    const actions = [
        {
            title: 'Nuova Assunzione',
            icon: UserPlus,
            iconColor: 'bg-emerald-500',
            desc: 'Criteri per la creazione di un nuovo profilo utente e associazione iniziale del contratto.',
            details: 'Assicurati di avere: Codice Fiscale, Matricola, IBAN e Livello di inquadramento.'
        },
        {
            title: 'Variazione Contrattuale',
            icon: FileText,
            iconColor: 'bg-blue-500',
            desc: 'Come gestire passaggi di livello, cambi di orario (FT/PT) o rinnovi di contratti a termine.',
            details: 'Ogni variazione deve essere registrata con una "Data Inizio Validità" corretta.'
        },
        {
            title: 'Cessazione Rapporto',
            icon: UserMinus,
            iconColor: 'bg-red-500',
            desc: 'Procedura per la disattivazione dell\'utenza e calcolo dei residui spettanti per il TFR.',
            details: 'La disattivazione inibisce l\'accesso al portale ma mantiene i dati storici per 10 anni.'
        },
        {
            title: 'Gestione Permessi Admin',
            icon: ShieldCheck,
            iconColor: 'bg-indigo-500',
            desc: 'Assegnazione dei ruoli e permessi dinamici con logica di Scopes (Global, Area, Own).',
            details: 'La sincronizzazione con Keycloak è automatica. I permessi sono ereditati gerarchicamente.'
        }
    ];

    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1">
                        <Users className="text-blue-600" size={24} />
                        Gestione Dipendenti
                    </h1>
                    <p className="text-sm text-gray-500">Guide alle azioni amministrative sul personale</p>
                </div>
                <Button as={Link} to="/wiki" variant="secondary" icon={<ArrowLeft size={18} />}>
                    Torna alla Wiki
                </Button>
            </div>

            {/* Action Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {actions.map((action, idx) => (
                    <div key={idx} className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-start gap-4">
                            <div className={`flex items-center justify-center w-12 h-12 rounded-lg ${action.iconColor} text-white shadow-sm shrink-0`}>
                                <action.icon size={20} />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h3 className="font-semibold text-gray-900 mb-1">{action.title}</h3>
                                <p className="text-sm text-gray-500 mb-3">{action.desc}</p>
                                <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg border border-blue-100">
                                    <ShieldCheck size={14} className="text-blue-600 shrink-0 mt-0.5" />
                                    <p className="text-xs text-blue-800">{action.details}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Best Practices */}
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-6">
                <h4 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
                    <Zap className="text-amber-500" size={20} />
                    Best Practices Operative
                </h4>
                <div className="space-y-4">
                    <div className="flex items-start gap-4">
                        <span className="text-lg font-bold text-indigo-600 shrink-0">01.</span>
                        <p className="text-sm text-gray-600">Verificare sempre la congruità tra il CCNL selezionato e il livello di inquadramento per evitare errori nei calcoli automatici dei ratei.</p>
                    </div>
                    <div className="flex items-start gap-4">
                        <span className="text-lg font-bold text-indigo-600 shrink-0">02.</span>
                        <p className="text-sm text-gray-600">Le modifiche ai dati anagrafici sensibili (IBAN, Indirizzo) dovrebbero essere validate dalla funzione HR prima dell'export per le paghe.</p>
                    </div>
                    <div className="flex items-start gap-4">
                        <span className="text-lg font-bold text-indigo-600 shrink-0">03.</span>
                        <p className="text-sm text-gray-600">Prima di procedere con una cessazione, assicurarsi che tutti i saldi ferie e ROL siano stati correttamente liquidati o fruiti.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default WikiManagement;
