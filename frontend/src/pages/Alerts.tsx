import { useEffect, useState } from 'react';
import { api, Alert, StopLoss, Notification } from '../api';
import { Bell, Shield, Plus, Trash2, RefreshCw } from 'lucide-react';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stopLosses, setStopLosses] = useState<StopLoss[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showAlertForm, setShowAlertForm] = useState(false);
  const [showSLForm, setShowSLForm] = useState(false);
  const [alertForm, setAlertForm] = useState({ symbol: '', alert_type: 'price_above', threshold: '', message: '' });
  const [slForm, setSlForm] = useState({ symbol: '', quantity: '', trigger_price: '', trailing_percent: '' });

  const load = () => {
    api.getAlerts().then(setAlerts);
    api.getStopLosses().then(setStopLosses);
    api.getNotifications().then(setNotifications);
  };

  useEffect(() => { load(); }, []);

  const handleCheck = async () => {
    await api.checkAlerts();
    load();
  };

  const createAlert = async () => {
    await api.createAlert({
      symbol: alertForm.symbol.toUpperCase(),
      alert_type: alertForm.alert_type,
      threshold: alertForm.threshold ? parseFloat(alertForm.threshold) : undefined,
      message: alertForm.message || undefined,
    });
    setShowAlertForm(false);
    setAlertForm({ symbol: '', alert_type: 'price_above', threshold: '', message: '' });
    load();
  };

  const createSL = async () => {
    await api.createStopLoss({
      symbol: slForm.symbol.toUpperCase(),
      quantity: parseFloat(slForm.quantity),
      trigger_price: parseFloat(slForm.trigger_price),
      trailing_percent: slForm.trailing_percent ? parseFloat(slForm.trailing_percent) : undefined,
    });
    setShowSLForm(false);
    setSlForm({ symbol: '', quantity: '', trigger_price: '', trailing_percent: '' });
    load();
  };

  const alertTypes = [
    { value: 'price_above', label: 'Precio por encima de' },
    { value: 'price_below', label: 'Precio por debajo de' },
    { value: 'rsi_overbought', label: 'RSI sobrecomprado' },
    { value: 'rsi_oversold', label: 'RSI sobrevendido' },
    { value: 'fibonacci_level', label: 'Nivel Fibonacci' },
    { value: 'take_profit', label: 'Take Profit' },
    { value: 'pattern_detected', label: 'Patrón detectado (IA)' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Alertas y Stop Loss</h1>
          <p className="text-slate-400">Sistema de alertas personalizadas y protección de capital</p>
        </div>
        <button onClick={handleCheck} className="btn-secondary flex items-center gap-2">
          <RefreshCw className="w-4 h-4" /> Verificar alertas
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Bell className="w-4 h-4 text-amber-400" /> Alertas activas
            </h3>
            <button onClick={() => setShowAlertForm(true)} className="btn-primary text-xs flex items-center gap-1">
              <Plus className="w-3 h-3" /> Nueva
            </button>
          </div>
          {alerts.length === 0 ? (
            <p className="text-slate-400 text-sm">No hay alertas configuradas</p>
          ) : (
            <div className="space-y-2">
              {alerts.map(a => (
                <div key={a.id} className={`flex items-center justify-between p-3 rounded-lg text-sm ${a.triggered ? 'bg-amber-500/10 border border-amber-500/30' : 'bg-surface-800/50'}`}>
                  <div>
                    <span className="font-mono font-bold">{a.symbol}</span>
                    <span className="text-slate-400 ml-2">{a.alert_type.replace(/_/g, ' ')}</span>
                    {a.threshold && <span className="text-slate-500 ml-1">@ ${a.threshold}</span>}
                    {a.triggered && <span className="badge-yellow ml-2">Activada</span>}
                  </div>
                  <button onClick={() => { api.deleteAlert(a.id).then(load); }} className="text-slate-500 hover:text-red-400">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Stop Loss */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Shield className="w-4 h-4 text-red-400" /> Stop Loss
            </h3>
            <button onClick={() => setShowSLForm(true)} className="btn-primary text-xs flex items-center gap-1">
              <Plus className="w-3 h-3" /> Nuevo
            </button>
          </div>
          {stopLosses.length === 0 ? (
            <p className="text-slate-400 text-sm">No hay stop loss configurados</p>
          ) : (
            <div className="space-y-2">
              {stopLosses.map(sl => (
                <div key={sl.id} className={`flex items-center justify-between p-3 rounded-lg text-sm ${sl.triggered ? 'bg-red-500/10 border border-red-500/30' : 'bg-surface-800/50'}`}>
                  <div>
                    <span className="font-mono font-bold">{sl.symbol}</span>
                    <span className="text-slate-400 ml-2">{sl.quantity} acciones</span>
                    <span className="text-red-400 ml-2">@ ${sl.trigger_price}</span>
                    {sl.trailing_percent && <span className="text-slate-500 ml-1">(trailing {sl.trailing_percent}%)</span>}
                  </div>
                  <button onClick={() => { api.deleteStopLoss(sl.id).then(load); }} className="text-slate-500 hover:text-red-400">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Notifications */}
      <div className="card">
        <h3 className="font-semibold mb-3">Notificaciones</h3>
        {notifications.length === 0 ? (
          <p className="text-slate-400 text-sm">Sin notificaciones</p>
        ) : (
          <div className="space-y-2">
            {notifications.map(n => (
              <div key={n.id} className={`p-3 rounded-lg text-sm ${n.is_read ? 'bg-surface-800/30' : 'bg-primary-500/10 border border-primary-500/20'}`}>
                <p className="font-medium">{n.title}</p>
                <p className="text-slate-400 text-xs mt-0.5">{n.message}</p>
                <p className="text-slate-600 text-xs mt-1">{new Date(n.created_at).toLocaleString()}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Alert Form Modal */}
      {showAlertForm && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md space-y-3">
            <h3 className="font-semibold">Nueva alerta</h3>
            <div>
              <label className="label">Símbolo</label>
              <input className="input" value={alertForm.symbol} onChange={e => setAlertForm({ ...alertForm, symbol: e.target.value })} />
            </div>
            <div>
              <label className="label">Tipo</label>
              <select className="input" value={alertForm.alert_type} onChange={e => setAlertForm({ ...alertForm, alert_type: e.target.value })}>
                {alertTypes.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Umbral ($)</label>
              <input type="number" className="input" value={alertForm.threshold} onChange={e => setAlertForm({ ...alertForm, threshold: e.target.value })} />
            </div>
            <div>
              <label className="label">Mensaje (opcional)</label>
              <input className="input" value={alertForm.message} onChange={e => setAlertForm({ ...alertForm, message: e.target.value })} />
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowAlertForm(false)} className="btn-secondary flex-1">Cancelar</button>
              <button onClick={createAlert} className="btn-primary flex-1">Crear</button>
            </div>
          </div>
        </div>
      )}

      {/* Stop Loss Form Modal */}
      {showSLForm && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md space-y-3">
            <h3 className="font-semibold">Nuevo Stop Loss</h3>
            <div>
              <label className="label">Símbolo</label>
              <input className="input" value={slForm.symbol} onChange={e => setSlForm({ ...slForm, symbol: e.target.value })} />
            </div>
            <div>
              <label className="label">Cantidad</label>
              <input type="number" className="input" value={slForm.quantity} onChange={e => setSlForm({ ...slForm, quantity: e.target.value })} />
            </div>
            <div>
              <label className="label">Precio de activación</label>
              <input type="number" className="input" value={slForm.trigger_price} onChange={e => setSlForm({ ...slForm, trigger_price: e.target.value })} />
            </div>
            <div>
              <label className="label">Trailing % (opcional)</label>
              <input type="number" className="input" value={slForm.trailing_percent} onChange={e => setSlForm({ ...slForm, trailing_percent: e.target.value })} placeholder="ej: 5" />
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowSLForm(false)} className="btn-secondary flex-1">Cancelar</button>
              <button onClick={createSL} className="btn-primary flex-1">Crear</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
