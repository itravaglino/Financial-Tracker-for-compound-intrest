import { describe, expect, it } from 'vitest';
import { calculateCompoundInterest, round2 } from '../lib/compoundInterest';

describe('compoundInterest', () => {
  it('calculates growth with monthly contributions', () => {
    const result = calculateCompoundInterest({
      principal: 10000,
      monthlyContribution: 500,
      annualRatePercent: 7,
      years: 10,
      frequency: 'monthly',
    });

    expect(result.finalBalance).toBeGreaterThan(result.totalContributions);
    expect(result.totalInterest).toBeGreaterThan(0);
    expect(result.breakdown.length).toBeGreaterThan(1);
  });

  it('rounds to two decimals', () => {
    expect(round2(1.005)).toBe(1.01);
  });
});
