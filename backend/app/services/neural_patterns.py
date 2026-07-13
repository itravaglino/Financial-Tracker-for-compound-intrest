import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from typing import Optional
from app.services.yahoo_finance import YahooFinanceService
from app.services.technical_analysis import TechnicalAnalysisService


class NeuralPatternService:
  """Red neuronal para detección de patrones Fibonacci y predicción de tendencias."""

  @staticmethod
  def _extract_features(df: pd.DataFrame) -> np.ndarray:
    closes = df["Close"].values
    volumes = df["Volume"].values
    features = []

    for i in range(20, len(closes)):
      window = closes[i - 20:i]
      vol_window = volumes[i - 20:i]

      returns = np.diff(window) / window[:-1]
      features.append([
        np.mean(returns),
        np.std(returns),
        returns[-1],
        (window[-1] - window[0]) / window[0],
        window[-1] / np.mean(window) - 1,
        np.mean(vol_window) / (vol_window[-1] + 1),
        NeuralPatternService._fibonacci_proximity(window),
        NeuralPatternService._golden_ratio_score(window),
        NeuralPatternService._momentum_score(window),
        NeuralPatternService._volatility_regime(window),
      ])

    return np.array(features)

  @staticmethod
  def _fibonacci_proximity(prices: np.ndarray) -> float:
    high, low = prices.max(), prices.min()
    if high == low:
      return 0.0
    current = prices[-1]
    levels = [high - (high - low) * r for r in [0.236, 0.382, 0.5, 0.618, 0.786]]
    min_dist = min(abs(current - l) / current for l in levels)
    return max(0, 1 - min_dist * 20)

  @staticmethod
  def _golden_ratio_score(prices: np.ndarray) -> float:
    if len(prices) < 13:
      return 0.0
    short = np.mean(prices[-8:])
    long = np.mean(prices[-13:])
    if long == 0:
      return 0.0
    ratio = short / long
    return max(0, 1 - abs(ratio - 1.618) * 5)

  @staticmethod
  def _momentum_score(prices: np.ndarray) -> float:
    if len(prices) < 10:
      return 0.0
    return (prices[-1] - prices[-10]) / prices[-10]

  @staticmethod
  def _volatility_regime(prices: np.ndarray) -> float:
    returns = np.diff(prices) / prices[:-1]
    return float(np.std(returns))

  @staticmethod
  def detect_patterns(symbol: str) -> Optional[dict]:
    df = YahooFinanceService.get_historical(symbol, period="2y")
    if df is None or len(df) < 60:
      return None

    closes = df["Close"].values
    features = NeuralPatternService._extract_features(df)

    if len(features) < 30:
      return None

    # Labels: 1 if price goes up in next 5 days, 0 otherwise
    labels = []
    for i in range(20, len(closes) - 5):
      future_return = (closes[i + 5] - closes[i]) / closes[i]
      labels.append(1 if future_return > 0.01 else 0)

    labels = np.array(labels)
    X = features[:len(labels)]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    split = int(len(X_scaled) * 0.8)
    X_train, X_test = X_scaled[:split], X_scaled[split:]
    y_train, y_test = labels[:split], labels[split:]

    model = MLPClassifier(
      hidden_layer_sizes=(64, 32, 16),
      activation="relu",
      max_iter=300,
      random_state=42,
      early_stopping=True,
      validation_fraction=0.1,
    )
    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test) if len(X_test) > 0 else 0.5
    latest_features = scaler.transform(features[-1:])
    prediction = model.predict(latest_features)[0]
    proba = model.predict_proba(latest_features)[0]
    confidence = float(max(proba))

    # Pattern detection
    patterns = TechnicalAnalysisService.detect_fibonacci_patterns(df)

    # Additional neural-detected patterns
    recent = closes[-20:]
    returns = np.diff(recent) / recent[:-1]

    if np.std(returns) < 0.01 and abs(recent[-1] - recent[0]) / recent[0] < 0.03:
      patterns.append({
        "type": "consolidation",
        "strength": "moderate",
        "neural_confidence": round(confidence, 3),
      })

    if len(returns) >= 5:
      recent_trend = np.mean(returns[-5:])
      prior_trend = np.mean(returns[-10:-5])
      if recent_trend > 0 and prior_trend < 0 and abs(recent_trend) > abs(prior_trend):
        patterns.append({
          "type": "reversal_bullish",
          "strength": "strong" if confidence > 0.7 else "moderate",
          "neural_confidence": round(confidence, 3),
        })
      elif recent_trend < 0 and prior_trend > 0 and abs(recent_trend) > abs(prior_trend):
        patterns.append({
          "type": "reversal_bearish",
          "strength": "strong" if confidence > 0.7 else "moderate",
          "neural_confidence": round(confidence, 3),
        })

    # Head and shoulders approximation via peaks
    peaks = NeuralPatternService._find_peaks(closes[-60:])
    if len(peaks) >= 3:
      left, head, right = peaks[-3], peaks[-2], peaks[-1]
      if closes[head] > closes[left] and closes[head] > closes[right]:
        if abs(closes[left] - closes[right]) / closes[head] < 0.05:
          patterns.append({
            "type": "head_and_shoulders",
            "strength": "strong",
            "neural_confidence": round(confidence, 3),
          })

    recent_high = float(df["High"].tail(60).max())
    recent_low = float(df["Low"].tail(60).min())
    fib_retracements = TechnicalAnalysisService.calculate_fibonacci_levels(recent_high, recent_low)

    return {
      "symbol": symbol.upper(),
      "patterns": patterns,
      "fibonacci_retracements": fib_retracements,
      "neural_confidence": round(confidence, 3),
      "neural_accuracy": round(accuracy, 3),
      "prediction_direction": "alcista" if prediction == 1 else "bajista",
      "prediction_confidence": round(confidence * 100, 1),
    }

  @staticmethod
  def _find_peaks(data: np.ndarray, distance: int = 5) -> list[int]:
    peaks = []
    for i in range(distance, len(data) - distance):
      if data[i] == max(data[i - distance:i + distance + 1]):
        peaks.append(i)
    return peaks

  @staticmethod
  def compare_portfolio(symbols: list[str]) -> dict:
    """Contrasta análisis técnico y patrones entre acciones del portfolio."""
    results = []
    correlations = {}

    price_data = {}
    for symbol in symbols:
      df = YahooFinanceService.get_historical(symbol, period="6mo")
      if df is not None and len(df) > 20:
        price_data[symbol] = df["Close"].pct_change().dropna()

    if len(price_data) >= 2:
      combined = pd.DataFrame(price_data)
      corr_matrix = combined.corr()
      correlations = {
        f"{a}-{b}": round(float(corr_matrix.loc[a, b]), 3)
        for a in corr_matrix.columns
        for b in corr_matrix.columns
        if a < b
      }

    for symbol in symbols:
      ta = TechnicalAnalysisService.analyze(symbol)
      patterns = NeuralPatternService.detect_patterns(symbol)
      if ta:
        results.append({
          "symbol": symbol,
          "trend": ta["trend"],
          "rsi": ta["rsi"],
          "signals": ta["signals"][:3],
          "patterns": patterns["patterns"][:3] if patterns else [],
          "prediction": patterns["prediction_direction"] if patterns else "neutral",
          "confidence": patterns["prediction_confidence"] if patterns else 0,
        })

    sectors = {}
    for symbol in symbols:
      fund = YahooFinanceService.get_fundamentals(symbol)
      sector = fund.get("sector") or "Desconocido"
      sectors[sector] = sectors.get(sector, 0) + 1

    recommendations = []
    bullish = [r for r in results if r.get("prediction") == "alcista"]
    bearish = [r for r in results if r.get("prediction") == "bajista"]

    if len(bearish) > len(bullish):
      recommendations.append("Mayoría de posiciones con señal bajista — considerar reducir exposición")
    if len(bullish) > len(symbols) * 0.6:
      recommendations.append("Portfolio con fuerte momentum alcista — oportunidad de acumulación")

    high_corr = [k for k, v in correlations.items() if v > 0.8]
    if high_corr:
      recommendations.append(f"Alta correlación detectada ({', '.join(high_corr[:3])}) — diversificar")

    diversification = min(100, len(sectors) * 20 + len(symbols) * 5)
    risk_score = min(100, sum(1 for r in results if r.get("rsi", 50) > 70 or r.get("rsi", 50) < 30) * 15)

    return {
      "holdings_analysis": results,
      "sector_allocation": sectors,
      "correlation_matrix": correlations,
      "risk_score": round(risk_score, 1),
      "diversification_score": round(diversification, 1),
      "recommendations": recommendations,
    }
