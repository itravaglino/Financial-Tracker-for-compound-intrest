import { NavLink } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">FinanceTracker Pro</div>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/portfolio">Portfolio</NavLink>
          <NavLink to="/analysis">Análisis</NavLink>
          <NavLink to="/alerts">Alertas</NavLink>
          <NavLink to="/trading">Trading</NavLink>
        </nav>
        <div className="sidebar-user">
          <div style={{ fontWeight: 600, marginBottom: 4 }}>{user?.username}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 12 }}>
            {user?.email}
          </div>
          <button className="btn btn-secondary btn-sm" onClick={logout} style={{ width: '100%' }}>
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}
