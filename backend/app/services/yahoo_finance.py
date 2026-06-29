import logging
import random
import time
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

from app.config import settings

logger = logging.getLogger(__name__)

FX_PAIRS = {
    "EUR": "EURUSD=X",
    "GBP": "GBPUSD=X",
    "JPY": "JPY=X",
    "CHF": "CHFUSD=X",
    "CAD": "USDCAD=X",
    "AUD": "AUDUSD=X",
    "MXN": "USDMXN=X",
    "BRL": "USDBRL=X",
}

DEMO_BASE_PRICES = {
    "AAPL": 195.50, "MSFT": 425.30, "GOOGL": 175.80, "AMZN": 185.20,
    "NVDA": 875.40, "TSLA": 248.90, "META": 505.60, "JPM": 198.30,
    "V": 280.15, "WMT": 68.40, "DIS": 112.25, "NFLX": 620.80,
    "AMD": 162.50, "INTC": 43.20, "BA": 178.60, "SPY": 520.30,
}


class YahooFinanceService:
    def __init__(self):
        self._cache: dict[str, tuple[datetime, dict]] = {}
        self._hist_cache: dict[str, tuple[datetime, pd.DataFrame]] = {}
        self._cache_ttl = timedelta(seconds=60)
        self._hist_cache_ttl = timedelta(seconds=300)
        self._demo_mode = False

    def _get_cached(self, key: str) -> Optional[dict]:
        if key in self._cache:
            ts, data = self._cache[key]
            if datetime.utcnow() - ts < self._cache_ttl:
                return data
        return None

    def _set_cache(self, key: str, data: dict):
        self._cache[key] = (datetime.utcnow(), data)

    def _generate_demo_history(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        base = DEMO_BASE_PRICES.get(symbol, 100.0)
        days_map = {"5d": 5, "1mo": 30, "6mo": 180, "1y": 365, "2y": 730}
        days = days_map.get(period, 365)

        dates = pd.date_range(end=datetime.now(), periods=days, freq="B")
        rng = np.random.default_rng(hash(symbol) % 2**32)
        returns = rng.normal(0.0003, 0.015, days)
        prices = base * np.cumprod(1 + returns)
        volumes = rng.integers(1_000_000, 50_000_000, days)

        return pd.DataFrame({
            "Open": prices * (1 + rng.normal(0, 0.002, days)),
            "High": prices * (1 + abs(rng.normal(0, 0.005, days))),
            "Low": prices * (1 - abs(rng.normal(0, 0.005, days))),
            "Close": prices,
            "Volume": volumes,
        }, index=dates)

    def _get_demo_quote(self, symbol: str) -> dict:
        base = DEMO_BASE_PRICES.get(symbol, 100.0 + random.uniform(-20, 20))
        change = random.uniform(-3, 3)
        return {
            "symbol": symbol,
            "price": round(base, 2),
            "currency": "USD",
            "change_percent": round(change, 2),
            "volume": random.randint(1_000_000, 30_000_000),
            "market_cap": base * 1e9,
            "name": f"{symbol} Inc.",
            "sector": random.choice(["Technology", "Finance", "Healthcare", "Consumer", "Energy"]),
            "exchange": "NMS",
            "demo": True,
        }

    def _download_history(self, symbol: str, period: str = "5d", retries: int = 3) -> pd.DataFrame:
        cache_key = f"{symbol}:{period}"
        if cache_key in self._hist_cache:
            ts, df = self._hist_cache[cache_key]
            if datetime.utcnow() - ts < self._hist_cache_ttl:
                return df

        last_error = None
        for attempt in range(retries):
            try:
                df = yf.download(
                    symbol.upper(),
                    period=period,
                    progress=False,
                    threads=False,
                    auto_adjust=True,
                )
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                if not df.empty:
                    self._hist_cache[cache_key] = (datetime.utcnow(), df)
                    self._demo_mode = False
                    return df
            except Exception as e:
                last_error = e
                logger.warning("Download attempt %d failed for %s: %s", attempt + 1, symbol, e)
                time.sleep(1 * (attempt + 1))

        logger.warning("Using demo data for %s (Yahoo Finance unavailable)", symbol)
        self._demo_mode = True
        df = self._generate_demo_history(symbol.upper(), period)
        self._hist_cache[cache_key] = (datetime.utcnow(), df)
        return df

    def _safe_info(self, ticker: yf.Ticker) -> dict:
        try:
            return ticker.info or {}
        except Exception as e:
            logger.warning("Could not fetch info: %s", e)
            return {"currency": "USD", "sector": "Unknown"}

    def get_quote(self, symbol: str) -> dict:
        symbol = symbol.upper()
        cache_key = f"quote:{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            hist = self._download_history(symbol, "5d")
            price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
            volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0

            if self._demo_mode:
                result = self._get_demo_quote(symbol)
                result["price"] = round(price, 4)
                result["change_percent"] = round(change_pct, 2)
            else:
                ticker = yf.Ticker(symbol)
                info = self._safe_info(ticker)
                result = {
                    "symbol": symbol,
                    "price": round(price, 4),
                    "currency": info.get("currency", "USD"),
                    "change_percent": round(change_pct, 2),
                    "volume": volume or int(info.get("volume", 0) or 0),
                    "market_cap": info.get("marketCap"),
                    "name": info.get("shortName", symbol),
                    "sector": info.get("sector", "Unknown"),
                    "exchange": info.get("exchange", ""),
                }
        except Exception as e:
            logger.warning("Quote fallback to demo for %s: %s", symbol, e)
            result = self._get_demo_quote(symbol)

        self._set_cache(cache_key, result)
        return result

    def get_historical(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        return self._download_history(symbol.upper(), period)

    def get_fx_rate(self, currency: str) -> float:
        defaults = {"EUR": 1.08, "GBP": 1.27, "JPY": 0.0067, "CHF": 1.12, "CAD": 0.74, "MXN": 0.058, "BRL": 0.20}
        if currency == "USD":
            return 1.0
        pair = FX_PAIRS.get(currency)
        if not pair:
            return defaults.get(currency, 1.0)
        try:
            hist = self._download_history(pair, "5d")
            rate = float(hist["Close"].iloc[-1])
            if pair.startswith("USD") and currency in ("CAD", "MXN", "BRL"):
                return 1.0 / rate
            return rate
        except Exception:
            return defaults.get(currency, 1.0)

    def convert_to_usd(self, amount: float, currency: str) -> float:
        return amount * self.get_fx_rate(currency)

    def get_isometric_value(self, symbol: str) -> dict:
        quote = self.get_quote(symbol)
        price = quote["price"]
        currency = quote["currency"]
        usd_price = self.convert_to_usd(price, currency)
        eur_rate = self.get_fx_rate("EUR")
        eur_price = usd_price / eur_rate if eur_rate else usd_price

        hist = self.get_historical(symbol, "6mo")
        returns = hist["Close"].pct_change().dropna()
        volatility = float(returns.std()) if len(returns) > 0 else 0.01
        independence_score = max(0, min(100, (1 - volatility * 10) * 100))
        normalized = usd_price / (1 + volatility)

        return {
            "symbol": symbol.upper(),
            "price_usd": round(usd_price, 4),
            "price_eur": round(eur_price, 4),
            "price_normalized": round(normalized, 4),
            "currency_independence_score": round(independence_score, 2),
            "relative_strength_index": 0.0,
            "original_currency": currency,
            "original_price": price,
        }

    def import_yahoo_portfolio(self, symbols: list[str]) -> list[dict]:
        holdings = []
        for symbol in symbols:
            try:
                quote = self.get_quote(symbol.strip().upper())
                holdings.append({
                    "symbol": quote["symbol"],
                    "quantity": 0,
                    "avg_cost": quote["price"],
                    "currency": quote["currency"],
                    "current_price": quote["price"],
                    "name": quote.get("name", symbol),
                    "sector": quote.get("sector", "Unknown"),
                })
                time.sleep(0.3)
            except Exception as e:
                logger.warning("Error importing %s: %s", symbol, e)
        return holdings

    def get_batch_quotes(self, symbols: list[str]) -> list[dict]:
        results = []
        for s in symbols:
            try:
                results.append(self.get_quote(s))
            except Exception as e:
                logger.warning("Batch quote error for %s: %s", s, e)
        return results


yahoo_service = YahooFinanceService()
