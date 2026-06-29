import { describe, expect, it } from 'vitest'
import {
  calculateCompoundInterest,
  formatCurrency,
  periodsPerYear,
} from './compoundInterest'

describe('calculateCompoundInterest', () => {
  it('compounds a lump sum annually with no contributions', () => {
    const result = calculateCompoundInterest({
      principal: 1000,
      monthlyContribution: 0,
      annualRatePercent: 10,
      years: 1,
      frequency: 'annually',
    })

    // 1000 * 1.10 = 1100
    expect(result.finalBalance).toBeCloseTo(1100, 2)
    expect(result.totalContributions).toBeCloseTo(1000, 2)
    expect(result.totalInterest).toBeCloseTo(100, 2)
  })

  it('matches the standard compound interest formula over multiple years', () => {
    const result = calculateCompoundInterest({
      principal: 5000,
      monthlyContribution: 0,
      annualRatePercent: 6,
      years: 10,
      frequency: 'annually',
    })

    // A = P (1 + r)^n = 5000 * 1.06^10
    const expected = 5000 * Math.pow(1.06, 10)
    expect(result.finalBalance).toBeCloseTo(expected, 0)
  })

  it('accounts for recurring monthly contributions', () => {
    const result = calculateCompoundInterest({
      principal: 0,
      monthlyContribution: 100,
      annualRatePercent: 0,
      years: 2,
      frequency: 'monthly',
    })

    // No interest, 24 months * 100 = 2400 contributed
    expect(result.totalContributions).toBeCloseTo(2400, 2)
    expect(result.finalBalance).toBeCloseTo(2400, 2)
    expect(result.totalInterest).toBeCloseTo(0, 2)
  })

  it('produces a yearly breakdown including year 0', () => {
    const result = calculateCompoundInterest({
      principal: 1000,
      monthlyContribution: 0,
      annualRatePercent: 5,
      years: 3,
      frequency: 'annually',
    })

    expect(result.breakdown[0]).toMatchObject({ year: 0, balance: 1000 })
    expect(result.breakdown).toHaveLength(4) // year 0..3
    expect(result.breakdown.at(-1)?.year).toBe(3)
  })

  it('earns more interest with more frequent compounding', () => {
    const annual = calculateCompoundInterest({
      principal: 10000,
      monthlyContribution: 0,
      annualRatePercent: 8,
      years: 20,
      frequency: 'annually',
    })
    const daily = calculateCompoundInterest({
      principal: 10000,
      monthlyContribution: 0,
      annualRatePercent: 8,
      years: 20,
      frequency: 'daily',
    })

    expect(daily.finalBalance).toBeGreaterThan(annual.finalBalance)
  })
})

describe('periodsPerYear', () => {
  it('maps frequencies to periods', () => {
    expect(periodsPerYear('annually')).toBe(1)
    expect(periodsPerYear('quarterly')).toBe(4)
    expect(periodsPerYear('monthly')).toBe(12)
    expect(periodsPerYear('daily')).toBe(365)
  })
})

describe('formatCurrency', () => {
  it('formats whole-dollar USD', () => {
    expect(formatCurrency(1234.56)).toBe('$1,235')
  })
})
