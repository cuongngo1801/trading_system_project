"""Configuration management for trading system."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str = Field(..., description="Database URL")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")


class KafkaConfig(BaseModel):
    """Kafka configuration."""

    bootstrap_servers: str = Field(..., description="Kafka bootstrap servers")
    group_id: str = Field(..., description="Consumer group ID")
    auto_offset_reset: str = Field(default="earliest", description="Auto offset reset")
    enable_auto_commit: bool = Field(default=True, description="Enable auto commit")
    session_timeout_ms: int = Field(default=30000, description="Session timeout")
    request_timeout_ms: int = Field(default=40000, description="Request timeout")


class RedisConfig(BaseModel):
    """Redis configuration."""

    url: str = Field(..., description="Redis URL")
    max_connections: int = Field(default=20, description="Max connections")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")


class TradingConfig(BaseModel):
    """Trading configuration."""

    symbols: list[str] = Field(..., description="Trading symbols")
    timeframes: list[str] = Field(..., description="Trading timeframes")
    risk_per_trade: float = Field(default=0.02, description="Risk per trade")
    max_drawdown: float = Field(default=0.15, description="Maximum drawdown")
    max_positions: int = Field(default=5, description="Maximum open positions")


class StrategyConfig(BaseModel):
    """Strategy configuration."""

    name: str = Field(..., description="Strategy name")
    d1_ema_fast: int = Field(default=50, description="D1 fast EMA period")
    d1_ema_slow: int = Field(default=200, description="D1 slow EMA period")
    h4_ema_fast: int = Field(default=20, description="H4 fast EMA period")
    h4_ema_slow: int = Field(default=50, description="H4 slow EMA period")
    adx_period: int = Field(default=14, description="ADX period")
    adx_threshold: float = Field(default=25.0, description="ADX threshold")
    atr_period: int = Field(default=14, description="ATR period")
    atr_multiplier: float = Field(default=2.0, description="ATR multiplier for stops")


class SessionConfig(BaseModel):
    """Session configuration."""

    timezone: str = Field(default="UTC", description="Base timezone")
    asian_start: str = Field(default="21:00", description="Asian session start")
    asian_end: str = Field(default="06:00", description="Asian session end")
    european_start: str = Field(default="06:00", description="European session start")
    european_end: str = Field(default="16:00", description="European session end")
    us_start: str = Field(default="13:00", description="US session start")
    us_end: str = Field(default="22:00", description="US session end")


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""

    prometheus_port: int = Field(default=9090, description="Prometheus port")
    grafana_port: int = Field(default=3000, description="Grafana port")
    metrics_interval: int = Field(default=60, description="Metrics collection interval")
    log_level: str = Field(default="INFO", description="Log level")


class Config(BaseSettings):
    """Main configuration class."""

    # Environment
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")

    # Database
    database: DatabaseConfig
    timescale_database: DatabaseConfig

    # Kafka
    kafka: KafkaConfig

    # Redis
    redis: RedisConfig

    # Trading
    trading: TradingConfig

    # Strategy
    strategy: StrategyConfig

    # Sessions
    sessions: SessionConfig

    # Monitoring
    monitoring: MonitoringConfig

    # API Keys (from environment)
    mt5_login: Optional[str] = Field(default=None, description="MT5 login")
    mt5_password: Optional[str] = Field(default=None, description="MT5 password")
    mt5_server: Optional[str] = Field(default=None, description="MT5 server")
    alpha_vantage_api_key: Optional[str] = Field(
        default=None, description="Alpha Vantage API key"
    )

    class Config:
        """Pydantic model configuration."""

        env_file = ".env"
        env_nested_delimiter = "__"


class ConfigManager:
    """Configuration manager for loading and managing configurations."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize config manager.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self._config: Optional[Config] = None
        self._config_data: Dict[str, Any] = {}

    def load_config(self, config_file: Optional[str] = None) -> Config:
        """Load configuration from file.

        Args:
            config_file: Configuration file path

        Returns:
            Loaded configuration
        """
        if config_file:
            self.config_path = config_file

        if not self.config_path:
            # Default to environment-based config
            env = os.getenv("ENVIRONMENT", "development")
            self.config_path = f"config/{env}.yaml"

        config_path = Path(self.config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as file:
            self._config_data = yaml.safe_load(file)

        # Merge with environment variables
        self._merge_env_vars()

        # Create config object
        self._config = Config(**self._config_data)

        return self._config

    def _merge_env_vars(self) -> None:
        """Merge environment variables into config."""
        # Database URLs
        if os.getenv("DATABASE_URL"):
            self._config_data.setdefault("database", {})["url"] = os.getenv(
                "DATABASE_URL"
            )

        if os.getenv("TIMESCALE_DB_URL"):
            self._config_data.setdefault("timescale_database", {})["url"] = os.getenv(
                "TIMESCALE_DB_URL"
            )

        # Kafka
        if os.getenv("KAFKA_BOOTSTRAP_SERVERS"):
            self._config_data.setdefault("kafka", {})["bootstrap_servers"] = os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS"
            )

        if os.getenv("KAFKA_GROUP_ID"):
            self._config_data.setdefault("kafka", {})["group_id"] = os.getenv(
                "KAFKA_GROUP_ID"
            )

        # Redis
        if os.getenv("REDIS_URL"):
            self._config_data.setdefault("redis", {})["url"] = os.getenv("REDIS_URL")

        # Trading
        symbols_env = os.getenv("SYMBOLS")
        if symbols_env:
            symbols = symbols_env.split(",")
            self._config_data.setdefault("trading", {})["symbols"] = symbols

        timeframes_env = os.getenv("TIMEFRAMES")
        if timeframes_env:
            timeframes = timeframes_env.split(",")
            self._config_data.setdefault("trading", {})["timeframes"] = timeframes

        # API Keys
        self._config_data["mt5_login"] = os.getenv("MT5_LOGIN")
        self._config_data["mt5_password"] = os.getenv("MT5_PASSWORD")
        self._config_data["mt5_server"] = os.getenv("MT5_SERVER")
        self._config_data["alpha_vantage_api_key"] = os.getenv("ALPHA_VANTAGE_API_KEY")

        # Environment
        self._config_data["environment"] = os.getenv("ENVIRONMENT", "development")
        self._config_data["debug"] = os.getenv("DEBUG", "false").lower() == "true"

    @property
    def config(self) -> Config:
        """Get current configuration."""
        if self._config is None:
            self.load_config()
        if self._config is None:
            raise RuntimeError("Failed to load configuration")
        return self._config

    def reload_config(self) -> Config:
        """Reload configuration from file."""
        self._config = None
        self.load_config()
        if self._config is None:
            raise RuntimeError("Failed to reload configuration")
        return self._config

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get configuration section.

        Args:
            section: Section name

        Returns:
            Configuration section
        """
        section_data = self._config_data.get(section, {})
        return section_data if isinstance(section_data, dict) else {}

    def validate_config(self) -> bool:
        """Validate configuration.

        Returns:
            True if valid, False otherwise
        """
        try:
            self.config
            return True
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False


# Global config instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get global configuration instance."""
    return config_manager.config


def load_config(config_file: str) -> Config:
    """Load configuration from specific file."""
    return config_manager.load_config(config_file)
