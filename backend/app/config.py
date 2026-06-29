from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "FinTrack Pro"
    secret_key: str = "change-me-in-production-use-env-var"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./fintrack.db"
    base_currency: str = "USD"
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    alert_check_interval_seconds: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
