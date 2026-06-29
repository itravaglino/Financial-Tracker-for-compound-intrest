from fastapi import APIRouter, Depends, HTTPException

from app.auth.security import get_current_user
from app.ml.technical_analysis import technical_service
from app.models import User
from app.services.valuation import valuation_service
from app.services.yahoo_finance import yahoo_service

router = APIRouter(prefix="/market", tags=["Mercado"])


@router.get("/quote/{symbol}")
def get_quote(symbol: str, user: User = Depends(get_current_user)):
    try:
        return yahoo_service.get_quote(symbol)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/quotes")
def get_quotes(symbols: str, user: User = Depends(get_current_user)):
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return yahoo_service.get_batch_quotes(symbol_list)


@router.get("/isometric/{symbol}")
def get_isometric_value(symbol: str, user: User = Depends(get_current_user)):
    try:
        return yahoo_service.get_isometric_value(symbol)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/valuation/{symbol}")
def get_valuation(symbol: str, user: User = Depends(get_current_user)):
    try:
        return valuation_service.get_valuation(symbol)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/technical/{symbol}")
def get_technical_analysis(symbol: str, user: User = Depends(get_current_user)):
    try:
        return technical_service.analyze(symbol)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/compare")
def compare_stocks(symbols: str, user: User = Depends(get_current_user)):
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if len(symbol_list) < 2:
        raise HTTPException(status_code=400, detail="Proporciona al menos 2 símbolos")
    return technical_service.compare_symbols(symbol_list)
