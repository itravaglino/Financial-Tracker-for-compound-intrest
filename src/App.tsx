import { useMemo, useState } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  calculateCompoundInterest,
  formatCurrency,
  type CompoundFrequency,
} from './lib/compoundInterest'
import './App.css'

interface FormState {
  principal: number
  monthlyContribution: number
  annualRatePercent: number
  years: number
  frequency: CompoundFrequency
}

const DEFAULTS: FormState = {
  principal: 10000,
  monthlyContribution: 500,
  annualRatePercent: 7,
  years: 30,
  frequency: 'monthly',
}

const FREQUENCY_OPTIONS: { value: CompoundFrequency; label: string }[] = [
  { value: 'annually', label: 'Annually' },
  { value: 'semiannually', label: 'Semi-annually' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'daily', label: 'Daily' },
]

function App() {
  const [form, setForm] = useState<FormState>(DEFAULTS)

  const result = useMemo(() => calculateCompoundInterest(form), [form])

  const chartData = useMemo(
    () =>
      result.breakdown.map((row) => ({
        year: `Yr ${row.year}`,
        Contributions: row.contributions,
        Interest: row.interest,
      })),
    [result],
  )

  const update = (key: keyof FormState) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const raw = e.target.value
    setForm((prev) => ({
      ...prev,
      [key]: key === 'frequency' ? (raw as CompoundFrequency) : Number(raw),
    }))
  }

  const growthMultiple =
    result.totalContributions > 0
      ? result.finalBalance / result.totalContributions
      : 0

  return (
    <div className="app">
      <header className="app__header">
        <span className="app__logo" aria-hidden="true">
          📈
        </span>
        <div>
          <h1>Compound Interest Tracker</h1>
          <p>See how steady investing and compounding grow your money over time.</p>
        </div>
      </header>

      <main className="layout">
        <section className="card form" aria-label="Investment inputs">
          <h2>Your plan</h2>

          <label className="field">
            <span>Initial investment</span>
            <div className="input-prefix">
              <span>$</span>
              <input
                type="number"
                min={0}
                step={100}
                value={form.principal}
                onChange={update('principal')}
                aria-label="Initial investment"
              />
            </div>
          </label>

          <label className="field">
            <span>Monthly contribution</span>
            <div className="input-prefix">
              <span>$</span>
              <input
                type="number"
                min={0}
                step={50}
                value={form.monthlyContribution}
                onChange={update('monthlyContribution')}
                aria-label="Monthly contribution"
              />
            </div>
          </label>

          <label className="field">
            <span>Annual return rate (%)</span>
            <input
              type="number"
              min={0}
              max={100}
              step={0.1}
              value={form.annualRatePercent}
              onChange={update('annualRatePercent')}
              aria-label="Annual return rate"
            />
          </label>

          <label className="field">
            <span>Years to grow: {form.years}</span>
            <input
              type="range"
              min={1}
              max={50}
              step={1}
              value={form.years}
              onChange={update('years')}
              aria-label="Years to grow"
            />
          </label>

          <label className="field">
            <span>Compounding frequency</span>
            <select
              value={form.frequency}
              onChange={update('frequency')}
              aria-label="Compounding frequency"
            >
              {FREQUENCY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>
        </section>

        <section className="results">
          <div className="stat-grid">
            <div className="card stat stat--primary">
              <span className="stat__label">Final balance</span>
              <span className="stat__value" data-testid="final-balance">
                {formatCurrency(result.finalBalance)}
              </span>
              <span className="stat__hint">
                {growthMultiple.toFixed(2)}× your contributions
              </span>
            </div>
            <div className="card stat">
              <span className="stat__label">Total contributions</span>
              <span className="stat__value">
                {formatCurrency(result.totalContributions)}
              </span>
            </div>
            <div className="card stat stat--accent">
              <span className="stat__label">Interest earned</span>
              <span className="stat__value" data-testid="total-interest">
                {formatCurrency(result.totalInterest)}
              </span>
            </div>
          </div>

          <div className="card chart">
            <h2>Growth over time</h2>
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={chartData} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="c" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#60a5fa" stopOpacity={0.05} />
                  </linearGradient>
                  <linearGradient id="i" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#34d399" stopOpacity={0.85} />
                    <stop offset="95%" stopColor="#34d399" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="year" stroke="#94a3b8" fontSize={12} />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={12}
                  tickFormatter={(v) => formatCurrency(Number(v))}
                  width={80}
                />
                <Tooltip
                  formatter={(v: number) => formatCurrency(v)}
                  contentStyle={{
                    background: '#0f172a',
                    border: '1px solid #1f2937',
                    borderRadius: 8,
                    color: '#e2e8f0',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="Contributions"
                  stackId="1"
                  stroke="#60a5fa"
                  fill="url(#c)"
                />
                <Area
                  type="monotone"
                  dataKey="Interest"
                  stackId="1"
                  stroke="#34d399"
                  fill="url(#i)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
      </main>

      <footer className="app__footer">
        Estimates are illustrative and assume a constant rate of return.
      </footer>
    </div>
  )
}

export default App
