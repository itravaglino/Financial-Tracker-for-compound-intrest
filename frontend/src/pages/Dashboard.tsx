import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { portfolio, market, alerts } from '../api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

interface Holding {
  symbol: string;
  quantity: number;
  current_price?: number;
  market_value?: number;
  gain_loss?: number;
  gain_loss_pct?: number;
}

interface PortfolioData {
  id: number;
  name: string;
  holdings: Holding[];
  total_value?: number;
  total_gain_loss?: number;
}

export default function Dashboard() {
  const [portfolios, setPortfolios] = useState<PortfolioData[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggeredAlerts, setTriggeredAlerts] = useState<unknown[]>([]);
  const [neuralSummary, setNeuralSummary] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [portRes, alertRes] = await Promise.all([
        portfolio.list(),
        alerts.check().catch(() => ({ data: { triggered_alerts: [], triggered_stop_losses: [] } })),
      ]);
      setPortfolios(portRes.data);
      setTriggeredAlerts([
        ...alertRes.data.triggered_alerts,
        ...alertRes.data.triggered_stop_losses,
      ]);

      const symbols = portRes.data.flatMap((p: PortfolioData) => p.holdings.map((h) => h.symbol));
      if (symbols.length > 0) {
        const neural = await market.portfolioNeural(symbols.join(','));
        setNeuralSummary(neural.data);
      }
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  const totalValue = portfolios.reduce((sum, p) => sum + (p.total_value || 0), 0);
  const totalGain = portfolios.reduce((sum, p) => sum + (p.total_gain_loss || 0), 0);
  const allHoldings = portfolios.flatMap((p) => p.holdings);
  const gainPct = totalValue > 0 ? (totalGain / (totalValue - totalGain)) * 100 : 0;

  const chartData = {
    labels: allHoldings.map((h) => h.symbol),
    datasets: [
      {
        label: 'Valor de mercado',
        data: allHoldings.map((h) => h.market_value || 0),
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: '#3b82f6',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  if (loading) return <div className="loading">Cargando dashboard...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Resumen de tu portfolio en tiempo real</p>
      </div>

      {triggeredAlerts.length > 0 && (
        <div className="card mb-4" style={{ borderColor: 'var(--accent-red)' }}>
          <div className="card-title" style={{ color: 'var(--accent-red)' }}>
            Alertas activadas ({triggeredAlerts.length})
          </div>
          {triggeredAlerts.map((a: unknown, i: number) => {
            const alert = a as { message?: string; symbol?: string; action?: string };
            return (
              <div key={i} className="alert-item">
                <span>{alert.message || `${alert.symbol}: ${alert.action}`}</span>
              </div>
            );
          })}
        </div>
      )}

      <div className="grid grid-4 mb-4">
        <div className="card stat-card">
          <div className="stat-value">${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          <div className="stat-label">Valor total</div>
        </div>
        <div className="card stat-card">
          <div className={`stat-value ${totalGain >= 0 ? 'positive' : 'negative'}`}>
            {totalGain >= 0 ? '+' : ''}${totalGain.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="stat-label">Ganancia/Pérdida</div>
        </div>
        <div className="card stat-card">
          <div className={`stat-value ${gainPct >= 0 ? 'positive' : 'negative'}`}>
            {gainPct >= 0 ? '+' : ''}{gainPct.toFixed(2)}%
          </div>
          <div className="stat-label">Rendimiento</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value">{allHoldings.length}</div>
          <div className="stat-label">Posiciones</div>
        </div>
      </div>

      <div className="grid grid-2 mb-4">
        <div className="card">
          <div className="card-title">Distribución del portfolio</div>
          <div className="chart-container">
            {allHoldings.length > 0 ? (
              <Line data={chartData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }} />
            ) : (
              <div className="loading">Agrega posiciones en Portfolio</div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-title">Análisis neuronal del portfolio</div>
          {neuralSummary ? (
            <div>
              <div className="grid grid-3 mt-4">
                <div className="stat-card">
                  <div className="stat-value positive">{(neuralSummary as { buy_signals?: number }).buy_signals}</div>
                  <div className="stat-label">Señales compra</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value negative">{(neuralSummary as { sell_signals?: number }).sell_signals}</div>
                  <div className="stat-label">Señales venta</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{(neuralSummary as { portfolio_recommendation?: string }).portfolio_recommendation}</div>
                  <div className="stat-label">Recomendación</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="loading">Sin datos de análisis</div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-title">Posiciones recientes</div>
        {allHoldings.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Símbolo</th>
                <th>Cantidad</th>
                <th>Precio</th>
                <th>Valor</th>
                <th>G/P</th>
              </tr>
            </thead>
            <tbody>
              {allHoldings.map((h, i) => (
                <tr key={i}>
                  <td><strong>{h.symbol}</strong></td>
                  <td>{h.quantity}</td>
                  <td>${h.current_price?.toFixed(2)}</td>
                  <td>${h.market_value?.toLocaleString()}</td>
                  <td className={(h.gain_loss || 0) >= 0 ? 'positive' : 'negative'}>
                    {(h.gain_loss || 0) >= 0 ? '+' : ''}{h.gain_loss_pct?.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="loading">No hay posiciones. Ve a Portfolio para agregar.</div>
        )}
      </div>
    </div>
  );
}
