import { useEffect, useState } from 'react';
import { portfolio } from '../api';

interface Holding {
  id: number;
  symbol: string;
  quantity: number;
  avg_cost: number;
  current_price?: number;
  market_value?: number;
  gain_loss?: number;
  gain_loss_pct?: number;
}

interface PortfolioData {
  id: number;
  name: string;
  source: string;
  holdings: Holding[];
  total_value?: number;
  total_cost?: number;
  total_gain_loss?: number;
}

export default function PortfolioPage() {
  const [portfolios, setPortfolios] = useState<PortfolioData[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [selectedPortfolio, setSelectedPortfolio] = useState<number | null>(null);
  const [form, setForm] = useState({ symbol: '', quantity: '', avg_cost: '' });
  const [importSymbols, setImportSymbols] = useState('');
  const [importName, setImportName] = useState('Yahoo Finance Import');
  const [message, setMessage] = useState('');

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const res = await portfolio.list();
      setPortfolios(res.data);
      if (res.data.length > 0 && !selectedPortfolio) {
        setSelectedPortfolio(res.data[0].id);
      }
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPortfolio) return;
    try {
      await portfolio.addHolding(selectedPortfolio, {
        symbol: form.symbol.toUpperCase(),
        quantity: parseFloat(form.quantity),
        avg_cost: parseFloat(form.avg_cost),
      });
      setMessage('Posición agregada');
      setShowAdd(false);
      setForm({ symbol: '', quantity: '', avg_cost: '' });
      load();
    } catch {
      setMessage('Error al agregar posición');
    }
  };

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    const symbols = importSymbols.split(/[,\s]+/).filter(Boolean);
    if (symbols.length === 0) return;
    try {
      await portfolio.importYahoo(symbols, importName);
      setMessage(`Importadas ${symbols.length} acciones desde Yahoo Finance`);
      setShowImport(false);
      load();
    } catch {
      setMessage('Error al importar desde Yahoo Finance');
    }
  };

  const handleDelete = async (holdingId: number) => {
    if (!confirm('¿Eliminar esta posición?')) return;
    await portfolio.deleteHolding(holdingId);
    load();
  };

  const handleCreatePortfolio = async () => {
    const name = prompt('Nombre del portfolio:');
    if (!name) return;
    await portfolio.create(name);
    load();
  };

  const current = portfolios.find((p) => p.id === selectedPortfolio);

  if (loading) return <div className="loading">Cargando portfolio...</div>;

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>Portfolio</h1>
          <p>Gestiona tus inversiones e importa desde Yahoo Finance</p>
        </div>
        <div className="flex-between gap-2">
          <button className="btn btn-secondary" onClick={handleCreatePortfolio}>Nuevo portfolio</button>
          <button className="btn btn-secondary" onClick={() => setShowImport(true)}>Importar Yahoo</button>
          <button className="btn btn-primary" onClick={() => setShowAdd(true)}>Agregar posición</button>
        </div>
      </div>

      {message && <div className="success-msg mb-4">{message}</div>}

      {portfolios.length > 1 && (
        <div className="tabs mb-4">
          {portfolios.map((p) => (
            <button
              key={p.id}
              className={`tab ${selectedPortfolio === p.id ? 'active' : ''}`}
              onClick={() => setSelectedPortfolio(p.id)}
            >
              {p.name}
            </button>
          ))}
        </div>
      )}

      {current && (
        <>
          <div className="grid grid-3 mb-4">
            <div className="card stat-card">
              <div className="stat-value">${current.total_value?.toLocaleString()}</div>
              <div className="stat-label">Valor total</div>
            </div>
            <div className="card stat-card">
              <div className="stat-value">${current.total_cost?.toLocaleString()}</div>
              <div className="stat-label">Costo total</div>
            </div>
            <div className="card stat-card">
              <div className={`stat-value ${(current.total_gain_loss || 0) >= 0 ? 'positive' : 'negative'}`}>
                ${current.total_gain_loss?.toLocaleString()}
              </div>
              <div className="stat-label">Ganancia/Pérdida</div>
            </div>
          </div>

          <div className="card">
            <div className="card-title">Posiciones — {current.name} ({current.source})</div>
            {current.holdings.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    <th>Símbolo</th>
                    <th>Cantidad</th>
                    <th>Costo promedio</th>
                    <th>Precio actual</th>
                    <th>Valor</th>
                    <th>G/P</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {current.holdings.map((h) => (
                    <tr key={h.id}>
                      <td><strong>{h.symbol}</strong></td>
                      <td>{h.quantity}</td>
                      <td>${h.avg_cost.toFixed(2)}</td>
                      <td>${h.current_price?.toFixed(2)}</td>
                      <td>${h.market_value?.toLocaleString()}</td>
                      <td className={(h.gain_loss || 0) >= 0 ? 'positive' : 'negative'}>
                        {(h.gain_loss || 0) >= 0 ? '+' : ''}{h.gain_loss_pct?.toFixed(2)}%
                      </td>
                      <td>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDelete(h.id)}>Eliminar</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="loading">Sin posiciones. Agrega manualmente o importa desde Yahoo Finance.</div>
            )}
          </div>
        </>
      )}

      {portfolios.length === 0 && (
        <div className="card">
          <div className="loading">Crea un portfolio o importa desde Yahoo Finance para empezar.</div>
        </div>
      )}

      {showAdd && (
        <div className="modal-overlay" onClick={() => setShowAdd(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Agregar posición</h2>
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
                <label>Costo promedio</label>
                <input type="number" step="any" value={form.avg_cost} onChange={(e) => setForm({ ...form, avg_cost: e.target.value })} required />
              </div>
              <div className="flex-between gap-2">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAdd(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Agregar</button>
              </div>
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
                <textarea
                  rows={3}
                  placeholder="AAPL, MSFT, GOOGL, TSLA, AMZN"
                  value={importSymbols}
                  onChange={(e) => setImportSymbols(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Nombre del portfolio</label>
                <input value={importName} onChange={(e) => setImportName(e.target.value)} />
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 16 }}>
                Se importarán los símbolos con precio actual de Yahoo Finance. Puedes editar cantidades después.
              </p>
              <div className="flex-between gap-2">
                <button type="button" className="btn btn-secondary" onClick={() => setShowImport(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Importar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
