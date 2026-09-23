"""Clock register helpers + modbus-connection field.

All SAJ families use the same 4-register clock layout::

    [year, (month << 8) + day, (hour << 8) + minute, second << 8 (+reserved)]

The pure ``decode_clock_words`` / ``encode_clock_words`` helpers carry the
logic so they can be unit-tested without Modbus or hardware. History fault
timestamps use the BCD twin ``decode_bcd_clock_words``.
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


def _bcd_byte(value: int) -> int | None:
    """One BCD-encoded byte to int; None if any nibble exceeds 9."""
    high, low = (value >> 4) & 0x0F, value & 0x0F
    if high > 9 or low > 9:
        return None
    return high * 10 + low


def decode_bcd_clock_words(words: list[int]) -> datetime | None:
    """Decode 4 BCD history-time words into a naive datetime (None if empty/invalid).

    Layout mirrors the binary clock (year word, month/day, hour/minute,
    second/reserved) with each byte BCD-encoded instead. All-zero and
    all-``0xFFFF`` slots (never-written history entries) decode to None.
    """
    try:
        year_high = _bcd_byte(words[0] >> 8)
        year_low = _bcd_byte(words[0] & 0xFF)
        month = _bcd_byte(words[1] >> 8)
        day = _bcd_byte(words[1] & 0xFF)
        hour = _bcd_byte(words[2] >> 8)
        minute = _bcd_byte(words[2] & 0xFF)
        second = _bcd_byte(words[3] >> 8)
    except IndexError:
        return None
    parts = (year_high, year_low, month, day, hour, minute, second)
    if any(part is None for part in parts):
        return None
    assert None not in parts  # for typing; checked above
    try:
        return datetime(
            year=year_high * 100 + year_low,  # type: ignore[operator]
            month=month,  # type: ignore[arg-type]
            day=day,  # type: ignore[arg-type]
            hour=hour,  # type: ignore[arg-type]
            minute=minute,  # type: ignore[arg-type]
            second=second,  # type: ignore[arg-type]
        )
    except ValueError:
        return None


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
