import { useState, useEffect } from 'react';
import { api } from '../api';
import { Shield, Plus, Trash2 } from 'lucide-react';

export default function StopLoss() {
  const [stops, setStops] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ symbol: '', quantity: '', stop_price: '', trailing_percent: '' });

  useEffect(() => { loadStops(); }, []);

  const loadStops = async () => {
    try { setStops(await api.getStopLosses()); } catch (e) { console.error(e); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    const data = {
      symbol: form.symbol.toUpperCase(),
      quantity: parseFloat(form.quantity),
      stop_price: parseFloat(form.stop_price),
    };
    if (form.trailing_percent) data.trailing_percent = parseFloat(form.trailing_percent);
    await api.createStopLoss(data);
    setShowForm(false);
    setForm({ symbol: '', quantity: '', stop_price: '', trailing_percent: '' });
    loadStops();
  };

  const handleDelete = async (id) => {
    await api.deleteStopLoss(id);
    loadStops();
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2><Shield size={24} style={{ verticalAlign: 'middle', marginRight: 8 }} />Stop Loss</h2>
          <p>Protege tu capital con stop loss fijos y trailing</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(true)}>
          <Plus size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />Nuevo Stop Loss
        </button>
      </div>

      <div className="card">
        {stops.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)' }}>No tienes stop loss configurados</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Símbolo</th>
                <th>Cantidad</th>
                <th>Stop Price</th>
                <th>Trailing %</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {stops.map((s) => (
                <tr key={s.id}>
                  <td><strong>{s.symbol}</strong></td>
                  <td>{s.quantity}</td>
                  <td>${s.stop_price}</td>
                  <td>{s.trailing_percent ? `${s.trailing_percent}%` : 'Fijo'}</td>
                  <td>
                    {s.triggered
                      ? <span className="badge badge-red">Ejecutado</span>
                      : <span className="badge badge-green">Activo</span>}
                  </td>
                  <td>
                    <button className="btn-secondary" style={{ padding: '6px 10px' }} onClick={() => handleDelete(s.id)}>
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
            <h2>Nuevo Stop Loss</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Símbolo</label>
                <input value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Cantidad</label>
                <input type="number" step="any" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Precio Stop</label>
                <input type="number" step="any" value={form.stop_price} onChange={(e) => setForm({ ...form, stop_price: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Trailing % (opcional)</label>
                <input type="number" step="any" value={form.trailing_percent} onChange={(e) => setForm({ ...form, trailing_percent: e.target.value })} placeholder="Ej: 5" />
              </div>
              <button type="submit" className="btn-primary" style={{ width: '100%' }}>Crear Stop Loss</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
