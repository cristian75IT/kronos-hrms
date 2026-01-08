/**
 * KRONOS - Main Sidebar Layout Component
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

import '../../styles/components/sidebar.css';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  /** Required permission to view this item (any single permission grants access) */
  permission?: string;
}

// Base items - available to all authenticated users
const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} /> },
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

// Admin - Access & Organization
const adminAccessItems: NavItem[] = [
  { label: 'Gestione Utenti', path: '/admin/users', icon: <Users size={20} />, permission: 'users:view' },
  { label: 'Gestione Ruoli', path: '/admin/roles', icon: <Shield size={20} />, permission: 'roles:view' },
  { label: 'Organizzazione', path: '/admin/organization', icon: <Briefcase size={20} />, permission: 'settings:edit' }, // Icon placeholder
];

// Admin - System Configuration
const adminConfigItems: NavItem[] = [
  { label: 'Workflow Approvazioni', path: '/admin/workflows', icon: <GitBranch size={20} />, permission: 'approvals:config' },
  { label: 'Calendari di Sistema', path: '/admin/system-calendars', icon: <Calendar size={20} />, permission: 'calendar:manage' },
  { label: 'Contratti CCNL', path: '/admin/national-contracts', icon: <FileText size={20} />, permission: 'contracts:view' },
  { label: 'Tipi Assenza', path: '/admin/leave-types', icon: <TreePalm size={20} />, permission: 'settings:edit' },
  { label: 'Strumenti Admin', path: '/admin/tools', icon: <Settings size={20} />, permission: 'settings:edit' },
];

// Admin - Monitoring & Logs
const adminLogItems: NavItem[] = [
  { label: 'Centro Notifiche', path: '/admin/notifications', icon: <Bell size={20} />, permission: 'notifications:send' },
  { label: 'Log Email', path: '/admin/email-logs', icon: <Mail size={20} />, permission: 'notifications:view' },
  { label: 'Audit Log', path: '/admin/audit-logs', icon: <Terminal size={20} />, permission: 'audit:view' },
  { label: 'Audit Trail', path: '/admin/audit-trail', icon: <HistoryIcon size={20} />, permission: 'audit:view' },
];

// HR section
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

  // Check if user can see a nav item (admin bypasses, or has required permission)
  const canSeeItem = (item: NavItem): boolean => {
    if (isAdmin) return true;
    if (!item.permission) return true; // No permission required
    return hasPermission(item.permission);
  };

  const renderNavItem = (item: NavItem) => {
    if (!canSeeItem(item)) return null;

    // Filter employee-only items for external users
    const employeeOnlyPaths = ['/leaves', '/trips', '/expenses', '/calendar'];
    if (user?.is_employee === false && employeeOnlyPaths.includes(item.path)) return null;

    return (
      <Link
        key={item.path}
        to={item.path}
        className={clsx(
          'sidebar-item',
          isActive(item.path) && 'active'
        )}
        title={collapsed ? item.label : undefined}
      >
        <span className="sidebar-item-icon">{item.icon}</span>
        {!collapsed && <span className="sidebar-item-label">{item.label}</span>}
      </Link>
    );
  };

  // Check if a section has any visible items
  const hasVisibleItems = (items: NavItem[]): boolean => {
    return items.some(item => canSeeItem(item));
  };

  return (
    <aside className={clsx('sidebar', collapsed && 'collapsed')}>
      {/* Logo */}
      <div className="sidebar-header">
        <Link to="/" className="sidebar-logo">
          <Logo size={32} />
          {!collapsed && <span className="sidebar-logo-text">KRONOS</span>}
        </Link>
        <button
          className="sidebar-toggle"
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? 'Espandi sidebar' : 'Comprimi sidebar'}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="sidebar-section">
          {navItems.map(renderNavItem)}
        </div>

        {hasVisibleItems(approverItems) && (
          <div className="sidebar-section">
            {!collapsed && <div className="sidebar-section-title">Approvazioni</div>}
            {approverItems.map(renderNavItem)}
          </div>
        )}

        {hasVisibleItems(hrItems) && (
          <div className="sidebar-section">
            {!collapsed && <div className="sidebar-section-title">Risorse Umane</div>}
            {hrItems.map(renderNavItem)}
          </div>
        )}

        {hasVisibleItems(adminAccessItems) && (
          <div className="sidebar-section">
            {!collapsed && <div className="sidebar-section-title">Accesso & Org</div>}
            {adminAccessItems.map(renderNavItem)}
          </div>
        )}

        {hasVisibleItems(adminConfigItems) && (
          <div className="sidebar-section">
            {!collapsed && <div className="sidebar-section-title">Configurazione</div>}
            {adminConfigItems.map(renderNavItem)}
          </div>
        )}

        {hasVisibleItems(adminLogItems) && (
          <div className="sidebar-section">
            {!collapsed && <div className="sidebar-section-title">Monitoraggio</div>}
            {adminLogItems.map(renderNavItem)}
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <button
          className="sidebar-footer-btn"
          onClick={toggleDarkMode}
          title={darkMode ? 'Modalità chiara' : 'Modalità scura'}
        >
          {darkMode ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <button
          className="sidebar-footer-btn"
          onClick={logout}
          title="Logout"
        >
          <LogOut size={18} />
        </button>
      </div>

      {/* User Info */}
      {!collapsed && user && (
        <div className="sidebar-user">
          <div className="avatar avatar-sm">
            {user.first_name?.[0]}{user.last_name?.[0]}
          </div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">
              {user.first_name} {user.last_name}
            </div>
            <div className="sidebar-user-email">{user.email}</div>
          </div>
        </div>
      )}

      <link rel="stylesheet" href="/src/styles/components/sidebar.css" />
    </aside>
  );
}

export default Sidebar;
