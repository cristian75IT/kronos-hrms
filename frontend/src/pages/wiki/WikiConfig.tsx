/**
 * KRONOS - Wiki Config Page
 */
import {
    Settings,
    MapPin,
    Layers,
    Calendar,
    Shield,
    ArrowLeft
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/common';

export function WikiConfig() {
    const settings = [
        {
            title: 'Sedi Operative (Locations)',
            icon: MapPin,
            iconColor: 'bg-emerald-500',
            desc: 'Configurazione degli indirizzi fisici dove i dipendenti prestano servizio.',
            details: 'Ogni sede può avere festività locali (es. Santo Patrono) differenziate.'
        },
        {
            title: 'Aree e Dipartimenti',
            icon: Layers,
            iconColor: 'bg-blue-500',
            desc: 'Strutturazione logica dell\'azienda per il raggruppamento dei dipendenti.',
            details: 'Le aree permettono di filtrare report e approvazioni in modo granulare.'
        },
        {
            title: 'Festività e Chiusure',
            icon: Calendar,
            iconColor: 'bg-amber-500',
            desc: 'Gestione del calendario solare aziendale, inclusi i ponti e le chiusure collettive.',
            details: 'Le chiusure possono essere "Totali" o "Parziali" per specifici dipartimenti.'
        }
    ];

    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1">
                        <Settings className="text-amber-600" size={24} />
                        Impostazioni di Sistema
                    </h1>
                    <p className="text-sm text-gray-500">Configurazione globale parametri aziendali</p>
                </div>
                <Button as={Link} to="/wiki" variant="secondary" icon={<ArrowLeft size={18} />}>
                    Torna alla Wiki
                </Button>
            </div>

            {/* Settings Cards */}
            <div className="space-y-4">
                {settings.map((item, idx) => (
                    <div key={idx} className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex flex-col md:flex-row items-start gap-6">
                            <div className={`flex items-center justify-center w-14 h-14 rounded-lg ${item.iconColor} text-white shadow-sm shrink-0`}>
                                <item.icon size={24} />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h3>
                                <p className="text-gray-500 mb-4">{item.desc}</p>
                                <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg border border-gray-100">
                                    <Shield size={16} className="text-amber-500 shrink-0 mt-0.5" />
                                    <p className="text-sm text-gray-600">{item.details}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Admin Warning */}
            <div className="bg-amber-600 rounded-xl p-6 text-white shadow-lg">
                <div className="flex flex-col md:flex-row items-center gap-6">
                    <div className="flex items-center justify-center w-16 h-16 rounded-xl bg-white/10 shrink-0">
                        <Shield size={32} className="text-amber-200" />
                    </div>
                    <div className="flex-1 text-center md:text-left">
                        <h4 className="text-xl font-semibold mb-1">Nota per gli Admin</h4>
                        <p className="text-amber-100 text-sm">
                            Le modifiche alle configurazioni di sistema hanno impatto immediato. Si consiglia di pianificare cambi radicali (es. orari di lavoro) a cavallo tra due mensilità.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default WikiConfig;
