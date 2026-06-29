import '@testing-library/jest-dom'

// jsdom does not implement ResizeObserver, which recharts' ResponsiveContainer relies on.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver =
  globalThis.ResizeObserver ?? (ResizeObserverStub as unknown as typeof ResizeObserver)
