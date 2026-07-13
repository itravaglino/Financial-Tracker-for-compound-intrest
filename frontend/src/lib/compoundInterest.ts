export type CompoundFrequency = 'annually' | 'semiannually' | 'quarterly' | 'monthly' | 'daily';

export interface CompoundInterestInput {
  principal: number;
  monthlyContribution: number;
  annualRatePercent: number;
  years: number;
  frequency: CompoundFrequency;
}

export interface YearlyBreakdown {
  year: number;
  contributions: number;
  interest: number;
  balance: number;
}

export interface CompoundInterestResult {
  finalBalance: number;
  totalContributions: number;
  totalInterest: number;
  breakdown: YearlyBreakdown[];
}

const PERIODS_PER_YEAR: Record<CompoundFrequency, number> = {
  annually: 1,
  semiannually: 2,
  quarterly: 4,
  monthly: 12,
  daily: 365,
};

export function periodsPerYear(frequency: CompoundFrequency): number {
  return PERIODS_PER_YEAR[frequency];
}

export function calculateCompoundInterest(input: CompoundInterestInput): CompoundInterestResult {
  const { principal, monthlyContribution, annualRatePercent, years, frequency } = input;

  const totalMonths = Math.max(0, Math.round(years * 12));
  const annualRate = annualRatePercent / 100;
  const ppy = periodsPerYear(frequency);
  const ratePerPeriod = annualRate / ppy;
  const monthlyFactor = Math.pow(1 + ratePerPeriod, ppy / 12);

  let balance = principal;
  let contributed = principal;

  const breakdown: YearlyBreakdown[] = [
    {
      year: 0,
      contributions: round2(contributed),
      interest: 0,
      balance: round2(balance),
    },
  ];

  for (let month = 1; month <= totalMonths; month++) {
    balance *= monthlyFactor;

    if (monthlyContribution > 0) {
      balance += monthlyContribution;
      contributed += monthlyContribution;
    }

    if (month % 12 === 0) {
      breakdown.push({
        year: month / 12,
        contributions: round2(contributed),
        interest: round2(balance - contributed),
        balance: round2(balance),
      });
    }
  }

  if (totalMonths % 12 !== 0) {
    breakdown.push({
      year: round2(totalMonths / 12),
      contributions: round2(contributed),
      interest: round2(balance - contributed),
      balance: round2(balance),
    });
  }

  return {
    finalBalance: round2(balance),
    totalContributions: round2(contributed),
    totalInterest: round2(balance - contributed),
    breakdown,
  };
}

export function round2(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}
