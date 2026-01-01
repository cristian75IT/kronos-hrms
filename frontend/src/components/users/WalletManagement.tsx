/**
 * KRONOS - Wallet Management Component
 * Allows admins to view and adjust user leave/ROL balances
 */
import { useState, useEffect } from 'react';
import {
    Wallet,
    Plus,
    History,
    Calendar,
    AlertCircle,
    CheckCircle,
    Info,
    ChevronDown,
    ArrowUpRight,
    ArrowDownLeft
} from 'lucide-react';
import { leavesService } from '../../services/leaves.service';
import type { LeaveBalance } from '../../types';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { useToast } from '../../context/ToastContext';

interface WalletManagementProps {
    userId: string;
    userName: string;
}

export function WalletManagement({ userId, userName }: WalletManagementProps) {
    const [balance, setBalance] = useState<LeaveBalance | null>(null);
    const [transactions, setTransactions] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showAdjustModal, setShowAdjustModal] = useState(false);
    const [year] = useState(new Date().getFullYear());
    const toast = useToast();

    // Adjustment Form State
    const [adjustForm, setAdjustForm] = useState({
        balance_type: 'vacation_ac',
        amount: 0,
        reason: '',
        expiry_date: ''
    });

    useEffect(() => {
        loadData();
    }, [userId, year]);

    const loadData = async () => {
        setIsLoading(true);
        try {
            const balanceData = await leavesService.getUserBalance(userId, year);
            setBalance(balanceData);

            if (balanceData?.id) {
                const txData = await leavesService.getTransactions(balanceIdToId(balanceData.id));
                setTransactions(txData);
            }
        } catch (error) {
            console.error('Failed to load wallet data', error);
            // toast.error('Errore nel caricamento del wallet');
        } finally {
            setIsLoading(false);
        }
    };

    // Helper to handle UUID vs string ID consistency
    const balanceIdToId = (id: any) => typeof id === 'object' ? id.id || id : id;

    const handleAdjust = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await leavesService.adjustBalance(userId, year, {
                ...adjustForm,
                expiry_date: adjustForm.expiry_date || undefined
            });
            toast.success('Wallet aggiornato con successo');
            setShowAdjustModal(false);
            setAdjustForm({
                balance_type: 'vacation_ac',
                amount: 0,
                reason: '',
                expiry_date: ''
            });
            loadData();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Errore nell\'aggiornamento del wallet');
        }
    };

    if (isLoading && !balance) {
        return (
            <div className="flex justify-center items-center py-12">
                <div className="spinner-md" />
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Balances Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Vacation Card */}
                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Calendar size={48} />
                    </div>
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Ferie Totali</h4>
                    <div className="text-3xl font-black text-gray-900 mb-4 flex items-baseline gap-1">
                        {balance?.vacation_available_total || 0}
                        <span className="text-sm font-medium text-gray-500">gg</span>
                    </div>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-500">Anno Corrente (AC):</span>
                            <span className="font-semibold text-gray-900">{balance?.vacation_available_ac || 0} gg</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-500">Anno Precedente (AP):</span>
                            <span className="font-semibold text-gray-900">{balance?.vacation_available_ap || 0} gg</span>
                        </div>
                    </div>
                </div>

                {/* ROL Card */}
                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Wallet size={48} />
                    </div>
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">ROL Disponibili</h4>
                    <div className="text-3xl font-black text-indigo-600 mb-4 flex items-baseline gap-1">
                        {balance?.rol_available || 0}
                        <span className="text-sm font-medium text-indigo-400">h</span>
                    </div>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-500">Maturati quest'anno:</span>
                            <span className="font-semibold text-gray-900">{balance?.rol_accrued || 0} h</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-500">Residui anno prec.:</span>
                            <span className="font-semibold text-gray-900">{balance?.rol_previous_year || 0} h</span>
                        </div>
                    </div>
                </div>

                {/* Permits Card */}
                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Info size={48} />
                    </div>
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Ex Festività</h4>
                    <div className="text-3xl font-black text-amber-600 mb-4 flex items-baseline gap-1">
                        {balance?.permits_available || 0}
                        <span className="text-sm font-medium text-amber-400">h</span>
                    </div>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-500">Totale spettanza:</span>
                            <span className="font-semibold text-gray-900">{balance?.permits_total || 0} h</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-500">Utilizzati:</span>
                            <span className="font-semibold text-gray-900">{balance?.permits_used || 0} h</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Actions Bar */}
            <div className="flex justify-between items-center bg-indigo-50 p-4 rounded-xl border border-indigo-100">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-sm">
                        <Plus size={20} />
                    </div>
                    <div>
                        <h4 className="font-bold text-indigo-900">Operazioni Wallet</h4>
                        <p className="text-xs text-indigo-700">Aggiungi o rimuovi ferie/ROL manualmente</p>
                    </div>
                </div>
                <button
                    onClick={() => setShowAdjustModal(true)}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold shadow-md transition-all transform active:scale-95"
                >
                    Effettua Ricarica
                </button>
            </div>

            {/* Transactions History */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                    <h4 className="font-bold text-gray-900 flex items-center gap-2">
                        <History size={18} className="text-gray-400" />
                        Storico Movimenti
                    </h4>
                    <span className="text-xs text-gray-500 uppercase font-semibold">Anno {year}</span>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-gray-50 text-[10px] uppercase font-black text-gray-400 tracking-widest">
                                <th className="px-6 py-3">Data</th>
                                <th className="px-6 py-3">Tipo</th>
                                <th className="px-6 py-3">Variazione</th>
                                <th className="px-6 py-3">Note / Scadenza</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {transactions.length === 0 ? (
                                <tr>
                                    <td colSpan={4} className="px-6 py-12 text-center text-gray-400 italic">
                                        Nessun movimento registrato per questo periodo
                                    </td>
                                </tr>
                            ) : (
                                transactions.map((tx) => (
                                    <tr key={tx.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="text-sm font-medium text-gray-900">
                                                {format(new Date(tx.created_at), 'd MMM yyyy', { locale: it })}
                                            </div>
                                            <div className="text-[10px] text-gray-400">
                                                {format(new Date(tx.created_at), 'HH:mm')}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide border ${tx.transaction_type === 'adjustment'
                                                    ? 'bg-indigo-50 text-indigo-700 border-indigo-100'
                                                    : tx.transaction_type === 'accrual'
                                                        ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
                                                        : 'bg-gray-50 text-gray-600 border-gray-100'
                                                }`}>
                                                {tx.balance_type.replace('_', ' ')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-1.5 font-black">
                                                {tx.amount > 0 ? (
                                                    <ArrowUpRight size={14} className="text-emerald-500" />
                                                ) : (
                                                    <ArrowDownLeft size={14} className="text-rose-500" />
                                                )}
                                                <span className={tx.amount > 0 ? 'text-emerald-700' : 'text-rose-700'}>
                                                    {tx.amount > 0 ? '+' : ''}{tx.amount}
                                                    <span className="text-[10px] ml-0.5">
                                                        {tx.balance_type.includes('vacation') ? 'gg' : 'h'}
                                                    </span>
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm text-gray-900 max-w-xs">{tx.reason || '-'}</div>
                                            {tx.expiry_date && (
                                                <div className="mt-1 flex items-center gap-1.5 text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded inline-flex">
                                                    <AlertCircle size={10} />
                                                    SCADE IL {format(new Date(tx.expiry_date), 'dd/MM/yyyy')}
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Adjustment Modal */}
            {showAdjustModal && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm animate-fadeIn">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-zoomIn">
                        <div className="bg-indigo-600 p-6 text-white text-center relative">
                            <button
                                onClick={() => setShowAdjustModal(false)}
                                className="absolute top-4 right-4 text-white/70 hover:text-white transition-colors"
                            >
                                <ChevronDown className="rotate-90" />
                            </button>
                            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 border-2 border-white/30">
                                <Plus size={32} />
                            </div>
                            <h3 className="text-xl font-black uppercase tracking-wider">Ricarica Wallet</h3>
                            <p className="text-indigo-100/80 text-sm mt-1">{userName}</p>
                        </div>

                        <form onSubmit={handleAdjust} className="p-8 space-y-5">
                            <div className="space-y-2">
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest">Tipo di Voce</label>
                                <select
                                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition-all font-medium"
                                    value={adjustForm.balance_type}
                                    onChange={e => setAdjustForm({ ...adjustForm, balance_type: e.target.value })}
                                    required
                                >
                                    <option value="vacation_ac">Ferie (Anno Corrente)</option>
                                    <option value="vacation_ap">Ferie (Anno Precedente)</option>
                                    <option value="rol">ROL</option>
                                    <option value="permits">Ex Festività</option>
                                </select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest">Quantità</label>
                                    <div className="relative">
                                        <input
                                            type="number"
                                            step="0.01"
                                            className="w-full pl-4 pr-10 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition-all font-black text-lg"
                                            value={adjustForm.amount}
                                            onChange={e => setAdjustForm({ ...adjustForm, amount: parseFloat(e.target.value) })}
                                            required
                                        />
                                        <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none text-gray-400 font-bold">
                                            {adjustForm.balance_type.includes('vacation') ? 'gg' : 'h'}
                                        </div>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest">Scadenza (opz.)</label>
                                    <input
                                        type="date"
                                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition-all font-medium"
                                        value={adjustForm.expiry_date}
                                        onChange={e => setAdjustForm({ ...adjustForm, expiry_date: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest">Nota / Causale</label>
                                <textarea
                                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition-all font-medium min-h-[100px]"
                                    placeholder="Inserisci una nota per questo movimento..."
                                    value={adjustForm.reason}
                                    onChange={e => setAdjustForm({ ...adjustForm, reason: e.target.value })}
                                    required
                                    minLength={10}
                                />
                                <p className="text-[10px] text-gray-400 flex items-center gap-1 mt-1">
                                    <Info size={10} />
                                    Minimo 10 caratteri per ragioni di audit.
                                </p>
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setShowAdjustModal(false)}
                                    className="flex-1 px-4 py-3 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-xl font-bold transition-all"
                                >
                                    Annulla
                                </button>
                                <button
                                    type="submit"
                                    className="flex-[2] px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2"
                                >
                                    <CheckCircle size={18} />
                                    Conferma Ricarica
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
