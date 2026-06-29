import { useEffect, useState } from 'react';
import { alerts, portfolio, trading } from '../api';

interface AlertItem {
  id: number;
  symbol: string;
  alert_type: string;
  condition: string;
  threshold: number;
  message: string;
  is_active: boolean;
  triggered: boolean;
}

interface Holding {
  id: number;
  symbol: string;
}

export default function AlertsPage() {
  const [alertList, setAlertList] = useState<AlertItem[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [showStopLoss, setShowStopLoss] = useState(false);
  const [form, setForm] = useState({
    symbol: '', alert_type: 'price', condition: 'above', threshold: '', message: '',
  });
  const [stopForm, setStopForm] = useState({ holding_id: '', trigger_price: '', stop_type: 'fixed', trailing_percent: '' });
  const [checkResult, setCheckResult] = useState<{ triggered_alerts: unknown[]; triggered_stop_losses: unknown[] } | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => { load(); }, []);

  const load = async () => {
    const [a, p] = await Promise.all([alerts.list(), portfolio.list()]);
    setAlertList(a.data);
    setHoldings(p.data.flatMap((port: { holdings: Holding[] }) => port.holdings));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await alerts.create({
      symbol: form.symbol.toUpperCase(),
      alert_type: form.alert_type,
      condition: form.condition,
      threshold: parseFloat(form.threshold),
      message: form.message,
    });
    setShowForm(false);
    setMessage('Alerta creada');
    load();
  };

  const handleDelete = async (id: number) => {
    await alerts.delete(id);
    load();
  };

  const handleCheck = async () => {
    const res = await alerts.check();
    setCheckResult(res.data);
    load();
  };

  const handleStopLoss = async (e: React.FormEvent) => {
    e.preventDefault();
    await trading.createStopLoss(parseInt(stopForm.holding_id), {
      trigger_price: parseFloat(stopForm.trigger_price),
      stop_type: stopForm.stop_type,
      trailing_percent: stopForm.stop_type === 'trailing' ? parseFloat(stopForm.trailing_percent) : null,
    });
    setShowStopLoss(false);
    setMessage('Stop loss configurado');
  };

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>Alertas y Stop Loss</h1>
          <p>Sistema de alertas personalizadas y protección de capital</p>
        </div>
        <div className="flex-between gap-2">
          <button className="btn btn-secondary" onClick={handleCheck}>Verificar alertas</button>
          <button className="btn btn-secondary" onClick={() => setShowStopLoss(true)}>Stop Loss</button>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>Nueva alerta</button>
        </div>
      </div>

      {message && <div className="success-msg mb-4">{message}</div>}

      {checkResult && (
        <div className="card mb-4">
          <div className="card-title">Resultado de verificación</div>
          <pre style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', overflow: 'auto' }}>
            {JSON.stringify(checkResult, null, 2)}
          </pre>
        </div>
      )}

      <div className="card">
        <div className="card-title">Alertas activas ({alertList.length})</div>
        {alertList.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Símbolo</th>
                <th>Tipo</th>
                <th>Condición</th>
                <th>Umbral</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {alertList.map((a) => (
                <tr key={a.id}>
                  <td><strong>{a.symbol}</strong></td>
                  <td>{a.alert_type}</td>
                  <td>{a.condition}</td>
                  <td>{a.threshold}</td>
                  <td>
                    {a.triggered ? (
                      <span className="badge badge-red">Activada</span>
                    ) : a.is_active ? (
                      <span className="badge badge-green">Activa</span>
                    ) : (
                      <span className="badge badge-yellow">Inactiva</span>
                    )}
                  </td>
                  <td>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(a.id)}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="loading">Sin alertas configuradas</div>
        )}
      </div>

      <div className="card mt-4">
        <div className="card-title">Tipos de alerta disponibles</div>
        <div className="grid grid-2 mt-4">
          <div><strong>price</strong> — Alerta por precio (above/below)</div>
          <div><strong>rsi</strong> — Alerta por RSI (above/below)</div>
          <div><strong>change_pct</strong> — Cambio porcentual (change_pct_above/below)</div>
        </div>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Nueva alerta</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Símbolo</label>
                <input value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Tipo</label>
                <select value={form.alert_type} onChange={(e) => setForm({ ...form, alert_type: e.target.value })}>
                  <option value="price">Precio</option>
                  <option value="rsi">RSI</option>
                  <option value="change_pct">Cambio %</option>
                </select>
              </div>
              <div className="form-group">
                <label>Condición</label>
                <select value={form.condition} onChange={(e) => setForm({ ...form, condition: e.target.value })}>
                  <option value="above">Por encima de</option>
                  <option value="below">Por debajo de</option>
                  <option value="change_pct_above">Cambio % arriba</option>
                  <option value="change_pct_below">Cambio % abajo</option>
                </select>
              </div>
              <div className="form-group">
                <label>Umbral</label>
                <input type="number" step="any" value={form.threshold} onChange={(e) => setForm({ ...form, threshold: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Mensaje (opcional)</label>
                <input value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
              </div>
              <div className="flex-between gap-2">
                <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Crear</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showStopLoss && (
        <div className="modal-overlay" onClick={() => setShowStopLoss(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Configurar Stop Loss</h2>
            <form onSubmit={handleStopLoss}>
              <div className="form-group">
                <label>Posición</label>
                <select value={stopForm.holding_id} onChange={(e) => setStopForm({ ...stopForm, holding_id: e.target.value })} required>
                  <option value="">Seleccionar...</option>
                  {holdings.map((h) => <option key={h.id} value={h.id}>{h.symbol}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Tipo</label>
                <select value={stopForm.stop_type} onChange={(e) => setStopForm({ ...stopForm, stop_type: e.target.value })}>
                  <option value="fixed">Fijo</option>
                  <option value="trailing">Trailing</option>
                </select>
              </div>
              <div className="form-group">
                <label>Precio de activación</label>
                <input type="number" step="any" value={stopForm.trigger_price} onChange={(e) => setStopForm({ ...stopForm, trigger_price: e.target.value })} required />
              </div>
              {stopForm.stop_type === 'trailing' && (
                <div className="form-group">
                  <label>Trailing %</label>
                  <input type="number" step="any" value={stopForm.trailing_percent} onChange={(e) => setStopForm({ ...stopForm, trailing_percent: e.target.value })} />
                </div>
              )}
              <div className="flex-between gap-2">
                <button type="button" className="btn btn-secondary" onClick={() => setShowStopLoss(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Configurar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
