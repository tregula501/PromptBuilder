"""
Command history for undo/redo functionality.

Implements the Command pattern to enable undo/redo of user selections.
"""

from typing import List, Any, Dict, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class CommandState:
    """Represents a state snapshot for undo/redo."""
    sports_selected: List[str]
    games_selected: List[str]


class Command(ABC):
    """Abstract base class for commands."""

    @abstractmethod
    def execute(self):
        """Execute the command."""
        pass

    @abstractmethod
    def undo(self):
        """Undo the command."""
        pass


class SelectionCommand(Command):
    """Command for selection changes."""

    def __init__(self, tab_widget, old_state: Any, new_state: Any, selection_type: str):
        """
        Initialize selection command.

        Args:
            tab_widget: The tab widget (SportsSelectionTab or GameSelectionTab)
            old_state: Previous selection state
            new_state: New selection state
            selection_type: "sports" or "games"
        """
        self.tab_widget = tab_widget
        self.old_state = old_state
        self.new_state = new_state
        self.selection_type = selection_type

    def execute(self):
        """Execute the command (apply new state)."""
        self._apply_state(self.new_state)

    def undo(self):
        """Undo the command (restore old state)."""
        self._apply_state(self.old_state)

    def _apply_state(self, state: Any):
        """Apply a state to the tab widget."""
        if self.selection_type == "sports":
            self.tab_widget.set_selected_sports(state)
        elif self.selection_type == "games":
            self.tab_widget.set_selected_games(state)


class CommandHistory:
    """Manages command history for undo/redo."""

    # Maximum history size to prevent unbounded memory growth
    MAX_HISTORY_SIZE = 50

    def __init__(self):
        """Initialize command history."""
        self.history: List[Command] = []
        self.current_index: int = -1

    def execute(self, command: Command):
        """
        Execute a command and add it to history.

        Args:
            command: Command to execute
        """
        # Execute the command
        command.execute()

        # Remove any commands after current index (when undoing then making new changes)
        self.history = self.history[:self.current_index + 1]

        # Add command to history
        self.history.append(command)
        self.current_index += 1

        # Limit history size
        if len(self.history) > self.MAX_HISTORY_SIZE:
            self.history.pop(0)
            self.current_index -= 1

        logger.debug(f"Command executed. History size: {len(self.history)}, Index: {self.current_index}")

    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self.current_index >= 0

    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self.current_index < len(self.history) - 1

    def undo(self):
        """Undo the last command."""
        if not self.can_undo():
            logger.warning("Cannot undo: no commands in history")
            return

        command = self.history[self.current_index]
        command.undo()
        self.current_index -= 1

        logger.info(f"Undo executed. New index: {self.current_index}")

    def redo(self):
        """Redo the next command."""
        if not self.can_redo():
            logger.warning("Cannot redo: at end of history")
            return

        self.current_index += 1
        command = self.history[self.current_index]
        command.execute()

        logger.info(f"Redo executed. New index: {self.current_index}")

    def clear(self):
        """Clear command history."""
        self.history.clear()
        self.current_index = -1
        logger.info("Command history cleared")


# Singleton instance
_command_history = None


def get_command_history() -> CommandHistory:
    """Get the singleton command history instance."""
    global _command_history
    if _command_history is None:
        _command_history = CommandHistory()
    return _command_history
