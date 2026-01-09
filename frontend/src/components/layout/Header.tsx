/**
 * KRONOS - Header Component
 */
import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, User, LogOut, Settings, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import NotificationDropdown from '../common/NotificationDropdown';

export function Header() {
  const { user, logout } = useAuth();
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="app-header">
      <div className="header-left">
        <div className="header-search">
          <Search size={18} className="header-search-icon" />
          <input
            type="text"
            placeholder="Cerca..."
            className="header-search-input"
          />
        </div>
      </div>

      <div className="header-right">
        <NotificationDropdown />

        {/* User Menu Dropdown */}
        <div className="header-user-menu" ref={menuRef}>
          <button
            className="header-user-button"
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
          >
            <div className="header-user-avatar">
              {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
            </div>
            <span className="header-user-name">{user?.first_name}</span>
            <ChevronDown size={16} className={`header-chevron ${isUserMenuOpen ? 'rotated' : ''}`} />
          </button>

          {isUserMenuOpen && (
            <div className="header-dropdown">
              <div className="header-dropdown-header">
                <div className="header-dropdown-name">{user?.full_name}</div>
                <div className="header-dropdown-email">{user?.email}</div>
              </div>
              <div className="header-dropdown-divider" />
              <Link to="/profile" className="header-dropdown-item" onClick={() => setIsUserMenuOpen(false)}>
                <User size={16} />
                <span>Il Mio Profilo</span>
              </Link>
              <Link to="/settings" className="header-dropdown-item" onClick={() => setIsUserMenuOpen(false)}>
                <Settings size={16} />
                <span>Impostazioni</span>
              </Link>
              <div className="header-dropdown-divider" />
              <button className="header-dropdown-item header-dropdown-logout" onClick={logout}>
                <LogOut size={16} />
                <span>Esci</span>
              </button>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .app-header {
          height: var(--header-height);
          background: var(--color-bg-primary);
          border-bottom: 1px solid var(--color-border);
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 var(--space-6);
          position: sticky;
          top: 0;
          z-index: var(--z-sticky);
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: var(--space-4);
        }

        .header-search {
          position: relative;
          width: 300px;
        }

        .header-search-icon {
          position: absolute;
          left: var(--space-3);
          top: 50%;
          transform: translateY(-50%);
          color: var(--color-text-muted);
        }

        .header-search-input {
          width: 100%;
          padding: var(--space-2) var(--space-3);
          padding-left: var(--space-10);
          background: var(--color-bg-tertiary);
          border: 1px solid transparent;
          border-radius: var(--radius-md);
          font-size: var(--font-size-sm);
          color: var(--color-text-primary);
          transition: all var(--transition-fast);
        }

        .header-search-input:focus {
          outline: none;
          background: var(--color-bg-primary);
          border-color: var(--color-primary);
        }

        .header-search-input::placeholder {
          color: var(--color-text-muted);
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: var(--space-4);
        }

        .header-user-menu {
          position: relative;
        }

        .header-user-button {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-1) var(--space-2);
          background: transparent;
          border: none;
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: background var(--transition-fast);
        }

        .header-user-button:hover {
          background: var(--color-bg-tertiary);
        }

        .header-user-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: var(--font-size-xs);
          font-weight: 600;
          text-transform: uppercase;
        }

        .header-user-name {
          font-size: var(--font-size-sm);
          font-weight: 500;
          color: var(--color-text-primary);
        }

        .header-chevron {
          color: var(--color-text-muted);
          transition: transform var(--transition-fast);
        }

        .header-chevron.rotated {
          transform: rotate(180deg);
        }

        .header-dropdown {
          position: absolute;
          top: calc(100% + 8px);
          right: 0;
          width: 240px;
          background: var(--color-bg-primary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
          box-shadow: var(--shadow-lg);
          overflow: hidden;
          animation: slideDown 0.15s ease-out;
        }

        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .header-dropdown-header {
          padding: var(--space-3) var(--space-4);
          background: var(--color-bg-secondary);
        }

        .header-dropdown-name {
          font-weight: 600;
          color: var(--color-text-primary);
          font-size: var(--font-size-sm);
        }

        .header-dropdown-email {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          margin-top: 2px;
        }

        .header-dropdown-divider {
          height: 1px;
          background: var(--color-border);
        }

        .header-dropdown-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3) var(--space-4);
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
          text-decoration: none;
          transition: background var(--transition-fast);
          cursor: pointer;
          border: none;
          background: transparent;
          width: 100%;
          text-align: left;
        }

        .header-dropdown-item:hover {
          background: var(--color-bg-secondary);
          color: var(--color-text-primary);
        }

        .header-dropdown-logout {
          color: var(--color-error);
        }

        .header-dropdown-logout:hover {
          background: rgba(239, 68, 68, 0.1);
          color: var(--color-error);
        }
      `}</style>
    </header>
  );
}

export default Header;
