import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class TradingService:
    def __init__(self):
        self.api_key = settings.alpaca_api_key
        self.secret_key = settings.alpaca_secret_key
        self.base_url = settings.alpaca_base_url

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.secret_key)

    def _headers(self) -> dict:
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json",
        }

    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        limit_price: Optional[float] = None,
    ) -> dict:
        if not self.is_configured:
            return self._simulate_order(symbol, side, quantity, order_type, limit_price)

        order_data = {
            "symbol": symbol.upper(),
            "qty": str(quantity),
            "side": side.lower(),
            "type": order_type.lower(),
            "time_in_force": "gtc",
        }
        if order_type.lower() == "limit" and limit_price:
            order_data["limit_price"] = str(limit_price)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v2/orders",
                    json=order_data,
                    headers=self._headers(),
                    timeout=30,
                )
                if response.status_code in (200, 201):
                    data = response.json()
                    return {
                        "status": data.get("status", "submitted"),
                        "external_id": data.get("id"),
                        "filled_price": float(data.get("filled_avg_price", 0) or 0),
                        "simulated": False,
                    }
                logger.error("Alpaca order failed: %s", response.text)
                return {"status": "failed", "error": response.text, "simulated": False}
        except Exception as e:
            logger.error("Trading API error: %s", e)
            return {"status": "failed", "error": str(e), "simulated": False}

    def _simulate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str,
        limit_price: Optional[float],
    ) -> dict:
        from app.services.yahoo_finance import yahoo_service

        quote = yahoo_service.get_quote(symbol)
        price = limit_price or quote["price"]
        return {
            "status": "filled",
            "external_id": f"SIM-{symbol}-{side}",
            "filled_price": price,
            "simulated": True,
            "message": "Orden simulada (configura ALPACA_API_KEY para trading real)",
        }

    async def get_account(self) -> dict:
        if not self.is_configured:
            return {"status": "simulated", "buying_power": 100000, "cash": 100000}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v2/account",
                    headers=self._headers(),
                    timeout=30,
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error("Account fetch error: %s", e)
        return {"status": "error"}


trading_service = TradingService()
