import { useMemo, useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  calculateCompoundInterest,
  formatCurrency,
  type CompoundFrequency,
} from '../lib/compoundInterest';
import { Calculator } from 'lucide-react';

interface FormState {
  principal: number;
  monthlyContribution: number;
  annualRatePercent: number;
  years: number;
  frequency: CompoundFrequency;
}

const DEFAULTS: FormState = {
  principal: 10000,
  monthlyContribution: 500,
  annualRatePercent: 7,
  years: 30,
  frequency: 'monthly',
};

const FREQUENCY_OPTIONS: { value: CompoundFrequency; label: string }[] = [
  { value: 'annually', label: 'Anual' },
  { value: 'semiannually', label: 'Semestral' },
  { value: 'quarterly', label: 'Trimestral' },
  { value: 'monthly', label: 'Mensual' },
  { value: 'daily', label: 'Diario' },
];

export default function CompoundInterestPage() {
  const [form, setForm] = useState<FormState>(DEFAULTS);

  const result = useMemo(() => calculateCompoundInterest(form), [form]);

  const chartData = useMemo(
    () =>
      result.breakdown.map((row) => ({
        year: `Año ${row.year}`,
        Aportes: row.contributions,
        Intereses: row.interest,
      })),
    [result],
  );

  const update = (key: keyof FormState) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const raw = e.target.value;
    setForm((prev) => ({
      ...prev,
      [key]: key === 'frequency' ? (raw as CompoundFrequency) : Number(raw),
    }));
  };

  const growthMultiple =
    result.totalContributions > 0 ? result.finalBalance / result.totalContributions : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Calculator className="w-6 h-6 text-primary-400" />
          Interés Compuesto
        </h1>
        <p className="text-slate-400">
          Proyecta el crecimiento de tus ahorros con aportes recurrentes y capitalización
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card space-y-4">
          <h2 className="font-semibold">Parámetros</h2>
          <div>
            <label className="label">Capital inicial ($)</label>
            <input type="number" className="input" value={form.principal} onChange={update('principal')} min={0} />
          </div>
          <div>
            <label className="label">Aporte mensual ($)</label>
            <input type="number" className="input" value={form.monthlyContribution} onChange={update('monthlyContribution')} min={0} />
          </div>
          <div>
            <label className="label">Tasa anual (%)</label>
            <input type="number" className="input" value={form.annualRatePercent} onChange={update('annualRatePercent')} min={0} step={0.1} />
          </div>
          <div>
            <label className="label">Horizonte (años)</label>
            <input type="number" className="input" value={form.years} onChange={update('years')} min={1} max={50} />
          </div>
          <div>
            <label className="label">Frecuencia de capitalización</label>
            <select className="input" value={form.frequency} onChange={update('frequency')}>
              {FREQUENCY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="card text-center">
              <p className="text-xs text-slate-400">Balance final</p>
              <p className="text-2xl font-bold text-primary-400">{formatCurrency(result.finalBalance)}</p>
            </div>
            <div className="card text-center">
              <p className="text-xs text-slate-400">Total aportado</p>
              <p className="text-2xl font-bold">{formatCurrency(result.totalContributions)}</p>
            </div>
            <div className="card text-center">
              <p className="text-xs text-slate-400">Intereses ganados</p>
              <p className="text-2xl font-bold text-emerald-400">{formatCurrency(result.totalInterest)}</p>
            </div>
          </div>

          <div className="card">
            <p className="text-sm text-slate-400 mb-4">
              Tu dinero crece <span className="text-emerald-400 font-semibold">{growthMultiple.toFixed(2)}x</span> respecto a lo aportado
            </p>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="year" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                    formatter={(value: number) => formatCurrency(value)}
                  />
                  <Area type="monotone" dataKey="Aportes" stackId="1" stroke="#6366f1" fill="#6366f1" fillOpacity={0.6} />
                  <Area type="monotone" dataKey="Intereses" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card overflow-x-auto">
            <h3 className="font-semibold mb-3">Desglose anual</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-surface-800">
                  <th className="text-left py-2">Año</th>
                  <th className="text-right py-2">Aportes</th>
                  <th className="text-right py-2">Intereses</th>
                  <th className="text-right py-2">Balance</th>
                </tr>
              </thead>
              <tbody>
                {result.breakdown.map((row) => (
                  <tr key={row.year} className="border-b border-surface-800/50">
                    <td className="py-2">{row.year}</td>
                    <td className="py-2 text-right">{formatCurrency(row.contributions)}</td>
                    <td className="py-2 text-right text-emerald-400">{formatCurrency(row.interest)}</td>
                    <td className="py-2 text-right font-medium">{formatCurrency(row.balance)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
