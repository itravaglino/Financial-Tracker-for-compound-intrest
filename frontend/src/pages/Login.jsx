import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { TrendingUp } from 'lucide-react';
import './Auth.css';

export default function Login() {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        await register(username, email, password);
      } else {
        await login(username, password);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-brand">
          <TrendingUp size={48} />
          <h1>FinTrack Pro</h1>
          <p>Tracking financiero avanzado con Yahoo Finance, IA y trading</p>
        </div>
        <div className="auth-form card">
          <div className="tabs">
            <button className={`tab ${!isRegister ? 'active' : ''}`} onClick={() => setIsRegister(false)}>
              Iniciar Sesión
            </button>
            <button className={`tab ${isRegister ? 'active' : ''}`} onClick={() => setIsRegister(true)}>
              Registrarse
            </button>
          </div>
          {error && <div className="error-msg">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Usuario</label>
              <input value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} />
            </div>
            {isRegister && (
              <div className="form-group">
                <label>Email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </div>
            )}
            <div className="form-group">
              <label>Contraseña</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
            </div>
            <button type="submit" className="btn-primary auth-submit" disabled={loading}>
              {loading ? 'Cargando...' : isRegister ? 'Crear Cuenta' : 'Entrar'}
            </button>
          </form>
        </div>
        <div className="auth-features">
          <span>Yahoo Finance en tiempo real</span>
          <span>Redes neuronales LSTM</span>
          <span>Patrones Fibonacci</span>
          <span>Valoración isométrica</span>
          <span>Trading via API</span>
        </div>
      </div>
    </div>
  );
}
