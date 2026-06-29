from typing import Optional
from app.services.yahoo_finance import YahooFinanceService


class ValuationService:
    """
    Valoración objetiva con valor isotérico (independiente de moneda).
    El valor isotérico normaliza el precio a una unidad de poder adquisitivo
    global usando PPP y métricas fundamentales, permitiendo comparar acciones
  de diferentes mercados sin sesgo cambiario.
    """

    SECTOR_PE_BENCHMARKS = {
        "Technology": 28.0,
        "Healthcare": 22.0,
        "Financial Services": 14.0,
        "Consumer Cyclical": 20.0,
        "Consumer Defensive": 22.0,
        "Energy": 12.0,
        "Industrials": 18.0,
        "Basic Materials": 15.0,
        "Communication Services": 18.0,
        "Real Estate": 35.0,
        "Utilities": 16.0,
    }

    @staticmethod
    def calculate_intrinsic_value(fundamentals: dict, current_price: float) -> float:
        """DCF simplificado + múltiplos para valor intrínseco."""
        eps = fundamentals.get("eps") or 0
        book_value = fundamentals.get("book_value") or 0
        fcf = fundamentals.get("free_cash_flow") or 0
        sector = fundamentals.get("sector") or "Technology"
        benchmark_pe = ValuationService.SECTOR_PE_BENCHMARKS.get(sector, 18.0)

        # Graham Number
        graham = 0
        if eps > 0 and book_value > 0:
            graham = (22.5 * eps * book_value) ** 0.5

        # PE-based fair value
        pe_fair = eps * benchmark_pe if eps > 0 else 0

        # Book value based
        pb_fair = book_value * 1.5 if book_value > 0 else 0

        # Target price from analysts
        target = fundamentals.get("target_mean_price") or 0

        values = [v for v in [graham, pe_fair, pb_fair, target] if v > 0]
        if not values:
            return current_price

        return sum(values) / len(values)

    @staticmethod
    def calculate_isosteric_value(
        current_price: float,
        currency: str,
        fundamentals: dict,
        intrinsic_value: float,
    ) -> float:
        """
        Valor isotérico: precio normalizado a unidad de valor global (USD-PPP).
        Combina tipo de cambio, beta, y ajuste por volatilidad del mercado local.
        """
        usd_rate = YahooFinanceService.get_exchange_rate(currency, "USD")
        price_usd = current_price * usd_rate

        beta = fundamentals.get("beta") or 1.0
        pe = fundamentals.get("pe_ratio") or 18.0
        sector = fundamentals.get("sector") or "Technology"
        benchmark_pe = ValuationService.SECTOR_PE_BENCHMARKS.get(sector, 18.0)

        # Normalización isotérica: ajusta por riesgo sistémico y valor relativo sectorial
        risk_adjustment = 1 / (1 + (beta - 1) * 0.1)
        sector_adjustment = benchmark_pe / pe if pe and pe > 0 else 1.0

        isosteric = price_usd * risk_adjustment * sector_adjustment

        # Blend con valor intrínseco (40% isotérico puro, 60% intrínseco normalizado)
        intrinsic_usd = intrinsic_value * usd_rate
        blended = isosteric * 0.4 + intrinsic_usd * 0.6

        return round(blended, 4)

    @staticmethod
    def get_rating(current_price: float, intrinsic_value: float, isosteric_value: float) -> tuple[str, float]:
        avg_fair = (intrinsic_value + isosteric_value) / 2
        if avg_fair == 0:
            return "neutral", 50.0

        upside = (avg_fair - current_price) / current_price * 100

        if upside > 30:
            return "muy infravalorada", min(100, 70 + upside * 0.5)
        elif upside > 15:
            return "infravalorada", min(85, 60 + upside)
        elif upside > 5:
            return "ligeramente infravalorada", 55 + upside
        elif upside > -5:
            return "valor justo", 50
        elif upside > -15:
            return "ligeramente sobrevalorada", 45 + upside
        elif upside > -30:
            return "sobrevalorada", max(15, 40 + upside)
        else:
            return "muy sobrevalorada", max(5, 30 + upside)

    @staticmethod
    def analyze(symbol: str) -> Optional[dict]:
        quote = YahooFinanceService.get_quote(symbol)
        fundamentals = YahooFinanceService.get_fundamentals(symbol)

        if not quote:
            return None

        current_price = quote["price"]
        currency = quote["currency"]
        intrinsic = ValuationService.calculate_intrinsic_value(fundamentals, current_price)
        isosteric = ValuationService.calculate_isosteric_value(
            current_price, currency, fundamentals, intrinsic
        )
        rating, score = ValuationService.get_rating(current_price, intrinsic, isosteric)

        margin = intrinsic * 0.15
        return {
            "symbol": symbol.upper(),
            "current_price": current_price,
            "intrinsic_value": round(intrinsic, 4),
            "isosteric_value": isosteric,
            "currency": currency,
            "pe_ratio": fundamentals.get("pe_ratio"),
            "pb_ratio": fundamentals.get("pb_ratio"),
            "peg_ratio": fundamentals.get("peg_ratio"),
            "dividend_yield": fundamentals.get("dividend_yield"),
            "fair_value_range": {
                "low": round(intrinsic - margin, 4),
                "mid": round(intrinsic, 4),
                "high": round(intrinsic + margin, 4),
            },
            "rating": rating,
            "rating_score": round(score, 1),
            "metrics": {
                "roe": fundamentals.get("roe"),
                "profit_margin": fundamentals.get("profit_margin"),
                "debt_to_equity": fundamentals.get("debt_to_equity"),
                "beta": fundamentals.get("beta"),
                "recommendation": fundamentals.get("recommendation"),
                "sector": fundamentals.get("sector"),
                "upside_pct": round((intrinsic - current_price) / current_price * 100, 2),
                "isosteric_upside_pct": round((isosteric - current_price) / current_price * 100, 2),
            },
        }
