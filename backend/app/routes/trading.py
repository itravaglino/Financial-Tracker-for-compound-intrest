from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database import get_db
from app.models import Order, StopLoss, User
from app.schemas import OrderCreate, OrderResponse, StopLossCreate, StopLossResponse
from app.services.alerts import alert_service, stop_loss_service
from app.services.trading import trading_service

router = APIRouter(prefix="/trading", tags=["Trading"])


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.side.lower() not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="Side debe ser 'buy' o 'sell'")

    result = await trading_service.place_order(
        symbol=data.symbol,
        side=data.side,
        quantity=data.quantity,
        order_type=data.order_type,
        limit_price=data.limit_price,
    )

    order = Order(
        user_id=user.id,
        symbol=data.symbol.upper(),
        side=data.side.lower(),
        quantity=data.quantity,
        order_type=data.order_type,
        limit_price=data.limit_price,
        status=result.get("status", "pending"),
        external_id=result.get("external_id"),
        filled_price=result.get("filled_price"),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/orders", response_model=list[OrderResponse])
def list_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()


@router.post("/stop-loss", response_model=StopLossResponse)
def create_stop_loss(
    data: StopLossCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stop = StopLoss(
        user_id=user.id,
        symbol=data.symbol.upper(),
        quantity=data.quantity,
        stop_price=data.stop_price,
        trailing_percent=data.trailing_percent,
    )
    db.add(stop)
    db.commit()
    db.refresh(stop)
    return stop


@router.get("/stop-loss", response_model=list[StopLossResponse])
def list_stop_losses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(StopLoss).filter(StopLoss.user_id == user.id).all()


@router.delete("/stop-loss/{stop_id}")
def delete_stop_loss(
    stop_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stop = db.query(StopLoss).filter(StopLoss.id == stop_id, StopLoss.user_id == user.id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop loss no encontrado")
    db.delete(stop)
    db.commit()
    return {"message": "Stop loss eliminado"}


@router.get("/account")
async def get_trading_account(user: User = Depends(get_current_user)):
    return await trading_service.get_account()


@router.post("/check-alerts")
def check_alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alerts = alert_service.process_alerts(db)
    stops = stop_loss_service.process_stop_losses(db)
    user_alerts = [a for a in alerts if a["user_id"] == user.id]
    user_stops = [s for s in stops if s["user_id"] == user.id]
    return {"triggered_alerts": user_alerts, "triggered_stop_losses": user_stops}
