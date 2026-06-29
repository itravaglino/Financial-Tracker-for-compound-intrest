import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class YahooFinanceService:
    """Servicio de datos en tiempo real desde Yahoo Finance."""

    @staticmethod
    def get_quote(symbol: str) -> Optional[dict]:
        try:
            ticker = yf.Ticker(symbol.upper())
            info = ticker.info
            hist = ticker.history(period="2d")
            if hist.empty:
                return None

            current = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
            change = current - prev
            change_pct = (change / prev * 100) if prev else 0

            return {
                "symbol": symbol.upper(),
                "price": current,
                "change": round(change, 4),
                "change_percent": round(change_pct, 2),
                "volume": int(hist["Volume"].iloc[-1]),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency", "USD"),
                "name": info.get("longName") or info.get("shortName", symbol),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "timestamp": datetime.utcnow(),
            }
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None

    @staticmethod
    def get_quotes(symbols: list[str]) -> list[dict]:
        results = []
        for symbol in symbols:
            quote = YahooFinanceService.get_quote(symbol)
            if quote:
                results.append(quote)
        return results

    @staticmethod
    def get_historical(symbol: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
        try:
            ticker = yf.Ticker(symbol.upper())
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                return None
            return df
        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {e}")
            return None

    @staticmethod
    def get_fundamentals(symbol: str) -> dict:
        try:
            ticker = yf.Ticker(symbol.upper())
            info = ticker.info
            return {
                "symbol": symbol.upper(),
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
            }
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return {"symbol": symbol.upper()}

    @staticmethod
    def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> float:
        if from_currency == to_currency:
            return 1.0
        try:
            pair = f"{from_currency}{to_currency}=X"
            ticker = yf.Ticker(pair)
            hist = ticker.history(period="1d")
            if not hist.empty:
                return float(hist["Close"].iloc[-1])
            pair_inv = f"{to_currency}{from_currency}=X"
            ticker = yf.Ticker(pair_inv)
            hist = ticker.history(period="1d")
            if not hist.empty:
                return 1.0 / float(hist["Close"].iloc[-1])
        except Exception:
            pass
        return 1.0

    @staticmethod
    def import_portfolio_symbols(symbols: list[str]) -> list[dict]:
        """Importa datos de símbolos para crear un portfolio desde Yahoo Finance."""
        holdings = []
        for symbol in symbols:
            quote = YahooFinanceService.get_quote(symbol.strip().upper())
            if quote:
                holdings.append({
                    "symbol": quote["symbol"],
                    "current_price": quote["price"],
                    "currency": quote["currency"],
                    "name": quote.get("name", symbol),
                    "sector": quote.get("sector"),
                })
        return holdings

    @staticmethod
    def search_symbols(query: str) -> list[dict]:
        try:
            # yfinance doesn't have a search API, use common validation
            ticker = yf.Ticker(query.upper())
            info = ticker.info
            if info.get("regularMarketPrice") or info.get("currentPrice"):
                return [{
                    "symbol": query.upper(),
                    "name": info.get("longName") or info.get("shortName", query),
                    "exchange": info.get("exchange"),
                    "type": info.get("quoteType"),
                }]
        except Exception:
            pass
        return []
