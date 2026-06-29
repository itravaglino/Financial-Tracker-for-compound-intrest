import { useEffect, useState } from 'react';
import { api, Portfolio, Holding } from '../api';
import { Plus, Download, Trash2, RefreshCw } from 'lucide-react';

export default function PortfolioPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [showImport, setShowImport] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [selectedPortfolio, setSelectedPortfolio] = useState<number | null>(null);
  const [importSymbols, setImportSymbols] = useState('');
  const [importName, setImportName] = useState('Importado de Yahoo Finance');
  const [newHolding, setNewHolding] = useState({ symbol: '', quantity: '', avg_cost: '' });
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    api.getPortfolios()
      .then(p => {
        setPortfolios(p);
        if (p.length && !selectedPortfolio) setSelectedPortfolio(p[0].id);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleImport = async () => {
    const symbols = importSymbols.split(/[,\s]+/).filter(Boolean);
    if (!symbols.length) return setError('Ingresa al menos un símbolo');
    try {
      await api.importYahoo(symbols, importName);
      setShowImport(false);
      setImportSymbols('');
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al importar');
    }
  };

  const handleAddHolding = async () => {
    if (!selectedPortfolio) return;
    try {
      await api.addHolding(selectedPortfolio, {
        symbol: newHolding.symbol.toUpperCase(),
        quantity: parseFloat(newHolding.quantity),
        avg_cost: parseFloat(newHolding.avg_cost),
      });
      setShowAdd(false);
      setNewHolding({ symbol: '', quantity: '', avg_cost: '' });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al agregar');
    }
  };

  const handleDelete = async (id: number) => {
    await api.deleteHolding(id);
    load();
  };

  const current = portfolios.find(p => p.id === selectedPortfolio);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Portfolio</h1>
          <p className="text-slate-400">Gestiona tus inversiones e importa desde Yahoo Finance</p>
        </div>
        <div className="flex gap-2">
          <button onClick={load} className="btn-secondary flex items-center gap-2">
            <RefreshCw className="w-4 h-4" /> Actualizar
          </button>
          <button onClick={() => setShowImport(true)} className="btn-secondary flex items-center gap-2">
            <Download className="w-4 h-4" /> Importar Yahoo
          </button>
          <button onClick={() => setShowAdd(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Agregar
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-3 py-2 rounded-lg">{error}</div>
      )}

      {portfolios.length > 1 && (
        <div className="flex gap-2">
          {portfolios.map(p => (
            <button
              key={p.id}
              onClick={() => setSelectedPortfolio(p.id)}
              className={`px-3 py-1.5 rounded-lg text-sm ${selectedPortfolio === p.id ? 'bg-primary-600 text-white' : 'bg-surface-800 text-slate-400'}`}
            >
              {p.name}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
        </div>
      ) : current ? (
        <>
          <div className="grid grid-cols-3 gap-4">
            <div className="card text-center">
              <p className="text-xs text-slate-400">Valor total</p>
              <p className="text-2xl font-bold">${current.total_value?.toLocaleString() ?? '0'}</p>
            </div>
            <div className="card text-center">
              <p className="text-xs text-slate-400">Ganancia/Pérdida</p>
              <p className={`text-2xl font-bold ${(current.total_gain_loss ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                ${current.total_gain_loss?.toLocaleString() ?? '0'}
              </p>
            </div>
            <div className="card text-center">
              <p className="text-xs text-slate-400">Rendimiento</p>
              <p className={`text-2xl font-bold ${(current.total_gain_loss_pct ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {(current.total_gain_loss_pct ?? 0) >= 0 ? '+' : ''}{current.total_gain_loss_pct?.toFixed(2) ?? '0'}%
              </p>
            </div>
          </div>

          <div className="card overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-surface-800">
                  <th className="text-left py-2">Símbolo</th>
                  <th className="text-right py-2">Cantidad</th>
                  <th className="text-right py-2">Costo prom.</th>
                  <th className="text-right py-2">Precio actual</th>
                  <th className="text-right py-2">Valor mercado</th>
                  <th className="text-right py-2">P&L</th>
                  <th className="text-right py-2">Valor isotérico</th>
                  <th className="text-right py-2">Valor intrínseco</th>
                  <th className="text-right py-2">Valoración</th>
                  <th className="py-2"></th>
                </tr>
              </thead>
              <tbody>
                {current.holdings.map((h: Holding) => (
                  <tr key={h.id} className="border-b border-surface-800/50 hover:bg-surface-800/30">
                    <td className="py-3 font-mono font-bold">{h.symbol}</td>
                    <td className="py-3 text-right">{h.quantity}</td>
                    <td className="py-3 text-right">${h.avg_cost.toFixed(2)}</td>
                    <td className="py-3 text-right">${h.current_price?.toFixed(2) ?? '—'}</td>
                    <td className="py-3 text-right">${h.market_value?.toLocaleString() ?? '—'}</td>
                    <td className={`py-3 text-right ${(h.gain_loss_pct ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {(h.gain_loss_pct ?? 0) >= 0 ? '+' : ''}{h.gain_loss_pct?.toFixed(2) ?? '—'}%
                    </td>
                    <td className="py-3 text-right font-mono text-blue-400">${h.isosteric_value?.toFixed(2) ?? '—'}</td>
                    <td className="py-3 text-right font-mono text-purple-400">${h.intrinsic_value?.toFixed(2) ?? '—'}</td>
                    <td className="py-3 text-right text-xs">{h.valuation_rating ?? '—'}</td>
                    <td className="py-3 text-right">
                      <button onClick={() => handleDelete(h.id)} className="text-slate-500 hover:text-red-400">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="card text-center py-12 text-slate-400">
          <p className="mb-4">No tienes portfolios. Importa desde Yahoo Finance o crea uno nuevo.</p>
          <button onClick={() => setShowImport(true)} className="btn-primary">Importar desde Yahoo Finance</button>
        </div>
      )}

      {showImport && (
        <Modal title="Importar desde Yahoo Finance" onClose={() => setShowImport(false)}>
          <p className="text-sm text-slate-400 mb-4">
            Ingresa los símbolos separados por coma (ej: AAPL, MSFT, GOOGL, TSLA, NVDA)
          </p>
          <div className="space-y-3">
            <div>
              <label className="label">Símbolos</label>
              <input className="input" value={importSymbols} onChange={e => setImportSymbols(e.target.value)} placeholder="AAPL, MSFT, GOOGL" />
            </div>
            <div>
              <label className="label">Nombre del portfolio</label>
              <input className="input" value={importName} onChange={e => setImportName(e.target.value)} />
            </div>
            <button onClick={handleImport} className="btn-primary w-full">Importar</button>
          </div>
        </Modal>
      )}

      {showAdd && (
        <Modal title="Agregar posición" onClose={() => setShowAdd(false)}>
          <div className="space-y-3">
            <div>
              <label className="label">Símbolo</label>
              <input className="input" value={newHolding.symbol} onChange={e => setNewHolding({ ...newHolding, symbol: e.target.value })} placeholder="AAPL" />
            </div>
            <div>
              <label className="label">Cantidad</label>
              <input type="number" className="input" value={newHolding.quantity} onChange={e => setNewHolding({ ...newHolding, quantity: e.target.value })} />
            </div>
            <div>
              <label className="label">Costo promedio</label>
              <input type="number" className="input" value={newHolding.avg_cost} onChange={e => setNewHolding({ ...newHolding, avg_cost: e.target.value })} />
            </div>
            <button onClick={handleAddHolding} className="btn-primary w-full">Agregar</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="card w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}
