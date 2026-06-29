import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.ml.technical_analysis import technical_service
from app.models import Alert, StopLoss
from app.services.yahoo_finance import yahoo_service

logger = logging.getLogger(__name__)


class AlertService:
    def check_alert(self, alert: Alert) -> bool:
        try:
            quote = yahoo_service.get_quote(alert.symbol)
            price = quote["price"]
            change_pct = quote["change_percent"]

            if alert.alert_type == "price":
                return self._check_condition(price, alert.condition, alert.threshold)
            if alert.alert_type == "change_percent":
                return self._check_condition(change_pct, alert.condition, alert.threshold)
            if alert.alert_type == "rsi":
                analysis = technical_service.analyze(alert.symbol)
                return self._check_condition(analysis["rsi"], alert.condition, alert.threshold)
            if alert.alert_type == "fibonacci":
                analysis = technical_service.analyze(alert.symbol)
                if analysis["pattern_detected"]:
                    return "fibonacci" in analysis["pattern_detected"]
            if alert.alert_type == "signal":
                analysis = technical_service.analyze(alert.symbol)
                return analysis["signal"] == alert.condition.upper()
        except Exception as e:
            logger.warning("Alert check failed for %s: %s", alert.symbol, e)
        return False

    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        ops = {
            "gt": value > threshold,
            "gte": value >= threshold,
            "lt": value < threshold,
            "lte": value <= threshold,
            "eq": abs(value - threshold) < 0.01,
        }
        return ops.get(condition, False)

    def process_alerts(self, db: Session) -> list[dict]:
        triggered = []
        alerts = db.query(Alert).filter(Alert.is_active == True, Alert.triggered == False).all()
        for alert in alerts:
            if self.check_alert(alert):
                alert.triggered = True
                alert.triggered_at = datetime.utcnow()
                triggered.append({
                    "id": alert.id,
                    "symbol": alert.symbol,
                    "type": alert.alert_type,
                    "message": alert.message or f"Alerta activada para {alert.symbol}",
                    "user_id": alert.user_id,
                })
        db.commit()
        return triggered


class StopLossService:
    def check_stop_loss(self, stop_loss: StopLoss) -> bool:
        try:
            quote = yahoo_service.get_quote(stop_loss.symbol)
            price = quote["price"]
            if stop_loss.trailing_percent:
                high = price * (1 + stop_loss.trailing_percent / 100)
                adjusted_stop = high * (1 - stop_loss.trailing_percent / 100)
                return price <= adjusted_stop
            return price <= stop_loss.stop_price
        except Exception:
            return False

    def process_stop_losses(self, db: Session) -> list[dict]:
        triggered = []
        stops = db.query(StopLoss).filter(StopLoss.is_active == True, StopLoss.triggered == False).all()
        for stop in stops:
            if self.check_stop_loss(stop):
                stop.triggered = True
                stop.triggered_at = datetime.utcnow()
                triggered.append({
                    "id": stop.id,
                    "symbol": stop.symbol,
                    "quantity": stop.quantity,
                    "stop_price": stop.stop_price,
                    "user_id": stop.user_id,
                    "action": "SELL",
                })
        db.commit()
        return triggered


alert_service = AlertService()
stop_loss_service = StopLossService()
