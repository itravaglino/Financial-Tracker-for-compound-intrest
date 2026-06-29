import { useEffect, useState } from 'react';
import { api, Order, AccountStatus } from '../api';
import { ArrowUpCircle, ArrowDownCircle, Clock } from 'lucide-react';

export default function TradingPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [account, setAccount] = useState<AccountStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ symbol: '', side: 'buy', quantity: '', order_type: 'market', limit_price: '' });
  const [message, setMessage] = useState('');

  useEffect(() => {
    api.getOrders().then(setOrders);
    api.getAccount().then(setAccount);
  }, []);

  const handleOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      const order = await api.placeOrder({
        symbol: form.symbol.toUpperCase(),
        side: form.side,
        quantity: parseFloat(form.quantity),
        order_type: form.order_type,
        limit_price: form.limit_price ? parseFloat(form.limit_price) : undefined,
      });
      setMessage(`Orden ${order.status === 'executed' ? 'ejecutada' : order.status}: ${order.side.toUpperCase()} ${order.quantity} ${order.symbol}`);
      setOrders(await api.getOrders());
      setForm({ symbol: '', side: 'buy', quantity: '', order_type: 'market', limit_price: '' });
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Error al ejecutar orden');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Trading</h1>
        <p className="text-slate-400">Compra y venta de acciones vía API (Alpaca Paper Trading)</p>
      </div>

      {account && (
        <div className={`card border ${account.configured ? 'border-emerald-500/30' : 'border-amber-500/30'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">
                Modo: <span className={account.configured ? 'text-emerald-400' : 'text-amber-400'}>{account.mode}</span>
              </p>
              {account.message && <p className="text-xs text-slate-400 mt-1">{account.message}</p>}
            </div>
            {account.buying_power !== undefined && (
              <div className="text-right">
                <p className="text-xs text-slate-400">Buying Power</p>
                <p className="font-mono font-bold">${account.buying_power.toLocaleString()}</p>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form onSubmit={handleOrder} className="card space-y-4">
          <h3 className="font-semibold">Nueva orden</h3>

          {message && (
            <div className={`text-sm px-3 py-2 rounded-lg ${message.includes('ejecutada') ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
              {message}
            </div>
          )}

          <div className="flex gap-2">
            <button type="button" onClick={() => setForm({ ...form, side: 'buy' })}
              className={`flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2 ${form.side === 'buy' ? 'bg-emerald-600 text-white' : 'bg-surface-800 text-slate-400'}`}>
              <ArrowUpCircle className="w-4 h-4" /> Comprar
            </button>
            <button type="button" onClick={() => setForm({ ...form, side: 'sell' })}
              className={`flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2 ${form.side === 'sell' ? 'bg-red-600 text-white' : 'bg-surface-800 text-slate-400'}`}>
              <ArrowDownCircle className="w-4 h-4" /> Vender
            </button>
          </div>

          <div>
            <label className="label">Símbolo</label>
            <input className="input" value={form.symbol} onChange={e => setForm({ ...form, symbol: e.target.value })} placeholder="AAPL" required />
          </div>
          <div>
            <label className="label">Cantidad</label>
            <input type="number" step="any" className="input" value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} required />
          </div>
          <div>
            <label className="label">Tipo de orden</label>
            <select className="input" value={form.order_type} onChange={e => setForm({ ...form, order_type: e.target.value })}>
              <option value="market">Market</option>
              <option value="limit">Limit</option>
            </select>
          </div>
          {form.order_type === 'limit' && (
            <div>
              <label className="label">Precio límite</label>
              <input type="number" step="any" className="input" value={form.limit_price} onChange={e => setForm({ ...form, limit_price: e.target.value })} />
            </div>
          )}
          <button type="submit" className={`w-full py-2.5 rounded-lg font-medium text-white ${form.side === 'buy' ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-red-600 hover:bg-red-500'}`} disabled={loading}>
            {loading ? 'Ejecutando...' : `${form.side === 'buy' ? 'Comprar' : 'Vender'} ${form.symbol || '...'}`}
          </button>
        </form>

        <div className="card">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4" /> Historial de órdenes
          </h3>
          {orders.length === 0 ? (
            <p className="text-slate-400 text-sm">No hay órdenes aún</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {orders.map(o => (
                <div key={o.id} className="flex items-center justify-between p-3 bg-surface-800/50 rounded-lg text-sm">
                  <div>
                    <span className={`font-bold ${o.side === 'buy' ? 'text-emerald-400' : 'text-red-400'}`}>
                      {o.side.toUpperCase()}
                    </span>
                    <span className="font-mono ml-2">{o.quantity} {o.symbol}</span>
                    <p className="text-xs text-slate-500 mt-0.5">{new Date(o.created_at).toLocaleString()}</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    o.status === 'executed' ? 'bg-emerald-500/20 text-emerald-400' :
                    o.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                    'bg-amber-500/20 text-amber-400'
                  }`}>
                    {o.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
