from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Portfolio, Holding
from app.schemas import (
    PortfolioCreate, PortfolioResponse, HoldingCreate, HoldingUpdate,
    HoldingResponse, YahooImportRequest,
)
from app.auth import get_current_user
from app.services.yahoo_finance import YahooFinanceService
from app.services.valuation import ValuationService

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


def _enrich_holding(holding: Holding) -> dict:
    quote = YahooFinanceService.get_quote(holding.symbol)
    valuation = ValuationService.analyze(holding.symbol)

    data = {
        "id": holding.id,
        "symbol": holding.symbol,
        "quantity": holding.quantity,
        "avg_cost": holding.avg_cost,
        "currency": holding.currency,
        "notes": holding.notes,
        "current_price": None,
        "market_value": None,
        "gain_loss": None,
        "gain_loss_pct": None,
        "isosteric_value": None,
        "intrinsic_value": None,
        "valuation_rating": None,
    }

    if quote:
        data["current_price"] = quote["price"]
        data["market_value"] = round(quote["price"] * holding.quantity, 2)
        cost_basis = holding.avg_cost * holding.quantity
        data["gain_loss"] = round(data["market_value"] - cost_basis, 2)
        data["gain_loss_pct"] = round((data["gain_loss"] / cost_basis * 100) if cost_basis else 0, 2)

    if valuation:
        data["isosteric_value"] = valuation["isosteric_value"]
        data["intrinsic_value"] = valuation["intrinsic_value"]
        data["valuation_rating"] = valuation["rating"]

    return data


@router.get("/", response_model=list[PortfolioResponse])
def list_portfolios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    result = []
    for p in portfolios:
        holdings_data = [_enrich_holding(h) for h in p.holdings]
        total_value = sum(h.get("market_value") or 0 for h in holdings_data)
        total_cost = sum(h["avg_cost"] * h["quantity"] for h in holdings_data)
        total_gl = total_value - total_cost
        result.append({
            "id": p.id,
            "name": p.name,
            "yahoo_portfolio_id": p.yahoo_portfolio_id,
            "created_at": p.created_at,
            "holdings": holdings_data,
            "total_value": round(total_value, 2),
            "total_gain_loss": round(total_gl, 2),
            "total_gain_loss_pct": round((total_gl / total_cost * 100) if total_cost else 0, 2),
        })
    return result


@router.post("/", response_model=PortfolioResponse, status_code=201)
def create_portfolio(
    data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = Portfolio(user_id=current_user.id, name=data.name)
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "yahoo_portfolio_id": None,
        "created_at": portfolio.created_at,
        "holdings": [],
        "total_value": 0,
        "total_gain_loss": 0,
        "total_gain_loss_pct": 0,
    }


@router.post("/import-yahoo", response_model=PortfolioResponse, status_code=201)
def import_from_yahoo(
    data: YahooImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Importa portfolio desde símbolos de Yahoo Finance."""
    if not data.symbols:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos un símbolo")

    portfolio = Portfolio(
        user_id=current_user.id,
        name=data.portfolio_name,
        yahoo_portfolio_id="yahoo_import",
    )
    db.add(portfolio)
    db.flush()

    imported = YahooFinanceService.import_portfolio_symbols(data.symbols)
    for item in imported:
        holding = Holding(
            portfolio_id=portfolio.id,
            symbol=item["symbol"],
            quantity=0,
            avg_cost=item["current_price"],
            currency=item["currency"],
            notes=f"Importado: {item.get('name', '')}",
        )
        db.add(holding)

    db.commit()
    db.refresh(portfolio)
    holdings_data = [_enrich_holding(h) for h in portfolio.holdings]
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "yahoo_portfolio_id": portfolio.yahoo_portfolio_id,
        "created_at": portfolio.created_at,
        "holdings": holdings_data,
        "total_value": 0,
        "total_gain_loss": 0,
        "total_gain_loss_pct": 0,
    }


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=201)
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
    holding = db.query(Holding).join(Portfolio).filter(
        Holding.id == holding_id, Portfolio.user_id == current_user.id
    ).first()
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


@router.delete("/holdings/{holding_id}", status_code=204)
def delete_holding(
    holding_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    holding = db.query(Holding).join(Portfolio).filter(
        Holding.id == holding_id, Portfolio.user_id == current_user.id
    ).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Posición no encontrada")
    db.delete(holding)
    db.commit()
