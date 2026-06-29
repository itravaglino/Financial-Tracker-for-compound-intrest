import { useState, useEffect } from 'react';
import { api } from '../api';
import { Bell, Plus, Trash2, RefreshCw } from 'lucide-react';

const ALERT_TYPES = [
  { value: 'price', label: 'Precio' },
  { value: 'change_percent', label: 'Cambio %' },
  { value: 'rsi', label: 'RSI' },
  { value: 'fibonacci', label: 'Patrón Fibonacci' },
  { value: 'signal', label: 'Señal IA' },
];

const CONDITIONS = [
  { value: 'gt', label: 'Mayor que' },
  { value: 'gte', label: 'Mayor o igual' },
  { value: 'lt', label: 'Menor que' },
  { value: 'lte', label: 'Menor o igual' },
  { value: 'COMPRAR', label: 'Señal COMPRAR' },
  { value: 'VENDER', label: 'Señal VENDER' },
];

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [triggered, setTriggered] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ symbol: '', alert_type: 'price', condition: 'gt', threshold: '', message: '' });

  useEffect(() => { loadAlerts(); }, []);

  const loadAlerts = async () => {
    try { setAlerts(await api.getAlerts()); } catch (e) { console.error(e); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    const data = { ...form, symbol: form.symbol.toUpperCase(), threshold: parseFloat(form.threshold) || 0 };
    if (form.alert_type === 'signal') data.condition = form.condition;
    if (form.alert_type === 'fibonacci') { data.condition = 'eq'; data.threshold = 0; }
    await api.createAlert(data);
    setShowForm(false);
    setForm({ symbol: '', alert_type: 'price', condition: 'gt', threshold: '', message: '' });
    loadAlerts();
  };

  const handleDelete = async (id) => {
    await api.deleteAlert(id);
    loadAlerts();
  };

  const checkNow = async () => {
    const result = await api.checkAlerts();
    setTriggered(result);
    loadAlerts();
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2><Bell size={24} style={{ verticalAlign: 'middle', marginRight: 8 }} />Alertas Personalizadas</h2>
          <p>Monitoreo automático de precios, RSI, Fibonacci y señales IA</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn-secondary" onClick={checkNow}><RefreshCw size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />Verificar</button>
          <button className="btn-primary" onClick={() => setShowForm(true)}><Plus size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />Nueva Alerta</button>
        </div>
      </div>

      {triggered && (triggered.triggered_alerts?.length > 0 || triggered.triggered_stop_losses?.length > 0) && (
        <div className="success-msg" style={{ marginBottom: 16 }}>
          {triggered.triggered_alerts?.length > 0 && `${triggered.triggered_alerts.length} alerta(s) activada(s). `}
          {triggered.triggered_stop_losses?.length > 0 && `${triggered.triggered_stop_losses.length} stop loss activado(s).`}
        </div>
      )}

      <div className="card">
        {alerts.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)' }}>No tienes alertas configuradas</p>
        ) : (
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
              {alerts.map((a) => (
                <tr key={a.id}>
                  <td><strong>{a.symbol}</strong></td>
                  <td>{a.alert_type}</td>
                  <td>{a.condition}</td>
                  <td>{a.threshold || '-'}</td>
                  <td>
                    {a.triggered
                      ? <span className="badge badge-red">Activada</span>
                      : a.is_active
                        ? <span className="badge badge-green">Activa</span>
                        : <span className="badge badge-yellow">Inactiva</span>}
                  </td>
                  <td>
                    <button className="btn-secondary" style={{ padding: '6px 10px' }} onClick={() => handleDelete(a.id)}>
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Nueva Alerta</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Símbolo</label>
                <input value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Tipo</label>
                <select value={form.alert_type} onChange={(e) => setForm({ ...form, alert_type: e.target.value })}>
                  {ALERT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              {form.alert_type !== 'fibonacci' && (
                <div className="form-group">
                  <label>Condición</label>
                  <select value={form.condition} onChange={(e) => setForm({ ...form, condition: e.target.value })}>
                    {(form.alert_type === 'signal' ? CONDITIONS.slice(4) : CONDITIONS.slice(0, 4)).map(c => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>
              )}
              {form.alert_type !== 'fibonacci' && form.alert_type !== 'signal' && (
                <div className="form-group">
                  <label>Umbral</label>
                  <input type="number" step="any" value={form.threshold} onChange={(e) => setForm({ ...form, threshold: e.target.value })} required />
                </div>
              )}
              <div className="form-group">
                <label>Mensaje (opcional)</label>
                <input value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
              </div>
              <button type="submit" className="btn-primary" style={{ width: '100%' }}>Crear Alerta</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
