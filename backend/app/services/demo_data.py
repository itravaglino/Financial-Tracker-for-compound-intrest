import hashlib
import math
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd


def _seed(symbol: str) -> int:
    return int(hashlib.md5(symbol.upper().encode()).hexdigest()[:8], 16)


def demo_quote(symbol: str) -> dict[str, Any]:
    s = _seed(symbol)
    base_price = 50 + (s % 450)
    change_pct = ((s % 200) - 100) / 50
    price = base_price * (1 + change_pct / 100)

    sectors = ["Technology", "Healthcare", "Finance", "Energy", "Consumer", "Industrial"]
    return {
        "symbol": symbol.upper(),
        "name": f"{symbol.upper()} Inc. (demo)",
        "price": round(price, 2),
        "currency": "USD",
        "change": round(price * change_pct / 100, 2),
        "change_pct": round(change_pct, 2),
        "volume": s % 10_000_000,
        "market_cap": base_price * 1_000_000_000,
        "pe_ratio": round(10 + (s % 30), 2),
        "forward_pe": round(8 + (s % 25), 2),
        "dividend_yield": round((s % 50) / 1000, 4),
        "fifty_two_week_high": round(price * 1.3, 2),
        "fifty_two_week_low": round(price * 0.7, 2),
        "sector": sectors[s % len(sectors)],
        "industry": "Demo Industry",
        "timestamp": datetime.utcnow().isoformat(),
        "demo_mode": True,
    }


def demo_history(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    s = _seed(symbol)
    days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 252, "2y": 504, "5y": 1260}
    days = days_map.get(period, 252)

    dates = pd.date_range(end=datetime.now(), periods=days, freq="B")
    base = 50 + (s % 450)
    t = np.linspace(0, 4 * math.pi, days)
    noise = np.random.RandomState(s).normal(0, 0.02, days)
    prices = base * (1 + 0.3 * np.sin(t) + np.cumsum(noise) * 0.1)

    high = prices * (1 + np.abs(np.random.RandomState(s + 1).normal(0, 0.01, days)))
    low = prices * (1 - np.abs(np.random.RandomState(s + 2).normal(0, 0.01, days)))
    volume = np.random.RandomState(s + 3).randint(1_000_000, 10_000_000, days)

    return pd.DataFrame({
        "Open": prices * 0.99,
        "High": high,
        "Low": low,
        "Close": prices,
        "Volume": volume,
    }, index=dates)


def demo_fundamentals(symbol: str) -> dict[str, Any]:
    s = _seed(symbol)
    return {
        "symbol": symbol.upper(),
        "name": f"{symbol.upper()} Inc.",
        "sector": "Technology",
        "industry": "Software",
        "market_cap": (50 + s % 450) * 1_000_000_000,
        "enterprise_value": (55 + s % 450) * 1_000_000_000,
        "pe_ratio": round(10 + s % 30, 2),
        "forward_pe": round(8 + s % 25, 2),
        "peg_ratio": round(0.5 + (s % 20) / 10, 2),
        "price_to_book": round(1 + (s % 15), 2),
        "price_to_sales": round(2 + (s % 10), 2),
        "ev_to_revenue": round(3 + (s % 8), 2),
        "ev_to_ebitda": round(8 + (s % 15), 2),
        "profit_margin": round(0.05 + (s % 30) / 100, 4),
        "operating_margin": round(0.08 + (s % 25) / 100, 4),
        "roe": round(0.1 + (s % 30) / 100, 4),
        "roa": round(0.05 + (s % 15) / 100, 4),
        "revenue_growth": round(0.02 + (s % 20) / 100, 4),
        "earnings_growth": round(0.01 + (s % 25) / 100, 4),
        "debt_to_equity": round(20 + s % 80, 2),
        "current_ratio": round(1 + (s % 20) / 10, 2),
        "free_cashflow": (s % 100) * 1_000_000_000,
        "dividend_yield": round((s % 40) / 1000, 4),
        "beta": round(0.5 + (s % 150) / 100, 2),
        "fifty_two_week_high": 50 + s % 450 + 50,
        "fifty_two_week_low": 50 + s % 450 - 50,
        "target_mean_price": 50 + s % 450 + 10,
        "recommendation": ["buy", "hold", "sell"][s % 3],
        "analyst_count": 10 + s % 30,
        "demo_mode": True,
    }
