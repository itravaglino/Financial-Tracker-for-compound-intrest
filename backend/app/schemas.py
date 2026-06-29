from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)


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


class HoldingCreate(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float = 0.0
    currency: str = "USD"


class HoldingResponse(BaseModel):
    id: int
    symbol: str
    quantity: float
    avg_cost: float
    currency: str

    class Config:
        from_attributes = True


class PortfolioCreate(BaseModel):
    name: str = "Mi Portfolio"


class PortfolioResponse(BaseModel):
    id: int
    name: str
    source: str
    holdings: list[HoldingResponse] = []

    class Config:
        from_attributes = True


class YahooImportRequest(BaseModel):
    portfolio_id: int
    symbols: list[str]


class AlertCreate(BaseModel):
    symbol: str
    alert_type: str
    condition: str
    threshold: float
    message: str = ""


class AlertResponse(BaseModel):
    id: int
    symbol: str
    alert_type: str
    condition: str
    threshold: float
    message: str
    is_active: bool
    triggered: bool
    triggered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StopLossCreate(BaseModel):
    symbol: str
    quantity: float
    stop_price: float
    trailing_percent: Optional[float] = None


class StopLossResponse(BaseModel):
    id: int
    symbol: str
    quantity: float
    stop_price: float
    trailing_percent: Optional[float]
    is_active: bool
    triggered: bool

    class Config:
        from_attributes = True


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
    filled_price: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class QuoteResponse(BaseModel):
    symbol: str
    price: float
    currency: str
    change_percent: float
    volume: int
    market_cap: Optional[float] = None


class IsometricValue(BaseModel):
    symbol: str
    price_usd: float
    price_eur: float
    price_normalized: float
    currency_independence_score: float
    relative_strength_index: float


class ValuationMetrics(BaseModel):
    symbol: str
    fair_value: float
    current_price: float
    upside_percent: float
    pe_ratio: Optional[float]
    peg_ratio: Optional[float]
    dcf_value: Optional[float]
    recommendation: str
    confidence: float


class TechnicalAnalysis(BaseModel):
    symbol: str
    rsi: float
    macd: float
    macd_signal: float
    bollinger_position: float
    trend: str
    support_levels: list[float]
    resistance_levels: list[float]
    fibonacci_levels: dict[str, float]
    pattern_detected: Optional[str]
    neural_confidence: float
    signal: str


class PortfolioAnalysis(BaseModel):
    total_value_usd: float
    total_gain_loss: float
    gain_loss_percent: float
    holdings_analysis: list[dict]
    sector_allocation: dict[str, float]
    risk_score: float
    diversification_score: float
    comparison: list[dict]
