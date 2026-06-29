import { useEffect, useState } from 'react';
import { trading } from '../api';

interface Order {
  id: number;
  symbol: string;
  side: string;
  quantity: number;
  order_type: string;
  status: string;
  created_at: string;
  error_message?: string;
}

interface AccountData {
  configured?: boolean;
  buying_power?: string;
  portfolio_value?: string;
  cash?: string;
  status?: string;
  is_paper?: boolean;
  message?: string;
  error?: string;
}

export default function TradingPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [account, setAccount] = useState<AccountData | null>(null);
  const [showOrder, setShowOrder] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [orderForm, setOrderForm] = useState({ symbol: '', side: 'buy', quantity: '', order_type: 'market', limit_price: '' });
  const [brokerForm, setBrokerForm] = useState({ api_key: '', secret_key: '', base_url: 'https://paper-api.alpaca.markets', is_paper: true });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const [o, a] = await Promise.all([trading.orders(), trading.account()]);
      setOrders(o.data);
      setAccount(a.data);
    } catch { /* ignore */ }
  };

  const handleOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const res = await trading.placeOrder({
        symbol: orderForm.symbol.toUpperCase(),
        side: orderForm.side,
        quantity: parseFloat(orderForm.quantity),
        order_type: orderForm.order_type,
        limit_price: orderForm.order_type === 'limit' ? parseFloat(orderForm.limit_price) : null,
      });
      if (res.data.status === 'failed') {
        setError(res.data.error_message || 'Error al ejecutar orden');
      } else {
        setMessage(`Orden ${res.data.status}: ${res.data.symbol} ${res.data.side} x${res.data.quantity}`);
        setShowOrder(false);
      }
      load();
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error al ejecutar orden');
    }
  };

  const handleConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    await trading.configureBroker(brokerForm);
    setMessage('Broker configurado correctamente');
    setShowConfig(false);
    load();
  };

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>Trading API</h1>
          <p>Ejecuta órdenes de compra/venta vía API de broker (Alpaca)</p>
        </div>
        <div className="flex-between gap-2">
          <button className="btn btn-secondary" onClick={() => setShowConfig(true)}>Configurar broker</button>
          <button className="btn btn-primary" onClick={() => setShowOrder(true)}>Nueva orden</button>
        </div>
      </div>

      {message && <div className="success-msg mb-4">{message}</div>}
      {error && <div className="error-msg mb-4">{error}</div>}

      <div className="grid grid-3 mb-4">
        <div className="card stat-card">
          <div className="stat-value">
            {account?.configured ? (
              <span className="badge badge-green">Conectado</span>
            ) : (
              <span className="badge badge-red">No configurado</span>
            )}
          </div>
          <div className="stat-label">Estado del broker</div>
        </div>
        {account?.configured && (
          <>
            <div className="card stat-card">
              <div className="stat-value">${parseFloat(account.buying_power || '0').toLocaleString()}</div>
              <div className="stat-label">Poder de compra</div>
            </div>
            <div className="card stat-card">
              <div className="stat-value">${parseFloat(account.portfolio_value || '0').toLocaleString()}</div>
              <div className="stat-label">Valor portfolio broker</div>
            </div>
          </>
        )}
      </div>

      <div className="card">
        <div className="card-title">Historial de órdenes</div>
        {orders.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Símbolo</th>
                <th>Lado</th>
                <th>Cantidad</th>
                <th>Tipo</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td>{new Date(o.created_at).toLocaleString()}</td>
                  <td><strong>{o.symbol}</strong></td>
                  <td>
                    <span className={`badge ${o.side === 'buy' ? 'badge-green' : 'badge-red'}`}>{o.side}</span>
                  </td>
                  <td>{o.quantity}</td>
                  <td>{o.order_type}</td>
                  <td>
                    <span className={`badge ${o.status === 'filled' || o.status === 'submitted' ? 'badge-green' : o.status === 'failed' ? 'badge-red' : 'badge-yellow'}`}>
                      {o.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="loading">Sin órdenes ejecutadas</div>
        )}
      </div>

      <div className="card mt-4">
        <div className="card-title">Información</div>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          Esta aplicación se integra con <strong>Alpaca Markets</strong> para trading programático.
          Usa <strong>paper trading</strong> (simulado) para pruebas sin riesgo.
          Obtén tus API keys en <a href="https://alpaca.markets" target="_blank" rel="noreferrer">alpaca.markets</a>.
        </p>
      </div>

      {showOrder && (
        <div className="modal-overlay" onClick={() => setShowOrder(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Nueva orden</h2>
            <form onSubmit={handleOrder}>
              <div className="form-group">
                <label>Símbolo</label>
                <input value={orderForm.symbol} onChange={(e) => setOrderForm({ ...orderForm, symbol: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Lado</label>
                <select value={orderForm.side} onChange={(e) => setOrderForm({ ...orderForm, side: e.target.value })}>
                  <option value="buy">Comprar</option>
                  <option value="sell">Vender</option>
                </select>
              </div>
              <div className="form-group">
                <label>Cantidad</label>
                <input type="number" step="any" value={orderForm.quantity} onChange={(e) => setOrderForm({ ...orderForm, quantity: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Tipo de orden</label>
                <select value={orderForm.order_type} onChange={(e) => setOrderForm({ ...orderForm, order_type: e.target.value })}>
                  <option value="market">Market</option>
                  <option value="limit">Limit</option>
                </select>
              </div>
              {orderForm.order_type === 'limit' && (
                <div className="form-group">
                  <label>Precio límite</label>
                  <input type="number" step="any" value={orderForm.limit_price} onChange={(e) => setOrderForm({ ...orderForm, limit_price: e.target.value })} required />
                </div>
              )}
              <div className="flex-between gap-2">
                <button type="button" className="btn btn-secondary" onClick={() => setShowOrder(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Ejecutar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showConfig && (
        <div className="modal-overlay" onClick={() => setShowConfig(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Configurar broker Alpaca</h2>
            <form onSubmit={handleConfig}>
              <div className="form-group">
                <label>API Key</label>
                <input value={brokerForm.api_key} onChange={(e) => setBrokerForm({ ...brokerForm, api_key: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Secret Key</label>
                <input type="password" value={brokerForm.secret_key} onChange={(e) => setBrokerForm({ ...brokerForm, secret_key: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Base URL</label>
                <select value={brokerForm.base_url} onChange={(e) => setBrokerForm({ ...brokerForm, base_url: e.target.value })}>
                  <option value="https://paper-api.alpaca.markets">Paper Trading (simulado)</option>
                  <option value="https://api.alpaca.markets">Live Trading (real)</option>
                </select>
              </div>
              <div className="flex-between gap-2">
                <button type="button" className="btn btn-secondary" onClick={() => setShowConfig(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
