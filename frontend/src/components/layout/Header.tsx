/**
 * KRONOS - Header Component
 * Refactored: CSS moved to index.css and Tailwind classes
 */
import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, User, LogOut, Settings, ChevronDown, Menu } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import NotificationDropdown from '../common/NotificationDropdown';
import { clsx } from 'clsx';
import { Logo } from '../common/Logo';

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
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
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 md:px-6 sticky top-0 z-40">
      {/* Left Section - Search & Mobile Menu */}
      <div className="flex items-center gap-4">
        {/* Mobile Menu Trigger */}
        <button
          onClick={onMenuClick}
          className="md:hidden p-2 -ml-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
          aria-label="Open menu"
        >
          <Menu size={24} />
        </button>

        {/* Mobile Logo (visible only on small screens) */}
        <div className="md:hidden flex items-center gap-2">
          <div className="bg-primary/10 p-1 rounded-md text-primary">
            <Logo size={20} />
          </div>
          <span className="font-bold text-lg text-slate-900 tracking-tight">KRONOS</span>
        </div>

        {/* Desktop Search */}
        <div className="relative w-72 hidden md:block">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Cerca..."
            className="w-full py-2 pl-10 pr-3 bg-slate-50 border border-transparent rounded-lg text-sm text-slate-900 placeholder-slate-400 transition-all focus:outline-none focus:bg-white focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>
      </div>

      {/* Right Section - Notifications & User */}
      <div className="flex items-center gap-2 md:gap-4">
        {/* Mobile Search Trigger (optional, for now hidden) */}
        <button className="md:hidden p-2 text-slate-500 hover:bg-slate-100 rounded-lg">
          <Search size={22} />
        </button>

        <NotificationDropdown />

        {/* User Menu Dropdown */}
        <div className="relative" ref={menuRef}>
          <button
            className="flex items-center gap-2 px-2 py-1 bg-transparent border-none rounded-lg cursor-pointer transition-colors hover:bg-slate-50"
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-slate-600 text-white flex items-center justify-center text-xs font-semibold uppercase ring-2 ring-white shadow-sm">
              {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
            </div>
            <span className="text-sm font-medium text-slate-900 hidden sm:block">{user?.first_name}</span>
            <ChevronDown
              size={16}
              className={clsx(
                'text-slate-400 transition-transform duration-150 hidden sm:block',
                isUserMenuOpen && 'rotate-180'
              )}
            />
          </button>

          {isUserMenuOpen && (
            <div className="absolute top-[calc(100%+8px)] right-0 w-60 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden animate-fadeInDown z-50">
              {/* User Info Header */}
              <div className="px-4 py-3 bg-slate-50 border-b border-slate-100">
                <div className="font-semibold text-sm text-slate-900">{user?.full_name}</div>
                <div className="text-xs text-slate-500 mt-0.5 truncate">{user?.email}</div>
              </div>

              {/* Menu Items */}
              <div className="py-1">
                <Link
                  to="/profile"
                  className="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors"
                  onClick={() => setIsUserMenuOpen(false)}
                >
                  <User size={16} className="text-slate-400" />
                  <span>Il Mio Profilo</span>
                </Link>
                <Link
                  to="/settings"
                  className="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors"
                  onClick={() => setIsUserMenuOpen(false)}
                >
                  <Settings size={16} className="text-slate-400" />
                  <span>Impostazioni</span>
                </Link>
              </div>

              {/* Logout */}
              <div className="border-t border-slate-100 py-1">
                <button
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                  onClick={logout}
                >
                  <LogOut size={16} />
                  <span>Esci</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
