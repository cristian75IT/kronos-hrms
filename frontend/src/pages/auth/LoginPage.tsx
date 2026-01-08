/**
 * KRONOS - Login / Landing Page
 */
import { useAuth } from '../../context/AuthContext';
import { Navigate, useLocation } from 'react-router-dom';
import { ArrowRight, User, Lock, AlertCircle, Shield } from 'lucide-react';
import { useState } from 'react';
import { Logo } from '../../components/common/Logo';

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const location = useLocation();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const from = (location.state as any)?.from?.pathname || '/';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [showOtp, setShowOtp] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;
    if (showOtp && !otp) return;

    setError('');
    setLoading(true);
    try {
      await login(username.trim(), password.trim(), otp.trim());
    } catch (err: any) {
      console.error(err);
      if (err.message && (err.message.includes('MFA required') || err.message.includes('totp'))) {
        // Detect if error is about missing TOTP, show OTP field
        // NOTE: Keycloak usually returns "Account is not fully set up" or checks "required actions".
        // If direct grant is used, Keycloak returns 401/400.
        // We need custom detection or just let user retry WITH otp if they know they have it.
        // For now, if login fails, we MIGHT show OTP info if we can distinguish it.
        // BUT - simplest path: If 401/400 and message suggests auth issue, user might HAVE 2FA.
        // Let's rely on backend error message or...
        // Actually, if using `password` grant, and user has OTP enabled, Keycloak usually fails unless `totp` param is present.
        // It doesn't always tell you "Code Required". It just says "Invalid credentials".
        setShowOtp(true);
        setError('Codice 2FA richiesto o credenziali errate.');
      } else {
        setError('Credenziali non valide. Riprova.');
        // If already showing OTP, keep showing it so they can retry code
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-xl border border-gray-200 shadow-sm">
        <div className="text-center">
          <div className="mx-auto h-20 w-20 flex items-center justify-center mb-4">
            <Logo size={80} />
          </div>
          <h2 className="text-3xl font-extrabold text-gray-900">KRONOS</h2>
          <p className="mt-2 text-sm text-gray-600">HR Management System</p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg flex items-center gap-2">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                Username o Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                  <User size={18} />
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="appearance-none block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm transition-all"
                  placeholder="Inserisci username"
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                  <Lock size={18} />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm transition-all"
                  placeholder="••••••••"
                  disabled={loading}
                />
              </div>
            </div>

            {showOtp && (
              <div className="animate-fadeIn">
                <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-1">
                  Codice 2FA
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                    <Shield size={18} />
                  </div>
                  <input
                    id="otp"
                    name="otp"
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="appearance-none block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm transition-all text-center tracking-widest font-mono"
                    placeholder="000 000"
                    disabled={loading}
                    autoFocus
                  />
                </div>
              </div>
            )}
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2.5 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900 disabled:opacity-70 disabled:cursor-not-allowed transition-all"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <span className="flex items-center gap-2">
                  Accedi
                  <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </span>
              )}
            </button>
          </div>
        </form>

        <div className="mt-6 pt-6 border-t border-gray-100 text-center text-xs text-gray-500 space-y-2">
          <p>
            <span className="font-semibold block mb-1">Utenti Demo:</span>
            admin@kronos.local (admin123)<br />
            manager@kronos.local (manager123)
          </p>
          <p className="pt-4 text-gray-400">&copy; {new Date().getFullYear()} Kronos Systems</p>
        </div>
      </div>
    </div>
  );
}
