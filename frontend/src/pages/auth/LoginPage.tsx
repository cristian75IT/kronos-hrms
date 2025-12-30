/**
 * KRONOS - Login / Landing Page
 */
import { useAuth } from '../../context/AuthContext';
import { Navigate, useLocation } from 'react-router-dom';
import { ArrowRight, ShieldCheck, Clock, Globe, User, Lock, AlertCircle } from 'lucide-react';
import { useState } from 'react';

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const location = useLocation();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const from = (location.state as any)?.from?.pathname || '/';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;

    setError('');
    setLoading(true);
    try {
      await login(username, password);
    } catch (err) {
      console.error(err);
      setError('Credenziali non valide. Riprova.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container glass-card">
        {/* Logo Area */}
        <div className="login-header">
          <div className="logo-icon">K</div>
          <h1 className="logo-text">KRONOS</h1>
          <p className="login-subtitle">Enterprise HR Management System</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="error-message">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Username o Email</label>
            <div className="input-wrapper">
              <User size={18} className="input-icon" />
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="inserisci username"
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper">
              <Lock size={18} className="input-icon" />
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading}
              />
            </div>
          </div>

          <button type="submit" className="btn-login group" disabled={loading}>
            {loading ? (
              <div className="spinner-sm" />
            ) : (
              <>
                <span>Accedi</span>
                <ArrowRight size={20} className="arrow-icon" />
              </>
            )}
          </button>
        </form>

        <div className="login-footer">
          <p>Utenti demo: admin@kronos.local (admin123)</p>
          <p>manager@kronos.local (manager123)</p>
          <p>&copy; {new Date().getFullYear()} Kronos Systems</p>
        </div>
      </div>

      {/* Decorative Background Elements */}
      <div className="bg-blob blob-1"></div>
      <div className="bg-blob blob-2"></div>
      <div className="bg-grid"></div>

      <style>{`
        .login-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--color-bg-primary);
          position: relative;
          overflow: hidden;
          padding: var(--space-4);
        }

        .login-container {
          width: 100%;
          max-width: 420px;
          padding: 3rem 2.5rem;
          border-radius: var(--radius-2xl);
          background: rgba(255, 255, 255, 0.7);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.5);
          box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.05),
            0 1px 3px rgba(0, 0, 0, 0.1);
          z-index: 10;
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }

        [data-theme='dark'] .login-container {
          background: rgba(30, 41, 59, 0.7);
          border-color: rgba(255, 255, 255, 0.1);
        }

        .login-header {
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .logo-icon {
          width: 64px;
          height: 64px;
          background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
          border-radius: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 800;
          font-size: 32px;
          margin-bottom: 1.5rem;
          box-shadow: 0 10px 25px -5px var(--color-primary-transparent);
        }

        .logo-text {
          font-size: 2rem;
          font-weight: 800;
          background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          letter-spacing: -0.02em;
          margin-bottom: 0.5rem;
        }

        .login-subtitle {
          color: var(--color-text-secondary);
          font-size: 0.875rem;
          font-weight: 500;
          letter-spacing: 0.02em;
        }

        .login-form {
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .form-group label {
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--color-text-primary);
            margin-left: 0.25rem;
        }

        .input-wrapper {
            position: relative;
        }

        .input-icon {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--color-text-muted);
            pointer-events: none;
        }

        .input-wrapper input {
            width: 100%;
            padding: 0.875rem 1rem 0.875rem 2.75rem;
            border-radius: var(--radius-xl);
            border: 1px solid var(--color-border-light);
            background: var(--color-bg-tertiary);
            color: var(--color-text-primary);
            font-size: 0.95rem;
            transition: all 0.2s;
        }

        .input-wrapper input:focus {
            outline: none;
            background: var(--color-bg-primary);
            border-color: var(--color-primary);
            box-shadow: 0 0 0 3px var(--color-primary-transparent);
        }

        .error-message {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem;
            background: #fee2e2;
            color: #ef4444;
            border-radius: var(--radius-lg);
            font-size: 0.875rem;
        }
        [data-theme='dark'] .error-message {
            background: rgba(239, 68, 68, 0.1);
        }

        .btn-login {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          padding: 1rem;
          background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
          color: white;
          border: none;
          border-radius: var(--radius-xl);
          font-weight: 600;
          font-size: 1rem;
          cursor: pointer;
          transition: all 0.2s;
          box-shadow: 0 4px 6px -1px var(--color-primary-transparent);
          margin-top: 0.5rem;
        }

        .btn-login:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 10px 15px -3px var(--color-primary-transparent);
          filter: brightness(1.05);
        }

        .btn-login:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }

        .spinner-sm {
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        .arrow-icon {
          transition: transform 0.2s;
        }

        .btn-login:hover .arrow-icon {
          transform: translateX(4px);
        }

        .login-footer {
          margin-top: 1rem;
          text-align: center;
          font-size: 0.75rem;
          color: var(--color-text-muted);
          line-height: 1.5;
        }

        /* Background Effects */
        .bg-blob {
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          opacity: 0.4;
          z-index: 0;
        }

        .blob-1 {
          top: -10%;
          left: -10%;
          width: 500px;
          height: 500px;
          background: var(--color-primary);
          animation: float 20s infinite alternate;
        }

        .blob-2 {
          bottom: -10%;
          right: -10%;
          width: 400px;
          height: 400px;
          background: var(--color-secondary);
          animation: float 15s infinite alternate-reverse;
        }

        .bg-grid {
          position: absolute;
          inset: 0;
          background-image: linear-gradient(var(--color-border-light) 1px, transparent 1px),
            linear-gradient(90deg, var(--color-border-light) 1px, transparent 1px);
          background-size: 50px 50px;
          opacity: 0.3;
          z-index: 0;
          mask-image: radial-gradient(circle at center, black 40%, transparent 80%);
        }

        @keyframes float {
          0% { transform: translate(0, 0) scale(1); }
          100% { transform: translate(50px, 50px) scale(1.1); }
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
