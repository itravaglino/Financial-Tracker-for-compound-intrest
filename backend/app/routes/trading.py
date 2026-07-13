from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Alert, StopLoss, Order, Notification
from app.schemas import (
    AlertCreate, AlertResponse, StopLossCreate, StopLossResponse,
    OrderCreate, OrderResponse, NotificationResponse,
)
from app.auth import get_current_user
from app.services.trading import TradingService, AlertService

router = APIRouter(prefix="/api/trading", tags=["Trading y Alertas"])


# --- Alerts ---
@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Alert).filter(Alert.user_id == current_user.id).all()


@router.post("/alerts", response_model=AlertResponse, status_code=201)
def create_alert(
    data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = Alert(
        user_id=current_user.id,
        symbol=data.symbol.upper(),
        alert_type=data.alert_type,
        threshold=data.threshold,
        message=data.message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/alerts/{alert_id}", status_code=204)
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


@router.post("/alerts/check")
def check_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = AlertService.check_alerts(db, current_user.id)
    return {"checked": True, "new_notifications": len(notifications)}


# --- Stop Loss ---
@router.get("/stop-loss", response_model=list[StopLossResponse])
def list_stop_losses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(StopLoss).filter(StopLoss.user_id == current_user.id).all()


@router.post("/stop-loss", response_model=StopLossResponse, status_code=201)
def create_stop_loss(
    data: StopLossCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sl = StopLoss(
        user_id=current_user.id,
        symbol=data.symbol.upper(),
        quantity=data.quantity,
        trigger_price=data.trigger_price,
        trailing_percent=data.trailing_percent,
    )
    db.add(sl)
    db.commit()
    db.refresh(sl)
    return sl


@router.delete("/stop-loss/{sl_id}", status_code=204)
def delete_stop_loss(
    sl_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sl = db.query(StopLoss).filter(StopLoss.id == sl_id, StopLoss.user_id == current_user.id).first()
    if not sl:
        raise HTTPException(status_code=404, detail="Stop loss no encontrado")
    db.delete(sl)
    db.commit()


@router.post("/stop-loss/check")
async def check_stop_losses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = await AlertService.check_stop_losses(db, current_user.id)
    return {"checked": True, "triggered": len(notifications)}


# --- Orders ---
@router.get("/orders", response_model=list[OrderResponse])
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()


@router.post("/orders", response_model=OrderResponse, status_code=201)
async def place_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.side not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="side debe ser 'buy' o 'sell'")
    order = await TradingService.place_order(
        db, current_user.id, data.symbol, data.side,
        data.quantity, data.order_type, data.limit_price,
    )
    return order


@router.get("/account")
async def get_account(current_user: User = Depends(get_current_user)):
    return await TradingService.get_account_status()


# --- Notifications ---
@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()


@router.put("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = db.query(Notification).filter(
        Notification.id == notif_id, Notification.user_id == current_user.id
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"ok": True}
