"""
logger.py

Append-only forensic acquisition logger.
"""

from pathlib import Path
from datetime import datetime, timezone


class AcquisitionLogger:
    """
    Append-only acquisition logger.
    """

    def __init__(self, log_path):
        self.log_path = Path(log_path)

    def _timestamp(self):
        """
        UTC timestamp with milliseconds.
        """

        return (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

    def write(self, level, message):
        """
        Write log entry.
        """

        entry = (
            f"{self._timestamp()} "
            f"[{level}] "
            f"{message}\n"
        )

        with open(
            self.log_path,
            "a",
            encoding="utf-8"
        ) as log_file:
            log_file.write(entry)

    def info(self, message):
        """
        INFO log.
        """

        self.write("INFO", message)

    def warn(self, message):
        """
        WARN log.
        """

        self.write("WARN", message)

    def error(self, message):
        """
        ERROR log.
        """

        self.write("ERROR", message)