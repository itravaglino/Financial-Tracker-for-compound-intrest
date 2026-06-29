import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { portfolio, market } from '../api';

export default function Analysis() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [selected, setSelected] = useState('');
  const [tab, setTab] = useState('technical');
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [isometric, setIsometric] = useState<Record<string, unknown> | null>(null);
  const [contrast, setContrast] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    portfolio.list().then((res) => {
      const syms = [...new Set(res.data.flatMap((p: { holdings: { symbol: string }[] }) => p.holdings.map((h) => h.symbol)))] as string[];
      setSymbols(syms);
      if (syms.length > 0) setSelected(syms[0]);
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    loadAnalysis();
  }, [selected, tab]);

  const loadAnalysis = async () => {
    setLoading(true);
    try {
      if (tab === 'technical') {
        const res = await market.technical(selected);
        setData(res.data);
      } else if (tab === 'neural') {
        const res = await market.neural(selected);
        setData(res.data);
      } else if (tab === 'valuation') {
        const res = await market.valuation(selected);
        setData(res.data);
      } else if (tab === 'metrics') {
        const res = await market.metrics(selected);
        setData(res.data);
      }
    } catch { setData(null); }
    finally { setLoading(false); }
  };

  const loadIsometric = async () => {
    if (symbols.length === 0) return;
    setLoading(true);
    try {
      const res = await market.isometric(symbols.join(','));
      setIsometric(res.data);
      setTab('isometric');
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const loadContrast = async () => {
    if (symbols.length === 0) return;
    setLoading(true);
    try {
      const res = await market.portfolioContrast(symbols.join(','));
      setContrast(res.data);
      setTab('contrast');
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const tech = data as {
    symbol?: string;
    current_price?: number;
    rsi?: number;
    trend?: string;
    fibonacci_levels?: Record<string, number>;
    fibonacci_patterns?: { type: string; level: string; signal: string }[];
    signals?: { indicator: string; signal: string; value: number }[];
    history?: { dates: string[]; close: number[] };
    neural_prediction?: string;
    confidence?: number;
    recommendation?: string;
    model_accuracy?: number;
    pattern_probabilities?: Record<string, number>;
    objective_score?: number;
    rating?: string;
    component_scores?: Record<string, number>;
    sharpe_ratio?: number;
    sortino_ratio?: number;
    max_drawdown_pct?: number;
    quality_score?: number;
  };

  const chartData = tech?.history ? {
    labels: tech.history.dates,
    datasets: [{
      label: tech.symbol,
      data: tech.history.close,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: true,
      tension: 0.3,
    }],
  } : null;

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>Análisis avanzado</h1>
          <p>Análisis técnico, redes neuronales, valoración objetiva y valor isotérico</p>
        </div>
        <div className="flex-between gap-2">
          <button className="btn btn-secondary" onClick={loadIsometric}>Valor isotérico</button>
          <button className="btn btn-secondary" onClick={loadContrast}>Contraste portfolio</button>
        </div>
      </div>

      {symbols.length > 0 && (
        <div className="form-group mb-4" style={{ maxWidth: 300 }}>
          <label>Símbolo</label>
          <select value={selected} onChange={(e) => { setSelected(e.target.value); setTab('technical'); setIsometric(null); setContrast(null); }}>
            {symbols.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      )}

      <div className="tabs">
        {['technical', 'neural', 'valuation', 'metrics'].map((t) => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => { setTab(t); setIsometric(null); setContrast(null); }}>
            {{ technical: 'Técnico', neural: 'Red neuronal', valuation: 'Valoración', metrics: 'Métricas' }[t]}
          </button>
        ))}
        {isometric && <button className={`tab ${tab === 'isometric' ? 'active' : ''}`} onClick={() => setTab('isometric')}>Isotérico</button>}
        {contrast && <button className={`tab ${tab === 'contrast' ? 'active' : ''}`} onClick={() => setTab('contrast')}>Contraste</button>}
      </div>

      {loading && <div className="loading">Analizando...</div>}

      {!loading && tab === 'technical' && data && (
        <div className="grid grid-2">
          <div className="card">
            <div className="card-title">Gráfico de precio — {tech.symbol}</div>
            {chartData && (
              <div className="chart-container">
                <Line data={chartData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }} />
              </div>
            )}
          </div>
          <div className="card">
            <div className="card-title">Indicadores</div>
            <div className="grid grid-2 mt-4">
              <div className="stat-card"><div className="stat-value">${tech.current_price?.toFixed(2)}</div><div className="stat-label">Precio</div></div>
              <div className="stat-card"><div className="stat-value">{tech.rsi}</div><div className="stat-label">RSI</div></div>
              <div className="stat-card"><div className={`stat-value ${tech.trend === 'bullish' ? 'positive' : tech.trend === 'bearish' ? 'negative' : ''}`}>{tech.trend}</div><div className="stat-label">Tendencia</div></div>
            </div>
            <div className="mt-4">
              <strong>Señales:</strong>
              {tech.signals?.map((s, i) => (
                <div key={i} className="mt-4">
                  <span className={`badge ${s.signal.includes('bull') || s.signal.includes('oversold') ? 'badge-green' : s.signal.includes('bear') || s.signal.includes('overbought') ? 'badge-red' : 'badge-yellow'}`}>
                    {s.indicator}: {s.signal}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <div className="card-title">Niveles Fibonacci</div>
            <table>
              <tbody>
                {tech.fibonacci_levels && Object.entries(tech.fibonacci_levels).map(([level, price]) => (
                  <tr key={level}><td>{level}</td><td>${price.toFixed(2)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card">
            <div className="card-title">Patrones Fibonacci detectados</div>
            {tech.fibonacci_patterns?.length ? tech.fibonacci_patterns.map((p, i) => (
              <div key={i} className="alert-item">
                <span>Nivel {p.level} — {p.signal}</span>
                <span className={`badge ${p.signal === 'support' ? 'badge-green' : 'badge-red'}`}>{p.type}</span>
              </div>
            )) : <div className="loading">Sin patrones detectados</div>}
          </div>
        </div>
      )}

      {!loading && tab === 'neural' && data && (
        <div className="grid grid-2">
          <div className="card">
            <div className="card-title">Predicción neuronal — {tech.symbol}</div>
            <div className="grid grid-2 mt-4">
              <div className="stat-card">
                <div className={`stat-value ${tech.neural_prediction?.includes('bull') ? 'positive' : tech.neural_prediction?.includes('bear') ? 'negative' : ''}`}>
                  {tech.neural_prediction}
                </div>
                <div className="stat-label">Predicción</div>
              </div>
              <div className="stat-card"><div className="stat-value">{tech.confidence}%</div><div className="stat-label">Confianza</div></div>
              <div className="stat-card"><div className="stat-value">{tech.model_accuracy}%</div><div className="stat-label">Precisión modelo</div></div>
              <div className="stat-card">
                <div className={`stat-value badge-${tech.recommendation === 'buy' ? 'green' : tech.recommendation === 'sell' ? 'red' : 'yellow'}`}>{tech.recommendation}</div>
                <div className="stat-label">Recomendación</div>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-title">Probabilidades por patrón</div>
            {tech.pattern_probabilities && Object.entries(tech.pattern_probabilities).map(([label, prob]) => (
              <div key={label} className="alert-item">
                <span>{label}</span>
                <span>{prob as number}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && tab === 'valuation' && data && (
        <div className="grid grid-2">
          <div className="card">
            <div className="card-title">Valoración objetiva — {tech.symbol}</div>
            <div className="grid grid-2 mt-4">
              <div className="stat-card"><div className="stat-value">{tech.objective_score}/100</div><div className="stat-label">Score objetivo</div></div>
              <div className="stat-card">
                <div className={`stat-value ${tech.rating === 'undervalued' ? 'positive' : tech.rating === 'overvalued' ? 'negative' : ''}`}>{tech.rating}</div>
                <div className="stat-label">Rating</div>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-title">Componentes de valoración</div>
            {tech.component_scores && Object.entries(tech.component_scores).map(([k, v]) => (
              <div key={k} className="alert-item"><span>{k.replace(/_/g, ' ')}</span><span>{v as number}/100</span></div>
            ))}
          </div>
        </div>
      )}

      {!loading && tab === 'metrics' && data && (
        <div className="grid grid-3">
          <div className="card stat-card"><div className="stat-value">{tech.sharpe_ratio}</div><div className="stat-label">Sharpe Ratio</div></div>
          <div className="card stat-card"><div className="stat-value">{tech.sortino_ratio}</div><div className="stat-label">Sortino Ratio</div></div>
          <div className="card stat-card"><div className="stat-value negative">{tech.max_drawdown_pct}%</div><div className="stat-label">Max Drawdown</div></div>
          <div className="card stat-card"><div className="stat-value">{tech.quality_score}</div><div className="stat-label">Quality Score</div></div>
        </div>
      )}

      {!loading && tab === 'isometric' && isometric && (
        <div className="card">
          <div className="card-title">Valor isotérico — Comparación sin dependencia de moneda</div>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>{(isometric as { methodology?: string }).methodology}</p>
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Símbolo</th>
                <th>Score isotérico</th>
                <th>Retorno anual</th>
                <th>Volatilidad</th>
                <th>Beta</th>
              </tr>
            </thead>
            <tbody>
              {((isometric as { symbols?: { symbol: string; isometric_rank?: number; isometric_normalized?: number; annual_return_pct?: number; volatility?: number; beta?: number }[] }).symbols || []).map((s) => (
                <tr key={s.symbol}>
                  <td>#{s.isometric_rank}</td>
                  <td><strong>{s.symbol}</strong></td>
                  <td>{s.isometric_normalized}/100</td>
                  <td className={(s.annual_return_pct || 0) >= 0 ? 'positive' : 'negative'}>{s.annual_return_pct}%</td>
                  <td>{s.volatility}%</td>
                  <td>{s.beta}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && tab === 'contrast' && contrast && (
        <div className="card">
          <div className="card-title">Contraste técnico del portfolio</div>
          <div className="grid grid-4 mb-4">
            <div className="stat-card"><div className="stat-value positive">{(contrast as { bullish_count?: number }).bullish_count}</div><div className="stat-label">Alcistas</div></div>
            <div className="stat-card"><div className="stat-value negative">{(contrast as { bearish_count?: number }).bearish_count}</div><div className="stat-label">Bajistas</div></div>
            <div className="stat-card"><div className="stat-value">{(contrast as { neutral_count?: number }).neutral_count}</div><div className="stat-label">Neutrales</div></div>
            <div className="stat-card"><div className="stat-value">{(contrast as { portfolio_sentiment?: string }).portfolio_sentiment}</div><div className="stat-label">Sentimiento</div></div>
          </div>
        </div>
      )}

      {symbols.length === 0 && <div className="card loading">Agrega posiciones en Portfolio para analizar.</div>}
    </div>
  );
}
