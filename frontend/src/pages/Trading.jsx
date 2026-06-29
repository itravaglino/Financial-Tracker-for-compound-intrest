import { useState, useEffect } from 'react';
import { api } from '../api';
import { ShoppingCart, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';

export default function Trading() {
  const [orders, setOrders] = useState([]);
  const [account, setAccount] = useState(null);
  const [form, setForm] = useState({ symbol: '', side: 'buy', quantity: '', order_type: 'market', limit_price: '' });
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadOrders();
    loadAccount();
  }, []);

  const loadOrders = async () => {
    try { setOrders(await api.getOrders()); } catch (e) { console.error(e); }
  };

  const loadAccount = async () => {
    try { setAccount(await api.getAccount()); } catch (e) { console.error(e); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg('');
    try {
      const data = {
        symbol: form.symbol.toUpperCase(),
        side: form.side,
        quantity: parseFloat(form.quantity),
        order_type: form.order_type,
      };
      if (form.order_type === 'limit') data.limit_price = parseFloat(form.limit_price);
      const order = await api.placeOrder(data);
      setMsg(`Orden ${order.status}: ${order.side.toUpperCase()} ${order.quantity} ${order.symbol}${order.filled_price ? ` @ $${order.filled_price}` : ''}`);
      setForm({ symbol: '', side: 'buy', quantity: '', order_type: 'market', limit_price: '' });
      loadOrders();
      loadAccount();
    } catch (e) {
      setMsg(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2><ShoppingCart size={24} style={{ verticalAlign: 'middle', marginRight: 8 }} />Trading</h2>
        <p>Compra y vende acciones via API (Alpaca Paper Trading)</p>
      </div>

      {account && (
        <div className="grid grid-2" style={{ marginBottom: 24 }}>
          <div className="card">
            <div className="card-title">Poder de Compra</div>
            <div className="card-value">${(account.buying_power || account.cash || 0).toLocaleString()}</div>
          </div>
          <div className="card">
            <div className="card-title">Modo</div>
            <div className="card-value" style={{ fontSize: 18 }}>
              {account.status === 'simulated' ? 'Simulado' : 'Alpaca Live'}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-2">
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Nueva Orden</h3>
          {msg && <div className={msg.startsWith('Error') ? 'error-msg' : 'success-msg'}>{msg}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Símbolo</label>
              <input value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} required placeholder="AAPL" />
            </div>
            <div className="form-group">
              <label>Operación</label>
              <select value={form.side} onChange={(e) => setForm({ ...form, side: e.target.value })}>
                <option value="buy">Comprar</option>
                <option value="sell">Vender</option>
              </select>
            </div>
            <div className="form-group">
              <label>Cantidad</label>
              <input type="number" step="any" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Tipo de Orden</label>
              <select value={form.order_type} onChange={(e) => setForm({ ...form, order_type: e.target.value })}>
                <option value="market">Market</option>
                <option value="limit">Limit</option>
              </select>
            </div>
            {form.order_type === 'limit' && (
              <div className="form-group">
                <label>Precio Límite</label>
                <input type="number" step="any" value={form.limit_price} onChange={(e) => setForm({ ...form, limit_price: e.target.value })} required />
              </div>
            )}
            <button type="submit" className={`btn-primary ${form.side === 'buy' ? '' : 'btn-danger'}`} style={{ width: '100%' }} disabled={loading}>
              {form.side === 'buy' ? <ArrowUpCircle size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} /> : <ArrowDownCircle size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />}
              {loading ? 'Procesando...' : form.side === 'buy' ? 'Comprar' : 'Vender'}
            </button>
          </form>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Historial de Órdenes</h3>
          {orders.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)' }}>No hay órdenes aún</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Símbolo</th>
                  <th>Lado</th>
                  <th>Cant.</th>
                  <th>Precio</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td>{new Date(o.created_at).toLocaleDateString()}</td>
                    <td><strong>{o.symbol}</strong></td>
                    <td className={o.side === 'buy' ? 'positive' : 'negative'}>{o.side.toUpperCase()}</td>
                    <td>{o.quantity}</td>
                    <td>{o.filled_price ? `$${o.filled_price}` : '-'}</td>
                    <td><span className="badge badge-blue">{o.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
