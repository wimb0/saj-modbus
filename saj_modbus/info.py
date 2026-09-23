"""Static device information (info block 0x8F00-0x8F1D). Common to all families."""

from __future__ import annotations

from modbus_connection.model import Component, gauge, integer, string


class InverterInfo(Component):
    """Static device information, read once at setup."""

    devtype = integer(0x8F00, signed=False)
    subtype = integer(0x8F01, signed=False)
    commver = gauge(0x8F02, 0.001, signed=False)
    sn = string(0x8F03, 10)
    pc = string(0x8F0D, 10)
    dv = gauge(0x8F17, 0.001, signed=False)
    mcv = gauge(0x8F18, 0.001, signed=False)
    scv = gauge(0x8F19, 0.001, signed=False)
    disphwversion = gauge(0x8F1A, 0.001, signed=False)
    ctrlhwversion = gauge(0x8F1B, 0.001, signed=False)
    powerhwversion = gauge(0x8F1C, 0.001, signed=False)
    # R5 doc only (0x8F1D): low byte = baud (4:9600 5:4800 6:2400 7:1200),
    # high byte = slave number 1-32. Optional: absent firmware refuses it.
    rs485_ate = integer(0x8F1D, signed=False)


def decode_rs485_ate(value: int | None) -> dict[str, int | None]:
    """Split the 0x8F1D word into baud rate and slave number."""
    if value is None:
        return {"baudrate": None, "slave": None}
    baud_code = value & 0xFF
    baud = {4: 9600, 5: 4800, 6: 2400, 7: 1200}.get(baud_code)
    return {"baudrate": baud, "slave": (value >> 8) & 0xFF}
