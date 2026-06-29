from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import User
from app.services.neural_analysis import NeuralAnalysisService
from app.services.technical_analysis import TechnicalAnalysisService
from app.services.valuation import ValuationService
from app.services.yahoo_finance import YahooFinanceService

router = APIRouter(prefix="/market", tags=["Mercado y Análisis"])


@router.get("/quote/{symbol}")
def get_quote(symbol: str, _: User = Depends(get_current_user)):
    return YahooFinanceService.get_quote(symbol)


@router.get("/fundamentals/{symbol}")
def get_fundamentals(symbol: str, _: User = Depends(get_current_user)):
    return YahooFinanceService.get_fundamentals(symbol)


@router.get("/analysis/technical/{symbol}")
def technical_analysis(symbol: str, period: str = "1y", _: User = Depends(get_current_user)):
    return TechnicalAnalysisService.full_analysis(symbol, period=period)


@router.get("/analysis/neural/{symbol}")
def neural_analysis(symbol: str, period: str = "2y", _: User = Depends(get_current_user)):
    return NeuralAnalysisService.analyze_symbol(symbol, period=period)


@router.get("/analysis/portfolio-contrast")
def portfolio_contrast(symbols: str, _: User = Depends(get_current_user)):
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return TechnicalAnalysisService.portfolio_contrast(symbol_list)


@router.get("/analysis/portfolio-neural")
def portfolio_neural(symbols: str, _: User = Depends(get_current_user)):
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return NeuralAnalysisService.portfolio_neural_analysis(symbol_list)


@router.get("/valuation/{symbol}")
def objective_valuation(symbol: str, _: User = Depends(get_current_user)):
    return ValuationService.objective_valuation(symbol)


@router.get("/valuation/isometric")
def isometric_valuation(symbols: str, _: User = Depends(get_current_user)):
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return ValuationService.isometric_value(symbol_list)


@router.get("/metrics/{symbol}")
def special_metrics(symbol: str, _: User = Depends(get_current_user)):
    return ValuationService.special_metrics(symbol)
