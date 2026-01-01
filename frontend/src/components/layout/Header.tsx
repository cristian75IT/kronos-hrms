/**
 * KRONOS - Header Component
 */
import { Bell, Search } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

export function Header() {
  const [showNotifications, setShowNotifications] = useState(false);
  const { user } = useAuth();

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
        <button
          className="header-notification-btn"
          onClick={() => setShowNotifications(!showNotifications)}
        >
          <Bell size={20} />
          <span className="notification-badge">3</span>
        </button>

        <div className="header-user">
          <span className="header-greeting">
            Ciao, <strong>{user?.first_name}</strong>
          </span>
        </div>
      </div>

      <style>{`
        .app-header {
          height: var(--header-height);
          background: var(--color-bg-primary); /* Solid header */
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
          border-radius: var(--radius-md); /* Consistent rounding */
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

        .header-notification-btn {
          position: relative;
          padding: var(--space-2);
          background: transparent; /* Cleaner look */
          border: 1px solid transparent;
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .header-notification-btn:hover {
          background: var(--color-bg-hover);
          color: var(--color-text-primary);
          border-color: var(--color-border);
        }

        .notification-badge {
          position: absolute;
          top: 4px; /* Adjusted for square button */
          right: 4px;
          width: 8px; /* Dot style badge */
          height: 8px;
          background: var(--color-danger);
          border-radius: var(--radius-full);
          border: 2px solid var(--color-bg-primary);
        }

        /* Hiding badge text for cleaner look, or just style as dot */
        .notification-badge span {
            display: none;
        }

        .header-user {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
        }

        .header-greeting strong {
          color: var(--color-text-primary);
        }
      `}</style>
    </header>
  );
}

export default Header;
