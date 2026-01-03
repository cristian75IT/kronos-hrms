/**
 * KRONOS - Leaves Page
 * Main page for managing personal leave requests
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Plus,
  Calendar as CalendarIcon,
  Clock,
  FileText,
  ArrowRight,
  TrendingUp,
  History,
  X
} from 'lucide-react';
import { useLeaveRequests, useBalanceSummary } from '../../hooks/useApi';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/common';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { walletsService } from '../../services/wallets.service';
import { useToast } from '../../context/ToastContext';

export function LeavesPage() {
  const [currentYear] = useState(new Date().getFullYear());
  const { user } = useAuth();
  const toast = useToast();

  const { data: balance } = useBalanceSummary(user?.id);
  const { data: requests } = useLeaveRequests();

  const [isWalletModalOpen, setIsWalletModalOpen] = useState(false);
  const [walletTransactions, setWalletTransactions] = useState<any[]>([]);
  const [isLoadingWallet, setIsLoadingWallet] = useState(false);

  const pendingCount = requests?.filter(r => r.status === 'pending').length || 0;
  const approvedCount = requests?.filter(r => r.status === 'approved').length || 0;

  const loadWalletDetails = async () => {
    if (!user?.id) return;
    setIsLoadingWallet(true);
    try {
      const wallet = await walletsService.getLeavesWallet(user.id, currentYear);
      if (wallet?.id) {
        const transactions = await walletsService.getLeavesTransactions(wallet.id);
        setWalletTransactions(transactions);
      }
    } catch (error) {
      console.error(error);
      toast.error('Errore caricamento dettagli wallet');
    } finally {
      setIsLoadingWallet(false);
    }
  };

  const openWalletModal = () => {
    setIsWalletModalOpen(true);
    loadWalletDetails();
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start border-b border-gray-200 pb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Le Mie Ferie</h1>
          <p className="text-sm text-gray-500">Gestisci le tue richieste di ferie e permessi</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={openWalletModal}
            icon={<History size={18} />}
            className="shrink-0"
          >
            Storico Saldi
          </Button>
          <Button
            as={Link}
            to="/calendar"
            variant="secondary"
            icon={<CalendarIcon size={18} />}
            className="shrink-0"
          >
            Calendario
          </Button>
          <Button
            as={Link}
            to="/leaves/new"
            variant="primary"
            icon={<Plus size={18} />}
            className="shrink-0"
          >
            Nuova Richiesta
          </Button>
        </div>
      </div>

      {/* Balance Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="relative flex items-center gap-4 p-5 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-amber-500 text-white shadow-sm shrink-0">
            <CalendarIcon size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs uppercase font-semibold text-gray-500 tracking-wider mb-0.5">Ferie AP</div>
            <div className="text-2xl font-bold text-gray-900 truncate">{balance?.vacation_available_ap ?? '-'}</div>
          </div>
          {balance?.ap_expiry_date && (
            <div className="absolute top-2 right-2 text-[10px] font-semibold text-amber-800 bg-amber-100 px-1.5 py-0.5 rounded">
              Scade: {new Date(balance.ap_expiry_date).toLocaleDateString('it-IT')}
            </div>
          )}
        </div>
        <div className="flex items-center gap-4 p-5 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-emerald-500 text-white shadow-sm shrink-0">
            <CalendarIcon size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs uppercase font-semibold text-gray-500 tracking-wider mb-0.5">Ferie AC</div>
            <div className="text-2xl font-bold text-gray-900 truncate">{balance?.vacation_available_ac ?? '-'}</div>
          </div>
        </div>
        <div className="flex items-center gap-4 p-5 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-amber-400 text-white shadow-sm shrink-0">
            <Clock size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs uppercase font-semibold text-gray-500 tracking-wider mb-0.5">In Attesa</div>
            <div className="text-2xl font-bold text-gray-900 truncate">{pendingCount}</div>
          </div>
        </div>
        <div className="flex items-center gap-4 p-5 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-indigo-500 text-white shadow-sm shrink-0">
            <FileText size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs uppercase font-semibold text-gray-500 tracking-wider mb-0.5">Approvate</div>
            <div className="text-2xl font-bold text-gray-900 truncate">{approvedCount}</div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-amber-600">AP</span>
          <span>= Anni Precedenti (residuo dall'anno scorso)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-semibold text-emerald-600">AC</span>
          <span>= Anno Corrente (maturato quest'anno)</span>
        </div>
      </div>

      {/* Requests List */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 bg-gray-50/50">
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-3">
            Le Mie Richieste
            {pendingCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">{pendingCount} in attesa</span>
            )}
          </h2>
        </div>

        <div className="divide-y divide-gray-100">
          {requests?.map((request) => (
            <Link
              key={request.id}
              to={`/leaves/${request.id}`}
              className="flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors group"
            >
              <div className={`px-2.5 py-0.5 rounded text-xs font-medium border uppercase tracking-wide ${getStatusBadge(request.status)}`}>
                {getStatusLabel(request.status)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-gray-900">{getLeaveTypeName(request.leave_type_code)}</div>
                <div className="text-sm text-gray-500">
                  {formatDateRange(request.start_date, request.end_date)}
                </div>
              </div>
              <div className="px-2 py-1 bg-gray-100 rounded text-sm font-semibold text-gray-700 group-hover:bg-white border border-transparent group-hover:border-gray-200 transition-all">
                {request.days_requested} gg
              </div>
              <ArrowRight size={16} className="text-gray-300 group-hover:text-indigo-600 transition-colors" />
            </Link>
          ))}

          {(!requests || requests.length === 0) && (
            <div className="flex flex-col items-center gap-3 p-12 text-center text-gray-500">
              <CalendarIcon size={48} className="text-gray-300" />
              <p className="text-lg font-medium text-gray-600">Nessuna richiesta per il {currentYear}</p>
              <p className="text-sm text-gray-400 mb-4">Inizia creando la tua prima richiesta di ferie</p>
              <Link to="/leaves/new" className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors">
                <Plus size={16} />
                Crea Richiesta
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Wallet Transactions Modal */}
      {isWalletModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden animate-scaleIn flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50 shrink-0">
              <h3 className="font-bold text-gray-900 flex items-center gap-2">
                <TrendingUp className="text-indigo-600" size={20} />
                Storico Movimenti Wallet
              </h3>
              <button onClick={() => setIsWalletModalOpen(false)} className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-0">
              {isLoadingWallet ? (
                <div className="flex flex-col items-center justify-center py-12 gap-3">
                  <div className="animate-spin text-indigo-600"><History size={32} /></div>
                  <span className="text-sm text-gray-500">Caricamento movimenti...</span>
                </div>
              ) : walletTransactions.length === 0 ? (
                <div className="text-center py-12 text-gray-400">Nessun movimento registrato.</div>
              ) : (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantità</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Causale</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {walletTransactions.map((tx: any) => (
                      <tr key={tx.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                          {format(new Date(tx.created_at), 'dd/MM/yyyy HH:mm', { locale: it })}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-xs font-semibold text-gray-700">
                          {tx.transaction_type}
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-bold ${tx.amount >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                          {tx.amount > 0 ? '+' : ''}{tx.amount}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500 max-w-xs truncate">
                          {tx.reason || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end shrink-0">
              <Button variant="secondary" onClick={() => setIsWalletModalOpen(false)}>Chiudi</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper functions (same as before)
function getStatusBadge(status: string): string {
  const map: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-700 border-gray-200',
    pending: 'bg-amber-50 text-amber-700 border-amber-200',
    approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    rejected: 'bg-red-50 text-red-700 border-red-200',
    cancelled: 'bg-gray-100 text-gray-700 border-gray-200',
    approved_conditional: 'bg-blue-50 text-blue-700 border-blue-200',
    recalled: 'bg-red-50 text-red-700 border-red-200',
  };
  return map[status] || 'bg-gray-100 text-gray-700 border-gray-200';
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: 'Bozza',
    pending: 'In Attesa',
    approved: 'Approvata',
    rejected: 'Rifiutata',
    cancelled: 'Annullata',
    approved_conditional: 'Condizionale',
    recalled: 'Richiamato',
  };
  return map[status] || status;
}

function getLeaveTypeName(code: string): string {
  const map: Record<string, string> = {
    FER: 'Ferie',
    ROL: 'ROL',
    PAR: 'Permessi',
    MAL: 'Malattia',
    MAT: 'Maternità/Paternità',
    LUT: 'Lutto',
    STU: 'Studio',
    DON: 'Donazione Sangue',
    L104: 'Legge 104',
    SW: 'Smart Working',
    NRT: 'Non Retribuito',
  };
  return map[code] || code;
}

function formatDateRange(start: string, end: string): string {
  const startDate = new Date(start);
  const endDate = new Date(end);

  if (start === end) {
    return format(startDate, 'd MMM yyyy', { locale: it });
  }

  return `${format(startDate, 'd MMM', { locale: it })} - ${format(endDate, 'd MMM yyyy', { locale: it })}`;
}

export default LeavesPage;
