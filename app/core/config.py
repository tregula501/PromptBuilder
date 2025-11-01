"""
Configuration management for PromptBuilder.

Handles loading environment variables, user settings, and application configuration.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Application configuration manager."""

    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    APP_DIR = PROJECT_ROOT / "app"
    TEMPLATES_DIR = PROJECT_ROOT / "templates"
    PROMPTS_DIR = PROJECT_ROOT / "prompts"
    ASSETS_DIR = PROJECT_ROOT / "assets"
    CONFIG_FILE = PROJECT_ROOT / "config.json"

    def __init__(self):
        """Initialize configuration by loading environment variables and user settings."""
        # Load environment variables from .env file
        env_path = self.PROJECT_ROOT / ".env"
        load_dotenv(env_path)

        # Ensure required directories exist
        self._create_directories()

        # Load or create user settings
        self.settings = self._load_settings()

        # API Configuration
        self.odds_api_key = os.getenv("ODDS_API_KEY", "")
        self.espn_api_key = os.getenv("ESPN_API_KEY", "")
        self.rapid_api_key = os.getenv("RAPID_API_KEY", "")

        # GitHub Configuration
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github_username = os.getenv("GITHUB_USERNAME", "tregula501")
        self.github_repo = os.getenv("GITHUB_REPO", "PromptBuilder")

        # Application Settings
        self.default_max_odds = int(os.getenv("DEFAULT_MAX_ODDS", "400"))
        self.auto_save_to_github = os.getenv("AUTO_SAVE_TO_GITHUB", "false").lower() == "true"
        self.auto_commit = os.getenv("AUTO_COMMIT", "false").lower() == "true"

        # Data Source Settings
        self.enable_api_fetch = os.getenv("ENABLE_API_FETCH", "true").lower() == "true"
        self.enable_web_scraping = os.getenv("ENABLE_WEB_SCRAPING", "false").lower() == "true"
        self.scraping_delay = int(os.getenv("SCRAPING_DELAY", "2"))

        # Advanced Settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.cache_duration = int(os.getenv("CACHE_DURATION", "15"))

        # Set log level
        logging.getLogger().setLevel(getattr(logging, self.log_level))

    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        for directory in [self.TEMPLATES_DIR, self.PROMPTS_DIR, self.ASSETS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

    def _load_settings(self) -> Dict[str, Any]:
        """Load user settings from config file."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    settings = json.load(f)
                    logger.info("Loaded user settings from config.json")
                    return settings
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                return self._default_settings()
        else:
            logger.info("No config file found, using default settings")
            return self._default_settings()

    def _default_settings(self) -> Dict[str, Any]:
        """Return default application settings."""
        return {
            "selected_sports": ["NFL", "NBA"],
            "max_combined_odds": 400,
            "bet_types": {
                "moneyline": True,
                "spread": True,
                "totals": True,
                "parlay": True,
                "props": False,
                "teasers": False
            },
            "analysis_types": {
                "value_betting": True,
                "risk_assessment": True,
                "statistical_predictions": True
            },
            "ai_model": "Generic/Multiple",
            "risk_tolerance": "Medium",
            "sportsbooks": [],
            "custom_prompt_template": "",
            "theme": "dark",
            "last_data_source": "api"
        }

    def save_settings(self):
        """Save current settings to config file."""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any):
        """Set a specific setting value."""
        self.settings[key] = value
        self.save_settings()

    def update_settings(self, updates: Dict[str, Any]):
        """Update multiple settings at once."""
        self.settings.update(updates)
        self.save_settings()

    def has_api_key(self, api_name: str) -> bool:
        """Check if a specific API key is configured."""
        api_keys = {
            "odds": self.odds_api_key,
            "espn": self.espn_api_key,
            "rapid": self.rapid_api_key
        }
        return bool(api_keys.get(api_name.lower(), ""))

    def has_github_configured(self) -> bool:
        """Check if GitHub is properly configured."""
        return bool(self.github_token and self.github_username and self.github_repo)

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all current settings."""
        return {
            "user_settings": self.settings,
            "api_configured": {
                "odds_api": self.has_api_key("odds"),
                "espn_api": self.has_api_key("espn"),
                "rapid_api": self.has_api_key("rapid")
            },
            "github_configured": self.has_github_configured(),
            "app_config": {
                "default_max_odds": self.default_max_odds,
                "auto_save_to_github": self.auto_save_to_github,
                "auto_commit": self.auto_commit,
                "enable_api_fetch": self.enable_api_fetch,
                "enable_web_scraping": self.enable_web_scraping
            }
        }


# Global config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reset_config():
    """Reset the global configuration instance (mainly for testing)."""
    global _config_instance
    _config_instance = None
