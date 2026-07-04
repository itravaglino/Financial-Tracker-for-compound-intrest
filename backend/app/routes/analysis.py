from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Portfolio
from app.schemas import (
    TechnicalAnalysisResponse, PatternDetectionResponse,
    ValuationResponse, PortfolioAnalysisResponse, QuoteResponse,
)
from app.auth import get_current_user
from app.services.yahoo_finance import YahooFinanceService
from app.services.technical_analysis import TechnicalAnalysisService
from app.services.neural_patterns import NeuralPatternService
from app.services.valuation import ValuationService

router = APIRouter(prefix="/api/analysis", tags=["Análisis"])


@router.get("/quote/{symbol}", response_model=QuoteResponse)
def get_quote(symbol: str, current_user: User = Depends(get_current_user)):
    quote = YahooFinanceService.get_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"No se encontró el símbolo {symbol}")
    return quote


@router.get("/quotes")
def get_quotes(symbols: str, current_user: User = Depends(get_current_user)):
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    return YahooFinanceService.get_quotes(symbol_list)


@router.get("/technical/{symbol}", response_model=TechnicalAnalysisResponse)
def technical_analysis(symbol: str, current_user: User = Depends(get_current_user)):
    result = TechnicalAnalysisService.analyze(symbol)
    if not result:
        raise HTTPException(status_code=404, detail=f"No hay datos suficientes para {symbol}")
    return result


@router.get("/patterns/{symbol}", response_model=PatternDetectionResponse)
def pattern_detection(symbol: str, current_user: User = Depends(get_current_user)):
    result = NeuralPatternService.detect_patterns(symbol)
    if not result:
        raise HTTPException(status_code=404, detail=f"No hay datos suficientes para {symbol}")
    return result


@router.get("/valuation/{symbol}", response_model=ValuationResponse)
def valuation(symbol: str, current_user: User = Depends(get_current_user)):
    result = ValuationService.analyze(symbol)
    if not result:
        raise HTTPException(status_code=404, detail=f"No se pudo valorar {symbol}")
    return result


@router.get("/portfolio/{portfolio_id}", response_model=PortfolioAnalysisResponse)
def portfolio_analysis(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")

    symbols = [h.symbol for h in portfolio.holdings]
    if not symbols:
        raise HTTPException(status_code=400, detail="El portfolio no tiene posiciones")

    analysis = NeuralPatternService.compare_portfolio(symbols)
    return {
        "portfolio_id": portfolio_id,
        **analysis,
    }
