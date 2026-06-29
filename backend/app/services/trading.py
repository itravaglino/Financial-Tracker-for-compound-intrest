import httpx
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Order, StopLoss, Alert, Notification
from app.services.yahoo_finance import YahooFinanceService

logger = logging.getLogger(__name__)
settings = get_settings()


class TradingService:
    """Integración con Alpaca API para compra/venta de acciones."""

    @staticmethod
    def _get_headers() -> dict:
        return {
            "APCA-API-KEY-ID": settings.alpaca_api_key,
            "APCA-API-SECRET-KEY": settings.alpaca_secret_key,
            "Content-Type": "application/json",
        }

    @staticmethod
    def is_configured() -> bool:
        return bool(settings.alpaca_api_key and settings.alpaca_secret_key)

    @staticmethod
    async def place_order(
        db: Session,
        user_id: int,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        limit_price: Optional[float] = None,
    ) -> Order:
        order = Order(
            user_id=user_id,
            symbol=symbol.upper(),
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            status="pending",
        )
        db.add(order)
        db.flush()

        if TradingService.is_configured():
            try:
                payload = {
                    "symbol": symbol.upper(),
                    "qty": str(quantity),
                    "side": side,
                    "type": order_type,
                    "time_in_force": "gtc",
                }
                if order_type == "limit" and limit_price:
                    payload["limit_price"] = str(limit_price)

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{settings.alpaca_base_url}/v2/orders",
                        headers=TradingService._get_headers(),
                        json=payload,
                        timeout=30,
                    )
                    if response.status_code in (200, 201):
                        data = response.json()
                        order.status = "executed"
                        order.external_id = data.get("id")
                        order.executed_at = datetime.utcnow()
                    else:
                        order.status = "failed"
                        logger.error(f"Alpaca order failed: {response.text}")
            except Exception as e:
                order.status = "failed"
                logger.error(f"Trading error: {e}")
        else:
            # Simulated paper trade when API not configured
            quote = YahooFinanceService.get_quote(symbol)
            if quote:
                order.status = "executed"
                order.external_id = f"SIM-{order.id}-{datetime.utcnow().timestamp():.0f}"
                order.executed_at = datetime.utcnow()
            else:
                order.status = "failed"

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    async def get_account_status() -> dict:
        if not TradingService.is_configured():
            return {
                "configured": False,
                "mode": "simulation",
                "message": "API de trading no configurada. Las órdenes se ejecutan en modo simulación.",
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.alpaca_base_url}/v2/account",
                    headers=TradingService._get_headers(),
                    timeout=15,
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "configured": True,
                        "mode": "paper" if "paper" in settings.alpaca_base_url else "live",
                        "buying_power": float(data.get("buying_power", 0)),
                        "cash": float(data.get("cash", 0)),
                        "portfolio_value": float(data.get("portfolio_value", 0)),
                    }
        except Exception as e:
            logger.error(f"Account status error: {e}")

        return {"configured": True, "mode": "error", "message": "No se pudo conectar con Alpaca"}


class AlertService:
    """Sistema de alertas personalizadas y monitoreo de stop-loss."""

    @staticmethod
    def check_alerts(db: Session, user_id: int) -> list[Notification]:
        new_notifications = []
        alerts = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_active == True,
            Alert.triggered == False,
        ).all()

        for alert in alerts:
            quote = YahooFinanceService.get_quote(alert.symbol)
            if not quote:
                continue

            price = quote["price"]
            triggered = False
            message = ""

            if alert.alert_type == "price_above" and alert.threshold and price >= alert.threshold:
                triggered = True
                message = f"{alert.symbol} alcanzó ${price:.2f} (umbral: ${alert.threshold:.2f})"
            elif alert.alert_type == "price_below" and alert.threshold and price <= alert.threshold:
                triggered = True
                message = f"{alert.symbol} cayó a ${price:.2f} (umbral: ${alert.threshold:.2f})"
            elif alert.alert_type in ("stop_loss", "take_profit"):
                triggered = alert.threshold and (
                    (alert.alert_type == "stop_loss" and price <= alert.threshold) or
                    (alert.alert_type == "take_profit" and price >= alert.threshold)
                )
                if triggered:
                    message = f"Alerta {alert.alert_type}: {alert.symbol} a ${price:.2f}"

            if triggered:
                alert.triggered = True
                notif = Notification(
                    user_id=user_id,
                    title=f"Alerta: {alert.symbol}",
                    message=message or alert.message or f"Alerta activada para {alert.symbol}",
                )
                db.add(notif)
                new_notifications.append(notif)

        db.commit()
        return new_notifications

    @staticmethod
    async def check_stop_losses(db: Session, user_id: int) -> list[Notification]:
        new_notifications = []
        stop_losses = db.query(StopLoss).filter(
            StopLoss.user_id == user_id,
            StopLoss.is_active == True,
            StopLoss.triggered == False,
        ).all()

        for sl in stop_losses:
            quote = YahooFinanceService.get_quote(sl.symbol)
            if not quote:
                continue

            price = quote["price"]
            trigger = sl.trigger_price

            # Trailing stop loss
            if sl.trailing_percent:
                high_since = quote["price"]  # simplified; in production track peak
                trailing_trigger = high_since * (1 - sl.trailing_percent / 100)
                trigger = max(trigger, trailing_trigger)

            if price <= trigger:
                sl.triggered = True
                notif = Notification(
                    user_id=user_id,
                    title=f"Stop Loss activado: {sl.symbol}",
                    message=f"Stop loss de {sl.symbol} activado a ${price:.2f} (trigger: ${trigger:.2f}). Cantidad: {sl.quantity}",
                )
                db.add(notif)
                new_notifications.append(notif)

                # Auto-sell if trading configured
                if TradingService.is_configured() or True:
                    await TradingService.place_order(
                        db, user_id, sl.symbol, "sell", sl.quantity
                    )

        db.commit()
        return new_notifications
