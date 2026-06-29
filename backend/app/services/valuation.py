from typing import Any

import numpy as np

from app.services.yahoo_finance import YahooFinanceService


class ValuationService:
  """Valoraciones objetivas y valor isotérico (independiente de moneda)."""

  @staticmethod
  def objective_valuation(symbol: str) -> dict[str, Any]:
    """Calcula valoración objetiva usando múltiples métodos."""
    fundamentals = YahooFinanceService.get_fundamentals(symbol)
    quote = YahooFinanceService.get_quote(symbol)
    current_price = quote["price"]

    scores = {}
    valuations = {}

    pe = fundamentals.get("pe_ratio")
    if pe and pe > 0:
      sector_avg_pe = 20
      pe_score = max(0, min(100, 100 - (pe - sector_avg_pe) * 3))
      scores["pe_valuation"] = round(pe_score, 2)
      fair_value_pe = current_price * (sector_avg_pe / pe) if pe else current_price
      valuations["pe_fair_value"] = round(fair_value_pe, 2)

    pb = fundamentals.get("price_to_book")
    if pb and pb > 0:
      pb_score = max(0, min(100, 100 - (pb - 3) * 15))
      scores["pb_valuation"] = round(pb_score, 2)

    peg = fundamentals.get("peg_ratio")
    if peg and peg > 0:
      peg_score = max(0, min(100, 100 - (peg - 1) * 40))
      scores["peg_valuation"] = round(peg_score, 2)

    target = fundamentals.get("target_mean_price")
    if target:
      upside = (target - current_price) / current_price * 100
      scores["analyst_target"] = round(max(0, min(100, 50 + upside)), 2)
      valuations["analyst_fair_value"] = round(target, 2)

    roe = fundamentals.get("roe")
    if roe:
      scores["profitability"] = round(min(100, roe * 300), 2)

    debt_eq = fundamentals.get("debt_to_equity")
    if debt_eq is not None:
      scores["financial_health"] = round(max(0, min(100, 100 - debt_eq / 2)), 2)

    growth = fundamentals.get("earnings_growth")
    if growth:
      scores["growth"] = round(min(100, max(0, 50 + growth * 100)), 2)

    overall = np.mean(list(scores.values())) if scores else 50
    rating = "undervalued" if overall > 65 else "overvalued" if overall < 35 else "fair_value"

    return {
      "symbol": symbol.upper(),
      "current_price": current_price,
      "currency": quote["currency"],
      "objective_score": round(float(overall), 2),
      "rating": rating,
      "component_scores": scores,
      "fair_value_estimates": valuations,
      "fundamentals": fundamentals,
      "recommendation": fundamentals.get("recommendation"),
    }

  @staticmethod
  def isometric_value(symbols: list[str]) -> dict[str, Any]:
    """
    Valor isotérico: normaliza acciones a una escala común independiente de moneda.
    Usa retornos normalizados, fuerza relativa y métricas de valoración ajustadas.
    """
    results = []
    base_currency = "USD"

    for symbol in symbols:
      try:
        quote = YahooFinanceService.get_quote(symbol)
        fundamentals = YahooFinanceService.get_fundamentals(symbol)
        history = YahooFinanceService.get_history(symbol, period="1y")

        currency = quote["currency"]
        fx_rate = YahooFinanceService.get_fx_rate(currency, base_currency)
        price_usd = quote["price"] * fx_rate

        returns = history["Close"].pct_change().dropna()
        volatility = float(returns.std() * np.sqrt(252))
        annual_return = float((history["Close"].iloc[-1] / history["Close"].iloc[0] - 1))

        pe = fundamentals.get("pe_ratio") or 20
        roe = fundamentals.get("roe") or 0.1
        beta = fundamentals.get("beta") or 1.0

        risk_adjusted_return = annual_return / (volatility + 0.01)
        value_score = (1 / pe) * 100 if pe > 0 else 0
        quality_score = roe * 100
        momentum_score = annual_return * 100

        isometric_score = (
          risk_adjusted_return * 30 +
          value_score * 0.25 +
          quality_score * 0.25 +
          momentum_score * 0.20
        ) / (beta * 0.5 + 0.5)

        results.append({
          "symbol": symbol.upper(),
          "name": quote["name"],
          "original_price": quote["price"],
          "original_currency": currency,
          "normalized_price_usd": round(price_usd, 4),
          "isometric_score": round(float(isometric_score), 4),
          "risk_adjusted_return": round(float(risk_adjusted_return), 4),
          "annual_return_pct": round(annual_return * 100, 2),
          "volatility": round(volatility * 100, 2),
          "beta": round(beta, 2),
          "pe_ratio": pe,
          "roe_pct": round(roe * 100, 2) if roe else None,
        })
      except Exception as e:
        results.append({"symbol": symbol.upper(), "error": str(e)})

    valid = [r for r in results if "isometric_score" in r]
    if valid:
      max_score = max(r["isometric_score"] for r in valid)
      min_score = min(r["isometric_score"] for r in valid)
      score_range = max_score - min_score or 1

      for r in valid:
        r["isometric_rank"] = sorted(valid, key=lambda x: x["isometric_score"], reverse=True).index(r) + 1
        r["isometric_normalized"] = round((r["isometric_score"] - min_score) / score_range * 100, 2)

    valid.sort(key=lambda x: x.get("isometric_score", 0), reverse=True)

    return {
      "base_currency": base_currency,
      "methodology": "Valor isotérico: combina retorno ajustado por riesgo, valoración, calidad y momentum, normalizado por beta y convertido a USD",
      "symbols": valid,
      "ranking": [{"rank": i + 1, "symbol": r["symbol"], "score": r.get("isometric_normalized", 0)} for i, r in enumerate(valid)],
      "best_pick": valid[0]["symbol"] if valid else None,
      "worst_pick": valid[-1]["symbol"] if valid else None,
    }

  @staticmethod
  def special_metrics(symbol: str) -> dict[str, Any]:
    """Métricas especiales avanzadas para una acción."""
    fundamentals = YahooFinanceService.get_fundamentals(symbol)
    quote = YahooFinanceService.get_quote(symbol)
    history = YahooFinanceService.get_history(symbol, period="2y")

    closes = history["Close"]
    returns = closes.pct_change().dropna()

    sharpe = float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    max_drawdown = float((closes / closes.cummax() - 1).min())
    sortino_downside = returns[returns < 0].std()
    sortino = float(returns.mean() / sortino_downside * np.sqrt(252)) if sortino_downside > 0 else 0

    sma_200 = closes.rolling(200).mean()
    above_sma200 = float(closes.iloc[-1] > sma_200.iloc[-1]) if len(closes) >= 200 else None

    return {
      "symbol": symbol.upper(),
      "sharpe_ratio": round(sharpe, 4),
      "sortino_ratio": round(sortino, 4),
      "max_drawdown_pct": round(max_drawdown * 100, 2),
      "above_sma_200": bool(above_sma200) if above_sma200 is not None else None,
      "volatility_annual_pct": round(float(returns.std() * np.sqrt(252) * 100), 2),
      "market_cap": fundamentals.get("market_cap"),
      "enterprise_value": fundamentals.get("enterprise_value"),
      "ev_to_revenue": fundamentals.get("ev_to_revenue"),
      "ev_to_ebitda": fundamentals.get("ev_to_ebitda"),
      "free_cashflow": fundamentals.get("free_cashflow"),
      "fcf_yield": round(fundamentals.get("free_cashflow", 0) / fundamentals.get("market_cap", 1) * 100, 4) if fundamentals.get("market_cap") else None,
      "dividend_yield_pct": round((fundamentals.get("dividend_yield") or 0) * 100, 2),
      "quality_score": round(
        (fundamentals.get("roe") or 0) * 50 +
        (1 / (fundamentals.get("debt_to_equity") or 1 + 1)) * 25 +
        (fundamentals.get("profit_margin") or 0) * 25,
        2
      ),
      "current_price": quote["price"],
    }
