import logging
from typing import Optional

import numpy as np
import pandas as pd
import ta

from app.services.yahoo_finance import yahoo_service

logger = logging.getLogger(__name__)

FIBONACCI_RATIOS = {
    "0.0%": 0.0,
    "23.6%": 0.236,
    "38.2%": 0.382,
    "50.0%": 0.5,
    "61.8%": 0.618,
    "78.6%": 0.786,
    "100.0%": 1.0,
}


class PatternDetector:
    def __init__(self):
        self._model = None
        self._model_loaded = False

    def _load_model(self):
        if self._model_loaded:
            return
        try:
            from tensorflow import keras

            self._model = keras.Sequential([
                keras.layers.Input(shape=(60, 5)),
                keras.layers.LSTM(64, return_sequences=True),
                keras.layers.Dropout(0.2),
                keras.layers.LSTM(32),
                keras.layers.Dropout(0.2),
                keras.layers.Dense(16, activation="relu"),
                keras.layers.Dense(4, activation="softmax"),
            ])
            self._model.compile(optimizer="adam", loss="categorical_crossentropy")
            self._model_loaded = True
        except Exception as e:
            logger.warning("Could not load neural model: %s", e)
            self._model_loaded = True

    def _prepare_features(self, df: pd.DataFrame) -> Optional[np.ndarray]:
        if len(df) < 60:
            return None

        features = pd.DataFrame({
            "close": df["Close"],
            "volume": df["Volume"],
            "rsi": ta.momentum.RSIIndicator(df["Close"]).rsi(),
            "macd": ta.trend.MACD(df["Close"]).macd(),
            "bb_pct": ta.volatility.BollingerBands(df["Close"]).bollinger_pband(),
        }).dropna()

        if len(features) < 60:
            return None

        window = features.iloc[-60:].values
        mean = window.mean(axis=0)
        std = window.std(axis=0) + 1e-8
        normalized = (window - mean) / std
        return normalized.reshape(1, 60, 5)

    def detect_pattern(self, df: pd.DataFrame) -> tuple[Optional[str], float]:
        self._load_model()

        fib_pattern = self._detect_fibonacci_pattern(df)
        if fib_pattern:
            return fib_pattern, 0.75

        if self._model is not None:
            features = self._prepare_features(df)
            if features is not None:
                try:
                    predictions = self._model.predict(features, verbose=0)[0]
                    patterns = ["none", "head_shoulders", "double_top", "ascending_triangle"]
                    idx = int(np.argmax(predictions))
                    confidence = float(predictions[idx])
                    if idx > 0 and confidence > 0.3:
                        return patterns[idx], confidence
                except Exception:
                    pass

        return self._rule_based_pattern(df)

    def _detect_fibonacci_pattern(self, df: pd.DataFrame) -> Optional[str]:
        if len(df) < 50:
            return None

        highs = df["High"].rolling(5).max()
        lows = df["Low"].rolling(5).min()
        recent_high = float(highs.iloc[-20:].max())
        recent_low = float(lows.iloc[-20:].min())
        current = float(df["Close"].iloc[-1])
        diff = recent_high - recent_low

        if diff <= 0:
            return None

        levels = {name: recent_high - ratio * diff for name, ratio in FIBONACCI_RATIOS.items()}
        tolerance = diff * 0.02

        for name, level in levels.items():
            if abs(current - level) < tolerance:
                if name in ("38.2%", "50.0%", "61.8%"):
                    return f"fibonacci_retracement_{name.replace('.', '').replace('%', 'pct')}"
                if name == "61.8%":
                    return "fibonacci_golden_ratio_support"

        retracement = (recent_high - current) / diff
        if 0.55 < retracement < 0.65:
            return "fibonacci_golden_pocket"
        if 0.35 < retracement < 0.42:
            return "fibonacci_382_retracement"

        return None

    def _rule_based_pattern(self, df: pd.DataFrame) -> tuple[Optional[str], float]:
        if len(df) < 30:
            return None, 0.0

        closes = df["Close"].values[-30:]
        peaks = []
        for i in range(2, len(closes) - 2):
            if closes[i] > closes[i - 1] and closes[i] > closes[i + 1]:
                peaks.append((i, closes[i]))

        if len(peaks) >= 3:
            _, p1 = peaks[-3]
            _, p2 = peaks[-2]
            _, p3 = peaks[-1]
            if p2 > p1 and p2 > p3 and abs(p1 - p3) / p2 < 0.03:
                return "head_and_shoulders", 0.7

        recent = closes[-10:]
        if recent[-1] > recent[0] * 1.05 and np.std(recent) < np.std(closes) * 0.5:
            return "ascending_triangle", 0.65

        return None, 0.0


class TechnicalAnalysisService:
    def __init__(self):
        self.pattern_detector = PatternDetector()

    def calculate_fibonacci_levels(self, df: pd.DataFrame) -> dict[str, float]:
        high = float(df["High"].max())
        low = float(df["Low"].min())
        diff = high - low
        return {name: round(high - ratio * diff, 2) for name, ratio in FIBONACCI_RATIOS.items()}

    def find_support_resistance(self, df: pd.DataFrame, n_levels: int = 3) -> tuple[list[float], list[float]]:
        closes = df["Close"].values
        supports = []
        resistances = []

        for i in range(5, len(closes) - 5):
            window = closes[i - 5 : i + 6]
            if closes[i] == window.min():
                supports.append(float(closes[i]))
            if closes[i] == window.max():
                resistances.append(float(closes[i]))

        supports = sorted(set(supports))[-n_levels:]
        resistances = sorted(set(resistances))[-n_levels:]
        return supports, resistances

    def analyze(self, symbol: str) -> dict:
        df = yahoo_service.get_historical(symbol, "1y")
        close = df["Close"]

        rsi = float(ta.momentum.RSIIndicator(close).rsi().iloc[-1])
        macd_ind = ta.trend.MACD(close)
        macd = float(macd_ind.macd().iloc[-1])
        macd_signal = float(macd_ind.macd_signal().iloc[-1])
        bb = ta.volatility.BollingerBands(close)
        bb_position = float(bb.bollinger_pband().iloc[-1])

        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        current = float(close.iloc[-1])

        if current > sma20 > sma50:
            trend = "ALCISTA"
        elif current < sma20 < sma50:
            trend = "BAJISTA"
        else:
            trend = "LATERAL"

        supports, resistances = self.find_support_resistance(df)
        fib_levels = self.calculate_fibonacci_levels(df)
        pattern, neural_confidence = self.pattern_detector.detect_pattern(df)

        signals = []
        if rsi < 30:
            signals.append("SOBREVENTA")
        elif rsi > 70:
            signals.append("SOBRECOMPRA")
        if macd > macd_signal:
            signals.append("MACD_ALCISTA")
        else:
            signals.append("MACD_BAJISTA")

        if trend == "ALCISTA" and rsi < 40:
            signal = "COMPRAR"
        elif trend == "BAJISTA" and rsi > 60:
            signal = "VENDER"
        else:
            signal = "MANTENER"

        return {
            "symbol": symbol.upper(),
            "rsi": round(rsi, 2),
            "macd": round(macd, 4),
            "macd_signal": round(macd_signal, 4),
            "bollinger_position": round(bb_position, 2),
            "trend": trend,
            "support_levels": supports,
            "resistance_levels": resistances,
            "fibonacci_levels": fib_levels,
            "pattern_detected": pattern,
            "neural_confidence": round(neural_confidence, 2),
            "signal": signal,
            "sub_signals": signals,
        }

    def compare_symbols(self, symbols: list[str]) -> list[dict]:
        results = []
        for symbol in symbols:
            try:
                analysis = self.analyze(symbol)
                quote = yahoo_service.get_quote(symbol)
                iso = yahoo_service.get_isometric_value(symbol)
                results.append({
                    "symbol": symbol.upper(),
                    "price": quote["price"],
                    "price_normalized": iso["price_normalized"],
                    "rsi": analysis["rsi"],
                    "trend": analysis["trend"],
                    "signal": analysis["signal"],
                    "pattern": analysis["pattern_detected"],
                    "neural_confidence": analysis["neural_confidence"],
                    "change_percent": quote["change_percent"],
                })
            except Exception as e:
                logger.warning("Compare error for %s: %s", symbol, e)
        return sorted(results, key=lambda x: x.get("neural_confidence", 0), reverse=True)


technical_service = TechnicalAnalysisService()
