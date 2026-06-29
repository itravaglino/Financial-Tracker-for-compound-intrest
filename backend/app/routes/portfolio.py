from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database import get_db
from app.models import Alert, Holding, Portfolio, User
from app.schemas import (
    AlertCreate,
    AlertResponse,
    HoldingCreate,
    HoldingResponse,
    PortfolioCreate,
    PortfolioResponse,
    YahooImportRequest,
)
from app.services.portfolio import portfolio_service
from app.services.yahoo_finance import yahoo_service

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post("/", response_model=PortfolioResponse)
def create_portfolio(
    data: PortfolioCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = Portfolio(user_id=user.id, name=data.name)
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.get("/", response_model=list[PortfolioResponse])
def list_portfolios(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Portfolio).filter(Portfolio.user_id == user.id).all()


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")
    return portfolio


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse)
def add_holding(
    portfolio_id: int,
    data: HoldingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")

    holding = Holding(
        portfolio_id=portfolio_id,
        symbol=data.symbol.upper(),
        quantity=data.quantity,
        avg_cost=data.avg_cost,
        currency=data.currency,
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding


@router.delete("/{portfolio_id}/holdings/{holding_id}")
def remove_holding(
    portfolio_id: int,
    holding_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    holding = (
        db.query(Holding)
        .join(Portfolio)
        .filter(
            Holding.id == holding_id,
            Holding.portfolio_id == portfolio_id,
            Portfolio.user_id == user.id,
        )
        .first()
    )
    if not holding:
        raise HTTPException(status_code=404, detail="Holding no encontrado")
    db.delete(holding)
    db.commit()
    return {"message": "Holding eliminado"}


@router.post("/import-yahoo")
def import_from_yahoo(
    data: YahooImportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == data.portfolio_id, Portfolio.user_id == user.id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")

    imported = yahoo_service.import_yahoo_portfolio(data.symbols)
    added = []
    for item in imported:
        existing = (
            db.query(Holding)
            .filter(Holding.portfolio_id == portfolio.id, Holding.symbol == item["symbol"])
            .first()
        )
        if existing:
            existing.avg_cost = item["avg_cost"]
            existing.currency = item["currency"]
        else:
            holding = Holding(
                portfolio_id=portfolio.id,
                symbol=item["symbol"],
                quantity=item.get("quantity", 0),
                avg_cost=item["avg_cost"],
                currency=item["currency"],
            )
            db.add(holding)
            added.append(item["symbol"])

    portfolio.source = "yahoo_finance"
    db.commit()
    return {"imported": len(imported), "symbols": [i["symbol"] for i in imported], "details": imported}


@router.get("/{portfolio_id}/analysis")
def analyze_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return portfolio_service.analyze_portfolio(db, portfolio_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/alerts", response_model=AlertResponse)
def create_alert(
    data: AlertCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    alert = Alert(
        user_id=user.id,
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


@router.get("/alerts/list", response_model=list[AlertResponse])
def list_alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Alert).filter(Alert.user_id == user.id).all()


@router.delete("/alerts/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    db.delete(alert)
    db.commit()
    return {"message": "Alerta eliminada"}
