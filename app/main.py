"""
PromptBuilder - AI Sportsbook Betting Prompt Generator

Main entry point for the application.
"""

import sys
import logging
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_config
from app.ui.app_window import PromptBuilderApp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / 'app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    try:
        logger.info("Starting PromptBuilder application...")

        # Load configuration
        config = get_config()
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Project root: {config.PROJECT_ROOT}")

        # Create and run the app
        app = PromptBuilderApp()
        app.mainloop()

    except Exception as e:
        logger.error(f"Fatal error starting application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
