import { useState } from 'react';
import { api } from '../api';
import { Search, Brain, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts';

export default function Analysis() {
  const [symbol, setSymbol] = useState('AAPL');
  const [compareSymbols, setCompareSymbols] = useState('AAPL,MSFT,GOOGL,NVDA');
  const [technical, setTechnical] = useState(null);
  const [valuation, setValuation] = useState(null);
  const [isometric, setIsometric] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState('technical');

  const analyze = async () => {
    setLoading(true);
    try {
      const [tech, val, iso] = await Promise.all([
        api.getTechnical(symbol),
        api.getValuation(symbol),
        api.getIsometric(symbol),
      ]);
      setTechnical(tech);
      setValuation(val);
      setIsometric(iso);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const compare = async () => {
    setLoading(true);
    try {
      const symbols = compareSymbols.split(',').map(s => s.trim()).filter(Boolean);
      const data = await api.compare(symbols);
      setComparison(data);
      setTab('compare');
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const radarData = technical ? [
    { metric: 'RSI', value: technical.rsi },
    { metric: 'MACD', value: Math.abs(technical.macd) * 100 },
    { metric: 'Bollinger', value: technical.bollinger_position * 100 },
    { metric: 'Neural', value: technical.neural_confidence * 100 },
  ] : [];

  const fibData = technical
    ? Object.entries(technical.fibonacci_levels).map(([level, price]) => ({ level, price }))
    : [];

  return (
    <div>
      <div className="page-header">
        <h2><Brain size={24} style={{ verticalAlign: 'middle', marginRight: 8 }} />Análisis IA</h2>
        <p>Redes neuronales LSTM, Fibonacci y valoración objetiva</p>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'end' }}>
          <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
            <label>Símbolo</label>
            <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder="AAPL" />
          </div>
          <button className="btn-primary" onClick={analyze} disabled={loading}>
            <Search size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />
            Analizar
          </button>
        </div>
      </div>

      {technical && (
        <div className="tabs">
          <button className={`tab ${tab === 'technical' ? 'active' : ''}`} onClick={() => setTab('technical')}>Técnico</button>
          <button className={`tab ${tab === 'valuation' ? 'active' : ''}`} onClick={() => setTab('valuation')}>Valoración</button>
          <button className={`tab ${tab === 'isometric' ? 'active' : ''}`} onClick={() => setTab('isometric')}>Isométrico</button>
          <button className={`tab ${tab === 'fibonacci' ? 'active' : ''}`} onClick={() => setTab('fibonacci')}>Fibonacci</button>
          <button className={`tab ${tab === 'compare' ? 'active' : ''}`} onClick={() => setTab('compare')}>Comparar</button>
        </div>
      )}

      {tab === 'technical' && technical && (
        <div className="grid grid-2">
          <div className="card">
            <h3 style={{ marginBottom: 16 }}>Indicadores Técnicos</h3>
            <div className="grid grid-2" style={{ gap: 12 }}>
              <div><span className="card-title">RSI</span><div className="card-value" style={{ fontSize: 20 }}>{technical.rsi}</div></div>
              <div><span className="card-title">Tendencia</span><div><span className={`badge ${technical.trend === 'ALCISTA' ? 'badge-green' : technical.trend === 'BAJISTA' ? 'badge-red' : 'badge-yellow'}`}>{technical.trend}</span></div></div>
              <div><span className="card-title">Señal</span><div><span className={`badge ${technical.signal === 'COMPRAR' ? 'badge-green' : technical.signal === 'VENDER' ? 'badge-red' : 'badge-blue'}`}>{technical.signal}</span></div></div>
              <div><span className="card-title">Confianza Neural</span><div className="card-value" style={{ fontSize: 20 }}>{(technical.neural_confidence * 100).toFixed(0)}%</div></div>
            </div>
            {technical.pattern_detected && (
              <div style={{ marginTop: 16, padding: 12, background: 'rgba(139, 92, 246, 0.1)', borderRadius: 8 }}>
                <strong>Patrón detectado:</strong> {technical.pattern_detected.replace(/_/g, ' ')}
              </div>
            )}
            <div style={{ marginTop: 16 }}>
              <strong>Soportes:</strong> {technical.support_levels.map(s => `$${s.toFixed(2)}`).join(', ') || 'N/A'}
              <br />
              <strong>Resistencias:</strong> {technical.resistance_levels.map(r => `$${r.toFixed(2)}`).join(', ') || 'N/A'}
            </div>
          </div>
          <div className="card">
            <h3 style={{ marginBottom: 16 }}>Radar de Análisis</h3>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#2d3748" />
                <PolarAngleAxis dataKey="metric" stroke="#94a3b8" />
                <Radar dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {tab === 'valuation' && valuation && (
        <div className="grid grid-3">
          <div className="card">
            <div className="card-title">Precio Actual</div>
            <div className="card-value">${valuation.current_price}</div>
          </div>
          <div className="card">
            <div className="card-title">Valor Justo (DCF)</div>
            <div className="card-value">${valuation.fair_value}</div>
          </div>
          <div className="card">
            <div className="card-title">Potencial</div>
            <div className={`card-value ${valuation.upside_percent >= 0 ? 'positive' : 'negative'}`}>
              {valuation.upside_percent >= 0 ? '+' : ''}{valuation.upside_percent}%
            </div>
          </div>
          <div className="card">
            <div className="card-title">P/E Ratio</div>
            <div className="card-value">{valuation.pe_ratio || 'N/A'}</div>
          </div>
          <div className="card">
            <div className="card-title">PEG Ratio</div>
            <div className="card-value">{valuation.peg_ratio || 'N/A'}</div>
          </div>
          <div className="card">
            <div className="card-title">Recomendación</div>
            <div><span className={`badge ${valuation.recommendation === 'COMPRAR' ? 'badge-green' : valuation.recommendation === 'VENDER' ? 'badge-red' : 'badge-yellow'}`}>
              {valuation.recommendation} ({(valuation.confidence * 100).toFixed(0)}%)
            </span></div>
          </div>
        </div>
      )}

      {tab === 'isometric' && isometric && (
        <div className="grid grid-2">
          <div className="card">
            <h3 style={{ marginBottom: 16 }}>Valor Isométrico (Independiente de Moneda)</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 16, fontSize: 14 }}>
              Normaliza el valor de la acción eliminando el sesgo cambiario para un juicio objetivo.
            </p>
            <div className="grid grid-2" style={{ gap: 12 }}>
              <div><span className="card-title">Precio Original</span><div className="card-value" style={{ fontSize: 20 }}>{isometric.original_price} {isometric.original_currency}</div></div>
              <div><span className="card-title">Precio USD</span><div className="card-value" style={{ fontSize: 20 }}>${isometric.price_usd}</div></div>
              <div><span className="card-title">Precio EUR</span><div className="card-value" style={{ fontSize: 20 }}>€{isometric.price_eur}</div></div>
              <div><span className="card-title">Valor Normalizado</span><div className="card-value" style={{ fontSize: 20 }}>${isometric.price_normalized}</div></div>
            </div>
            <div style={{ marginTop: 16 }}>
              <span className="card-title">Score de Independencia Cambiaria</span>
              <div className="card-value">{isometric.currency_independence_score}/100</div>
            </div>
          </div>
        </div>
      )}

      {tab === 'fibonacci' && fibData.length > 0 && (
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Niveles de Fibonacci</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={fibData}>
              <XAxis dataKey="level" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Bar dataKey="price" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {tab === 'compare' && (
        <div>
          <div className="card" style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', gap: 12, alignItems: 'end' }}>
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label>Símbolos a comparar</label>
                <input value={compareSymbols} onChange={(e) => setCompareSymbols(e.target.value)} />
              </div>
              <button className="btn-primary" onClick={compare} disabled={loading}>
                <TrendingUp size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                Comparar
              </button>
            </div>
          </div>
          {comparison && (
            <div className="card">
              <table>
                <thead>
                  <tr>
                    <th>Símbolo</th>
                    <th>Precio</th>
                    <th>Valor Normalizado</th>
                    <th>RSI</th>
                    <th>Tendencia</th>
                    <th>Patrón IA</th>
                    <th>Confianza</th>
                    <th>Señal</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.map((c) => (
                    <tr key={c.symbol}>
                      <td><strong>{c.symbol}</strong></td>
                      <td>${c.price?.toFixed(2)}</td>
                      <td>${c.price_normalized?.toFixed(2)}</td>
                      <td>{c.rsi}</td>
                      <td><span className={`badge ${c.trend === 'ALCISTA' ? 'badge-green' : 'badge-red'}`}>{c.trend}</span></td>
                      <td>{c.pattern?.replace(/_/g, ' ') || '-'}</td>
                      <td>{(c.neural_confidence * 100).toFixed(0)}%</td>
                      <td><span className={`badge ${c.signal === 'COMPRAR' ? 'badge-green' : c.signal === 'VENDER' ? 'badge-red' : 'badge-blue'}`}>{c.signal}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
