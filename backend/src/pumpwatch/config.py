from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/pumpwatch"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    admin_api_key: str = ""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    dex_screener_api_url: str = "https://api.dexscreener.com/latest"
    gecko_terminal_api_url: str = "https://api.geckoterminal.com/api/v2"

    request_timeout: int = 30
    rate_limit_delay: float = 1.0

    min_liquidity_usd: float = 5000.0
    momentum_threshold: int = 65
    alert_cooldown_minutes: int = 60

    # Background scanner
    scan_interval_minutes: int = 5
    scan_on_startup: bool = True

    # Historical data archive
    archive_interval_minutes: int = 60
    archive_retention_days: int = 90

    # Analytics aggregation
    analytics_aggregation_interval_minutes: int = 60

    # Backtest
    backtest_default_fee_percent: float = 0.01
    backtest_default_slippage_percent: float = 0.005
    backtest_max_concurrent_runs: int = 2


settings = Settings()
