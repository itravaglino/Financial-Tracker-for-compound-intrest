import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';
import { Plus, Download, RefreshCw } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

export default function Dashboard() {
  const [portfolios, setPortfolios] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [form, setForm] = useState({ symbol: '', quantity: '', avg_cost: '' });
  const [importSymbols, setImportSymbols] = useState('AAPL,MSFT,GOOGL,AMZN,NVDA');
  const [msg, setMsg] = useState('');

  const loadPortfolios = useCallback(async () => {
    try {
      const data = await api.getPortfolios();
      setPortfolios(data);
      if (data.length && !selectedId) setSelectedId(data[0].id);
      if (!data.length) {
        const p = await api.createPortfolio('Mi Portfolio');
        setPortfolios([p]);
        setSelectedId(p.id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  const loadAnalysis = useCallback(async () => {
    if (!selectedId) return;
    try {
      const data = await api.analyzePortfolio(selectedId);
      setAnalysis(data);
    } catch (e) {
      console.error(e);
    }
  }, [selectedId]);

  useEffect(() => { loadPortfolios(); }, [loadPortfolios]);
  useEffect(() => { loadAnalysis(); const i = setInterval(loadAnalysis, 60000); return () => clearInterval(i); }, [loadAnalysis]);

  const handleAdd = async (e) => {
    e.preventDefault();
    await api.addHolding(selectedId, {
      symbol: form.symbol.toUpperCase(),
      quantity: parseFloat(form.quantity),
      avg_cost: parseFloat(form.avg_cost) || 0,
    });
    setShowAdd(false);
    setForm({ symbol: '', quantity: '', avg_cost: '' });
    setMsg('Acción agregada');
    loadAnalysis();
  };

  const handleImport = async (e) => {
    e.preventDefault();
    const symbols = importSymbols.split(',').map(s => s.trim()).filter(Boolean);
    const result = await api.importYahoo(selectedId, symbols);
    setShowImport(false);
    setMsg(`Importadas ${result.imported} acciones desde Yahoo Finance`);
    loadAnalysis();
  };

  if (loading) return <div className="loading"><div className="spinner" /></div>;

  const sectorData = analysis
    ? Object.entries(analysis.sector_allocation).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Dashboard</h2>
          <p>Portfolio en tiempo real con Yahoo Finance</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn-secondary" onClick={() => setShowImport(true)}>
            <Download size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />
            Importar Yahoo
          </button>
          <button className="btn-primary" onClick={() => setShowAdd(true)}>
            <Plus size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />
            Agregar
          </button>
          <button className="btn-secondary" onClick={loadAnalysis}>
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {msg && <div className="success-msg">{msg}</div>}

      {analysis && (
        <>
          <div className="grid grid-4" style={{ marginBottom: 24 }}>
            <div className="card">
              <div className="card-title">Valor Total (USD)</div>
              <div className="card-value">${analysis.total_value_usd.toLocaleString()}</div>
            </div>
            <div className="card">
              <div className="card-title">Ganancia/Pérdida</div>
              <div className={`card-value ${analysis.total_gain_loss >= 0 ? 'positive' : 'negative'}`}>
                {analysis.total_gain_loss >= 0 ? '+' : ''}${analysis.total_gain_loss.toLocaleString()}
                <span style={{ fontSize: 16, marginLeft: 8 }}>
                  ({analysis.gain_loss_percent}%)
                </span>
              </div>
            </div>
            <div className="card">
              <div className="card-title">Score de Riesgo</div>
              <div className="card-value">{analysis.risk_score}/100</div>
            </div>
            <div className="card">
              <div className="card-title">Diversificación</div>
              <div className="card-value">{analysis.diversification_score}/100</div>
            </div>
          </div>

          <div className="grid grid-2" style={{ marginBottom: 24 }}>
            <div className="card">
              <h3 style={{ marginBottom: 16 }}>Holdings</h3>
              <table>
                <thead>
                  <tr>
                    <th>Símbolo</th>
                    <th>Precio USD</th>
                    <th>Valor Isométrico</th>
                    <th>G/P</th>
                    <th>Señal IA</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.holdings_analysis.map((h) => (
                    <tr key={h.symbol}>
                      <td><strong>{h.symbol}</strong></td>
                      <td>${h.price_usd?.toFixed(2)}</td>
                      <td>${h.price_normalized?.toFixed(2)}</td>
                      <td className={h.gain_loss >= 0 ? 'positive' : 'negative'}>
                        {h.gain_loss >= 0 ? '+' : ''}{h.gain_loss_percent}%
                      </td>
                      <td>
                        <span className={`badge ${h.technical?.signal === 'COMPRAR' ? 'badge-green' : h.technical?.signal === 'VENDER' ? 'badge-red' : 'badge-blue'}`}>
                          {h.technical?.signal}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card">
              <h3 style={{ marginBottom: 16 }}>Asignación por Sector</h3>
              {sectorData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={sectorData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                      {sectorData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => `${v.toFixed(1)}%`} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p style={{ color: 'var(--text-secondary)' }}>Agrega acciones para ver la distribución</p>
              )}
            </div>
          </div>
        </>
      )}

      {showAdd && (
        <div className="modal-overlay" onClick={() => setShowAdd(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Agregar Acción</h2>
            <form onSubmit={handleAdd}>
              <div className="form-group">
                <label>Símbolo (ej: AAPL)</label>
                <input value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Cantidad</label>
                <input type="number" step="any" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Costo Promedio</label>
                <input type="number" step="any" value={form.avg_cost} onChange={(e) => setForm({ ...form, avg_cost: e.target.value })} />
              </div>
              <button type="submit" className="btn-primary" style={{ width: '100%' }}>Agregar</button>
            </form>
          </div>
        </div>
      )}

      {showImport && (
        <div className="modal-overlay" onClick={() => setShowImport(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Importar desde Yahoo Finance</h2>
            <form onSubmit={handleImport}>
              <div className="form-group">
                <label>Símbolos (separados por coma)</label>
                <textarea rows={3} value={importSymbols} onChange={(e) => setImportSymbols(e.target.value)} />
              </div>
              <button type="submit" className="btn-primary" style={{ width: '100%' }}>Importar</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
