import { useEffect, useState } from 'react';
import { api, Portfolio, Notification } from '../api';
import { TrendingUp, TrendingDown, DollarSign, Activity, Bell } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getPortfolios(), api.getNotifications()])
      .then(([p, n]) => {
        setPortfolios(p);
        setNotifications(n.filter(x => !x.is_read).slice(0, 5));
      })
      .finally(() => setLoading(false));
  }, []);

  const totalValue = portfolios.reduce((s, p) => s + (p.total_value || 0), 0);
  const totalGain = portfolios.reduce((s, p) => s + (p.total_gain_loss || 0), 0);
  const totalCost = totalValue - totalGain;
  const totalGainPct = totalCost ? (totalGain / totalCost) * 100 : 0;
  const allHoldings = portfolios.flatMap(p => p.holdings);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-slate-400">Resumen de tu situación financiera</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          icon={DollarSign}
          label="Valor total"
          value={`$${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          color="primary"
        />
        <StatCard
          icon={totalGain >= 0 ? TrendingUp : TrendingDown}
          label="Ganancia/Pérdida"
          value={`${totalGain >= 0 ? '+' : ''}$${totalGain.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          sub={`${totalGainPct >= 0 ? '+' : ''}${totalGainPct.toFixed(2)}%`}
          color={totalGain >= 0 ? 'green' : 'red'}
        />
        <StatCard
          icon={Activity}
          label="Posiciones"
          value={String(allHoldings.length)}
          sub={`${portfolios.length} portfolio(s)`}
          color="blue"
        />
        <StatCard
          icon={Bell}
          label="Alertas"
          value={String(notifications.length)}
          sub="sin leer"
          color="yellow"
        />
      </div>

      {notifications.length > 0 && (
        <div className="card">
          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <Bell className="w-4 h-4 text-amber-400" /> Notificaciones recientes
          </h2>
          <div className="space-y-2">
            {notifications.map(n => (
              <div key={n.id} className="flex items-start gap-3 p-3 bg-surface-800/50 rounded-lg">
                <div className="w-2 h-2 mt-2 rounded-full bg-amber-400 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium">{n.title}</p>
                  <p className="text-xs text-slate-400">{n.message}</p>
                </div>
              </div>
            ))}
          </div>
          <Link to="/alerts" className="text-sm text-primary-400 hover:text-primary-300 mt-3 inline-block">
            Ver todas las alertas →
          </Link>
        </div>
      )}

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">Posiciones principales</h2>
          <Link to="/portfolio" className="text-sm text-primary-400 hover:text-primary-300">Ver portfolio →</Link>
        </div>
        {allHoldings.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            <p>No tienes posiciones aún.</p>
            <Link to="/portfolio" className="text-primary-400 hover:text-primary-300 text-sm mt-2 inline-block">
              Importar desde Yahoo Finance →
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-surface-800">
                  <th className="text-left py-2 font-medium">Símbolo</th>
                  <th className="text-right py-2 font-medium">Precio</th>
                  <th className="text-right py-2 font-medium">Valor</th>
                  <th className="text-right py-2 font-medium">P&L</th>
                  <th className="text-right py-2 font-medium">Valoración</th>
                </tr>
              </thead>
              <tbody>
                {allHoldings.slice(0, 8).map(h => (
                  <tr key={h.id} className="border-b border-surface-800/50 hover:bg-surface-800/30">
                    <td className="py-3 font-mono font-medium">{h.symbol}</td>
                    <td className="py-3 text-right">${h.current_price?.toFixed(2) ?? '—'}</td>
                    <td className="py-3 text-right">${h.market_value?.toLocaleString() ?? '—'}</td>
                    <td className={`py-3 text-right ${(h.gain_loss_pct ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {(h.gain_loss_pct ?? 0) >= 0 ? '+' : ''}{h.gain_loss_pct?.toFixed(2) ?? '—'}%
                    </td>
                    <td className="py-3 text-right">
                      <RatingBadge rating={h.valuation_rating} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub, color }: {
  icon: React.ElementType; label: string; value: string; sub?: string; color: string;
}) {
  const colors: Record<string, string> = {
    primary: 'bg-primary-500/20 text-primary-400',
    green: 'bg-emerald-500/20 text-emerald-400',
    red: 'bg-red-500/20 text-red-400',
    blue: 'bg-blue-500/20 text-blue-400',
    yellow: 'bg-amber-500/20 text-amber-400',
  };
  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-xs text-slate-400">{label}</p>
          <p className="text-lg font-bold">{value}</p>
          {sub && <p className="text-xs text-slate-500">{sub}</p>}
        </div>
      </div>
    </div>
  );
}

function RatingBadge({ rating }: { rating?: string }) {
  if (!rating) return <span className="text-slate-500">—</span>;
  const isGood = rating.includes('infravalorada');
  const isBad = rating.includes('sobrevalorada');
  return (
    <span className={isGood ? 'badge-green' : isBad ? 'badge-red' : 'badge-yellow'}>
      {rating}
    </span>
  );
}
