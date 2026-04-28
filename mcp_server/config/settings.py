"""
Configuration management for MCP Server using Pydantic Settings.

Supports configuration from:
1. Environment variables (highest priority)
2. YAML configuration files
3. Default values (lowest priority)

Environment variable format:
    MCP_TRANSPORT__MODE=http
    MCP_API__BASE_URL=http://localhost:8080/reports
    MCP_LOGGING__LEVEL=DEBUG

Legacy env vars (backward-compatible):
    REPORTS_API_BASE_URL  ->  api.base_url
    MCP_TRANSPORT         ->  transport.mode
    PORT                  ->  transport.http_port
    HOST                  ->  transport.http_host
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class TransportSettings(BaseSettings):
    """Transport mode configuration."""

    mode: Literal["stdio", "http"] = Field(
        default="stdio",
        description="Transport mode: stdio (local) or http (server)"
    )
    http_host: str = Field(
        default="0.0.0.0",
        description="HTTP server host address"
    )
    http_port: int = Field(
        default=5000,
        description="HTTP server port"
    )

    model_config = SettingsConfigDict(
        env_prefix="MCP_TRANSPORT__",
        extra="ignore"
    )


class ApiSettings(BaseSettings):
    """FABRIC Reports API configuration."""

    base_url: str = Field(
        default="https://reports.fabric-testbed.net/reports",
        description="Reports API base URL"
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="API request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts"
    )
    pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="HTTP connection pool size"
    )

    model_config = SettingsConfigDict(
        env_prefix="MCP_API__",
        extra="ignore"
    )

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate that base_url starts with http:// or https://."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v.rstrip("/")


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    format: Literal["json", "text"] = Field(
        default="json",
        description="Log format: json (structured) or text (human-readable)"
    )
    destination: Literal["stdout", "file", "both"] = Field(
        default="stdout",
        description="Log destination: stdout, file, or both"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Log file path (required if destination includes 'file')"
    )
    rotation_size: str = Field(
        default="100MB",
        description="Log file rotation size (e.g., '100MB', '1GB')"
    )
    retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of days to retain log files"
    )

    model_config = SettingsConfigDict(
        env_prefix="MCP_LOGGING__",
        extra="ignore"
    )


class Settings(BaseSettings):
    """Main application settings."""

    transport: TransportSettings = Field(default_factory=TransportSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> "Settings":
        """
        Load settings from YAML file.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            Settings instance loaded from YAML

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValueError: If YAML is invalid
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        try:
            with open(yaml_path, "r") as f:
                config_dict = yaml.safe_load(f)

            if config_dict is None:
                config_dict = {}

            # Ignore monitoring section from old YAML configs
            config_dict.pop("monitoring", None)

            return cls(
                transport=TransportSettings(**config_dict.get("transport", {})),
                api=ApiSettings(**config_dict.get("api", {})),
                logging=LoggingSettings(**config_dict.get("logging", {})),
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {yaml_path}: {e}")

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Load settings from environment variables with optional YAML file.

        Supports legacy env vars for backward compatibility:
            REPORTS_API_BASE_URL -> api.base_url
            MCP_TRANSPORT        -> transport.mode
            PORT                 -> transport.http_port
            HOST                 -> transport.http_host

        Priority order:
        1. Environment variables (highest)
        2. YAML config file (if MCP_CONFIG_FILE is set)
        3. Default YAML based on MCP_ENV (dev/staging/prod)
        4. Default values (lowest)

        Returns:
            Settings instance
        """
        # Map legacy env vars before loading settings
        _map_legacy_env()

        # Check for explicit config file
        config_file = os.getenv("MCP_CONFIG_FILE")

        # If no explicit file, check for environment-based config
        if not config_file:
            mcp_env = os.getenv("MCP_ENV", "prod")
            default_config_path = Path(__file__).parent / f"config.{mcp_env}.yml"

            if default_config_path.exists():
                config_file = str(default_config_path)

        # Load from YAML if available
        if config_file and Path(config_file).exists():
            settings = cls.from_yaml(config_file)
        else:
            settings = cls()

        return settings

    def validate(self) -> None:
        """
        Validate configuration and fail fast on errors.

        Raises:
            ValueError: If configuration is invalid
        """
        errors = []

        # Validate logging configuration
        if self.logging.destination in ["file", "both"]:
            if not self.logging.file_path:
                errors.append(
                    "logging.file_path is required when destination is 'file' or 'both'"
                )

        # Validate transport configuration
        if self.transport.mode not in ["stdio", "http"]:
            errors.append(
                f"Invalid transport.mode: {self.transport.mode}. Must be 'stdio' or 'http'"
            )

        if errors:
            raise ValueError(f"Configuration validation failed:\n  " + "\n  ".join(errors))


def _map_legacy_env() -> None:
    """
    Map legacy environment variables to the new nested format.

    Only sets the new variable if it is not already defined,
    so explicit new-style vars always win.
    """
    mapping = {
        # legacy var -> new-style var
        "REPORTS_API_BASE_URL": "MCP_API__BASE_URL",
        "MCP_TRANSPORT": "MCP_TRANSPORT__MODE",
        "PORT": "MCP_TRANSPORT__HTTP_PORT",
        "HOST": "MCP_TRANSPORT__HTTP_HOST",
    }
    for old_key, new_key in mapping.items():
        val = os.environ.get(old_key)
        if val is not None and new_key not in os.environ:
            os.environ[new_key] = val


def get_settings() -> Settings:
    """
    Get application settings.

    This is the main entry point for accessing configuration.
    Loads settings from environment variables and optional YAML file.

    Returns:
        Validated Settings instance
    """
    settings = Settings.from_env()
    settings.validate()
    return settings
