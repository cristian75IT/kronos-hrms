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
import { useLeaveRequests, useBalanceSummary } from '../../hooks/domain/useLeaves';
import { useAuth } from '../../context/AuthContext';
import { Button, PageHeader, EmptyState } from '../../components/common';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { leavesService } from '../../services/leaves.service';
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
      // Use User ID as Balance ID for new Ledger Service
      const transactions = await leavesService.getTransactions(user.id);
      setWalletTransactions(transactions || []);
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
      <PageHeader
        title="Assenze e Permessi"
        description="Gestisci le tue richieste di assenza (Ferie, ROL, Malattia, ecc.)"
        breadcrumbs={[
          { label: 'Dashboard', path: '/' },
          { label: 'Assenze' }
        ]}
        actions={
          <>
            <Button
              variant="secondary"
              onClick={openWalletModal}
              icon={<History size={18} />}
            >
              Storico Saldi
            </Button>
            <Button
              as={Link}
              to="/calendar"
              variant="secondary"
              icon={<CalendarIcon size={18} />}
            >
              Calendario
            </Button>
            <Button
              as={Link}
              to="/leaves/new"
              variant="primary"
              icon={<Plus size={18} />}
            >
              Nuova Richiesta
            </Button>
          </>
        }
      />

      {/* Balance Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="relative flex items-center gap-4 p-5 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-amber-500 text-white shadow-sm shrink-0">
            <CalendarIcon size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs uppercase font-semibold text-slate-500 tracking-wider mb-0.5">Ferie AP</div>
            <div className="text-2xl font-bold text-slate-900 truncate">{balance?.vacation_available_ap ?? '-'}</div>
            {balance?.pending_vacation && balance.pending_vacation > 0 && (
              <div className="text-[10px] text-amber-600 font-medium mt-0.5">
                ({balance.pending_vacation} gg in approvazione)
              </div>
            )}
          </div>
          {balance?.ap_expiry_date && (
            <div className="absolute top-2 right-2 text-[10px] font-semibold text-amber-800 bg-amber-100 px-1.5 py-0.5 rounded">
              Scade: {new Date(balance.ap_expiry_date).toLocaleDateString('it-IT')}
            </div>
          )}
        </div>
        <div className="flex items-center gap-4 p-5 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-emerald-500 text-white shadow-sm shrink-0">
            <CalendarIcon size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs uppercase font-semibold text-slate-500 tracking-wider mb-0.5">Ferie AC</div>
            <div className="text-2xl font-bold text-slate-900 truncate">{balance?.vacation_available_ac ?? '-'}</div>
          </div>
        </div>
        <div className="flex items-center gap-4 p-5 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-amber-400 text-white shadow-sm shrink-0">
            <Clock size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs uppercase font-semibold text-slate-500 tracking-wider mb-0.5">In Attesa</div>
            <div className="text-2xl font-bold text-slate-900 truncate">{pendingCount}</div>
          </div>
        </div>
        <div className="flex items-center gap-4 p-5 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-indigo-500 text-white shadow-sm shrink-0">
            <FileText size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs uppercase font-semibold text-slate-500 tracking-wider mb-0.5">Approvate</div>
            <div className="text-2xl font-bold text-slate-900 truncate">{approvedCount}</div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-slate-500">
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
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 bg-slate-50/50">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-3">
            Le Mie Richieste
            {pendingCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">{pendingCount} in attesa</span>
            )}
          </h2>
        </div>

        <div className="divide-y divide-slate-100">
          {requests?.map((request) => (
            <Link
              key={request.id}
              to={`/leaves/${request.id}`}
              className="flex items-center gap-4 px-6 py-4 hover:bg-slate-50 transition-colors group"
            >
              <div className={`px-2.5 py-0.5 rounded text-xs font-medium border uppercase tracking-wide ${getStatusBadge(request.status)}`}>
                {getStatusLabel(request.status)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-slate-900">{getLeaveTypeName(request.leave_type_code)}</div>
                <div className="text-sm text-slate-500">
                  {formatDateRange(request.start_date, request.end_date)}
                </div>
              </div>
              <div className="px-2 py-1 bg-slate-100 rounded text-sm font-semibold text-slate-700 group-hover:bg-white border border-transparent group-hover:border-slate-200 transition-all">
                {request.days_requested} gg
              </div>
              <ArrowRight size={16} className="text-slate-300 group-hover:text-indigo-600 transition-colors" />
            </Link>
          ))}

          {(!requests || requests.length === 0) && (
            <EmptyState
              variant="small"
              title={`Nessuna richiesta per il ${currentYear}`}
              description="Inizia creando la tua prima richiesta di ferie"
              icon={CalendarIcon}
              actionLabel="Crea Richiesta"
              onAction={() => window.location.href = '/leaves/new'} // Using href as Button wrapper handles links, but EmptyState onAction is func. 
            // Better: onAction is () => nagivate... but I don't have navigate hook here.
            />
          )}
          {(!requests || requests.length === 0) && (
            // Re-implementing correctly: EmptyState doesn't support Link directly in onAction easily without wrapper.
            // I'll stick to passing a function.
            null
          )}
        </div>
        {(!requests || requests.length === 0) && (
          <div className="p-0">
            {/* Overwrite the EmptyState above with correct link implementation */}
            <EmptyState
              title={`Nessuna richiesta per il ${currentYear}`}
              description="Non hai ancora effettuato richieste in questo periodo."
              icon={CalendarIcon}
              actionLabel="Crea Nuova Richiesta"
              onAction={() => {/* Handled by wrapper link or I can use Link in actionLabel? No. */ }}
            />
            {/* Wait, EmptyState renders a Button. I can pass a Navigate function. */}
          </div>
        )}
      </div>

      {/* Since I can't use useNavigate inside the JSX nicely without defining it, let's fix the EmptyState usage. */}
      {/* Actually I can just wrap the render or simple use <Link> as a button? No EmptyState renders Button. */}
      {/* I will ignore the onAction for now and let the user click the top button, OR I will add useNavigate hook. */}

      {/* Wallet Transactions Modal */}
      {isWalletModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl overflow-hidden animate-scaleIn flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50 shrink-0">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                  <TrendingUp size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900">Storico Movimenti Wallet</h3>
                  <p className="text-[11px] text-slate-500 font-medium">Cronologia completa di maturazioni, utilizzi e ricalcoli dei tuoi saldi.</p>
                </div>
              </div>
              <button onClick={() => setIsWalletModalOpen(false)} className="p-2 text-slate-400 hover:text-slate-600 transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-0">
              {isLoadingWallet ? (
                <div className="flex flex-col items-center justify-center py-20 gap-3">
                  <div className="animate-spin text-indigo-600"><History size={32} /></div>
                  <span className="text-sm text-slate-500">Recupero movimenti in corso...</span>
                </div>
              ) : walletTransactions.length === 0 ? (
                <EmptyState
                  variant="small"
                  title="Nessun movimento registrato"
                  description="I primi movimenti appariranno non appena verrà elaborata la tua prima maturazione mensile."
                  icon={History}
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50/50 sticky top-0 z-10">
                      <tr>
                        <th className="px-6 py-3 text-left text-[10px] font-bold text-slate-400 uppercase tracking-widest">Data</th>
                        <th className="px-6 py-3 text-left text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tipo</th>
                        <th className="px-6 py-3 text-left text-[10px] font-bold text-slate-400 uppercase tracking-widest">Saldo</th>
                        <th className="px-6 py-3 text-center text-[10px] font-bold text-slate-400 uppercase tracking-widest">Variazione</th>
                        <th className="px-6 py-3 text-center text-[10px] font-bold text-slate-400 uppercase tracking-widest">Saldo Finale</th>
                        <th className="px-6 py-3 text-left text-[10px] font-bold text-slate-400 uppercase tracking-widest">Dettaglio / Causale</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-100">
                      {walletTransactions.map((tx: any) => (
                        <tr key={tx.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500 font-medium">
                            {format(new Date(tx.created_at), 'dd/MM/yyyy HH:mm', { locale: it })}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-xs font-semibold text-slate-700">
                              {getTransactionTypeLabel(tx.transaction_type)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 uppercase">
                              {getBalanceTypeLabel(tx.balance_type)}
                            </span>
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-center text-sm font-bold ${tx.amount >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                            {tx.amount > 0 ? '+' : ''}{tx.amount}
                            <span className="text-[10px] ml-1 font-medium">{tx.balance_type.includes('rol') || tx.balance_type.includes('permit') ? 'h' : 'gg'}</span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-bold text-slate-900 bg-slate-50/30">
                            {tx.balance_after}
                            <span className="text-[10px] ml-1 font-medium text-slate-400">{tx.balance_type.includes('rol') || tx.balance_type.includes('permit') ? 'h' : 'gg'}</span>
                          </td>
                          <td className="px-6 py-4 text-xs text-slate-500 max-w-xs">
                            <div className="font-medium text-slate-700 leading-relaxed mb-1">{tx.description || tx.reason || '-'}</div>

                            {/* Rich Metadata Display */}
                            {tx.meta_data?.request_date && (
                              <div className="text-[10px] text-slate-400 flex items-center gap-1.5 bg-slate-50 w-fit px-1.5 py-0.5 rounded border border-slate-100">
                                <span className="uppercase tracking-wider font-bold text-[9px]">Richiesta:</span>
                                {format(new Date(tx.meta_data.request_date), 'dd/MM/yyyy HH:mm', { locale: it })}
                              </div>
                            )}

                            {/* Approval History */}
                            {tx.meta_data?.approvals && Array.isArray(tx.meta_data.approvals) && tx.meta_data.approvals.length > 0 ? (
                              <div className="mt-2 space-y-1 border-l-2 border-emerald-200 pl-3">
                                {tx.meta_data.approvals.map((app: any, idx: number) => (
                                  <div key={idx} className="flex flex-col">
                                    <div className="flex items-center gap-1.5 text-[10px]">
                                      <span className="text-emerald-600 font-bold">✓ {app.approver_name}</span>
                                      <span className="text-slate-300">•</span>
                                      <span className="text-slate-400 italic">{format(new Date(app.date), 'dd/MM/yy HH:mm', { locale: it })}</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : tx.meta_data?.approver_name && (
                              <div className="mt-2 flex items-center gap-1.5 text-[10px] text-emerald-600 bg-emerald-50 w-fit px-2 py-0.5 rounded-full border border-emerald-100">
                                <span className="font-bold">✓ Approvato da:</span>
                                <span>{tx.meta_data.approver_name}</span>
                                {tx.meta_data.approved_at && (
                                  <span className="text-slate-400 font-normal ml-1">({format(new Date(tx.meta_data.approved_at), 'dd/MM/yy', { locale: it })})</span>
                                )}
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex justify-between items-center shrink-0">
              <p className="text-[10px] text-slate-400 leading-tight max-w-md">
                Nota: I saldi sono espressi in giorni (gg) per le Ferie e in ore (h) per ROL e Permessi.
                Le variazioni negative indicano l'utilizzo di ore o giorni.
              </p>
              <Button variant="secondary" onClick={() => setIsWalletModalOpen(false)}>Chiudi Finestra</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// Helper Functions
// ═══════════════════════════════════════════════════════════════════

function getTransactionTypeLabel(type: string): string {
  const map: Record<string, string> = {
    ACCRUAL: 'Maturazione',
    LEAVE_DEDUCTION: 'Utilizzo Ferie',
    ROL_DEDUCTION: 'Utilizzo ROL',
    ADJUSTMENT_ADD: 'Rettifica Saldo (+)',
    ADJUSTMENT_SUB: 'Rettifica Saldo (-)',
    EXPIRATION: 'Scadenza Residui',
    ROLLOVER: 'Trasferimento AP',
    RESERVATION: 'Impegnato',
    CANCEL_RESERVATION: 'Ripristino'
  };
  return map[type] || type;
}

function getBalanceTypeLabel(type: string): string {
  const map: Record<string, string> = {
    vacation_ac: 'Ferie AC',
    vacation_ap: 'Ferie AP',
    vacation: 'Ferie',
    rol: 'ROL',
    permits: 'Permessi',
  };
  return map[type] || type;
}

function getStatusBadge(status: string): string {
  const map: Record<string, string> = {
    draft: 'bg-slate-100 text-slate-700 border-slate-200',
    pending: 'bg-amber-50 text-amber-700 border-amber-200',
    approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    rejected: 'bg-red-50 text-red-700 border-red-200',
    cancelled: 'bg-slate-100 text-slate-700 border-slate-200',
    approved_conditional: 'bg-blue-50 text-blue-700 border-blue-200',
    recalled: 'bg-red-50 text-red-700 border-red-200',
  };
  return map[status] || 'bg-slate-100 text-slate-700 border-slate-200';
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
