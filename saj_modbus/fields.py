"""Clock register helpers + modbus-connection field.

All SAJ families use the same 4-register clock layout::

    [year, (month << 8) + day, (hour << 8) + minute, second << 8 (+reserved)]

The pure ``decode_clock_words`` / ``encode_clock_words`` helpers carry the
logic so they can be unit-tested without Modbus or hardware.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def decode_clock_words(words: list[int]) -> datetime | None:
    """Decode 4 clock words into a local-timezone datetime (None if invalid)."""
    try:
        return datetime(
            year=words[0],
            month=words[1] >> 8,
            day=words[1] & 0xFF,
            hour=words[2] >> 8,
            minute=words[2] & 0xFF,
            second=words[3] >> 8,
        ).astimezone()
    except (ValueError, IndexError):
        return None


def encode_clock_words(value: datetime) -> list[int]:
    """Pack a datetime into 4 clock words."""
    return [
        value.year,
        (value.month << 8) + value.day,
        (value.hour << 8) + value.minute,
        value.second << 8,
    ]


try:  # optional at test time; required at runtime
    from modbus_connection.model import RegisterField

    class DateTimeField(RegisterField[datetime]):
        """Inverter clock: year word, then month/day, hour/minute, second bytes."""

        def decode(
            self, words: list[int], scale_exponent: int | None = None
        ) -> datetime | None:
            return decode_clock_words(words)

        def encode(
            self, value: Any, scale_exponent: int | None = None
        ) -> list[int]:
            return encode_clock_words(value)

except ImportError:  # pragma: no cover - allows pure-logic tests w/o dependency

    class DateTimeField:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("modbus-connection is required at runtime")
