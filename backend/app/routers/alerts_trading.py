from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Alert, BrokerConfig, Holding, Portfolio, StopLoss, User
from app.schemas import (
    AlertCreate,
    AlertResponse,
    BrokerConfigCreate,
    BrokerConfigResponse,
    StopLossCreate,
    StopLossResponse,
    TradeOrderCreate,
    TradeOrderResponse,
)
from app.services.alerts_trading import AlertService, TradingService

router = APIRouter(tags=["Alertas y Trading"])


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Alert).filter(Alert.user_id == current_user.id).all()


@router.post("/alerts", response_model=AlertResponse)
def create_alert(
    data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = Alert(
        user_id=current_user.id,
        symbol=data.symbol.upper(),
        alert_type=data.alert_type,
        condition=data.condition,
        threshold=data.threshold,
        message=data.message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/alerts/{alert_id}")
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    db.delete(alert)
    db.commit()
    return {"message": "Alerta eliminada"}


@router.post("/alerts/check")
def check_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    triggered = AlertService.evaluate_alerts(db, current_user.id)
    stop_losses = AlertService.evaluate_stop_losses(db, current_user.id)
    return {"triggered_alerts": triggered, "triggered_stop_losses": stop_losses}


@router.post("/stop-loss/{holding_id}", response_model=StopLossResponse)
def create_stop_loss(
    holding_id: int,
    data: StopLossCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    holding = (
        db.query(Holding)
        .join(Portfolio)
        .filter(Holding.id == holding_id, Portfolio.user_id == current_user.id)
        .first()
    )
    if not holding:
        raise HTTPException(status_code=404, detail="Posición no encontrada")

    stop_loss = StopLoss(
        holding_id=holding_id,
        trigger_price=data.trigger_price,
        stop_type=data.stop_type,
        trailing_percent=data.trailing_percent,
    )
    db.add(stop_loss)
    db.commit()
    db.refresh(stop_loss)
    return stop_loss


@router.get("/stop-loss", response_model=list[StopLossResponse])
def list_stop_losses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    result = []
    for p in portfolios:
        for h in p.holdings:
            result.extend(h.stop_losses)
    return result


@router.post("/trading/order", response_model=TradeOrderResponse)
async def place_order(
    data: TradeOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = await TradingService.place_order(
        db, current_user, data.symbol, data.side, data.quantity, data.order_type, data.limit_price
    )
    return order


@router.get("/trading/orders", response_model=list[TradeOrderResponse])
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import TradeOrder
    return db.query(TradeOrder).filter(TradeOrder.user_id == current_user.id).order_by(TradeOrder.created_at.desc()).limit(50).all()


@router.get("/trading/account")
async def broker_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return await TradingService.get_account_status(db, current_user)


@router.post("/trading/broker-config", response_model=BrokerConfigResponse)
def configure_broker(
    data: BrokerConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = db.query(BrokerConfig).filter(BrokerConfig.user_id == current_user.id).first()
    if config:
        config.api_key = data.api_key
        config.secret_key = data.secret_key
        config.base_url = data.base_url
        config.is_paper = data.is_paper
    else:
        config = BrokerConfig(
            user_id=current_user.id,
            api_key=data.api_key,
            secret_key=data.secret_key,
            base_url=data.base_url,
            is_paper=data.is_paper,
        )
        db.add(config)
    db.commit()
    db.refresh(config)
    return BrokerConfigResponse(id=config.id, base_url=config.base_url, is_paper=config.is_paper, configured=True)
