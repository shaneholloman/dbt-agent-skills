"""Logging configuration for skill-eval."""

import sys
import threading
from typing import Any

from loguru import logger

# Custom format function to include context when available
def _format_record(record: Any) -> str:
    """Format log record with optional context (scenario, skill_set, thread)."""
    extra = record.get("extra", {})

    # Build context prefix
    context_parts = []
    if "scenario" in extra:
        context_parts.append(extra["scenario"])
    if "skill_set" in extra:
        context_parts.append(extra["skill_set"])

    # Add thread number for parallel runs
    thread_id = threading.current_thread().name
    if thread_id != "MainThread":
        # Extract thread number from ThreadPoolExecutor naming (e.g., "ThreadPoolExecutor-0_1")
        if "_" in thread_id:
            thread_num = thread_id.split("_")[-1]
            context_parts.insert(0, f"T{thread_num}")

    context = "/".join(context_parts)
    context_str = f"<cyan>[{context}]</cyan> " if context else ""

    return (
        "<dim>{time:HH:mm:ss}</dim> | "
        "<level>{level: <7}</level> | "
        f"{context_str}"
        "{message}\n"
    )


# Remove default handler
logger.remove()

# Add custom handler
logger.add(
    sys.stderr,
    format=_format_record,
    level="INFO",
    colorize=True,
)


def set_level(level: str) -> None:
    """Set the logging level."""
    logger.remove()
    logger.add(
        sys.stderr,
        format=_format_record,
        level=level.upper(),
        colorize=True,
    )


__all__ = ["logger", "set_level"]
