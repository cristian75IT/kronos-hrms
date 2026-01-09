/**
 * KRONOS - Main Layout Component
 * Responsive layout with mobile support and dynamic sidebar
 */
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useState, useEffect } from 'react';
import { BottomNav } from './BottomNav';
import { clsx } from 'clsx';

export function MainLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Initialize from localStorage or default to false (expanded)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebarCollapsed');
    return saved === 'true';
  });

  // Persist state
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  return (
    <div className="flex min-h-screen bg-slate-50/30">
      {/* Sidebar - Desktop (static) & Mobile (drawer) */}
      <Sidebar
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />

      {/* Main Content Area */}
      <div
        className={clsx(
          "flex-1 flex flex-col min-w-0 transition-all duration-300 ease-in-out",
          "pb-24 md:pb-0", // Bottom spacing for mobile nav
          sidebarCollapsed ? "md:ml-20" : "md:ml-72" // Dynamic desktop margin
        )}
      >
        <Header onMenuClick={() => setMobileMenuOpen(true)} />

        <main className="flex-1 p-4 md:p-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>

      <BottomNav />
    </div>
  );
}

export default MainLayout;
