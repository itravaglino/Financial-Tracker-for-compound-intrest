from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# Auth
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Portfolio
class HoldingCreate(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    currency: str = "USD"
    notes: Optional[str] = None


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_cost: Optional[float] = None
    notes: Optional[str] = None


class HoldingResponse(BaseModel):
    id: int
    symbol: str
    quantity: float
    avg_cost: float
    currency: str
    notes: Optional[str]
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    gain_loss: Optional[float] = None
    gain_loss_pct: Optional[float] = None
    isosteric_value: Optional[float] = None
    intrinsic_value: Optional[float] = None
    valuation_rating: Optional[str] = None

    class Config:
        from_attributes = True


class PortfolioCreate(BaseModel):
    name: str = "Mi Portfolio"


class PortfolioResponse(BaseModel):
    id: int
    name: str
    yahoo_portfolio_id: Optional[str]
    created_at: datetime
    holdings: list[HoldingResponse] = []
    total_value: Optional[float] = None
    total_gain_loss: Optional[float] = None
    total_gain_loss_pct: Optional[float] = None

    class Config:
        from_attributes = True


class YahooImportRequest(BaseModel):
    symbols: list[str]
    portfolio_name: str = "Importado de Yahoo Finance"


# Analysis
class TechnicalAnalysisResponse(BaseModel):
    symbol: str
    rsi: Optional[float]
    macd: Optional[float]
    macd_signal: Optional[float]
    sma_20: Optional[float]
    sma_50: Optional[float]
    sma_200: Optional[float]
    bollinger_upper: Optional[float]
    bollinger_lower: Optional[float]
    fibonacci_levels: dict
    support_levels: list[float]
    resistance_levels: list[float]
    trend: str
    signals: list[str]


class PatternDetectionResponse(BaseModel):
    symbol: str
    patterns: list[dict]
    fibonacci_retracements: dict
    neural_confidence: float
    neural_accuracy: Optional[float] = None
    prediction_direction: str
    prediction_confidence: float


class ValuationResponse(BaseModel):
    symbol: str
    current_price: float
    intrinsic_value: float
    isosteric_value: float
    currency: str
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    peg_ratio: Optional[float]
    dividend_yield: Optional[float]
    fair_value_range: dict
    rating: str
    rating_score: float
    metrics: dict


class PortfolioAnalysisResponse(BaseModel):
    portfolio_id: int
    holdings_analysis: list[dict]
    sector_allocation: dict
    risk_score: float
    diversification_score: float
    correlation_matrix: dict
    recommendations: list[str]


# Alerts
class AlertCreate(BaseModel):
    symbol: str
    alert_type: str
    threshold: Optional[float] = None
    message: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    symbol: str
    alert_type: str
    threshold: Optional[float]
    message: Optional[str]
    is_active: bool
    triggered: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Stop Loss
class StopLossCreate(BaseModel):
    symbol: str
    quantity: float
    trigger_price: float
    trailing_percent: Optional[float] = None


class StopLossResponse(BaseModel):
    id: int
    symbol: str
    quantity: float
    trigger_price: float
    trailing_percent: Optional[float]
    is_active: bool
    triggered: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Trading
class OrderCreate(BaseModel):
    symbol: str
    side: str
    quantity: float
    order_type: str = "market"
    limit_price: Optional[float] = None


class OrderResponse(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: float
    order_type: str
    limit_price: Optional[float]
    status: str
    external_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class QuoteResponse(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float]
    currency: str
    timestamp: datetime


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
