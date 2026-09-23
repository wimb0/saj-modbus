"""Shared model tables: device types, family detection, working modes.

Family detection is driven **only** by the Type register (info ``0x8F00``)
that the inverter itself reports — see :func:`detect_family`. There is no
address probing: the wrong realtime map against the wrong hardware is exactly
how inverters get mis-controlled.

C6 is deliberately unsupported (Modbus control is known to cause issues on
those units) and fails closed: any C6 type — or any type not explicitly
listed — raises :class:`UnsupportedInverterError` instead of guessing.
"""

from __future__ import annotations

from typing import Literal

Family = Literal["plus_r5", "r6_3k", "r6_50k"]


class UnsupportedInverterError(Exception):
    """Raised when the reported device type is not a supported inverter.

    Carries the raw ``devtype`` value so it can be reported back and, for a
    genuinely new R6 unit, added via :func:`register_devtype`.
    """

    def __init__(self, devtype: int | None, message: str = "") -> None:
        self.devtype = devtype
        hint = (
            f" (reported type 0x{devtype:04X})" if isinstance(devtype, int) else ""
        )
        super().__init__(f"{message}{hint}" if message else f"Unsupported inverter{hint}")


# DeviceType (info 0x8F00) -> marketing family.
# From the three PDFs + your hub's _DEVTYPE_MODELS (kept verbatim where known).
# The per-variant MPPT counts in the documents do not reliably match hardware,
# so these stay family-level on purpose.
DEVTYPE_MODELS: dict[int, str] = {
    0x11: "Sununo Plus (single-phase)",
    0x12: "Sununo Plus (single-phase)",
    0x13: "R5 (single-phase)",
    0x14: "R5 (single-phase)",
    0x15: "R5 (single-phase)",
    0x21: "Suntrio Plus (three-phase)",
    0x22: "R5 (three-phase)",
}

# DeviceType -> realtime/control family. This is the single source of truth
# for auto-detection. R6 type codes are not published in the PDFs: add yours
# with register_devtype() once read back from the hardware (see probe_devtype
# in device.py), e.g. register_devtype(0xXX, "r6_3k", "R6 8K-T2").
DEVTYPE_FAMILY: dict[int, Family] = {
    0x11: "plus_r5",
    0x12: "plus_r5",
    0x13: "plus_r5",
    0x14: "plus_r5",
    0x15: "plus_r5",
    0x21: "plus_r5",
    0x22: "plus_r5",
}

# DeviceType values known to be C6. Rejected with a dedicated message even if
# someone registers them above by mistake. The PDFs do not publish C6 type
# codes; extend this set if a C6 unit ever reports one.
C6_DEVTYPES: set[int] = set()


def register_devtype(devtype: int, family: Family, model: str) -> None:
    """Register a new device type, e.g. an R6 unit the PDFs do not list.

    Raises if the code is a known C6 type — C6 stays unsupported on purpose.
    """
    if devtype in C6_DEVTYPES:
        raise UnsupportedInverterError(devtype, "C6 inverters are not supported")
    DEVTYPE_FAMILY[devtype] = family
    DEVTYPE_MODELS[devtype] = model


def detect_family(devtype: int | None) -> Family:
    """Map a reported Type-register value to its inverter family.

    - ``None`` (unreadable info block) -> raises; without the reported type
      there is nothing safe to detect from.
    - known C6 type -> raises with a C6-specific message.
    - listed type -> its family.
    - anything else -> raises; report the value so it can be classified.
    """
    if devtype is None:
        raise UnsupportedInverterError(
            None, "Device type unreadable; refusing to guess the inverter family"
        )
    if devtype in C6_DEVTYPES:
        raise UnsupportedInverterError(
            devtype, "C6 inverters are not supported (Modbus control issues)"
        )
    try:
        return DEVTYPE_FAMILY[devtype]
    except KeyError:
        raise UnsupportedInverterError(
            devtype,
            f"Unknown device type 0x{devtype:04X}; not C6 but not listed either",
        ) from None


# PLUS / R5 / R6 17-50K working mode (realtime 0x0100 / 0x6013).
# Your hub's DEVICE_STATUSSES extended with UPDATE from the PDFs.
PLUS_R5_STATUSES: dict[int, str] = {
    0: "Not Connected",
    1: "Waiting",
    2: "Normal",
    3: "Error",
    4: "Upgrading",
}

# R6 3-15K working mode (realtime 0x4004). Distinct enum in the 2022 map.
R6_3K_MODES: dict[int, str] = {
    0: "Initialize",
    1: "Waiting",
    2: "Operate",
    3: "Off-grid (storage)",
    4: "Grid with load (storage)",
    5: "Fault",
    6: "Upgrade",
    7: "Debug",
    8: "Auto-Check",
    9: "Reset",
}


def describe_plus_r5_mode(value: int | None) -> str:
    """Human status for PLUS/R5/R6-50K mpvmode values."""
    if value is None:
        return "Unknown"
    return PLUS_R5_STATUSES.get(value, "Unknown")

def describe_r6_3k_mode(value: int | None) -> str:
    """Human status for R6 3-15K mpvmode values."""
    if value is None:
        return "Unknown"
    return R6_3K_MODES.get(value, "Unknown")


def rated_power_w(subtype: int | None) -> int | None:
    """Machine power in watts from info SubType (``0x8F01``).

    Verified against R5 hardware (2500 = 2.5 kW); unwritten ``0xFFFF``
    already decodes to ``None`` upstream.
    """
    return subtype


def describe_model(base: str | None, subtype: int | None) -> str | None:
    """Family label with the rated power appended, e.g. ``R5 (single-phase, 2.5K)``."""
    if base is None:
        return None
    power = rated_power_w(subtype)
    if power is None:
        return base
    suffix = f"{power / 1000:g}K" if power >= 1000 else f"{power}W"
    return f"{base}, {suffix}"
