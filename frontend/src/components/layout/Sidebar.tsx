/**
 * KRONOS - Main Sidebar Layout Component
 */
import { useState } from 'react';
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
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { clsx } from 'clsx';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  roles?: string[];
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} /> },
  { label: 'Le Mie Ferie', path: '/leaves', icon: <Calendar size={20} /> },
  { label: 'Trasferte', path: '/trips', icon: <Briefcase size={20} /> },
  { label: 'Note Spese', path: '/expenses', icon: <FileText size={20} /> },
];

const approverItems: NavItem[] = [
  { label: 'Approvazioni', path: '/approvals', icon: <Users size={20} />, roles: ['approver', 'admin'] },
];

const adminItems: NavItem[] = [
  { label: 'Gestione Utenti', path: '/admin/users', icon: <Users size={20} />, roles: ['admin', 'hr'] },
  { label: 'Configurazione', path: '/admin/config', icon: <Settings size={20} />, roles: ['admin'] },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  });
  const location = useLocation();
  const { user, logout, hasRole, isAdmin, isApprover } = useAuth();

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

  const renderNavItem = (item: NavItem) => {
    if (item.roles && !item.roles.some(r => hasRole(r))) return null;

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

  return (
    <aside className={clsx('sidebar', collapsed && 'collapsed')}>
      {/* Logo */}
      <div className="sidebar-header">
        <Link to="/" className="sidebar-logo">
          <div className="sidebar-logo-icon">K</div>
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

        {(isApprover || isAdmin) && (
          <div className="sidebar-section">
            {!collapsed && <div className="sidebar-section-title">Approvazioni</div>}
            {approverItems.map(renderNavItem)}
          </div>
        )}

        {isAdmin && (
          <div className="sidebar-section">
            {!collapsed && <div className="sidebar-section-title">Amministrazione</div>}
            {adminItems.map(renderNavItem)}
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
          background: var(--glass-bg);
          backdrop-filter: blur(var(--glass-blur));
          border-right: 1px solid var(--glass-border);
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
          border-bottom: 1px solid var(--color-border-light);
        }

        .sidebar-logo {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          text-decoration: none;
        }

        .sidebar-logo-icon {
          width: 40px;
          height: 40px;
          background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
          border-radius: var(--radius-lg);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: var(--font-weight-bold);
          font-size: var(--font-size-xl);
        }

        .sidebar-logo-text {
          font-size: var(--font-size-xl);
          font-weight: var(--font-weight-bold);
          background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .sidebar-toggle {
          padding: var(--space-2);
          background: var(--color-bg-tertiary);
          border: none;
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .sidebar-toggle:hover {
          background: var(--color-bg-hover);
          color: var(--color-text-primary);
        }

        .sidebar-nav {
          flex: 1;
          padding: var(--space-4);
          overflow-y: auto;
        }

        .sidebar-section {
          margin-bottom: var(--space-6);
        }

        .sidebar-section-title {
          font-size: var(--font-size-xs);
          font-weight: var(--font-weight-semibold);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--color-text-muted);
          padding: var(--space-2) var(--space-3);
          margin-bottom: var(--space-2);
        }

        .sidebar-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-2) var(--space-3);
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          text-decoration: none;
          margin-bottom: var(--space-1);
          transition: all var(--transition-fast);
        }

        .sidebar-item:hover {
          background: var(--color-bg-hover);
          color: var(--color-text-primary);
        }

        .sidebar-item.active {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
          color: var(--color-primary);
        }

        .sidebar-item.active .sidebar-item-icon {
          color: var(--color-primary);
        }

        .sidebar-item-icon {
          flex-shrink: 0;
        }

        .sidebar-item-label {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-medium);
        }

        .sidebar-footer {
          display: flex;
          gap: var(--space-2);
          padding: var(--space-3) var(--space-4);
          border-top: 1px solid var(--color-border-light);
        }

        .sidebar-footer-btn {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: var(--space-2);
          background: var(--color-bg-tertiary);
          border: none;
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .sidebar-footer-btn:hover {
          background: var(--color-bg-hover);
          color: var(--color-text-primary);
        }

        .sidebar-user {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-4);
          border-top: 1px solid var(--color-border-light);
        }

        .sidebar-user-info {
          flex: 1;
          min-width: 0;
        }

        .sidebar-user-name {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-medium);
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
