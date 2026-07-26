"""
Logging utility using Rich console formatting.
"""

import logging
from rich.console import Console
from rich.logging import RichHandler

console = Console()


def setup_logger(level=logging.INFO):
    """Configures structured logging with Rich styling."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True)]
    )
    return logging.getLogger("android_agent")


logger = setup_logger()
