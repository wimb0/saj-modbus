"""Writable settings (never polled, only written).

Classic control block (PLUS/R5/R6, map PDF 4.3.1), the R6 3-15K
block (4.3.2), the legacy LimitPower register your component uses (PLUS doc
4.6, 0x801F), and the special registers (map PDF 4.4 + R5 doc).

C6 is not supported and has no settings here on purpose.
"""

from __future__ import annotations

from modbus_connection.model import Component, boolean, gauge, integer

from .fields import DateTimeField


class ClassicSettings(Component):
    """PLUS/R5/R6 parameters (0x1008-0x1046, R/W)."""

    safetytype = integer(0x1008, signed=False, writable=True)
    funmask = integer(0x1009, signed=False, writable=True)
    isolimit = integer(0x1019, signed=False, writable=True)
    # 0-1100 = 0-110 %, scale -3.
    powerlimited = gauge(0x101C, 0.001, signed=False, writable=True, force_fc16=True)
    reactivemode = integer(0x101D, signed=False, writable=True)
    reactivevalue = gauge(0x101E, 0.001, signed=False, writable=True, force_fc16=True)
    pvininputmode = integer(0x1046, signed=False, writable=True)


class R6_3KSettings(Component):
    """R6 3-15K parameters (0x3408-0x343A, R/W)."""

    funmask = integer(0x3408, signed=False, writable=True)
    powerlimited = gauge(0x340B, 0.001, signed=False, writable=True, force_fc16=True)
    isolimit = integer(0x3410, signed=False, writable=True)
    reactivemode = integer(0x3416, signed=False, writable=True)
    reactivevalue = gauge(0x3417, 0.001, signed=False, writable=True, force_fc16=True)
    safetytype = integer(0x3421, signed=False, writable=True)
    pvinputmode = integer(0x343A, signed=False, writable=True)


class LegacySettings(Component):
    """Write-only controls kept for backwards compatibility + specials."""

    # PLUS doc 4.6 LimitPower (your component's limiter, percent, 0.1).
    # The 2022 map prefers 0x101C/0x340B; both are exposed so old and new
    # firmware work. The R5 only accepts FC16 writes, hence force_fc16.
    limitpower = gauge(0x801F, 0.1, writable=True, force_fc16=True)
    datetime = DateTimeField(0x8020, count=4, writable=True)
    # Specials (map PDF 4.4): RS485 baud/slave, clear faults, clear energy.
    rs485_ate = integer(0x8014, signed=False, writable=True, force_fc16=True)
    cleanhistory = integer(0x8015, signed=False, writable=True, force_fc16=True)
    cleanpower = integer(0x801B, signed=False, writable=True, force_fc16=True)


class PlusR5Power(Component):
    """Remote power on/off at 0x1037 (PLUS/R5/R6).

    Own component so firmware that rejects it only loses the switch.
    The R5 only accepts FC16 writes, hence force_fc16.
    """

    poweronoff = boolean(0x1037, writable=True, force_fc16=True)


class R6_3KPower(Component):
    """R6 3-15K stop register 0x340C. NOTE: inverted vs 0x1037.

    1 = power off, 0 = power on.
    """

    inverterstop = boolean(0x340C, writable=True, force_fc16=True)


# Pure helpers live in controls.py (importable without modbus-connection);
# re-exported here for convenience.
from .controls import (  # noqa: E402
    encode_rs485_ate,
    power_limit_from_register_101c,
    power_limit_to_register_101c,
)

__all__ = [
    "ClassicSettings",
    "R6_3KSettings",
    "LegacySettings",
    "PlusR5Power",
    "R6_3KPower",
    "encode_rs485_ate",
    "power_limit_from_register_101c",
    "power_limit_to_register_101c",
]
