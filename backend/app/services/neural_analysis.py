from typing import Any

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from app.services.technical_analysis import TechnicalAnalysisService
from app.services.yahoo_finance import YahooFinanceService


class NeuralAnalysisService:
  """Red neuronal para detección de patrones Fibonacci y predicción de tendencias."""

  PATTERN_LABELS = ["bullish", "bearish", "neutral", "fibonacci_support", "fibonacci_resistance"]

  @staticmethod
  def _extract_features(df: pd.DataFrame) -> np.ndarray:
    closes = df["Close"]
    features = []

    rsi = TechnicalAnalysisService.calculate_rsi(closes)
    macd = TechnicalAnalysisService.calculate_macd(closes)
    bollinger = TechnicalAnalysisService.calculate_bollinger(closes)
    atr = TechnicalAnalysisService.calculate_atr(df)

    sma_20 = closes.rolling(20).mean()
    sma_50 = closes.rolling(50).mean()

    for i in range(50, len(closes)):
      row = [
        float(rsi.iloc[i]) if not np.isnan(rsi.iloc[i]) else 50,
        float(macd["macd"].iloc[i]) if not np.isnan(macd["macd"].iloc[i]) else 0,
        float(macd["histogram"].iloc[i]) if not np.isnan(macd["histogram"].iloc[i]) else 0,
        float((closes.iloc[i] - bollinger["lower"].iloc[i]) / (bollinger["upper"].iloc[i] - bollinger["lower"].iloc[i] + 1e-10)),
        float(atr.iloc[i] / closes.iloc[i]) if not np.isnan(atr.iloc[i]) else 0,
        float(closes.iloc[i] / sma_20.iloc[i] - 1) if not np.isnan(sma_20.iloc[i]) else 0,
        float(closes.iloc[i] / sma_50.iloc[i] - 1) if not np.isnan(sma_50.iloc[i]) else 0,
        float(closes.pct_change().iloc[i]) if not np.isnan(closes.pct_change().iloc[i]) else 0,
        float(closes.pct_change(5).iloc[i]) if not np.isnan(closes.pct_change(5).iloc[i]) else 0,
        float(closes.pct_change(20).iloc[i]) if not np.isnan(closes.pct_change(20).iloc[i]) else 0,
      ]
      features.append(row)

    return np.array(features)

  @staticmethod
  def _generate_labels(df: pd.DataFrame) -> np.ndarray:
    closes = df["Close"].values
    labels = []

    high_52 = df["High"].max()
    low_52 = df["Low"].min()
    fib_levels = TechnicalAnalysisService.fibonacci_levels(high_52, low_52)

    for i in range(50, len(closes)):
      price = closes[i]
      future_return = (closes[min(i + 5, len(closes) - 1)] - price) / price

      near_fib_support = any(
        abs(price - level) / price < 0.02 and level_name in ("0.618", "0.786", "1.0")
        for level_name, level in fib_levels.items()
      )
      near_fib_resistance = any(
        abs(price - level) / price < 0.02 and level_name in ("0.0", "0.236", "0.382")
        for level_name, level in fib_levels.items()
      )

      if near_fib_support and future_return > 0.01:
        labels.append(3)
      elif near_fib_resistance and future_return < -0.01:
        labels.append(4)
      elif future_return > 0.02:
        labels.append(0)
      elif future_return < -0.02:
        labels.append(1)
      else:
        labels.append(2)

    return np.array(labels)

  @staticmethod
  def analyze_symbol(symbol: str, period: str = "2y") -> dict[str, Any]:
    df = YahooFinanceService.get_history(symbol, period=period)

    if len(df) < 100:
      return {"symbol": symbol, "error": "Datos insuficientes para análisis neuronal"}

    features = NeuralAnalysisService._extract_features(df)
    labels = NeuralAnalysisService._generate_labels(df)

    if len(features) < 50:
      return {"symbol": symbol, "error": "Muestras insuficientes"}

    split = int(len(features) * 0.8)
    X_train, X_test = features[:split], features[split:]
    y_train, y_test = labels[:split], labels[split:]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = MLPClassifier(
      hidden_layer_sizes=(64, 32, 16),
      activation="relu",
      max_iter=300,
      random_state=42,
      early_stopping=True,
      validation_fraction=0.1,
    )
    model.fit(X_train_scaled, y_train)

    accuracy = float(model.score(X_test_scaled, y_test)) if len(X_test) > 0 else 0.0

    current_features = features[-1:].copy()
    current_scaled = scaler.transform(current_features)
    prediction_idx = int(model.predict(current_scaled)[0])
    probabilities = model.predict_proba(current_scaled)[0]

    prediction = NeuralAnalysisService.PATTERN_LABELS[prediction_idx]
    confidence = float(max(probabilities))

    fib_patterns = TechnicalAnalysisService.detect_fibonacci_patterns(df)
    tech = TechnicalAnalysisService.full_analysis(symbol, period=period)

    recommendation = "hold"
    if prediction in ("bullish", "fibonacci_support") and confidence > 0.55:
      recommendation = "buy"
    elif prediction in ("bearish", "fibonacci_resistance") and confidence > 0.55:
      recommendation = "sell"

    return {
      "symbol": symbol.upper(),
      "neural_prediction": prediction,
      "confidence": round(confidence * 100, 2),
      "model_accuracy": round(accuracy * 100, 2),
      "recommendation": recommendation,
      "pattern_probabilities": {
        label: round(float(prob) * 100, 2)
        for label, prob in zip(model.classes_, probabilities)
        if int(label) < len(NeuralAnalysisService.PATTERN_LABELS)
      },
      "fibonacci_patterns_detected": len(fib_patterns),
      "recent_fibonacci_patterns": fib_patterns[-3:],
      "technical_summary": {
        "trend": tech.get("trend"),
        "rsi": tech.get("rsi"),
        "signals": tech.get("signals", []),
      },
      "neural_layers": "64-32-16 MLP",
    }

  @staticmethod
  def portfolio_neural_analysis(symbols: list[str]) -> dict[str, Any]:
    results = {}
    buy_signals = 0
    sell_signals = 0

    for symbol in symbols:
      try:
        analysis = NeuralAnalysisService.analyze_symbol(symbol)
        results[symbol.upper()] = analysis
        if analysis.get("recommendation") == "buy":
          buy_signals += 1
        elif analysis.get("recommendation") == "sell":
          sell_signals += 1
      except Exception as e:
        results[symbol.upper()] = {"error": str(e)}

    return {
      "symbols_analyzed": len(results),
      "buy_signals": buy_signals,
      "sell_signals": sell_signals,
      "hold_signals": len(results) - buy_signals - sell_signals,
      "portfolio_recommendation": "accumulate" if buy_signals > sell_signals else "reduce" if sell_signals > buy_signals else "hold",
      "analyses": results,
    }
