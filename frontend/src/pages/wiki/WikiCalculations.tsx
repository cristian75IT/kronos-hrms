/**
 * KRONOS - Wiki Calculations Page
 */
import {
    Calculator,
    CheckCircle2,
    AlertCircle,
    Calendar,
    Clock,
    ArrowLeft
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/common';

export function WikiCalculations() {
    return (
        <div className="space-y-6 animate-fadeIn pb-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1">
                        <Calculator className="text-emerald-600" size={24} />
                        Calcolo Ferie e ROL
                    </h1>
                    <p className="text-sm text-gray-500">Metodologie di calcolo dei ratei mensili</p>
                </div>
                <Button as={Link} to="/wiki" variant="secondary" icon={<ArrowLeft size={18} />}>
                    Torna alla Wiki
                </Button>
            </div>

            {/* Vacation Section */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center gap-3">
                    <Calendar className="text-amber-500" size={20} />
                    <h3 className="font-semibold text-gray-900">Maturazione Ferie (GG)</h3>
                </div>
                <div className="p-6 space-y-4">
                    <p className="text-gray-600">
                        Le ferie maturano su base mensile a condizione che il dipendente abbia lavorato almeno <strong>15 giorni solari</strong> nel mese di riferimento (o secondo quanto previsto dal CCNL specifico).
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Formula Standard</span>
                            <p className="font-mono text-lg font-semibold text-gray-900 mt-1">Giorni_Annuo / 12</p>
                            <p className="text-xs text-gray-500 mt-1">Esempio: 26gg / 12 = 2.16gg al mese</p>
                        </div>
                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Pro-Rata Part Time</span>
                            <p className="font-mono text-lg font-semibold text-gray-900 mt-1">Base_Calcolo × %_Part_Time</p>
                            <p className="text-xs text-gray-500 mt-1">Esempio: 2.16gg × 50% = 1.08gg al mese</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* ROL Section */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center gap-3">
                    <Clock className="text-emerald-500" size={20} />
                    <h3 className="font-semibold text-gray-900">ROL ed Ex-Festività (h)</h3>
                </div>
                <div className="p-6 space-y-4">
                    <p className="text-gray-600">
                        I permessi ROL (Riduzione Orario Lavoro) e le Ex-Festività maturano in <strong>ore</strong>. A differenza delle ferie, la loro quantità può variare significativamente tra i livelli e le anzianità aziendali.
                    </p>
                    <div className="space-y-3">
                        <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg shrink-0">
                                <CheckCircle2 size={18} />
                            </div>
                            <div>
                                <h4 className="font-medium text-gray-900">Arrotondamento</h4>
                                <p className="text-sm text-gray-500 mt-0.5">KRONOS calcola fino a 4 cifre decimali, arrotondando alla seconda per la visualizzazione.</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div className="p-2 bg-amber-100 text-amber-600 rounded-lg shrink-0">
                                <AlertCircle size={18} />
                            </div>
                            <div>
                                <h4 className="font-medium text-gray-900">Scadenza e Residui</h4>
                                <p className="text-sm text-gray-500 mt-0.5">Il sistema gestisce automaticamente il riporto "Anni Precedenti" (AP) e la loro eventuale scadenza (18 o 24 mesi).</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Special Cases */}
            <div className="bg-gray-900 rounded-xl p-6 text-white">
                <h4 className="text-lg font-semibold mb-4">Casi Particolari</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                        <h5 className="font-medium text-indigo-300 mb-1">Assunzioni in corso di mese</h5>
                        <p className="text-sm text-gray-400">Se l'assunzione avviene dopo il giorno 15, la maturazione del primo rateo scatta dal mese successivo.</p>
                    </div>
                    <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                        <h5 className="font-medium text-indigo-300 mb-1">Malattia ed Infortuni</h5>
                        <p className="text-sm text-gray-400">Durante i periodi di malattia ed infortunio, la maturazione dei ratei prosegue regolarmente.</p>
                    </div>
                    <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                        <h5 className="font-medium text-indigo-300 mb-1">Congedi Non Retribuiti</h5>
                        <p className="text-sm text-gray-400">I periodi di congedo non retribuito sospendono la maturazione di tutti i ratei contrattuali.</p>
                    </div>
                    <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                        <h5 className="font-medium text-indigo-300 mb-1">Scatto d'Anzianità</h5>
                        <p className="text-sm text-gray-400">Il raggiungimento di determinati scaglioni può sbloccare bonus di ferie o ROL extra secondo le tabelle CCNL.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default WikiCalculations;
