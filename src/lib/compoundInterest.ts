export type CompoundFrequency = 'annually' | 'semiannually' | 'quarterly' | 'monthly' | 'daily'

export interface CompoundInterestInput {
  /** Initial lump sum invested at the start. */
  principal: number
  /** Recurring contribution added at the end of every month. */
  monthlyContribution: number
  /** Nominal annual interest rate as a percentage, e.g. 7 for 7%. */
  annualRatePercent: number
  /** Investment horizon in years. */
  years: number
  /** How often interest is compounded per year. */
  frequency: CompoundFrequency
}

export interface YearlyBreakdown {
  year: number
  /** Total amount contributed by the investor up to and including this year. */
  contributions: number
  /** Cumulative interest earned up to and including this year. */
  interest: number
  /** Total balance (contributions + interest) at the end of this year. */
  balance: number
}

export interface CompoundInterestResult {
  finalBalance: number
  totalContributions: number
  totalInterest: number
  breakdown: YearlyBreakdown[]
}

const PERIODS_PER_YEAR: Record<CompoundFrequency, number> = {
  annually: 1,
  semiannually: 2,
  quarterly: 4,
  monthly: 12,
  daily: 365,
}

export function periodsPerYear(frequency: CompoundFrequency): number {
  return PERIODS_PER_YEAR[frequency]
}

/**
 * Simulates investment growth with an initial principal plus fixed monthly
 * contributions, compounding interest at the chosen frequency.
 *
 * The simulation steps month-by-month so recurring monthly contributions combine
 * cleanly with any compounding frequency. Each month the balance grows by the
 * equivalent monthly factor derived from the chosen frequency, so the result
 * matches the standard compound interest formula at year boundaries while
 * supporting sub-monthly compounding (e.g. daily) correctly.
 */
export function calculateCompoundInterest(
  input: CompoundInterestInput,
): CompoundInterestResult {
  const { principal, monthlyContribution, annualRatePercent, years, frequency } = input

  const totalMonths = Math.max(0, Math.round(years * 12))
  const annualRate = annualRatePercent / 100
  const ppy = periodsPerYear(frequency)
  const ratePerPeriod = annualRate / ppy
  // Growth factor applied each month, equivalent to compounding `ppy` times a year.
  const monthlyFactor = Math.pow(1 + ratePerPeriod, ppy / 12)

  let balance = principal
  let contributed = principal

  const breakdown: YearlyBreakdown[] = [
    {
      year: 0,
      contributions: round2(contributed),
      interest: 0,
      balance: round2(balance),
    },
  ]

  for (let month = 1; month <= totalMonths; month++) {
    // Grow the existing balance for this month, then add the contribution.
    balance *= monthlyFactor

    if (monthlyContribution > 0) {
      balance += monthlyContribution
      contributed += monthlyContribution
    }

    if (month % 12 === 0) {
      breakdown.push({
        year: month / 12,
        contributions: round2(contributed),
        interest: round2(balance - contributed),
        balance: round2(balance),
      })
    }
  }

  // Capture a final partial year if the horizon isn't a whole number of years.
  if (totalMonths % 12 !== 0) {
    breakdown.push({
      year: round2(totalMonths / 12),
      contributions: round2(contributed),
      interest: round2(balance - contributed),
      balance: round2(balance),
    })
  }

  return {
    finalBalance: round2(balance),
    totalContributions: round2(contributed),
    totalInterest: round2(balance - contributed),
    breakdown,
  }
}

export function round2(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100
}

export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(value)
}
