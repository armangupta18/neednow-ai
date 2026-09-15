import logging
import sys
import json
from datetime import datetime, timezone
import os

from app.core.settings import settings


class HumanFormatter(logging.Formatter):
    """Human-friendly, compact logging formatter.

    Output format (single line):
      2026-09-12T21:49:15.832Z | INFO | name | Short 4-5 word message [id=...]

    If an exception is present, the full traceback is printed on the
    following lines prefixed with "EXCEPTION:" so the single-line feed
    stays compact for quick scanning.
    """

    def format(self, record: logging.LogRecord) -> str:
        # ISO-like UTC timestamp with Z
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        # Shorten message to first 4-5 words
        full_msg = record.getMessage()
        words = full_msg.strip().split()
        short_msg = " ".join(words[:5])
        if len(words) > 5:
            short_msg = short_msg + "..."
        # Build compact single-line message WITHOUT source file or request id
        # (user requested to omit those from compact header)
        extras = []
        if hasattr(record, "key_number"):
            extras.append(f"key={record.key_number}")

        extras_txt = ""
        if extras:
            extras_txt = " [" + ", ".join(extras) + "]"

        base = f"{ts} | {record.levelname} | {short_msg}{extras_txt}"

        # Colorize level (if terminal supports ANSI). Use colorama on Windows if available
        COLOR_RESET = "\x1b[0m"
        COLOR_MAP = {
            "DEBUG": "\x1b[36m",
            "INFO": "\x1b[32m",
            "WARNING": "\x1b[33m",
            "ERROR": "\x1b[31m",
            "CRITICAL": "\x1b[41m",
        }

        def supports_color() -> bool:
            if os.name == "nt":
                try:
                    # try enabling colorama if available
                    import colorama

                    colorama.init()
                    return True
                except Exception:
                    return False
            return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

        if supports_color():
            level_color = COLOR_MAP.get(record.levelname, "")
            # Replace level name in the single-line output with colored level
            base = base.replace(f"| {record.levelname} |", f"| {level_color}{record.levelname}{COLOR_RESET} |")

        # If there's exception info, append full traceback on next lines with label
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            if supports_color():
                exc_header = "\nEXCEPTION:\n"
                exc_block = f"{COLOR_MAP.get('ERROR','')}" + exc_text + COLOR_RESET
                return base + exc_header + exc_block
            return base + "\nEXCEPTION:\n" + exc_text

        return base


def setup_logger():
    """Configure root logger to emit JSON-formatted log lines to stdout."""

    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(HumanFormatter())

    root.handlers.clear()
    root.addHandler(console_handler)

    return logging.getLogger("neednow")


logger = setup_logger()