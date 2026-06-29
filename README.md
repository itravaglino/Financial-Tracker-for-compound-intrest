# FinanceTracker Pro

Aplicación web completa para trackear finanzas personales con datos de Yahoo Finance en tiempo real, análisis técnico avanzado, redes neuronales, valoración objetiva y trading por API.

## Características

- **Multi-usuario** — Registro e inicio de sesión con JWT para que varias personas usen la app de forma independiente
- **Yahoo Finance en tiempo real** — Cotizaciones, fundamentales y datos históricos
- **Importar portfolio** — Importa símbolos directamente desde Yahoo Finance
- **Análisis técnico** — RSI, MACD, Bollinger Bands, ATR, medias móviles, detección de patrones Fibonacci
- **Redes neuronales** — MLP (64-32-16) para detectar patrones Fibonacci y predecir tendencias
- **Valoración objetiva** — Score multi-factor (P/E, P/B, PEG, analistas, ROE, deuda)
- **Valor isotérico** — Comparación de acciones independiente de moneda (normalizado a USD con score ajustado por riesgo)
- **Métricas especiales** — Sharpe, Sortino, Max Drawdown, Quality Score, FCF Yield
- **Contraste de portfolio** — Análisis técnico comparativo de todas tus posiciones
- **Alertas personalizadas** — Por precio, RSI, cambio porcentual (verificación automática cada 5 min)
- **Stop Loss** — Fijo y trailing stop loss por posición
- **Trading API** — Compra/venta vía Alpaca Markets (paper trading o live)

## Arquitectura

```
├── backend/          FastAPI + SQLAlchemy + yfinance + scikit-learn
├── frontend/         React + TypeScript + Vite + Chart.js
├── docker-compose.yml
└── .github/workflows/deploy.yml
```

## Inicio rápido con Docker

```bash
docker compose up --build
```

- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Desarrollo local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173 — el proxy de Vite redirige `/api` al backend.

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `SECRET_KEY` | Clave secreta para JWT (genera con `openssl rand -hex 32`) |
| `DATABASE_URL` | URL de base de datos (default: SQLite) |
| `ALPACA_API_KEY` | API key de Alpaca (opcional) |
| `ALPACA_SECRET_KEY` | Secret key de Alpaca (opcional) |
| `VITE_API_URL` | URL del backend para el frontend en producción |

## Deploy en GitHub Pages

El workflow `.github/workflows/deploy.yml` despliega el frontend automáticamente en GitHub Pages.

> **Nota:** GitHub Pages solo sirve el frontend estático. Para el backend necesitas un servicio adicional (Railway, Render, Fly.io, VPS con Docker, etc.) y configurar `VITE_API_URL` apuntando a tu API.

### Deploy completo (recomendado)

1. Despliega el backend en Railway/Render con las variables de entorno
2. Configura `VITE_API_URL=https://tu-api.com/api` al buildear el frontend
3. Activa GitHub Pages en Settings → Pages → GitHub Actions

## API Endpoints principales

| Endpoint | Descripción |
|----------|-------------|
| `POST /api/auth/register` | Registro de usuario |
| `POST /api/auth/login` | Inicio de sesión |
| `GET /api/portfolio/` | Listar portfolios |
| `POST /api/portfolio/import/yahoo` | Importar desde Yahoo Finance |
| `GET /api/market/quote/{symbol}` | Cotización en tiempo real |
| `GET /api/market/analysis/technical/{symbol}` | Análisis técnico completo |
| `GET /api/market/analysis/neural/{symbol}` | Análisis con red neuronal |
| `GET /api/market/valuation/isometric?symbols=AAPL,MSFT` | Valor isotérico |
| `POST /api/alerts` | Crear alerta personalizada |
| `POST /api/trading/order` | Ejecutar orden de compra/venta |

## Trading con Alpaca

1. Crea una cuenta en [alpaca.markets](https://alpaca.markets)
2. Genera API keys (usa Paper Trading para pruebas)
3. En la app, ve a Trading → Configurar broker
4. Ejecuta órdenes de compra/venta

## Licencia

MIT
