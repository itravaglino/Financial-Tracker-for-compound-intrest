import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.ml.technical_analysis import technical_service
from app.models import Holding, Portfolio
from app.services.valuation import valuation_service
from app.services.yahoo_finance import yahoo_service

logger = logging.getLogger(__name__)


class PortfolioService:
    def analyze_portfolio(self, db: Session, portfolio_id: int, user_id: int) -> dict:
        portfolio = (
            db.query(Portfolio)
            .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
            .first()
        )
        if not portfolio:
            raise ValueError("Portfolio no encontrado")

        total_value = 0.0
        total_cost = 0.0
        holdings_analysis = []
        sectors: dict[str, float] = {}

        for holding in portfolio.holdings:
            try:
                quote = yahoo_service.get_quote(holding.symbol)
                iso = yahoo_service.get_isometric_value(holding.symbol)
                valuation = valuation_service.get_valuation(holding.symbol)
                technical = technical_service.analyze(holding.symbol)

                price_usd = iso["price_usd"]
                value = price_usd * holding.quantity
                cost = yahoo_service.convert_to_usd(holding.avg_cost, holding.currency) * holding.quantity
                gain = value - cost
                gain_pct = (gain / cost * 100) if cost else 0

                total_value += value
                total_cost += cost

                sector = quote.get("sector", "Unknown")
                sectors[sector] = sectors.get(sector, 0) + value

                holdings_analysis.append({
                    "symbol": holding.symbol,
                    "quantity": holding.quantity,
                    "current_price": quote["price"],
                    "price_usd": price_usd,
                    "price_normalized": iso["price_normalized"],
                    "value_usd": round(value, 2),
                    "gain_loss": round(gain, 2),
                    "gain_loss_percent": round(gain_pct, 2),
                    "valuation": valuation,
                    "technical": {
                        "rsi": technical["rsi"],
                        "trend": technical["trend"],
                        "signal": technical["signal"],
                        "pattern": technical["pattern_detected"],
                    },
                    "sector": sector,
                })
            except Exception as e:
                logger.warning("Error analyzing %s: %s", holding.symbol, e)

        sector_allocation = {
            k: round(v / total_value * 100, 2) if total_value else 0
            for k, v in sectors.items()
        }

        symbols = [h.symbol for h in portfolio.holdings]
        comparison = technical_service.compare_symbols(symbols) if symbols else []

        n = len(holdings_analysis)
        diversification = min(100, n * 15) if n else 0
        avg_volatility = sum(
            abs(h.get("gain_loss_percent", 0)) for h in holdings_analysis
        ) / max(n, 1)
        risk_score = min(100, avg_volatility * 2)

        return {
            "total_value_usd": round(total_value, 2),
            "total_gain_loss": round(total_value - total_cost, 2),
            "gain_loss_percent": round(
                (total_value - total_cost) / total_cost * 100 if total_cost else 0, 2
            ),
            "holdings_analysis": holdings_analysis,
            "sector_allocation": sector_allocation,
            "risk_score": round(risk_score, 2),
            "diversification_score": round(diversification, 2),
            "comparison": comparison,
        }


portfolio_service = PortfolioService()
