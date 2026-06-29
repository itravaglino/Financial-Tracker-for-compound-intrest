import hashlib
import math
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

DEMO_BASE_PRICES = {
    "AAPL": 195.50,
    "MSFT": 425.30,
    "GOOGL": 175.80,
    "AMZN": 185.20,
    "NVDA": 875.40,
    "TSLA": 248.90,
    "META": 505.60,
    "JPM": 198.30,
    "V": 280.15,
    "WMT": 68.40,
    "DIS": 112.25,
    "NFLX": 620.80,
    "AMD": 162.50,
    "INTC": 43.20,
    "BA": 178.60,
    "SPY": 520.30,
}

SECTORS = ["Technology", "Healthcare", "Finance", "Energy", "Consumer", "Industrial"]


def _seed(symbol: str) -> int:
    return int(hashlib.md5(symbol.upper().encode()).hexdigest()[:8], 16)


def demo_quote(symbol: str) -> dict[str, Any]:
    sym = symbol.upper()
    s = _seed(sym)
    base = DEMO_BASE_PRICES.get(sym, 50 + (s % 450))
    change_pct = ((s % 200) - 100) / 50
    price = round(base * (1 + change_pct / 100), 2)
    change = round(price * change_pct / 100, 4)

    return {
        "symbol": sym,
        "price": price,
        "change": change,
        "change_percent": round(change_pct, 2),
        "volume": s % 10_000_000,
        "market_cap": base * 1_000_000_000,
        "currency": "USD",
        "name": f"{sym} Inc.",
        "sector": SECTORS[s % len(SECTORS)],
        "industry": "Demo Industry",
        "timestamp": datetime.utcnow(),
        "demo_mode": True,
    }


def demo_history(symbol: str, period: str = "1y") -> pd.DataFrame:
    sym = symbol.upper()
    s = _seed(sym)
    base = DEMO_BASE_PRICES.get(sym, 50 + (s % 450))
    days_map = {
        "5d": 5,
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 252,
        "2y": 504,
        "5y": 1260,
    }
    days = days_map.get(period, 252)

    dates = pd.date_range(end=datetime.now(), periods=days, freq="B")
    t = np.linspace(0, 4 * math.pi, days)
    rng = np.random.RandomState(s)
    noise = rng.normal(0, 0.02, days)
    prices = base * (1 + 0.3 * np.sin(t) + np.cumsum(noise) * 0.1)

    high = prices * (1 + np.abs(rng.normal(0, 0.01, days)))
    low = prices * (1 - np.abs(rng.normal(0, 0.01, days)))
    volume = rng.randint(1_000_000, 10_000_000, days)

    return pd.DataFrame(
        {
            "Open": prices * 0.99,
            "High": high,
            "Low": low,
            "Close": prices,
            "Volume": volume,
        },
        index=dates,
    )


def demo_fundamentals(symbol: str) -> dict[str, Any]:
    sym = symbol.upper()
    s = _seed(sym)
    base = DEMO_BASE_PRICES.get(sym, 50 + (s % 450))
    return {
        "symbol": sym,
        "pe_ratio": round(10 + s % 30, 2),
        "pb_ratio": round(1 + (s % 15), 2),
        "peg_ratio": round(0.5 + (s % 20) / 10, 2),
        "dividend_yield": round((s % 50) / 1000, 4),
        "eps": round(base / (10 + s % 30), 2),
        "revenue": (s % 100) * 1_000_000_000,
        "profit_margin": round(0.05 + (s % 30) / 100, 4),
        "roe": round(0.1 + (s % 30) / 100, 4),
        "debt_to_equity": round(20 + s % 80, 2),
        "free_cash_flow": (s % 100) * 1_000_000_000,
        "book_value": round(base * 0.4, 2),
        "target_mean_price": round(base * 1.1, 2),
        "recommendation": ["buy", "hold", "sell"][s % 3],
        "currency": "USD",
        "sector": SECTORS[s % len(SECTORS)],
        "industry": "Demo Industry",
        "beta": round(0.5 + (s % 150) / 100, 2),
        "fifty_two_week_high": round(base * 1.3, 2),
        "fifty_two_week_low": round(base * 0.7, 2),
        "demo_mode": True,
    }
