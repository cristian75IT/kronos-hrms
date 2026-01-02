/**
 * KRONOS - Main Layout Component
 */
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export function MainLayout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Header />
        <main className="page-content">
          <Outlet />
        </main>
      </div>

      <style>{`
        .app-layout {
          min-height: 100vh;
          display: flex;
        }

        .main-content {
          flex: 1;
          margin-left: var(--sidebar-width);
          display: flex;
          flex-direction: column;
          transition: margin-left var(--transition-normal);
        }

        .page-content {
          flex: 1;
          padding: var(--space-6);
          max-width: var(--content-max-width);
          margin: 0 auto;
          width: 100%;
          position: relative; 
          z-index: 1;
        }

        @media (max-width: 768px) {
          .main-content {
            margin-left: 0;
          }
        }
      `}</style>
    </div>
  );
}

export default MainLayout;
