import numpy as np
import pandas as pd
from typing import Optional
from app.services.yahoo_finance import YahooFinanceService


class TechnicalAnalysisService:
    """Análisis técnico avanzado con indicadores y niveles Fibonacci."""

    @staticmethod
    def calculate_fibonacci_levels(high: float, low: float) -> dict:
        diff = high - low
        return {
            "0.0%": round(high, 4),
            "23.6%": round(high - diff * 0.236, 4),
            "38.2%": round(high - diff * 0.382, 4),
            "50.0%": round(high - diff * 0.5, 4),
            "61.8%": round(high - diff * 0.618, 4),
            "78.6%": round(high - diff * 0.786, 4),
            "100.0%": round(low, 4),
            "161.8%": round(high + diff * 0.618, 4),
            "261.8%": round(high + diff * 1.618, 4),
        }

    @staticmethod
    def find_support_resistance(df: pd.DataFrame, window: int = 20) -> tuple[list[float], list[float]]:
        closes = df["Close"].values
        supports, resistances = [], []

        for i in range(window, len(closes) - window):
            local_min = closes[i - window:i + window + 1].min()
            local_max = closes[i - window:i + window + 1].max()
            if closes[i] == local_min:
                supports.append(float(closes[i]))
            if closes[i] == local_max:
                resistances.append(float(closes[i]))

        # Deduplicate and keep most recent significant levels
        supports = sorted(set(supports), reverse=True)[:5]
        resistances = sorted(set(resistances))[:5]
        return supports, resistances

    @staticmethod
    def detect_fibonacci_patterns(df: pd.DataFrame) -> list[dict]:
        patterns = []
        closes = df["Close"].values
        if len(closes) < 50:
            return patterns

        recent_high = float(df["High"].tail(50).max())
        recent_low = float(df["Low"].tail(50).min())
        current = float(closes[-1])
        fib_levels = TechnicalAnalysisService.calculate_fibonacci_levels(recent_high, recent_low)

        for level_name, level_price in fib_levels.items():
            distance_pct = abs(current - level_price) / current * 100
            if distance_pct < 1.5:
                patterns.append({
                    "type": "fibonacci_retracement",
                    "level": level_name,
                    "price": level_price,
                    "distance_pct": round(distance_pct, 2),
                    "strength": "strong" if distance_pct < 0.5 else "moderate",
                })

        # Golden ratio cross detection
        sma_20 = df["Close"].rolling(20).mean().iloc[-1]
        sma_50 = df["Close"].rolling(50).mean().iloc[-1]
        if not np.isnan(sma_20) and not np.isnan(sma_50):
            ratio = sma_20 / sma_50 if sma_50 != 0 else 1
            if 0.618 <= ratio <= 0.65 or 1.55 <= ratio <= 1.65:
                patterns.append({
                    "type": "golden_ratio_cross",
                    "ratio": round(ratio, 4),
                    "strength": "strong",
                })

        return patterns

    @staticmethod
    def analyze(symbol: str) -> Optional[dict]:
        df = YahooFinanceService.get_historical(symbol, period="1y")
        if df is None or len(df) < 30:
            return None

        closes = df["Close"]
        highs = df["High"]
        lows = df["Low"]

        # RSI
        delta = closes.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else None

        # MACD
        ema_12 = closes.ewm(span=12).mean()
        ema_26 = closes.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        current_macd = float(macd_line.iloc[-1])
        current_signal = float(signal_line.iloc[-1])

        # Moving averages
        sma_20 = float(closes.rolling(20).mean().iloc[-1])
        sma_50 = float(closes.rolling(50).mean().iloc[-1])
        sma_200 = float(closes.rolling(200).mean().iloc[-1]) if len(closes) >= 200 else None

        # Bollinger Bands
        bb_mid = closes.rolling(20).mean()
        bb_std = closes.rolling(20).std()
        bb_upper = float((bb_mid + 2 * bb_std).iloc[-1])
        bb_lower = float((bb_mid - 2 * bb_std).iloc[-1])

        # Fibonacci
        recent_high = float(highs.tail(60).max())
        recent_low = float(lows.tail(60).min())
        fib_levels = TechnicalAnalysisService.calculate_fibonacci_levels(recent_high, recent_low)

        supports, resistances = TechnicalAnalysisService.find_support_resistance(df)
        fib_patterns = TechnicalAnalysisService.detect_fibonacci_patterns(df)

        current_price = float(closes.iloc[-1])
        signals = []

        if current_rsi:
            if current_rsi > 70:
                signals.append("RSI sobrecomprado (>70)")
            elif current_rsi < 30:
                signals.append("RSI sobrevendido (<30)")

        if current_macd > current_signal:
            signals.append("MACD alcista (cruce positivo)")
        else:
            signals.append("MACD bajista (cruce negativo)")

        if current_price > sma_20 > sma_50:
            trend = "alcista"
            signals.append("Tendencia alcista confirmada (precio > SMA20 > SMA50)")
        elif current_price < sma_20 < sma_50:
            trend = "bajista"
            signals.append("Tendencia bajista confirmada (precio < SMA20 < SMA50)")
        else:
            trend = "lateral"
            signals.append("Tendencia lateral / consolidación")

        if current_price <= bb_lower:
            signals.append("Precio en banda inferior de Bollinger (posible rebote)")
        elif current_price >= bb_upper:
            signals.append("Precio en banda superior de Bollinger (posible corrección)")

        for pattern in fib_patterns:
            if pattern["type"] == "fibonacci_retracement":
                signals.append(f"Nivel Fibonacci {pattern['level']} cerca del precio actual")

        return {
            "symbol": symbol.upper(),
            "rsi": round(current_rsi, 2) if current_rsi else None,
            "macd": round(current_macd, 4),
            "macd_signal": round(current_signal, 4),
            "sma_20": round(sma_20, 4),
            "sma_50": round(sma_50, 4),
            "sma_200": round(sma_200, 4) if sma_200 else None,
            "bollinger_upper": round(bb_upper, 4),
            "bollinger_lower": round(bb_lower, 4),
            "fibonacci_levels": fib_levels,
            "fibonacci_patterns": fib_patterns,
            "support_levels": supports,
            "resistance_levels": resistances,
            "trend": trend,
            "signals": signals,
            "current_price": current_price,
        }
