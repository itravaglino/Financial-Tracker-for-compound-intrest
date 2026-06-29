import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders the tracker heading and a computed final balance', () => {
    render(<App />)
    expect(
      screen.getByRole('heading', { name: /compound interest tracker/i }),
    ).toBeInTheDocument()

    const balance = screen.getByTestId('final-balance')
    expect(balance.textContent).toMatch(/^\$[\d,]+$/)
  })

  it('recalculates when an input changes', () => {
    render(<App />)
    const before = screen.getByTestId('final-balance').textContent

    fireEvent.change(screen.getByLabelText(/annual return rate/i), {
      target: { value: '12' },
    })

    const after = screen.getByTestId('final-balance').textContent
    expect(after).not.toEqual(before)
  })
})
