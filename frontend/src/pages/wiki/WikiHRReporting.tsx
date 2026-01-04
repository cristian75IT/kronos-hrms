/**
 * KRONOS - Wiki HR Reporting & Compliance Page
 */
import {
    Activity,
    ClipboardList,
    GraduationCap,
    Stethoscope,
    AlertTriangle,
    BarChart3,
    ArrowLeft,
    CheckCircle2,
    Clock
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/common';

export function WikiHRReporting() {
    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1">
                        <Activity className="text-rose-600" size={24} />
                        HR Reporting & Compliance
                    </h1>
                    <p className="text-sm text-gray-500">Monitoraggio forza lavoro e conformità normativa</p>
                </div>
                <Button as={Link} to="/wiki" variant="secondary" icon={<ArrowLeft size={18} />}>
                    Torna alla Wiki
                </Button>
            </div>

            {/* Dashboards & Metrics */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center gap-3">
                    <BarChart3 className="text-blue-500" size={20} />
                    <h3 className="font-semibold text-gray-900">Dashboard & Metriche Real-time</h3>
                </div>
                <div className="p-6">
                    <p className="text-gray-600 mb-4">
                        Il modulo di reporting fornisce una visione immediata dello stato dell'azienda, aggregando dati da tutti i microservizi.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                            <CheckCircle2 className="text-emerald-500 shrink-0 mt-0.5" size={16} />
                            <div>
                                <h4 className="text-sm font-semibold text-gray-900">Workforce Status</h4>
                                <p className="text-xs text-gray-500">Conteggio real-time di dipendenti attivi, in missione, in ferie o in malattia.</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                            <Clock className="text-indigo-500 shrink-0 mt-0.5" size={16} />
                            <div>
                                <h4 className="text-sm font-semibold text-gray-900">Absence Rate</h4>
                                <p className="text-xs text-gray-500">Calcolo automatico del tasso di assenteismo giornaliero e mensile.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Safety Compliance Section */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center gap-3">
                    <AlertTriangle className="text-amber-500" size={20} />
                    <h3 className="font-semibold text-gray-900">Conformità D.Lgs. 81/08</h3>
                </div>
                <div className="p-6 space-y-6">
                    <p className="text-gray-600">
                        KRONOS monitora attivamente la sicurezza sul lavoro e la sorveglianza sanitaria per proteggere l'azienda da rischi legali.
                    </p>

                    <div className="space-y-4">
                        <div className="flex gap-4">
                            <div className="w-10 h-10 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center shrink-0">
                                <GraduationCap size={20} />
                            </div>
                            <div className="flex-1">
                                <h4 className="font-semibold text-gray-900 text-sm">Formazione Obbligatoria</h4>
                                <p className="text-xs text-gray-500 mt-1">
                                    Tracciamento dei corsi (Generale, Specifica, Antincendio, Primo Soccorso). Il sistema segnala automaticamente le scadenze imminenti e i certificati mancanti.
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-4">
                            <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
                                <Stethoscope size={20} />
                            </div>
                            <div className="flex-1">
                                <h4 className="font-semibold text-gray-900 text-sm">Sorveglianza Sanitaria</h4>
                                <p className="text-xs text-gray-500 mt-1">
                                    Gestione delle visite mediche periodiche e dell'idoneità lavorativa. Include il monitoraggio delle limitazioni o prescrizioni impartite dal medico competente.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Automated Reports */}
            <div className="bg-gray-900 rounded-xl p-6 text-white">
                <h4 className="text-lg font-semibold mb-2 flex items-center gap-2">
                    <ClipboardList className="text-rose-400" size={20} />
                    Report Automatizzati
                </h4>
                <p className="text-sm text-gray-400 mb-6">Il sistema genera periodicamente i seguenti flussi di dati:</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                        <h5 className="text-rose-300 font-medium text-sm mb-2">Daily Snapshot</h5>
                        <p className="text-xs text-gray-500 leading-relaxed">Ogni notte viene salvata una "fotografia" dello stato aziendale per analisi storiche di trend.</p>
                    </div>
                    <div>
                        <h5 className="text-rose-300 font-medium text-sm mb-2">Monthly Statement</h5>
                        <p className="text-xs text-gray-500 leading-relaxed">Chiusura mensile con aggregazione di ore lavorate, ferie godute e giustificativi per lo studio paghe.</p>
                    </div>
                    <div>
                        <h5 className="text-rose-300 font-medium text-sm mb-2">Alerts Engine</h5>
                        <p className="text-xs text-gray-500 leading-relaxed">Notifiche proattive in caso di anomalie nei saldi o violazioni delle policy aziendali.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default WikiHRReporting;
