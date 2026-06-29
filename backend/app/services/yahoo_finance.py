from datetime import datetime
from typing import Any

import pandas as pd
import yfinance as yf

from app.services.demo_data import demo_fundamentals, demo_history, demo_quote


def _safe_info(ticker: yf.Ticker) -> dict[str, Any]:
    try:
        info = ticker.info
        if info and isinstance(info, dict) and info.get("regularMarketPrice") or info.get("currentPrice"):
            return info
    except Exception:
        pass
    return {}


def _price_from_history(symbol: str, period: str = "5d", interval: str = "1d") -> pd.DataFrame:
    df = yf.download(symbol.upper(), period=period, interval=interval, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


class YahooFinanceService:
    """Servicio de datos de mercado en tiempo real vía Yahoo Finance."""

    @staticmethod
    def get_quote(symbol: str) -> dict[str, Any]:
        sym = symbol.upper()
        try:
            ticker = yf.Ticker(sym)
            info = _safe_info(ticker)

            hist = _price_from_history(sym, period="5d", interval="1d")
            if hist.empty:
                hist = ticker.history(period="5d", interval="1d")

            if not hist.empty:
                current = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
                change = current - prev
                change_pct = (change / prev * 100) if prev else 0
            else:
                current = info.get("currentPrice") or info.get("regularMarketPrice", 0)
                change = info.get("regularMarketChange", 0)
                change_pct = info.get("regularMarketChangePercent", 0)

            if not current:
                raise ValueError("No price data")

            return {
                "symbol": sym,
                "name": info.get("longName") or info.get("shortName", sym),
                "price": round(float(current), 4),
                "currency": info.get("currency", "USD"),
                "change": round(float(change or 0), 4),
                "change_pct": round(float(change_pct or 0), 4),
                "volume": info.get("regularMarketVolume", int(hist["Volume"].iloc[-1]) if not hist.empty else 0),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "timestamp": datetime.utcnow().isoformat(),
                "demo_mode": False,
            }
        except Exception:
            return demo_quote(sym)

    @staticmethod
    def get_history(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        try:
            df = _price_from_history(symbol, period=period, interval=interval)
            if df.empty:
                ticker = yf.Ticker(symbol.upper())
                df = ticker.history(period=period, interval=interval)
            if df.empty:
                raise ValueError("No data")
            return df
        except Exception:
            return demo_history(symbol, period=period, interval=interval)

    @staticmethod
    def get_multiple_quotes(symbols: list[str]) -> list[dict[str, Any]]:
        return [YahooFinanceService.get_quote(s) for s in symbols]

    @staticmethod
    def import_portfolio(symbols: list[str]) -> list[dict[str, Any]]:
        holdings = []
        for symbol in symbols:
            try:
                quote = YahooFinanceService.get_quote(symbol)
                holdings.append({
                    "symbol": quote["symbol"],
                    "name": quote["name"],
                    "price": quote["price"],
                    "currency": quote["currency"],
                    "sector": quote["sector"],
                    "pe_ratio": quote["pe_ratio"],
                    "market_cap": quote["market_cap"],
                })
            except Exception:
                holdings.append({"symbol": symbol.upper(), "error": "No se pudo obtener datos"})
        return holdings

    @staticmethod
    def get_fundamentals(symbol: str) -> dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol.upper())
            info = _safe_info(ticker)
            if not info:
                raise ValueError("No fundamentals")
            return {
                "symbol": symbol.upper(),
                "name": info.get("longName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "ev_to_revenue": info.get("enterpriseToRevenue"),
                "ev_to_ebitda": info.get("enterpriseToEbitda"),
                "profit_margin": info.get("profitMargins"),
                "operating_margin": info.get("operatingMargins"),
                "roe": info.get("returnOnEquity"),
                "roa": info.get("returnOnAssets"),
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "free_cashflow": info.get("freeCashflow"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "target_mean_price": info.get("targetMeanPrice"),
                "recommendation": info.get("recommendationKey"),
                "analyst_count": info.get("numberOfAnalystOpinions"),
                "demo_mode": False,
            }
        except Exception:
            return demo_fundamentals(symbol)

    @staticmethod
    def get_fx_rate(from_currency: str, to_currency: str = "USD") -> float:
        if from_currency == to_currency:
            return 1.0
        pair = f"{from_currency}{to_currency}=X"
        try:
            hist = _price_from_history(pair, period="5d", interval="1d")
            if not hist.empty:
                return float(hist["Close"].iloc[-1])
        except Exception:
            pass
        return 1.0
