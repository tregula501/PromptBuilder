"""
Session state management for persisting user progress.

Automatically saves and restores application state to prevent data loss
from crashes or accidental closures.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SessionState:
    """Manages session state persistence."""

    # Session file location (in project root)
    STATE_FILE = Path(".promptbuilder_session.json")

    def __init__(self):
        """Initialize session state manager."""
        self.state: Dict[str, Any] = {}
        self._load_state()

    def _load_state(self):
        """Load saved state from file."""
        if not self.STATE_FILE.exists():
            logger.info("No existing session state found")
            self.state = self._get_default_state()
            return

        try:
            with open(self.STATE_FILE, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
                logger.info(f"Loaded session state from {self.STATE_FILE}")
                logger.debug(f"State: {self.state}")
        except Exception as e:
            logger.error(f"Error loading session state: {e}")
            self.state = self._get_default_state()

    def _get_default_state(self) -> Dict[str, Any]:
        """Get default empty state."""
        return {
            "selected_sports": [],
            "selected_game_keys": [],
            "current_tab": "Sports",
            "last_saved": None
        }

    def save(self):
        """Save current state to file."""
        try:
            self.state["last_saved"] = datetime.now().isoformat()

            with open(self.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)

            logger.debug(f"Session state saved to {self.STATE_FILE}")
        except Exception as e:
            logger.error(f"Error saving session state: {e}")

    def set(self, key: str, value: Any):
        """
        Set a state value and auto-save.

        Args:
            key: State key
            value: Value to store
        """
        self.state[key] = value
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a state value.

        Args:
            key: State key
            default: Default value if key doesn't exist

        Returns:
            Stored value or default
        """
        return self.state.get(key, default)

    def update(self, updates: Dict[str, Any]):
        """
        Update multiple state values and save.

        Args:
            updates: Dictionary of key-value pairs to update
        """
        self.state.update(updates)
        self.save()

    def clear(self):
        """Clear all state and delete file."""
        self.state = self._get_default_state()
        if self.STATE_FILE.exists():
            self.STATE_FILE.unlink()
            logger.info("Session state cleared")


# Singleton instance
_session_state = None


def get_session_state() -> SessionState:
    """Get the singleton session state instance."""
    global _session_state
    if _session_state is None:
        _session_state = SessionState()
    return _session_state
