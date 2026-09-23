"""Measurement field factories with unpopulated-input sentinel handling.

SAJ inverters answer unconnected inputs (spare phases, missing MPPT strings)
with all-set words (``0xFFFF`` / ``0xFFFFFFFF``). Passing those through as
readings produces phantom data (6553.5 V, 655.35 A, ...), so every numeric
*measurement* field is declared through these wrappers, which set the
library-native ``nan=`` sentinel: such words decode to ``None`` (unavailable)
instead of a bogus value.

Enum/mode/fault/direction words and writable settings keep the raw factories
from ``modbus_connection.model`` — with an explicit ``nan=None`` where the
distinction matters.
"""

from __future__ import annotations

from typing import Any

from modbus_connection.model import gauge as _gauge
from modbus_connection.model import integer as _integer
from modbus_connection.model import uint32 as _uint32


def mgauge(address: int, *args: Any, **kwargs: Any) -> Any:
    """Like :func:`gauge`, but raw ``0xFFFF`` decodes to ``None``."""
    kwargs.setdefault("nan", 0xFFFF)
    return _gauge(address, *args, **kwargs)


def minteger(address: int, *args: Any, **kwargs: Any) -> Any:
    """Like :func:`integer`, but raw ``0xFFFF`` decodes to ``None``."""
    kwargs.setdefault("nan", 0xFFFF)
    return _integer(address, *args, **kwargs)


def muint32(address: int, *args: Any, **kwargs: Any) -> Any:
    """Like :func:`uint32`, but raw ``0xFFFFFFFF`` decodes to ``None``."""
    kwargs.setdefault("nan", 0xFFFFFFFF)
    return _uint32(address, *args, **kwargs)
