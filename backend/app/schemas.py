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
    quantity: float = Field(gt=0)
    avg_cost: float = Field(gt=0)
    currency: str = "USD"
    notes: str = ""


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
    notes: str
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    gain_loss: Optional[float] = None
    gain_loss_pct: Optional[float] = None

    class Config:
        from_attributes = True


class PortfolioCreate(BaseModel):
    name: str = "Mi Portfolio"


class PortfolioResponse(BaseModel):
    id: int
    name: str
    source: str
    holdings: list[HoldingResponse] = []
    total_value: Optional[float] = None
    total_cost: Optional[float] = None
    total_gain_loss: Optional[float] = None

    class Config:
        from_attributes = True


class YahooImportRequest(BaseModel):
    symbols: list[str]
    portfolio_name: str = "Yahoo Finance Import"


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
    trigger_price: float = Field(gt=0)
    stop_type: str = "fixed"
    trailing_percent: Optional[float] = None


class StopLossResponse(BaseModel):
    id: int
    holding_id: int
    trigger_price: float
    stop_type: str
    trailing_percent: Optional[float] = None
    is_active: bool
    triggered: bool

    class Config:
        from_attributes = True


class TradeOrderCreate(BaseModel):
    symbol: str
    side: str
    quantity: float = Field(gt=0)
    order_type: str = "market"
    limit_price: Optional[float] = None


class TradeOrderResponse(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: float
    order_type: str
    limit_price: Optional[float] = None
    status: str
    broker_order_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BrokerConfigCreate(BaseModel):
    api_key: str
    secret_key: str
    base_url: str = "https://paper-api.alpaca.markets"
    is_paper: bool = True


class BrokerConfigResponse(BaseModel):
    id: int
    base_url: str
    is_paper: bool
    configured: bool = True

    class Config:
        from_attributes = True
