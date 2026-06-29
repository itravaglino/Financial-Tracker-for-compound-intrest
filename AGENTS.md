# AGENTS.md

## Project overview

Single-page web app ("Compound Interest Tracker") built with Vite + React 18 +
TypeScript. The compound-interest math lives in `src/lib/compoundInterest.ts`
(pure functions, unit-tested); the UI lives in `src/App.tsx`.

## Common commands

See `README.md` for the full list. In short: `npm run dev`, `npm run build`,
`npm run lint`, `npm test`.

## Cursor Cloud specific instructions

- Dependencies (`npm install`) are refreshed automatically by the startup update
  script; you don't need to run it manually.
- Run the app with `npm run dev`. The dev server is configured with `host: true`
  on port `5173` (see `vite.config.ts`), so it is reachable on all interfaces.
- The test environment is jsdom. Recharts' `ResponsiveContainer` needs
  `ResizeObserver`, which jsdom lacks; a stub is registered in
  `src/test/setup.ts`. Keep that stub if you add more chart-based component tests.
- `npm run build` runs `tsc -b` first, so type errors fail the build. The app's
  TS lib target is `ES2022` (`tsconfig.app.json`) — newer JS built-ins like
  `Array.prototype.at` are available.
