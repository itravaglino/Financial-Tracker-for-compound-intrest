# Financial Tracker for Compound Interest

A small, modern web app for visualizing how an initial investment plus recurring
monthly contributions grow under compound interest over time.

Enter your initial investment, monthly contribution, expected annual return,
time horizon, and compounding frequency to see your projected final balance,
total contributions, interest earned, and a year-by-year growth chart.

## Tech stack

- [Vite](https://vitejs.dev/) + [React 18](https://react.dev/) + TypeScript
- [Recharts](https://recharts.org/) for the growth chart
- [Vitest](https://vitest.dev/) + [Testing Library](https://testing-library.com/) for tests
- [ESLint](https://eslint.org/) for linting

## Getting started

Requires Node.js 18+ (developed on Node 22).

```bash
npm install      # install dependencies
npm run dev      # start the dev server at http://localhost:5173
```

## Available scripts

| Command          | Description                                  |
| ---------------- | -------------------------------------------- |
| `npm run dev`    | Start the Vite dev server (hot reload)       |
| `npm run build`  | Type-check and build the production bundle    |
| `npm run preview`| Preview the production build locally          |
| `npm run lint`   | Run ESLint over the project                   |
| `npm test`       | Run the Vitest test suite once                |
| `npm run test:watch` | Run tests in watch mode                  |

## Project structure

```
src/
  lib/compoundInterest.ts        # pure, tested compound-interest math
  lib/compoundInterest.test.ts   # unit tests for the math
  App.tsx                        # UI: inputs, summary stats, growth chart
  App.test.tsx                   # component tests
```
