from typing import Any

import numpy as np
import pandas as pd

from app.services.yahoo_finance import YahooFinanceService


class TechnicalAnalysisService:
  """Análisis técnico avanzado con indicadores y patrones Fibonacci."""

  @staticmethod
  def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

  @staticmethod
  def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

  @staticmethod
  def calculate_bollinger(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> dict:
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    return {
      "upper": sma + std_dev * std,
      "middle": sma,
      "lower": sma - std_dev * std,
    }

  @staticmethod
  def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

  @staticmethod
  def fibonacci_levels(high: float, low: float) -> dict[str, float]:
    diff = high - low
    levels = {
      "0.0": high,
      "0.236": high - diff * 0.236,
      "0.382": high - diff * 0.382,
      "0.5": high - diff * 0.5,
      "0.618": high - diff * 0.618,
      "0.786": high - diff * 0.786,
      "1.0": low,
      "1.272": low - diff * 0.272,
      "1.618": low - diff * 0.618,
    }
    return levels

  @staticmethod
  def detect_fibonacci_patterns(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Detecta retrocesos y extensiones Fibonacci en el precio."""
    patterns = []
    prices = df["Close"].values
    if len(prices) < 50:
      return patterns

    window = 20
    for i in range(window, len(prices) - window):
      segment = prices[i - window : i + window]
      local_high = segment.max()
      local_low = segment.min()
      current = prices[i]

      if local_high == local_low:
        continue

      levels = TechnicalAnalysisService.fibonacci_levels(local_high, local_low)
      for level_name, level_price in levels.items():
        tolerance = (local_high - local_low) * 0.02
        if abs(current - level_price) <= tolerance:
          patterns.append({
            "type": "fibonacci_retracement",
            "level": level_name,
            "price": round(level_price, 4),
            "current_price": round(current, 4),
            "index": i,
            "signal": "support" if current > level_price else "resistance",
          })
    return patterns[-10:]

  @staticmethod
  def detect_chart_patterns(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Detecta patrones de velas y formaciones básicas."""
    patterns = []
    closes = df["Close"].values
    highs = df["High"].values
    lows = df["Low"].values

    if len(closes) < 5:
      return patterns

    for i in range(2, len(closes) - 2):
      if highs[i] > highs[i - 1] and highs[i] > highs[i + 1] and highs[i] > highs[i - 2] and highs[i] > highs[i + 2]:
        patterns.append({"type": "double_top_candidate", "index": i, "price": float(highs[i])})
      if lows[i] < lows[i - 1] and lows[i] < lows[i + 1] and lows[i] < lows[i - 2] and lows[i] < lows[i + 2]:
        patterns.append({"type": "double_bottom_candidate", "index": i, "price": float(lows[i])})

    return patterns[-5:]

  @staticmethod
  def full_analysis(symbol: str, period: str = "1y") -> dict[str, Any]:
    df = YahooFinanceService.get_history(symbol, period=period)
    closes = df["Close"]
    current_price = float(closes.iloc[-1])

    rsi = TechnicalAnalysisService.calculate_rsi(closes)
    macd = TechnicalAnalysisService.calculate_macd(closes)
    bollinger = TechnicalAnalysisService.calculate_bollinger(closes)
    atr = TechnicalAnalysisService.calculate_atr(df)

    rsi_val = float(rsi.iloc[-1]) if not rsi.isna().iloc[-1] else 50
    macd_val = float(macd["macd"].iloc[-1]) if not macd["macd"].isna().iloc[-1] else 0
    signal_val = float(macd["signal"].iloc[-1]) if not macd["signal"].isna().iloc[-1] else 0

    high_52 = float(df["High"].max())
    low_52 = float(df["Low"].min())
    fib_levels = TechnicalAnalysisService.fibonacci_levels(high_52, low_52)

    signals = []
    if rsi_val < 30:
      signals.append({"indicator": "RSI", "signal": "oversold", "value": rsi_val})
    elif rsi_val > 70:
      signals.append({"indicator": "RSI", "signal": "overbought", "value": rsi_val})

    if macd_val > signal_val:
      signals.append({"indicator": "MACD", "signal": "bullish_crossover", "value": macd_val})
    else:
      signals.append({"indicator": "MACD", "signal": "bearish_crossover", "value": macd_val})

    bb_upper = float(bollinger["upper"].iloc[-1]) if not bollinger["upper"].isna().iloc[-1] else current_price
    bb_lower = float(bollinger["lower"].iloc[-1]) if not bollinger["lower"].isna().iloc[-1] else current_price

    if current_price <= bb_lower:
      signals.append({"indicator": "Bollinger", "signal": "below_lower_band", "value": current_price})
    elif current_price >= bb_upper:
      signals.append({"indicator": "Bollinger", "signal": "above_upper_band", "value": current_price})

    fib_patterns = TechnicalAnalysisService.detect_fibonacci_patterns(df)
    chart_patterns = TechnicalAnalysisService.detect_chart_patterns(df)

    sma_20 = float(closes.rolling(20).mean().iloc[-1])
    sma_50 = float(closes.rolling(50).mean().iloc[-1]) if len(closes) >= 50 else sma_20
    sma_200 = float(closes.rolling(200).mean().iloc[-1]) if len(closes) >= 200 else sma_50

    trend = "bullish" if current_price > sma_50 > sma_200 else "bearish" if current_price < sma_50 < sma_200 else "neutral"

    return {
      "symbol": symbol.upper(),
      "current_price": current_price,
      "rsi": round(rsi_val, 2),
      "macd": round(macd_val, 4),
      "macd_signal": round(signal_val, 4),
      "macd_histogram": round(macd_val - signal_val, 4),
      "bollinger_upper": round(bb_upper, 2),
      "bollinger_middle": round(float(bollinger["middle"].iloc[-1]), 2) if not bollinger["middle"].isna().iloc[-1] else current_price,
      "bollinger_lower": round(bb_lower, 2),
      "atr": round(float(atr.iloc[-1]), 4) if not atr.isna().iloc[-1] else 0,
      "sma_20": round(sma_20, 2),
      "sma_50": round(sma_50, 2),
      "sma_200": round(sma_200, 2),
      "trend": trend,
      "fibonacci_levels": {k: round(v, 2) for k, v in fib_levels.items()},
      "fibonacci_patterns": fib_patterns,
      "chart_patterns": chart_patterns,
      "signals": signals,
      "history": {
        "dates": [d.strftime("%Y-%m-%d") for d in df.index[-90:]],
        "close": [round(float(v), 2) for v in closes.iloc[-90:]],
        "volume": [int(v) for v in df["Volume"].iloc[-90:]],
      },
    }

  @staticmethod
  def portfolio_contrast(symbols: list[str]) -> dict[str, Any]:
    """Contrasta análisis técnico de múltiples acciones del portfolio."""
    analyses = {}
    for symbol in symbols:
      try:
        analyses[symbol.upper()] = TechnicalAnalysisService.full_analysis(symbol)
      except Exception as e:
        analyses[symbol.upper()] = {"error": str(e)}

    bullish = sum(1 for a in analyses.values() if a.get("trend") == "bullish")
    bearish = sum(1 for a in analyses.values() if a.get("trend") == "bearish")
    neutral = len(analyses) - bullish - bearish

    avg_rsi = np.mean([a.get("rsi", 50) for a in analyses.values() if "rsi" in a])

    return {
      "symbols_analyzed": len(analyses),
      "bullish_count": bullish,
      "bearish_count": bearish,
      "neutral_count": neutral,
      "portfolio_sentiment": "bullish" if bullish > bearish else "bearish" if bearish > bullish else "neutral",
      "average_rsi": round(float(avg_rsi), 2),
      "individual_analysis": analyses,
    }
