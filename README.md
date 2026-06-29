# FinTrack Pro

Plataforma web avanzada de tracking financiero personal con datos de Yahoo Finance en tiempo real, redes neuronales, análisis técnico y trading via API.

## Características

- **Multi-usuario**: Registro e inicio de sesión con JWT (bcrypt)
- **Yahoo Finance**: Cotizaciones en tiempo real, datos históricos e importación de portfolio
- **Valoración isométrica**: Precios normalizados independientes de la moneda para juicios objetivos
- **Valoración objetiva**: DCF, P/E, PEG y recomendaciones automáticas
- **Redes neuronales LSTM**: Detección de patrones (head & shoulders, triángulos, etc.)
- **Fibonacci**: Retracements, golden pocket y golden ratio
- **Análisis técnico**: RSI, MACD, Bollinger Bands, soportes/resistencias
- **Comparación de acciones**: Contraste entre holdings del portfolio
- **Alertas personalizadas**: Precio, cambio %, RSI, Fibonacci, señales IA
- **Stop Loss**: Fijos y trailing, monitoreo automático
- **Trading API**: Compra/venta via Alpaca (paper trading o real)

## Arquitectura

```
frontend/          React + Vite (UI moderna dark theme)
backend/           FastAPI + SQLAlchemy + TensorFlow
  app/
    auth/          JWT authentication
    ml/            LSTM + Fibonacci pattern detection
    services/      Yahoo Finance, valuation, alerts, trading
    routes/        REST API endpoints
```

## Inicio Rápido

### Con Docker (recomendado)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Documentación API: http://localhost:8000/docs

### Manual

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Configuración

Copia `.env.example` a `.env` y configura:

| Variable | Descripción |
|----------|-------------|
| `SECRET_KEY` | Clave secreta para JWT (obligatorio en producción) |
| `ALPACA_API_KEY` | API key de Alpaca para trading real |
| `ALPACA_SECRET_KEY` | Secret key de Alpaca |
| `ALPACA_BASE_URL` | URL de Alpaca (paper: `https://paper-api.alpaca.markets`) |

Sin credenciales de Alpaca, el trading funciona en **modo simulado**.

## Despliegue en GitHub

### Frontend (GitHub Pages)

1. Ve a Settings > Pages > Source: GitHub Actions
2. Push a `main` activa el workflow de deploy automático
3. Configura `VITE_API_URL` apuntando a tu backend desplegado

### Backend

Despliega el backend en cualquier servicio que soporte Docker:

- [Railway](https://railway.app)
- [Render](https://render.com)
- [Fly.io](https://fly.io)
- [Google Cloud Run](https://cloud.google.com/run)

### Alertas programadas

Configura estos secrets en GitHub para el workflow de alertas:

- `FINTRACK_API_URL`: URL del backend desplegado
- `FINTRACK_API_TOKEN`: Token JWT de un usuario

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/register` | Registro de usuario |
| POST | `/api/auth/login` | Inicio de sesión |
| GET | `/api/portfolio/` | Listar portfolios |
| POST | `/api/portfolio/import-yahoo` | Importar desde Yahoo Finance |
| GET | `/api/portfolio/{id}/analysis` | Análisis completo del portfolio |
| GET | `/api/market/quote/{symbol}` | Cotización en tiempo real |
| GET | `/api/market/isometric/{symbol}` | Valor isométrico |
| GET | `/api/market/valuation/{symbol}` | Valoración objetiva |
| GET | `/api/market/technical/{symbol}` | Análisis técnico + IA |
| GET | `/api/market/compare?symbols=A,B,C` | Comparar acciones |
| POST | `/api/trading/orders` | Crear orden de compra/venta |
| POST | `/api/trading/stop-loss` | Configurar stop loss |
| POST | `/api/portfolio/alerts` | Crear alerta personalizada |

## Licencia

MIT
