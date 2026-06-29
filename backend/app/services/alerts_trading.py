from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Alert, BrokerConfig, Holding, StopLoss, TradeOrder, User
from app.services.yahoo_finance import YahooFinanceService


class AlertService:
  """Sistema de alertas personalizadas."""

  @staticmethod
  def check_alert(alert: Alert, current_data: dict[str, Any]) -> bool:
    value = current_data.get(alert.alert_type, current_data.get("price", 0))

    if alert.condition == "above" and value >= alert.threshold:
      return True
    if alert.condition == "below" and value <= alert.threshold:
      return True
    if alert.condition == "equals" and abs(value - alert.threshold) < 0.01:
      return True
    if alert.condition == "change_pct_above" and current_data.get("change_pct", 0) >= alert.threshold:
      return True
    if alert.condition == "change_pct_below" and current_data.get("change_pct", 0) <= alert.threshold:
      return True
    return False

  @staticmethod
  def evaluate_alerts(db: Session, user_id: int) -> list[dict[str, Any]]:
    alerts = db.query(Alert).filter(Alert.user_id == user_id, Alert.is_active == True, Alert.triggered == False).all()
    triggered_alerts = []

    for alert in alerts:
      try:
        if alert.alert_type in ("price", "change_pct"):
          data = YahooFinanceService.get_quote(alert.symbol)
        elif alert.alert_type == "rsi":
          from app.services.technical_analysis import TechnicalAnalysisService
          data = TechnicalAnalysisService.full_analysis(alert.symbol)
        else:
          data = YahooFinanceService.get_quote(alert.symbol)

        if AlertService.check_alert(alert, data):
          alert.triggered = True
          alert.triggered_at = datetime.utcnow()
          triggered_alerts.append({
            "alert_id": alert.id,
            "symbol": alert.symbol,
            "message": alert.message or f"Alerta activada: {alert.symbol} {alert.condition} {alert.threshold}",
            "current_value": data.get(alert.alert_type, data.get("price")),
          })
      except Exception:
        continue

    db.commit()
    return triggered_alerts

  @staticmethod
  def evaluate_stop_losses(db: Session, user_id: int) -> list[dict[str, Any]]:
    from app.models import Portfolio

    portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    triggered = []

    for portfolio in portfolios:
      for holding in portfolio.holdings:
        for stop_loss in holding.stop_losses:
          if not stop_loss.is_active or stop_loss.triggered:
            continue

          try:
            quote = YahooFinanceService.get_quote(holding.symbol)
            current_price = quote["price"]

            if stop_loss.stop_type == "trailing" and stop_loss.trailing_percent:
              high_since = current_price
              trigger = high_since * (1 - stop_loss.trailing_percent / 100)
              if current_price <= trigger:
                stop_loss.triggered = True
                stop_loss.triggered_at = datetime.utcnow()
                triggered.append({
                  "stop_loss_id": stop_loss.id,
                  "symbol": holding.symbol,
                  "type": "trailing",
                  "trigger_price": trigger,
                  "current_price": current_price,
                  "action": "SELL recommended",
                })
            elif current_price <= stop_loss.trigger_price:
              stop_loss.triggered = True
              stop_loss.triggered_at = datetime.utcnow()
              triggered.append({
                "stop_loss_id": stop_loss.id,
                "symbol": holding.symbol,
                "type": "fixed",
                "trigger_price": stop_loss.trigger_price,
                "current_price": current_price,
                "action": "SELL recommended",
              })
          except Exception:
            continue

    db.commit()
    return triggered


class TradingService:
  """Ejecución de órdenes vía API de broker (Alpaca)."""

  @staticmethod
  def get_broker_config(db: Session, user: User) -> BrokerConfig | None:
    return db.query(BrokerConfig).filter(BrokerConfig.user_id == user.id).first()

  @staticmethod
  async def place_order(
    db: Session,
    user: User,
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "market",
    limit_price: float | None = None,
  ) -> TradeOrder:
    order = TradeOrder(
      user_id=user.id,
      symbol=symbol.upper(),
      side=side.lower(),
      quantity=quantity,
      order_type=order_type,
      limit_price=limit_price,
      status="pending",
    )
    db.add(order)
    db.flush()

    config = TradingService.get_broker_config(db, user)
    api_key = config.api_key if config else settings.alpaca_api_key
    secret_key = config.secret_key if config else settings.alpaca_secret_key
    base_url = config.base_url if config else settings.alpaca_base_url

    if not api_key or not secret_key:
      order.status = "failed"
      order.error_message = "API de broker no configurada. Configura tus credenciales de Alpaca."
      db.commit()
      return order

    payload: dict[str, Any] = {
      "symbol": symbol.upper(),
      "qty": str(quantity),
      "side": side.lower(),
      "type": order_type,
      "time_in_force": "day",
    }
    if order_type == "limit" and limit_price:
      payload["limit_price"] = str(limit_price)

    headers = {
      "APCA-API-KEY-ID": api_key,
      "APCA-API-SECRET-KEY": secret_key,
      "Content-Type": "application/json",
    }

    try:
      async with httpx.AsyncClient() as client:
        response = await client.post(
          f"{base_url}/v2/orders",
          json=payload,
          headers=headers,
          timeout=30,
        )

        if response.status_code in (200, 201):
          data = response.json()
          order.status = data.get("status", "submitted")
          order.broker_order_id = data.get("id")
        else:
          order.status = "failed"
          order.error_message = response.text
    except Exception as e:
      order.status = "failed"
      order.error_message = str(e)

    db.commit()
    db.refresh(order)
    return order

  @staticmethod
  async def get_account_status(db: Session, user: User) -> dict[str, Any]:
    config = TradingService.get_broker_config(db, user)
    api_key = config.api_key if config else settings.alpaca_api_key
    secret_key = config.secret_key if config else settings.alpaca_secret_key
    base_url = config.base_url if config else settings.alpaca_base_url

    if not api_key or not secret_key:
      return {"configured": False, "message": "Broker no configurado"}

    headers = {
      "APCA-API-KEY-ID": api_key,
      "APCA-API-SECRET-KEY": secret_key,
    }

    try:
      async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/v2/account", headers=headers, timeout=15)
        if response.status_code == 200:
          data = response.json()
          return {
            "configured": True,
            "buying_power": data.get("buying_power"),
            "cash": data.get("cash"),
            "portfolio_value": data.get("portfolio_value"),
            "status": data.get("status"),
            "is_paper": config.is_paper if config else True,
          }
        return {"configured": True, "error": response.text}
    except Exception as e:
      return {"configured": True, "error": str(e)}
