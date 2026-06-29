import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, Briefcase, LineChart, ArrowLeftRight,
  Bell, LogOut, TrendingUp, Calculator,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/portfolio', icon: Briefcase, label: 'Portfolio' },
  { to: '/analysis', icon: LineChart, label: 'Análisis' },
  { to: '/trading', icon: ArrowLeftRight, label: 'Trading' },
  { to: '/alerts', icon: Bell, label: 'Alertas' },
  { to: '/compound', icon: Calculator, label: 'Interés Compuesto' },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-surface-900 border-r border-surface-800 flex flex-col">
        <div className="p-5 border-b border-surface-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-sm">FinanceTracker</h1>
              <p className="text-xs text-slate-500">Pro Edition</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-600/20 text-primary-400'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-surface-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">{user?.username}</p>
              <p className="text-xs text-slate-500">{user?.email}</p>
            </div>
            <button onClick={handleLogout} className="p-2 text-slate-500 hover:text-red-400 transition-colors" title="Cerrar sesión">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="p-6 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
