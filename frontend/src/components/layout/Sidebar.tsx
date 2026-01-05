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

      <style>{`
        .sidebar {
          position: fixed;
          left: 0;
          top: 0;
          bottom: 0;
          width: var(--sidebar-width);
          background: var(--color-bg-primary); /* Solid sidebar */
          border-right: 1px solid var(--color-border);
          display: flex;
          flex-direction: column;
          z-index: var(--z-sticky);
          transition: width var(--transition-normal);
        }

        .sidebar.collapsed {
          width: var(--sidebar-collapsed-width);
        }

        .sidebar-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--space-4);
          border-bottom: 1px solid var(--color-border);
          background: var(--color-bg-primary);
        }

        .sidebar-logo {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          text-decoration: none;
        }

        .sidebar-logo-icon {
          width: 32px;
          height: 32px;
          background: var(--color-primary);
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: var(--font-weight-bold);
          font-size: var(--font-size-lg);
        }

        .sidebar-logo-text {
          font-size: var(--font-size-lg);
          font-weight: var(--font-weight-bold);
          color: var(--color-primary-dark);
        }

        .sidebar-toggle {
          padding: var(--space-1-5);
          background: transparent;
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .sidebar-toggle:hover {
          background: var(--color-bg-hover);
          color: var(--color-text-primary);
        }

        .sidebar-nav {
          flex: 1;
          padding: var(--space-3) var(--space-2);
          overflow-y: auto;
        }

        .sidebar-section {
          margin-bottom: var(--space-4);
          padding-bottom: var(--space-2);
          border-bottom: 1px solid var(--color-border-light);
        }
        
        .sidebar-section:last-child {
          border-bottom: none;
        }

        .sidebar-section-title {
          font-size: 0.65rem; /* Smaller, sharper */
          font-weight: var(--font-weight-bold);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--color-text-muted);
          padding: var(--space-2) var(--space-3);
          margin-bottom: var(--space-1);
        }

        .sidebar-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-2) var(--space-3);
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          text-decoration: none;
          margin-bottom: 1px;
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-medium);
          transition: all var(--transition-fast);
          border-left: 3px solid transparent; /* Prepare for active border */
        }

        .sidebar-item:hover {
          background: var(--color-bg-hover);
          color: var(--color-text-primary);
        }

        .sidebar-item.active {
          background: var(--color-bg-active);
          color: var(--color-primary-dark);
          border-left-color: var(--color-primary); /* Enterprise Accent */
          font-weight: var(--font-weight-semibold);
        }

        .sidebar-item.active .sidebar-item-icon {
          color: var(--color-primary);
        }

        .sidebar-item-icon {
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 20px;
        }

        .sidebar-item-label {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .sidebar-footer {
          display: flex;
          gap: var(--space-2);
          padding: var(--space-3) var(--space-4);
          border-top: 1px solid var(--color-border);
          background: var(--color-bg-tertiary); /* Distinct footer area */
        }

        .sidebar-footer-btn {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: var(--space-2);
          background: var(--color-bg-primary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .sidebar-footer-btn:hover {
          background: var(--color-bg-hover);
          color: var(--color-text-primary);
          border-color: var(--color-border-strong);
        }

        .sidebar-user {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-4);
          border-top: 1px solid var(--color-border);
          background: var(--color-bg-primary);
        }

        .sidebar-user-info {
          flex: 1;
          min-width: 0;
        }

        .sidebar-user-name {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-semibold);
          color: var(--color-text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .sidebar-user-email {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .collapsed .sidebar-item {
          justify-content: center;
          padding: var(--space-3);
          border-left: none; /* No border in collapsed to keep centered */
        }
        
        .collapsed .sidebar-item.active {
          background: var(--color-bg-active);
          color: var(--color-primary);
        }

        .collapsed .sidebar-section-title,
        .collapsed .sidebar-item-label {
          display: none;
        }
      `}</style>
    </aside>
  );
}

export default Sidebar;
