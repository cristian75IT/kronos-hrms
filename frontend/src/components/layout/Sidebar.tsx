/**
 * KRONOS - Main Sidebar Layout Component
 * Enterprise Styled with Tailwind CSS
 */
import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Calendar, Briefcase, FileText, Settings, Users, LayoutDashboard,
  ChevronLeft, ChevronRight, LogOut, Sun, Moon, Book, Terminal,
  Activity, Bell, Mail, History as HistoryIcon, GraduationCap,
  TreePalm, Plane, Receipt, GitBranch, Shield, ChevronDown, Layers,
  PieChart, X, CalendarCheck
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { clsx } from 'clsx';
import { Logo } from '../common/Logo';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  permission?: string;
  end?: boolean;
}

// ... (Item definitions unchanged) ...
const baseItems: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} />, end: true },
  { label: 'Lavoro Agile', path: '/smart-working', icon: <Briefcase size={20} /> },
];

const myItems: NavItem[] = [
  { label: 'Giornaliero', path: '/timesheet', icon: <CalendarCheck size={20} /> },
  { label: 'Assenze e Permessi', path: '/leaves', icon: <TreePalm size={20} />, permission: 'leaves:view' },
  { label: 'Trasferte', path: '/trips', icon: <Briefcase size={20} />, permission: 'trips:view' },
  { label: 'Note Spese', path: '/expenses', icon: <FileText size={20} />, permission: 'expenses:view' },
  { label: 'Calendario', path: '/calendar', icon: <Calendar size={20} />, permission: 'calendar:view' },
  { label: 'Wiki & Documenti', path: '/wiki', icon: <Book size={20} />, permission: 'wiki:view' },
];

// Approver section
const approverItems: NavItem[] = [
  { label: 'Approvazioni', path: '/approvals/pending', icon: <Users size={20} />, permission: 'approvals:process' },
];

// Admin Sections
const organizationItems: NavItem[] = [
  { label: 'Utenti', path: '/admin/users', icon: <Users size={20} />, permission: 'users:view' },
  { label: 'Ruoli & Permessi', path: '/admin/roles', icon: <Shield size={20} />, permission: 'roles:view' },
  { label: 'Organigramma', path: '/admin/organization', icon: <Layers size={20} />, permission: 'settings:edit' },
];

const configItems: NavItem[] = [
  { label: 'Workflow', path: '/admin/workflows', icon: <GitBranch size={20} />, permission: 'approvals:config' },
  { label: 'Calendari', path: '/admin/system-calendars', icon: <Calendar size={20} />, permission: 'calendar:manage' },
  { label: 'Contratti CCNL', path: '/admin/national-contracts', icon: <FileText size={20} />, permission: 'contracts:view' },
  { label: 'Tipi Assenza', path: '/admin/leave-types', icon: <TreePalm size={20} />, permission: 'settings:edit' },
  { label: 'Impostazioni Sistema', path: '/admin/tools', icon: <Settings size={20} />, permission: 'settings:edit' },
];

const monitorItems: NavItem[] = [
  { label: 'Centro Notifiche', path: '/admin/notifications', icon: <Bell size={20} />, permission: 'notifications:send' },
  { label: 'Log Email', path: '/admin/audit/emails', icon: <Mail size={20} />, permission: 'notifications:view' },
  { label: 'Audit Log', path: '/admin/audit/logs', icon: <Terminal size={20} />, permission: 'audit:view' },
  { label: 'Audit Trail', path: '/admin/audit/trail', icon: <HistoryIcon size={20} />, permission: 'audit:view' },
];

const hrItems: NavItem[] = [
  { label: 'HR Console', path: '/hr/console', icon: <PieChart size={20} />, permission: 'reports:view' },
  { label: 'Reportistica', path: '/hr/reports', icon: <Activity size={20} />, permission: 'reports:view' },
  { label: 'Formazione', path: '/hr/training', icon: <GraduationCap size={20} />, permission: 'training:view' },
  { label: 'Gestione Assenze', path: '/hr/leaves', icon: <TreePalm size={20} />, permission: 'leaves:manage' },
  { label: 'Gestione Trasferte', path: '/hr/trips', icon: <Plane size={20} />, permission: 'trips:manage' },
  { label: 'Gestione Spese', path: '/hr/expenses', icon: <Receipt size={20} />, permission: 'expenses:manage' },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
}

export function Sidebar({ mobileOpen = false, onMobileClose, collapsed, setCollapsed }: SidebarProps) {
  const [darkMode, setDarkMode] = useState(() => document.documentElement.getAttribute('data-theme') === 'dark');

  // Accordion state
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    'my-items': true,
    'approver': true,
  });

  const location = useLocation();
  const { user, logout, isAdmin, hasPermission } = useAuth();

  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    document.documentElement.setAttribute('data-theme', newMode ? 'dark' : 'light');
    localStorage.setItem('theme', newMode ? 'dark' : 'light');
  };

  // Close mobile sidebar on route change
  useEffect(() => {
    if (onMobileClose) {
      onMobileClose();
    }
  }, [location.pathname]);

  // Auto-expand groups logic
  useEffect(() => {
    if (collapsed) return;
    const sections = {
      'my-items': myItems, 'approver': approverItems, 'hr': hrItems,
      'config': configItems, 'organization': organizationItems, 'monitor': monitorItems
    };

    const newExpanded = { ...expandedGroups };
    let changed = false;

    Object.entries(sections).forEach(([key, items]) => {
      const hasActive = items.some(item => {
        if (item.path === '/' || item.end) return location.pathname === item.path;
        return location.pathname.startsWith(item.path);
      });
      if (hasActive && !newExpanded[key]) {
        newExpanded[key] = true;
        changed = true;
      }
    });

    if (changed) setExpandedGroups(newExpanded);
  }, [location.pathname, collapsed]);

  const isActive = (path: string, end?: boolean) => {
    if (path === '/' || end) return location.pathname === path;
    return location.pathname.startsWith(path);
  };

  const canSeeItem = (item: NavItem): boolean => {
    if (isAdmin) return true;
    if (!item.permission) return true;
    return hasPermission(item.permission);
  };

  const toggleGroup = (groupKey: string) => {
    setExpandedGroups(prev => ({ ...prev, [groupKey]: !prev[groupKey] }));
  };

  const renderNavItem = (item: NavItem) => {
    if (!canSeeItem(item)) return null;
    const employeeOnlyPaths = ['/leaves', '/trips', '/expenses', '/calendar'];
    if (user?.is_employee === false && employeeOnlyPaths.includes(item.path) && !item.path.startsWith('/hr')) return null;

    const active = isActive(item.path, item.end);

    return (
      <Link
        key={item.path}
        to={item.path}
        className={clsx(
          'flex items-center gap-3 px-3 py-2 mx-2 rounded-lg text-sm font-medium transition-all duration-200 mb-0.5',
          active ? 'bg-primary/10 text-primary' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
          collapsed ? 'justify-center px-2' : ''
        )}
        title={collapsed ? item.label : undefined}
      >
        <span className={clsx('shrink-0', active ? 'text-primary' : 'text-slate-400 group-hover:text-slate-600')}>
          {item.icon}
        </span>
        {!collapsed && <span className="truncate">{item.label}</span>}
      </Link>
    );
  };

  const SidebarGroup = ({ title, items, groupKey, icon: GroupIcon }: { title: string; items: NavItem[]; groupKey: string; icon?: React.ElementType; }) => {
    const visibleItems = items.filter(canSeeItem);
    if (visibleItems.length === 0) return null;
    const isExpanded = expandedGroups[groupKey];
    const hasActiveChild = visibleItems.some(item => isActive(item.path, item.end));

    if (collapsed) {
      return (
        <div className="mb-2">
          <div className="h-px bg-slate-100 mx-4 my-2" />
          {visibleItems.map(renderNavItem)}
        </div>
      );
    }

    return (
      <div className="mb-1">
        <button
          onClick={() => toggleGroup(groupKey)}
          className={clsx(
            "w-full flex items-center justify-between px-4 py-2 text-xs font-bold uppercase tracking-wider text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors mb-1",
            hasActiveChild && !isExpanded && "text-primary bg-primary/5"
          )}
        >
          <div className="flex items-center gap-2">
            {GroupIcon && <GroupIcon size={14} />}
            <span>{title}</span>
          </div>
          <ChevronDown size={14} className={clsx("transition-transform duration-200", isExpanded ? "rotate-180" : "")} />
        </button>
        <div className={clsx(
          "overflow-hidden transition-all duration-300 ease-in-out pl-2 border-l border-slate-100 ml-4 space-y-0.5",
          isExpanded ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"
        )}>
          {visibleItems.map(renderNavItem)}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-slate-900/50 z-40 md:hidden backdrop-blur-sm transition-opacity animate-fadeIn"
          onClick={onMobileClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={clsx(
          'fixed top-0 bottom-0 z-50 flex flex-col bg-slate-50 border-r border-slate-200 shadow-xl md:shadow-none transition-all duration-300 ease-in-out',
          // Mobile: drawer behavior
          'w-72',
          !mobileOpen ? '-translate-x-full' : 'translate-x-0',
          // Desktop: sticky/normal behavior
          'md:translate-x-0',
          collapsed ? 'md:w-20' : 'md:w-72',
          // Layout positioning
          'left-0'
        )}
      >
        {/* Header / Logo */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-slate-200 bg-white z-10 shrink-0">
          <Link to="/" className={clsx('flex items-center gap-3 overflow-hidden', collapsed && 'md:justify-center w-full')}>
            <div className="bg-primary/10 p-1.5 rounded-lg shrink-0 text-primary">
              <Logo size={24} />
            </div>
            {/* Show title on mobile OR if not collapsed on desktop */}
            {(!collapsed || mobileOpen) && (
              <span className="font-bold text-lg tracking-tight text-slate-900 leading-none">
                KRONOS<span className="text-primary">.hr</span>
              </span>
            )}
          </Link>

          {/* Desktop Collapse Button */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden md:flex p-1.5 rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>

          {/* Mobile Close Button */}
          <button
            onClick={onMobileClose}
            className="md:hidden p-1.5 rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation Scroll Area */}
        <nav className="flex-1 overflow-y-auto py-4 scrollbar-thin scrollbar-thumb-slate-200 hover:scrollbar-thumb-slate-300 bg-white">
          <div className="space-y-1 mb-6">
            {baseItems.map(renderNavItem)}
          </div>
          <div className="space-y-2">
            <SidebarGroup title="Le Mie Attività" groupKey="my-items" items={myItems} />
            <SidebarGroup title="Approvazioni" groupKey="approver" items={approverItems} />
            <SidebarGroup title="Risorse Umane" groupKey="hr" items={hrItems} />
            <SidebarGroup title="Configurazione" groupKey="config" items={configItems} />
            <SidebarGroup title="Organizzazione" groupKey="org" items={organizationItems} />
            <SidebarGroup title="Monitoraggio" groupKey="monitor" items={monitorItems} />
          </div>
        </nav>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-200 bg-slate-50/80 shrink-0">
          {(!collapsed || mobileOpen) && user && (
            <div className="mb-4 flex items-center gap-3 px-1 p-2 rounded-xl hover:bg-white hover:shadow-sm transition-all cursor-pointer border border-transparent hover:border-slate-200 group">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-md">
                {user.first_name?.[0]}{user.last_name?.[0]}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-bold text-slate-900 truncate group-hover:text-primary transition-colors">
                  {user.first_name} {user.last_name}
                </div>
                <div className="text-xs text-slate-500 truncate">{user.email}</div>
              </div>
              <Link to="/settings" className="p-1.5 text-slate-400 hover:text-primary rounded-lg hover:bg-slate-100">
                <Settings size={16} />
              </Link>
            </div>
          )}

          <div className={clsx('flex gap-2', (collapsed && !mobileOpen) ? 'flex-col' : 'flex-row')}>
            <button
              onClick={toggleDarkMode}
              className="flex-1 flex items-center justify-center gap-2 p-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all shadow-sm"
              title={darkMode ? 'Modalità chiara' : 'Modalità scura'}
            >
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <button
              onClick={logout}
              className="flex-1 flex items-center justify-center gap-2 p-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-all shadow-sm"
              title="Logout"
            >
              <LogOut size={18} />
              {(!collapsed || mobileOpen) && <span className="text-xs font-medium">Esci</span>}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
