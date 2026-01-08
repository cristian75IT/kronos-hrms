/**
 * KRONOS - Dashboard Page
 * Enterprise command center with premium aesthetics
 */
import { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  AlertCircle,
  CheckCircle,
  Briefcase,
  ArrowRight,
  ChevronRight,
  Bell,
  Target,
  CalendarDays,
  ListChecks
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useBalanceSummary, useLeaveRequests, usePendingApprovals } from '../hooks/domain/useLeaves';
import { useAuth } from '../context/AuthContext';
import type { LeaveRequest } from '../types';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import approvalsService from '../services/approvals.service';
import type { PendingCountResponse } from '../services/approvals.service';

export function DashboardPage() {
  const navigate = useNavigate();
  const { user, isApprover, isHR, isAdmin } = useAuth();
  const { data: balance, isLoading: balanceLoading } = useBalanceSummary(user?.id);
  const { data: pendingApprovals } = usePendingApprovals();
  const { data: recentRequests } = useLeaveRequests(new Date().getFullYear());

  const [approvalCounts, setApprovalCounts] = useState<PendingCountResponse | null>(null);
  const canSeeApprovals = isApprover || isHR || isAdmin;

  useEffect(() => {
    if (canSeeApprovals) {
      approvalsService.getPendingCount().then(setApprovalCounts).catch(() => { });
    }
  }, [canSeeApprovals]);

  const currentDate = new Date();
  const greeting = currentDate.getHours() < 12 ? 'Buongiorno' : currentDate.getHours() < 18 ? 'Buon pomeriggio' : 'Buonasera';

  const stats = [
    {
      label: 'Ferie Disponibili',
      value: balance?.vacation_total_available ?? '-',
      suffix: 'giorni',
      icon: Calendar,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
    {
      label: isApprover ? 'Da Approvare' : 'In Attesa',
      value: isApprover ? (pendingApprovals?.length ?? 0) : (recentRequests?.filter((r: LeaveRequest) => r.status === 'pending').length ?? 0),
      suffix: 'richieste',
      icon: AlertCircle,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
  ];

  const quickActions = [
    {
      label: 'Richiedi Ferie',
      description: 'Nuova richiesta ferie o permessi',
      path: '/leaves/new',
      icon: CalendarDays,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50',
    },
    {
      label: 'Nuova Trasferta',
      description: 'Pianifica una missione di lavoro',
      path: '/trips/new',
      icon: Briefcase,
      color: 'text-cyan-600',
      bg: 'bg-cyan-50',
    },
    {
      label: 'Nota Spese',
      description: 'Registra rimborsi e spese',
      path: '/expenses/new',
      icon: Target,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
  ];

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto pb-8">
      {/* Enterprise Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-6">
        <div>
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            <span className="uppercase tracking-wider text-xs font-bold">KRONOS</span>
            <span>•</span>
            <span>{format(currentDate, 'EEEE d MMMM', { locale: it })}</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            {greeting}, {user?.first_name}
          </h1>
        </div>

        {isApprover && (pendingApprovals?.length ?? 0) > 0 && (
          <Link to="/approvals" className="flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 hover:bg-amber-100 transition-colors text-sm font-medium">
            <Bell size={16} className="text-amber-600" />
            <span>{pendingApprovals?.length} approvazioni in attesa</span>
            <ArrowRight size={14} />
          </Link>
        )}
      </div>

      {/* Stats Grid */}
      {/* Stats Grid - Employee Only */}
      {user?.is_employee !== false && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="p-5 bg-white rounded-lg border border-gray-200 hover:border-primary/50 hover:shadow-sm transition-all"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className={`p-2 rounded-md ${stat.bg} ${stat.color}`}>
                  <stat.icon size={20} />
                </div>
                <div className="text-xs font-bold text-gray-500 uppercase tracking-wide">{stat.label}</div>
              </div>

              <div>
                {balanceLoading ? (
                  <div className="h-8 w-20 bg-gray-100 rounded animate-pulse" />
                ) : (
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-2xl font-bold text-gray-900">
                      {typeof stat.value === 'number' || typeof stat.value === 'string' ? stat.value : '-'}
                    </span>
                    <span className="text-sm font-medium text-gray-400">{stat.suffix}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* AP Expiry Warning - Employee Only */}
      {user?.is_employee !== false && balance?.days_until_ap_expiry && balance.days_until_ap_expiry <= 60 && (
        <div className="p-4 rounded-lg bg-orange-50 border border-orange-200 flex flex-col md:flex-row items-center gap-4">
          <div className="p-2 bg-orange-100 rounded-full text-orange-600">
            <AlertCircle size={20} />
          </div>
          <div className="flex-1 text-center md:text-left">
            <h3 className="text-sm font-bold text-orange-800">Scadenza Ferie Anno Precedente</h3>
            <p className="text-orange-700 text-sm">
              Hai <strong>{balance.vacation_available_ap} giorni</strong> in scadenza tra <strong>{balance.days_until_ap_expiry} giorni</strong>.
            </p>
          </div>
          <Link to="/leaves/new" className="btn btn-sm bg-white text-orange-700 border-orange-200 hover:bg-orange-50 font-medium">
            Pianifica Ora
          </Link>
        </div>
      )}

      {/* Pending Approvals Widget - for Approvers/HR/Admin */}
      {canSeeApprovals && approvalCounts && approvalCounts.total > 0 && (
        <Link to="/approvals/pending" className="block">
          <div className="p-5 rounded-lg bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 hover:border-indigo-300 hover:shadow-md transition-all">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-indigo-100 rounded-lg text-indigo-600">
                <ListChecks size={24} />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900">Approvazioni Centralizzate</h3>
                <p className="text-sm text-gray-600">
                  Hai <strong className="text-indigo-600">{approvalCounts.total}</strong> richieste in attesa di approvazione
                  {approvalCounts.urgent > 0 && (
                    <span className="ml-2 text-red-600">({approvalCounts.urgent} urgenti)</span>
                  )}
                </p>
                {Object.keys(approvalCounts.by_type).length > 0 && (
                  <div className="flex gap-3 mt-2">
                    {Object.entries(approvalCounts.by_type).map(([type, count]) => (
                      <span key={type} className="text-xs px-2 py-0.5 bg-white rounded-full border border-gray-200">
                        {type === 'LEAVE' ? 'Ferie' : type === 'TRIP' ? 'Trasferte' : type === 'EXPENSE' ? 'Note Spese' : type}: {count}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <ArrowRight size={20} className="text-indigo-400" />
            </div>
          </div>
        </Link>
      )}

      {/* Quick Actions & Recent Activity Grid - Employee Only */}
      {user?.is_employee !== false && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Quick Actions */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-lg font-bold text-gray-900">Azioni Rapide</h2>
            <div className="grid gap-3">
              {quickActions.map((action, index) => (
                <Link
                  key={index}
                  to={action.path}
                  className="group flex items-center gap-4 p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all"
                >
                  <div className={`p-2 rounded-md ${action.bg} ${action.color}`}>
                    <action.icon size={20} />
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-sm text-gray-900">{action.label}</div>
                    <div className="text-xs text-gray-500">{action.description}</div>
                  </div>
                  <ChevronRight size={16} className="text-gray-300 group-hover:text-gray-500 transition-colors" />
                </Link>
              ))}
            </div>
          </div>

          {/* Recent Requests */}
          <div className="lg:col-span-3 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900">Richieste Recenti</h2>
              <Link to="/leaves" className="text-primary text-sm font-medium hover:underline">
                Vedi tutte
              </Link>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              {recentRequests?.slice(0, 5).map((request, index) => (
                <div
                  key={request.id}
                  onClick={() => navigate(`/leaves/${request.id}`)}
                  className={`group flex items-center gap-4 p-4 cursor-pointer hover:bg-gray-50 transition-colors ${index !== 0 ? 'border-t border-gray-100' : ''}`}
                >
                  <div className={`w-8 h-8 rounded-md flex items-center justify-center ${request.status === 'approved' ? 'bg-emerald-50 text-emerald-600' :
                    request.status === 'pending' ? 'bg-amber-50 text-amber-600' :
                      request.status === 'rejected' ? 'bg-red-50 text-red-600' :
                        'bg-gray-100 text-gray-400'
                    }`}>
                    {request.status === 'approved' && <CheckCircle size={16} />}
                    {request.status === 'pending' && <Clock size={16} />}
                    {request.status === 'rejected' && <AlertCircle size={16} />}
                    {!['approved', 'pending', 'rejected'].includes(request.status) && <Calendar size={16} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-gray-900">{getLeaveTypeName(request.leave_type_code)}</span>
                      <span className={`px-2 py-0.5 rounded text-[0.65rem] font-bold uppercase ${request.status === 'approved' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' :
                        request.status === 'pending' ? 'bg-amber-50 text-amber-700 border border-amber-100' :
                          request.status === 'rejected' ? 'bg-red-50 text-red-700 border border-red-100' :
                            'bg-gray-100 text-gray-600 border border-gray-200'
                        }`}>
                        {getStatusLabel(request.status)}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {format(new Date(request.start_date), 'd MMM', { locale: it })} - {format(new Date(request.end_date), 'd MMM yyyy', { locale: it })}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-900">{request.days_requested}</div>
                    <div className="text-[0.65rem] text-gray-400 uppercase">gg</div>
                  </div>
                  <ChevronRight size={16} className="text-gray-300 group-hover:text-gray-500 transition-colors" />
                </div>
              ))}
              {(!recentRequests || recentRequests.length === 0) && (
                <div className="flex flex-col items-center justify-center p-8 text-center text-gray-400">
                  <Calendar size={32} className="mb-2 opacity-50" />
                  <p className="text-sm">Nessuna richiesta recente</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function getLeaveTypeName(code: string): string {
  const types: Record<string, string> = {
    'FER': 'Ferie',
    'ROL': 'ROL',
    'PER': 'Permessi',
    'MAL': 'Malattia',
    'LUT': 'Lutto',
    'MAT': 'Matrimonio',
    'L104': 'Legge 104',
    'DON': 'Donazione Sangue',
  };
  return types[code] || code;
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    'approved': 'Approvata',
    'pending': 'In Attesa',
    'rejected': 'Rifiutata',
    'draft': 'Bozza',
    'cancelled': 'Annullata',
  };
  return labels[status] || status;
}

export default DashboardPage;
