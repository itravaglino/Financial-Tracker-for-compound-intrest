import logging
from typing import Optional

import numpy as np
import pandas as pd

from app.services.yahoo_finance import yahoo_service

logger = logging.getLogger(__name__)


class ValuationService:
    def calculate_dcf(self, symbol: str) -> Optional[float]:
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.info
            fcf = info.get("freeCashflow")
            if not fcf or fcf <= 0:
                return None

            growth_rate = min(info.get("earningsGrowth", 0.05) or 0.05, 0.15)
            discount_rate = 0.10
            terminal_growth = 0.025
            shares = info.get("sharesOutstanding", 1)

            pv = 0
            projected_fcf = fcf
            for year in range(1, 6):
                projected_fcf *= 1 + growth_rate
                pv += projected_fcf / ((1 + discount_rate) ** year)

            terminal_value = projected_fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
            pv += terminal_value / ((1 + discount_rate) ** 5)
            return round(pv / shares, 2)
        except Exception as e:
            logger.warning("DCF error for %s: %s", symbol, e)
            return None

    def get_valuation(self, symbol: str) -> dict:
        import yfinance as yf

        from app.services.yahoo_finance import yahoo_service

        quote = yahoo_service.get_quote(symbol)
        current_price = quote["price"]

        pe = None
        peg = None
        dcf = None
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            pe = info.get("trailingPE") or info.get("forwardPE")
            peg = info.get("pegRatio")
            dcf = self.calculate_dcf(symbol)
        except Exception as e:
            logger.warning("Valuation info unavailable for %s: %s", symbol, e)

        fair_values = []
        if pe and pe > 0:
            sector_pe = info.get("trailingPE") or 20
            avg_pe = 18
            fair_values.append(current_price * (avg_pe / pe))
        if dcf:
            fair_values.append(dcf)

        if fair_values:
            fair_value = float(np.mean(fair_values))
        else:
            fair_value = current_price

        upside = ((fair_value - current_price) / current_price * 100) if current_price else 0

        if upside > 20:
            recommendation = "COMPRAR"
            confidence = min(0.95, 0.6 + upside / 100)
        elif upside > 5:
            recommendation = "MANTENER"
            confidence = 0.65
        elif upside > -10:
            recommendation = "NEUTRAL"
            confidence = 0.55
        else:
            recommendation = "VENDER"
            confidence = min(0.9, 0.6 + abs(upside) / 100)

        return {
            "symbol": symbol.upper(),
            "fair_value": round(fair_value, 2),
            "current_price": current_price,
            "upside_percent": round(upside, 2),
            "pe_ratio": round(pe, 2) if pe else None,
            "peg_ratio": round(peg, 2) if peg else None,
            "dcf_value": dcf,
            "recommendation": recommendation,
            "confidence": round(confidence, 2),
        }


valuation_service = ValuationService()
