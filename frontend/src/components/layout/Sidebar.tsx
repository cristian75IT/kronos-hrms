/**
 * KRONOS - Main Sidebar Layout Component
 * Enterprise Styled with Tailwind CSS
 */
import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Calendar,
  Briefcase,
  FileText,
  Settings,
  Users,
  LayoutDashboard,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Sun,
  Moon,
  Book,
  Terminal,
  Activity,
  Bell,
  Mail,
  History as HistoryIcon,
  GraduationCap,
  TreePalm,
  Plane,
  Receipt,
  GitBranch,
  Shield,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { clsx } from 'clsx';
import { Logo } from '../common/Logo';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  permission?: string;
}

// Base items
const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} /> },
  { label: 'Lavoro Agile', path: '/smart-working', icon: <Briefcase size={20} /> },
  { label: 'Le Mie Ferie', path: '/leaves', icon: <TreePalm size={20} />, permission: 'leaves:view' },
  { label: 'Trasferte', path: '/trips', icon: <Briefcase size={20} />, permission: 'trips:view' },
  { label: 'Note Spese', path: '/expenses', icon: <FileText size={20} />, permission: 'expenses:view' },
  { label: 'Calendario', path: '/calendar', icon: <Calendar size={20} />, permission: 'calendar:view' },
  { label: 'Documenti & Wiki', path: '/wiki', icon: <Book size={20} />, permission: 'wiki:view' },
];

// Approver section
const approverItems: NavItem[] = [
  { label: 'Approvazioni', path: '/approvals/pending', icon: <Users size={20} />, permission: 'approvals:process' },
];

// Admin Sections
const adminAccessItems: NavItem[] = [
  { label: 'Gestione Utenti', path: '/admin/users', icon: <Users size={20} />, permission: 'users:view' },
  { label: 'Gestione Ruoli', path: '/admin/roles', icon: <Shield size={20} />, permission: 'roles:view' },
  { label: 'Organizzazione', path: '/admin/organization', icon: <Briefcase size={20} />, permission: 'settings:edit' },
];

const adminConfigItems: NavItem[] = [
  { label: 'Workflow Approvazioni', path: '/admin/workflows', icon: <GitBranch size={20} />, permission: 'approvals:config' },
  { label: 'Calendari di Sistema', path: '/admin/system-calendars', icon: <Calendar size={20} />, permission: 'calendar:manage' },
  { label: 'Contratti CCNL', path: '/admin/national-contracts', icon: <FileText size={20} />, permission: 'contracts:view' },
  { label: 'Tipi Assenza', path: '/admin/leave-types', icon: <TreePalm size={20} />, permission: 'settings:edit' },
  { label: 'Strumenti Admin', path: '/admin/tools', icon: <Settings size={20} />, permission: 'settings:edit' },
];

const adminLogItems: NavItem[] = [
  { label: 'Centro Notifiche', path: '/admin/notifications', icon: <Bell size={20} />, permission: 'notifications:send' },
  { label: 'Log Email', path: '/admin/email-logs', icon: <Mail size={20} />, permission: 'notifications:view' },
  { label: 'Audit Log', path: '/admin/audit-logs', icon: <Terminal size={20} />, permission: 'audit:view' },
  { label: 'Audit Trail', path: '/admin/audit-trail', icon: <HistoryIcon size={20} />, permission: 'audit:view' },
];

// HR Section
const hrItems: NavItem[] = [
  { label: 'HR Console', path: '/hr/console', icon: <LayoutDashboard size={20} />, permission: 'reports:view' },
  { label: 'Report Presenze', path: '/hr/reports', icon: <Activity size={20} />, permission: 'reports:view' },
  { label: 'Formazione', path: '/hr/training', icon: <GraduationCap size={20} />, permission: 'training:view' },
  { label: 'Gestione Ferie', path: '/hr/leaves', icon: <TreePalm size={20} />, permission: 'leaves:manage' },
  { label: 'Gestione Trasferte', path: '/hr/trips', icon: <Plane size={20} />, permission: 'trips:manage' },
  { label: 'Gestione Spese', path: '/hr/expenses', icon: <Receipt size={20} />, permission: 'expenses:manage' },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  });
  const location = useLocation();
  const { user, logout, isAdmin, hasPermission } = useAuth();

  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    document.documentElement.setAttribute('data-theme', newMode ? 'dark' : 'light');
    localStorage.setItem('theme', newMode ? 'dark' : 'light');
  };

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  const canSeeItem = (item: NavItem): boolean => {
    if (isAdmin) return true;
    if (!item.permission) return true;
    return hasPermission(item.permission);
  };

  const renderNavItem = (item: NavItem) => {
    if (!canSeeItem(item)) return null;

    const employeeOnlyPaths = ['/leaves', '/trips', '/expenses', '/calendar'];
    if (user?.is_employee === false && employeeOnlyPaths.includes(item.path)) return null;

    const active = isActive(item.path);

    return (
      <Link
        key={item.path}
        to={item.path}
        className={clsx(
          'flex items-center gap-3 px-3 py-2.5 mx-2 rounded-lg text-sm font-medium transition-all duration-200 mb-0.5',
          active
            ? 'bg-primary/10 text-primary'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
          collapsed && 'justify-center px-2'
        )}
        title={collapsed ? item.label : undefined}
      >
        <span className={clsx('shrink-0', active ? 'text-primary' : 'text-slate-500 group-hover:text-slate-700')}>
          {item.icon}
        </span>
        {!collapsed && <span className="truncate">{item.label}</span>}
      </Link>
    );
  };

  const hasVisibleItems = (items: NavItem[]) => items.some(item => canSeeItem(item));

  const renderSectionHeader = (title: string) => {
    if (collapsed) return <div className="h-px bg-slate-200 mx-4 my-4" />;
    return (
      <div className="px-5 py-2 mt-4 mb-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">
        {title}
      </div>
    );
  };

  return (
    <aside
      className={clsx(
        'fixed left-0 top-0 bottom-0 z-50 flex flex-col bg-white border-r border-slate-200 transition-all duration-300 ease-in-out',
        collapsed ? 'w-20' : 'w-72'
      )}
    >
      {/* Header / Logo */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-slate-100">
        <Link to="/" className={clsx('flex items-center gap-3 overflow-hidden', collapsed && 'justify-center w-full')}>
          <div className="bg-primary/10 p-1.5 rounded-lg shrink-0">
            <Logo size={24} />
          </div>
          {!collapsed && (
            <span className="font-bold text-lg tracking-tight text-slate-900">
              KRONOS
            </span>
          )}
        </Link>
        {!collapsed && (
          <button
            onClick={() => setCollapsed(true)}
            className="p-1.5 rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <ChevronLeft size={18} />
          </button>
        )}
      </div>

      {collapsed && (
        <div className="flex justify-center py-4 border-b border-slate-100">
          <button
            onClick={() => setCollapsed(false)}
            className="p-1.5 rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      )}

      {/* Navigation Scroll Area */}
      <nav className="flex-1 overflow-y-auto py-4 scrollbar-thin scrollbar-thumb-slate-200 hover:scrollbar-thumb-slate-300">
        <div className="space-y-0.5">
          {navItems.map(renderNavItem)}
        </div>

        {hasVisibleItems(approverItems) && (
          <>
            {renderSectionHeader('Approvazioni')}
            <div className="space-y-0.5">{approverItems.map(renderNavItem)}</div>
          </>
        )}

        {hasVisibleItems(hrItems) && (
          <>
            {renderSectionHeader('Risorse Umane')}
            <div className="space-y-0.5">{hrItems.map(renderNavItem)}</div>
          </>
        )}

        {hasVisibleItems(adminAccessItems) && (
          <>
            {renderSectionHeader('Organizzazione')}
            <div className="space-y-0.5">{adminAccessItems.map(renderNavItem)}</div>
          </>
        )}

        {hasVisibleItems(adminConfigItems) && (
          <>
            {renderSectionHeader('Configurazione')}
            <div className="space-y-0.5">{adminConfigItems.map(renderNavItem)}</div>
          </>
        )}

        {hasVisibleItems(adminLogItems) && (
          <>
            {renderSectionHeader('Monitoraggio')}
            <div className="space-y-0.5">{adminLogItems.map(renderNavItem)}</div>
          </>
        )}
      </nav>

      {/* Footer Actions */}
      <div className="p-4 border-t border-slate-200 bg-slate-50/50">
        <div className={clsx('flex gap-2', collapsed ? 'flex-col' : 'flex-row')}>
          <button
            onClick={toggleDarkMode}
            className="flex-1 flex items-center justify-center gap-2 p-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all shadow-sm"
            title={darkMode ? 'Modalità chiara' : 'Modalità scura'}
          >
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            {!collapsed && <span className="text-xs font-medium">Tema</span>}
          </button>

          <button
            onClick={logout}
            className="flex-1 flex items-center justify-center gap-2 p-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-all shadow-sm"
            title="Logout"
          >
            <LogOut size={18} />
            {!collapsed && <span className="text-xs font-medium">Esci</span>}
          </button>
        </div>

        {/* User User Profile Tiny */}
        {!collapsed && user && (
          <div className="mt-4 flex items-center gap-3 px-1">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
              {user.first_name?.[0]}{user.last_name?.[0]}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-slate-900 truncate">
                {user.first_name} {user.last_name}
              </div>
              <div className="text-xs text-slate-500 truncate">{user.email}</div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

export default Sidebar;
