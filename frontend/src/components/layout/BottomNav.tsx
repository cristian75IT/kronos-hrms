/**
 * KRONOS - Bottom Navigation Component
 * Mobile-only navigation bar for quick access
 */
import { NavLink } from 'react-router-dom';
import { Home, Calendar, PlusCircle, FileText, User } from 'lucide-react';
import { clsx } from 'clsx';
import { useState } from 'react';

export function BottomNav() {
    const [showFabMenu, setShowFabMenu] = useState(false);

    const navItems = [
        { label: 'Home', path: '/', icon: <Home size={20} /> },
        { label: 'Assenze', path: '/leaves', icon: <FileText size={20} /> },
        { label: 'Calendario', path: '/calendar', icon: <Calendar size={20} /> },
        { label: 'Profilo', path: '/profile', icon: <User size={20} /> },
    ];

    return (
        <>
            {/* FAB Overlay (Optional for future expansion) */}
            {showFabMenu && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm md:hidden animate-fadeIn"
                    onClick={() => setShowFabMenu(false)}
                />
            )}

            {/* Floating Action Button - Center */}
            <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 md:hidden">
                <button
                    onClick={() => setShowFabMenu(!showFabMenu)}
                    className={clsx(
                        "flex items-center justify-center w-14 h-14 rounded-full shadow-lg transition-transform duration-200",
                        "bg-gradient-to-r from-primary to-indigo-600 text-white",
                        showFabMenu ? "rotate-45" : "hover:scale-105"
                    )}
                >
                    <PlusCircle size={28} />
                </button>

                {/* FAB Menu Items */}
                {showFabMenu && (
                    <div className="absolute bottom-16 left-1/2 -translate-x-1/2 w-48 flex flex-col gap-2 animate-slideUp">
                        <NavLink
                            to="/leaves/new"
                            onClick={() => setShowFabMenu(false)}
                            className="flex items-center gap-3 px-4 py-3 bg-white text-slate-700 rounded-xl shadow-lg border border-slate-100 hover:bg-slate-50"
                        >
                            <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
                                <FileText size={16} />
                            </div>
                            <span className="text-sm font-semibold">Richiedi Ferie</span>
                        </NavLink>
                        <NavLink
                            to="/expenses/new"
                            onClick={() => setShowFabMenu(false)}
                            className="flex items-center gap-3 px-4 py-3 bg-white text-slate-700 rounded-xl shadow-lg border border-slate-100 hover:bg-slate-50"
                        >
                            <div className="w-8 h-8 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center">
                                <FileText size={16} />
                            </div>
                            <span className="text-sm font-semibold">Nota Spese</span>
                        </NavLink>
                    </div>
                )}
            </div>

            {/* Bottom Bar */}
            <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-6 py-2 pb-safe z-40 md:hidden flex justify-between items-center h-16 shadow-[0_-4px_20px_rgba(0,0,0,0.05)]">
                {navItems.map((item, index) => {
                    // Add spacer for FAB in the middle
                    if (index === 2) {
                        return <div key="spacer" className="w-12" />;
                    }

                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) => clsx(
                                "flex flex-col items-center gap-1 min-w-[60px] transition-colors",
                                isActive ? "text-primary" : "text-slate-400 hover:text-slate-600"
                            )}
                        >
                            {item.icon}
                            <span className="text-[10px] font-medium">{item.label}</span>
                        </NavLink>
                    );
                })}
            </nav>
        </>
    );
}
