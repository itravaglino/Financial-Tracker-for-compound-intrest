import { useState } from 'react';
import { api, TechnicalAnalysis, PatternAnalysis, Valuation, PortfolioAnalysis } from '../api';
import { Search, Brain, BarChart3, Target } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts';

export default function AnalysisPage() {
  const [symbol, setSymbol] = useState('');
  const [activeSymbol, setActiveSymbol] = useState('');
  const [loading, setLoading] = useState(false);
  const [technical, setTechnical] = useState<TechnicalAnalysis | null>(null);
  const [patterns, setPatterns] = useState<PatternAnalysis | null>(null);
  const [valuation, setValuation] = useState<Valuation | null>(null);
  const [portfolioAnalysis, setPortfolioAnalysis] = useState<PortfolioAnalysis | null>(null);
  const [tab, setTab] = useState<'technical' | 'neural' | 'valuation' | 'portfolio'>('technical');

  const analyze = async (sym?: string) => {
    const s = (sym || symbol).toUpperCase().trim();
    if (!s) return;
    setActiveSymbol(s);
    setLoading(true);
    try {
      const [ta, pat, val] = await Promise.all([
        api.getTechnical(s),
        api.getPatterns(s),
        api.getValuation(s),
      ]);
      setTechnical(ta);
      setPatterns(pat);
      setValuation(val);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const analyzePortfolio = async () => {
    setLoading(true);
    try {
      const portfolios = await api.getPortfolios();
      if (portfolios.length) {
        const analysis = await api.getPortfolioAnalysis(portfolios[0].id);
        setPortfolioAnalysis(analysis);
        setTab('portfolio');
      }
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'technical' as const, label: 'Análisis Técnico', icon: BarChart3 },
    { id: 'neural' as const, label: 'Redes Neuronales', icon: Brain },
    { id: 'valuation' as const, label: 'Valoración', icon: Target },
    { id: 'portfolio' as const, label: 'Contraste Portfolio', icon: Search },
  ];

  const fibData = technical ? Object.entries(technical.fibonacci_levels).map(([k, v]) => ({ level: k, price: v })) : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Análisis Avanzado</h1>
        <p className="text-slate-400">Análisis técnico, patrones Fibonacci con IA y valoración isotérica</p>
      </div>

      <div className="flex gap-3">
        <input
          className="input flex-1 max-w-xs"
          placeholder="Símbolo (ej: AAPL)"
          value={symbol}
          onChange={e => setSymbol(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && analyze()}
        />
        <button onClick={() => analyze()} className="btn-primary flex items-center gap-2" disabled={loading}>
          <Search className="w-4 h-4" /> Analizar
        </button>
        <button onClick={analyzePortfolio} className="btn-secondary" disabled={loading}>
          Analizar Portfolio
        </button>
      </div>

      {loading && (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
        </div>
      )}

      {(technical || patterns || valuation) && !loading && (
        <>
          <div className="flex gap-2 border-b border-surface-800 pb-1">
            {tabs.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-3 py-2 text-sm rounded-t-lg transition-colors ${
                  tab === t.id ? 'bg-surface-800 text-primary-400' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <t.icon className="w-4 h-4" /> {t.label}
              </button>
            ))}
          </div>

          {tab === 'technical' && technical && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="card">
                <h3 className="font-semibold mb-3">{activeSymbol} — Indicadores</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <Metric label="RSI (14)" value={technical.rsi?.toFixed(1)} alert={technical.rsi ? (technical.rsi > 70 ? 'Sobrecomprado' : technical.rsi < 30 ? 'Sobrevendido' : null) : null} />
                  <Metric label="MACD" value={technical.macd.toFixed(4)} />
                  <Metric label="SMA 20" value={`$${technical.sma_20.toFixed(2)}`} />
                  <Metric label="SMA 50" value={`$${technical.sma_50.toFixed(2)}`} />
                  <Metric label="SMA 200" value={technical.sma_200 ? `$${technical.sma_200.toFixed(2)}` : 'N/A'} />
                  <Metric label="Tendencia" value={technical.trend} highlight />
                  <Metric label="BB Superior" value={`$${technical.bollinger_upper.toFixed(2)}`} />
                  <Metric label="BB Inferior" value={`$${technical.bollinger_lower.toFixed(2)}`} />
                </div>
              </div>

              <div className="card">
                <h3 className="font-semibold mb-3">Señales</h3>
                <ul className="space-y-2">
                  {technical.signals.map((s, i) => (
                    <li key={i} className="text-sm flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary-400 mt-1.5 flex-shrink-0" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="card lg:col-span-2">
                <h3 className="font-semibold mb-3">Niveles Fibonacci</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={fibData}>
                    <XAxis dataKey="level" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} />
                    <Bar dataKey="price" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="card">
                <h3 className="font-semibold mb-3">Soportes</h3>
                {technical.support_levels.map((l, i) => (
                  <p key={i} className="text-sm font-mono text-emerald-400">${l.toFixed(2)}</p>
                ))}
              </div>
              <div className="card">
                <h3 className="font-semibold mb-3">Resistencias</h3>
                {technical.resistance_levels.map((l, i) => (
                  <p key={i} className="text-sm font-mono text-red-400">${l.toFixed(2)}</p>
                ))}
              </div>
            </div>
          )}

          {tab === 'neural' && patterns && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="card">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-primary-400" /> Predicción Neural
                </h3>
                <div className="text-center py-4">
                  <p className={`text-3xl font-bold ${patterns.prediction_direction === 'alcista' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {patterns.prediction_direction.toUpperCase()}
                  </p>
                  <p className="text-slate-400 mt-1">Confianza: {patterns.prediction_confidence}%</p>
                  <p className="text-xs text-slate-500 mt-1">Precisión del modelo: {((patterns.neural_accuracy ?? 0) * 100).toFixed(1)}%</p>
                </div>
                <div className="w-full bg-surface-800 rounded-full h-2 mt-2">
                  <div
                    className={`h-2 rounded-full ${patterns.prediction_direction === 'alcista' ? 'bg-emerald-500' : 'bg-red-500'}`}
                    style={{ width: `${patterns.prediction_confidence}%` }}
                  />
                </div>
              </div>

              <div className="card">
                <h3 className="font-semibold mb-3">Patrones Detectados</h3>
                {patterns.patterns.length === 0 ? (
                  <p className="text-slate-400 text-sm">No se detectaron patrones significativos</p>
                ) : (
                  <div className="space-y-2">
                    {patterns.patterns.map((p, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-surface-800/50 rounded-lg text-sm">
                        <span className="font-medium">{p.type.replace(/_/g, ' ')}</span>
                        <div className="flex items-center gap-2">
                          {p.level && <span className="text-slate-400">{p.level}</span>}
                          <span className={p.strength === 'strong' ? 'badge-green' : 'badge-yellow'}>{p.strength}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="card lg:col-span-2">
                <h3 className="font-semibold mb-3">Retracciones Fibonacci (IA)</h3>
                <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
                  {Object.entries(patterns.fibonacci_retracements).map(([k, v]) => (
                    <div key={k} className="text-center p-2 bg-surface-800/50 rounded-lg">
                      <p className="text-xs text-slate-400">{k}</p>
                      <p className="font-mono text-sm">${v.toFixed(2)}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {tab === 'valuation' && valuation && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="card">
                <h3 className="font-semibold mb-3">Valoración Objetiva — {activeSymbol}</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Precio actual</span>
                    <span className="font-mono">${valuation.current_price.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Valor intrínseco</span>
                    <span className="font-mono text-purple-400">${valuation.intrinsic_value.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Valor isotérico (sin sesgo FX)</span>
                    <span className="font-mono text-blue-400">${valuation.isosteric_value.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Rating</span>
                    <span className={valuation.rating.includes('infravalorada') ? 'badge-green' : valuation.rating.includes('sobrevalorada') ? 'badge-red' : 'badge-yellow'}>
                      {valuation.rating} ({valuation.rating_score}/100)
                    </span>
                  </div>
                </div>
              </div>

              <div className="card">
                <h3 className="font-semibold mb-3">Rango de valor justo</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-slate-400">Bajo</span><span className="font-mono">${valuation.fair_value_range.low.toFixed(2)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Medio</span><span className="font-mono">${valuation.fair_value_range.mid.toFixed(2)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Alto</span><span className="font-mono">${valuation.fair_value_range.high.toFixed(2)}</span></div>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                  <Metric label="P/E" value={valuation.pe_ratio?.toFixed(2) ?? 'N/A'} />
                  <Metric label="P/B" value={valuation.pb_ratio?.toFixed(2) ?? 'N/A'} />
                  <Metric label="PEG" value={valuation.peg_ratio?.toFixed(2) ?? 'N/A'} />
                  <Metric label="Div. Yield" value={valuation.dividend_yield ? `${(valuation.dividend_yield * 100).toFixed(2)}%` : 'N/A'} />
                </div>
              </div>
            </div>
          )}

          {tab === 'portfolio' && portfolioAnalysis && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="card">
                <h3 className="font-semibold mb-3">Scores del Portfolio</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <RadarChart data={[
                    { metric: 'Diversificación', value: portfolioAnalysis.diversification_score },
                    { metric: 'Riesgo (inv)', value: 100 - portfolioAnalysis.risk_score },
                    { metric: 'Momentum', value: portfolioAnalysis.holdings_analysis.filter(h => h.prediction === 'alcista').length / Math.max(portfolioAnalysis.holdings_analysis.length, 1) * 100 },
                  ]}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <Radar dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              <div className="card">
                <h3 className="font-semibold mb-3">Recomendaciones</h3>
                {portfolioAnalysis.recommendations.length ? (
                  <ul className="space-y-2">
                    {portfolioAnalysis.recommendations.map((r, i) => (
                      <li key={i} className="text-sm p-2 bg-surface-800/50 rounded-lg">{r}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-slate-400 text-sm">Portfolio bien balanceado</p>
                )}
              </div>

              <div className="card lg:col-span-2 overflow-x-auto">
                <h3 className="font-semibold mb-3">Contraste entre posiciones</h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-400 border-b border-surface-800">
                      <th className="text-left py-2">Símbolo</th>
                      <th className="text-left py-2">Tendencia</th>
                      <th className="text-right py-2">RSI</th>
                      <th className="text-left py-2">Predicción IA</th>
                      <th className="text-right py-2">Confianza</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolioAnalysis.holdings_analysis.map(h => (
                      <tr key={h.symbol} className="border-b border-surface-800/50">
                        <td className="py-2 font-mono font-bold">{h.symbol}</td>
                        <td className="py-2">{h.trend}</td>
                        <td className="py-2 text-right">{h.rsi?.toFixed(1) ?? '—'}</td>
                        <td className={`py-2 ${h.prediction === 'alcista' ? 'text-emerald-400' : 'text-red-400'}`}>{h.prediction}</td>
                        <td className="py-2 text-right">{h.confidence}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Metric({ label, value, alert, highlight }: { label: string; value?: string; alert?: string | null; highlight?: boolean }) {
  return (
    <div className="p-2 bg-surface-800/50 rounded-lg">
      <p className="text-xs text-slate-400">{label}</p>
      <p className={`font-mono font-medium ${highlight ? 'text-primary-400' : ''}`}>{value ?? '—'}</p>
      {alert && <p className="text-xs text-amber-400 mt-0.5">{alert}</p>}
    </div>
  );
}
