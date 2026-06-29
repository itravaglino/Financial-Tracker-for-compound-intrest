from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Holding, Portfolio, User
from app.schemas import (
    HoldingCreate,
    HoldingResponse,
    HoldingUpdate,
    PortfolioCreate,
    PortfolioResponse,
    YahooImportRequest,
)
from app.services.yahoo_finance import YahooFinanceService

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


def _enrich_holding(holding: Holding) -> HoldingResponse:
    try:
        quote = YahooFinanceService.get_quote(holding.symbol)
        current_price = quote["price"]
        market_value = current_price * holding.quantity
        cost = holding.avg_cost * holding.quantity
        gain_loss = market_value - cost
        gain_loss_pct = (gain_loss / cost * 100) if cost > 0 else 0
        return HoldingResponse(
            id=holding.id,
            symbol=holding.symbol,
            quantity=holding.quantity,
            avg_cost=holding.avg_cost,
            currency=holding.currency,
            notes=holding.notes or "",
            current_price=round(current_price, 2),
            market_value=round(market_value, 2),
            gain_loss=round(gain_loss, 2),
            gain_loss_pct=round(gain_loss_pct, 2),
        )
    except Exception:
        return HoldingResponse(
            id=holding.id,
            symbol=holding.symbol,
            quantity=holding.quantity,
            avg_cost=holding.avg_cost,
            currency=holding.currency,
            notes=holding.notes or "",
        )


@router.get("/", response_model=list[PortfolioResponse])
def list_portfolios(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    result = []
    for p in portfolios:
        holdings = [_enrich_holding(h) for h in p.holdings]
        total_value = sum(h.market_value or 0 for h in holdings)
        total_cost = sum(h.avg_cost * h.quantity for h in holdings)
        result.append(PortfolioResponse(
            id=p.id,
            name=p.name,
            source=p.source,
            holdings=holdings,
            total_value=round(total_value, 2),
            total_cost=round(total_cost, 2),
            total_gain_loss=round(total_value - total_cost, 2),
        ))
    return result


@router.post("/", response_model=PortfolioResponse)
def create_portfolio(
    data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = Portfolio(user_id=current_user.id, name=data.name)
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return PortfolioResponse(id=portfolio.id, name=portfolio.name, source=portfolio.source)


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse)
def add_holding(
    portfolio_id: int,
    data: HoldingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")

    holding = Holding(
        portfolio_id=portfolio_id,
        symbol=data.symbol.upper(),
        quantity=data.quantity,
        avg_cost=data.avg_cost,
        currency=data.currency,
        notes=data.notes,
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return _enrich_holding(holding)


@router.put("/holdings/{holding_id}", response_model=HoldingResponse)
def update_holding(
    holding_id: int,
    data: HoldingUpdate,
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

    if data.quantity is not None:
        holding.quantity = data.quantity
    if data.avg_cost is not None:
        holding.avg_cost = data.avg_cost
    if data.notes is not None:
        holding.notes = data.notes

    db.commit()
    db.refresh(holding)
    return _enrich_holding(holding)


@router.delete("/holdings/{holding_id}")
def delete_holding(
    holding_id: int,
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
    db.delete(holding)
    db.commit()
    return {"message": "Posición eliminada"}


@router.post("/import/yahoo", response_model=PortfolioResponse)
def import_from_yahoo(
    data: YahooImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    imported = YahooFinanceService.import_portfolio(data.symbols)
    portfolio = Portfolio(user_id=current_user.id, name=data.portfolio_name, source="yahoo_finance")
    db.add(portfolio)
    db.flush()

    holdings = []
    for item in imported:
        if "error" in item:
            continue
        holding = Holding(
            portfolio_id=portfolio.id,
            symbol=item["symbol"],
            quantity=1.0,
            avg_cost=item.get("price", 0),
            currency=item.get("currency", "USD"),
            notes=f"Importado de Yahoo Finance - {item.get('name', '')}",
        )
        db.add(holding)
        holdings.append(holding)

    db.commit()
    db.refresh(portfolio)

    enriched = [_enrich_holding(h) for h in holdings]
    total_value = sum(h.market_value or 0 for h in enriched)
    total_cost = sum(h.avg_cost * h.quantity for h in enriched)

    return PortfolioResponse(
        id=portfolio.id,
        name=portfolio.name,
        source=portfolio.source,
        holdings=enriched,
        total_value=round(total_value, 2),
        total_cost=round(total_cost, 2),
        total_gain_loss=round(total_value - total_cost, 2),
    )
