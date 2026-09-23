"""Pure control helpers (no Modbus import, safe to unit-test)."""

from __future__ import annotations


def encode_rs485_ate(baudrate: int, slave: int) -> int:
    """Pack baud rate + slave number for special register 0x8014.

    Baud codes: 9600 -> 4, 4800 -> 5, 2400 -> 6, 1200 -> 7. Slave 1-32.
    """
    codes = {9600: 4, 4800: 5, 2400: 6, 1200: 7}
    if baudrate not in codes:
        raise ValueError(f"unsupported baudrate {baudrate}, use one of {sorted(codes)}")
    if not 1 <= slave <= 32:
        raise ValueError(f"slave must be 1-32, got {slave}")
    return ((slave & 0xFF) << 8) | codes[baudrate]


def power_limit_to_register_101c(percent: float) -> int:
    """Percent (0-110) -> raw 0x101C/0x340B word (0-1100)."""
    if not 0 <= percent <= 110:
        raise ValueError(f"power limit must be 0-110 %, got {percent}")
    return round(percent * 10)


def power_limit_from_register_101c(raw: int) -> float:
    """Raw 0x101C/0x340B word (0-1100) -> percent."""
    return raw / 10.0
