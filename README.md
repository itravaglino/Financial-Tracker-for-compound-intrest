# FinanceTracker Pro

Aplicación web avanzada para gestionar finanzas personales con datos en tiempo real de Yahoo Finance, análisis técnico con redes neuronales, valoración isotérica y trading por API.

## Características

- **Interés compuesto** — Calculadora de proyección de ahorros con aportes recurrentes
- **Multi-usuario** — Registro e inicio de sesión con JWT y contraseñas encriptadas (bcrypt)
- **Portfolio** — Gestión de posiciones e importación desde Yahoo Finance por símbolos
- **Datos en tiempo real** — Cotizaciones, históricos y fundamentales vía Yahoo Finance
- **Valoración objetiva** — Valor intrínseco (DCF + Graham + múltiplos) y **valor isotérico** normalizado sin sesgo cambiario
- **Análisis técnico** — RSI, MACD, Bollinger Bands, SMAs, soportes/resistencias y niveles Fibonacci
- **Redes neuronales** — MLP para detección de patrones (Fibonacci, golden ratio, reversals, head & shoulders) y predicción de tendencia
- **Contraste de portfolio** — Correlaciones, diversificación, riesgo y recomendaciones entre posiciones
- **Alertas personalizadas** — Precio, RSI, Fibonacci, take profit y patrones detectados por IA
- **Stop Loss** — Fijo y trailing con venta automática al activarse
- **Trading API** — Compra/venta vía Alpaca (paper trading) o modo simulación

## Inicio rápido con Docker

```bash
# Clonar el repositorio
git clone https://github.com/itravaglino/Financial-Tracker-for-compound-intrest.git
cd Financial-Tracker-for-compound-intrest

# Configurar variables de entorno
cp .env.example .env

# Iniciar la aplicación
docker compose up --build
```

Abre **http://localhost:8000** en tu navegador (frontend + API integrados).

Para desarrollo con hot-reload del frontend:

```bash
docker compose --profile dev up --build
```

Abre **http://localhost:5173** (proxy `/api` → backend).

## Desarrollo local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Abre **http://localhost:5173** (el proxy redirige `/api` al backend).

## Configuración de Trading (Alpaca)

1. Crea una cuenta en [Alpaca Markets](https://alpaca.markets)
2. Obtén tus API keys de paper trading
3. Configura en `.env`:

```
ALPACA_API_KEY=tu_api_key
ALPACA_SECRET_KEY=tu_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

Sin configurar Alpaca, las órdenes se ejecutan en **modo simulación**.

## Importar portfolio desde Yahoo Finance

1. Ve a **Portfolio** → **Importar Yahoo**
2. Ingresa los símbolos separados por coma: `AAPL, MSFT, GOOGL, TSLA, NVDA`
3. Ajusta cantidades y costos promedio después de importar

## Valor isotérico

El valor isotérico normaliza el precio de una acción a una unidad de poder adquisitivo global (USD-PPP), ajustando por:

- Tipo de cambio en tiempo real
- Beta (riesgo sistémico)
- Múltiplos sectoriales de referencia

Permite comparar acciones de distintos mercados (US, Europa, LATAM) sin sesgo cambiario.

## Hosting gratuito (Render)

La forma más simple de hostear **frontend + API** gratis:

1. Entrá a [Render](https://render.com) y conectá este repositorio
2. Usá el Blueprint `render.yaml` (plan free)
3. Render va a buildear el Dockerfile y publicar la app en una URL `*.onrender.com`

Botón de deploy:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

> El plan free de Render apaga el servicio tras ~15 min de inactividad; el primer request puede tardar ~30–60s en despertarlo.

### Demo rápida local + túnel

```bash
# Backend + frontend build
cd frontend && npm install && npm run build && cd ..
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# En otra terminal (URL HTTPS pública gratis)
cloudflared tunnel --url http://127.0.0.1:8000
```

## Despliegue en GitHub

- **GitHub Actions** — CI/CD automático en cada push (tests, build, Docker)
- **GitHub Pages** — Frontend desplegado automáticamente desde `main`
- **Docker** — Imagen lista para Railway, Render, Fly.io o cualquier VPS

### GitHub Pages + Backend separado

El frontend en GitHub Pages necesita un backend desplegado. Configura `VITE_API_URL` apuntando a tu backend:

```bash
VITE_API_URL=https://tu-backend.onrender.com/api npm run build
```

## Estructura del proyecto

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── auth.py              # JWT authentication
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── routes/              # API endpoints
│   │   └── services/
│   │       ├── yahoo_finance.py # Datos Yahoo Finance
│   │       ├── technical_analysis.py
│   │       ├── neural_patterns.py  # Redes neuronales
│   │       ├── valuation.py     # Valoración + isotérico
│   │       └── trading.py       # Alpaca + alertas
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/               # Dashboard, Portfolio, Análisis, Trading, Alertas
│       └── api.ts               # API client
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/register` | Registro de usuario |
| POST | `/api/auth/login` | Inicio de sesión |
| GET | `/api/portfolio/` | Listar portfolios |
| POST | `/api/portfolio/import-yahoo` | Importar desde Yahoo |
| GET | `/api/analysis/technical/{symbol}` | Análisis técnico |
| GET | `/api/analysis/patterns/{symbol}` | Patrones IA + Fibonacci |
| GET | `/api/analysis/valuation/{symbol}` | Valoración isotérica |
| GET | `/api/analysis/portfolio/{id}` | Contraste de portfolio |
| POST | `/api/trading/orders` | Ejecutar orden |
| POST | `/api/trading/alerts` | Crear alerta |
| POST | `/api/trading/stop-loss` | Crear stop loss |

## Licencia

MIT
