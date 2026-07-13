import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf

from app.services.demo_data import demo_fundamentals, demo_history, demo_quote

logger = logging.getLogger(__name__)

FX_DEFAULTS = {
    "EUR": 1.08,
    "GBP": 1.27,
    "JPY": 0.0067,
    "CHF": 1.12,
    "CAD": 0.74,
    "AUD": 0.65,
    "MXN": 0.058,
    "BRL": 0.20,
}


class _YahooFinanceBackend:
    """Backend con caché, reintentos y fallback a datos demo."""

    def __init__(self):
        self._quote_cache: dict[str, tuple[datetime, dict]] = {}
        self._hist_cache: dict[str, tuple[datetime, pd.DataFrame]] = {}
        self._quote_ttl = timedelta(seconds=60)
        self._hist_ttl = timedelta(seconds=300)
        self._demo_mode = False

    @property
    def demo_mode(self) -> bool:
        return self._demo_mode

    def _download_history(self, symbol: str, period: str = "1y", retries: int = 3) -> pd.DataFrame:
        cache_key = f"{symbol}:{period}"
        cached = self._hist_cache.get(cache_key)
        if cached and datetime.utcnow() - cached[0] < self._hist_ttl:
            return cached[1]

        sym = symbol.upper()
        for attempt in range(retries):
            try:
                df = yf.download(
                    sym,
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
            except Exception as exc:
                logger.warning("Yahoo download attempt %d failed for %s: %s", attempt + 1, sym, exc)
                time.sleep(0.5 * (attempt + 1))

        logger.warning("Using demo history for %s (Yahoo Finance unavailable)", sym)
        self._demo_mode = True
        df = demo_history(sym, period)
        self._hist_cache[cache_key] = (datetime.utcnow(), df)
        return df

    @staticmethod
    def _safe_info(ticker: yf.Ticker) -> dict:
        try:
            return ticker.info or {}
        except Exception as exc:
            logger.warning("Could not fetch ticker info: %s", exc)
            return {}

    def get_quote(self, symbol: str) -> dict:
        sym = symbol.upper()
        cache_key = f"quote:{sym}"
        cached = self._quote_cache.get(cache_key)
        if cached and datetime.utcnow() - cached[0] < self._quote_ttl:
            return cached[1]

        try:
            hist = self._download_history(sym, "5d")
            price = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
            change = price - prev
            change_pct = (change / prev * 100) if prev else 0.0
            volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0

            if self._demo_mode:
                result = demo_quote(sym)
                result["price"] = round(price, 4)
                result["change"] = round(change, 4)
                result["change_percent"] = round(change_pct, 2)
                result["volume"] = volume or result["volume"]
            else:
                info = self._safe_info(yf.Ticker(sym))
                result = {
                    "symbol": sym,
                    "price": round(price, 4),
                    "change": round(change, 4),
                    "change_percent": round(change_pct, 2),
                    "volume": volume or int(info.get("volume") or 0),
                    "market_cap": info.get("marketCap"),
                    "currency": info.get("currency", "USD"),
                    "name": info.get("longName") or info.get("shortName", sym),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "timestamp": datetime.utcnow(),
                    "demo_mode": False,
                }
        except Exception as exc:
            logger.warning("Quote fallback to demo for %s: %s", sym, exc)
            self._demo_mode = True
            result = demo_quote(sym)

        self._quote_cache[cache_key] = (datetime.utcnow(), result)
        return result

    def get_historical(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        return self._download_history(symbol.upper(), period)

    def get_fundamentals(self, symbol: str) -> dict:
        sym = symbol.upper()
        if self._demo_mode:
            return demo_fundamentals(sym)

        try:
            info = self._safe_info(yf.Ticker(sym))
            if not info or not (info.get("regularMarketPrice") or info.get("currentPrice") or info.get("trailingPE")):
                self._demo_mode = True
                return demo_fundamentals(sym)

            return {
                "symbol": sym,
                "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "peg_ratio": info.get("pegRatio"),
                "dividend_yield": info.get("dividendYield"),
                "eps": info.get("trailingEps"),
                "revenue": info.get("totalRevenue"),
                "profit_margin": info.get("profitMargins"),
                "roe": info.get("returnOnEquity"),
                "debt_to_equity": info.get("debtToEquity"),
                "free_cash_flow": info.get("freeCashflow"),
                "book_value": info.get("bookValue"),
                "target_mean_price": info.get("targetMeanPrice"),
                "recommendation": info.get("recommendationKey"),
                "currency": info.get("currency", "USD"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "beta": info.get("beta"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "demo_mode": False,
            }
        except Exception as exc:
            logger.warning("Fundamentals fallback to demo for %s: %s", sym, exc)
            self._demo_mode = True
            return demo_fundamentals(sym)

    def get_exchange_rate(self, from_currency: str, to_currency: str = "USD") -> float:
        if from_currency == to_currency:
            return 1.0

        if self._demo_mode:
            if to_currency == "USD":
                return FX_DEFAULTS.get(from_currency, 1.0)
            if from_currency == "USD":
                rate = FX_DEFAULTS.get(to_currency, 1.0)
                return 1.0 / rate if rate else 1.0
            return FX_DEFAULTS.get(from_currency, 1.0)

        try:
            pair = f"{from_currency}{to_currency}=X"
            hist = self._download_history(pair, "5d")
            if not hist.empty:
                return float(hist["Close"].iloc[-1])
            pair_inv = f"{to_currency}{from_currency}=X"
            hist = self._download_history(pair_inv, "5d")
            if not hist.empty:
                return 1.0 / float(hist["Close"].iloc[-1])
        except Exception:
            pass

        return FX_DEFAULTS.get(from_currency, 1.0)

    def import_portfolio_symbols(self, symbols: list[str]) -> list[dict]:
        holdings = []
        for raw in symbols:
            sym = raw.strip().upper()
            if not sym:
                continue
            quote = self.get_quote(sym)
            holdings.append(
                {
                    "symbol": quote["symbol"],
                    "current_price": quote["price"],
                    "currency": quote["currency"],
                    "name": quote.get("name", sym),
                    "sector": quote.get("sector"),
                }
            )
            time.sleep(0.1)
        return holdings

    def search_symbols(self, query: str) -> list[dict]:
        sym = query.upper().strip()
        if not sym:
            return []
        quote = self.get_quote(sym)
        return [
            {
                "symbol": quote["symbol"],
                "name": quote.get("name", sym),
                "exchange": "DEMO" if quote.get("demo_mode") else "NMS",
                "type": "EQUITY",
            }
        ]


_backend = _YahooFinanceBackend()


class YahooFinanceService:
    """API estática sobre el backend unificado con fallback demo."""

    @staticmethod
    def get_quote(symbol: str) -> Optional[dict]:
        return _backend.get_quote(symbol)

    @staticmethod
    def get_quotes(symbols: list[str]) -> list[dict]:
        return [_backend.get_quote(s) for s in symbols]

    @staticmethod
    def get_historical(symbol: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
        df = _backend.get_historical(symbol, period, interval)
        return df if not df.empty else None

    @staticmethod
    def get_fundamentals(symbol: str) -> dict:
        return _backend.get_fundamentals(symbol)

    @staticmethod
    def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> float:
        return _backend.get_exchange_rate(from_currency, to_currency)

    @staticmethod
    def import_portfolio_symbols(symbols: list[str]) -> list[dict]:
        return _backend.import_portfolio_symbols(symbols)

    @staticmethod
    def search_symbols(query: str) -> list[dict]:
        return _backend.search_symbols(query)

    @staticmethod
    def is_demo_mode() -> bool:
        return _backend.demo_mode
