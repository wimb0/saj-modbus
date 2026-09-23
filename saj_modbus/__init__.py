"""saj-modbus: read (and control) SAJ PLUS / R5 / R6 inverters over Modbus.

C6 is excluded on purpose (Modbus control issues) and fails closed.
"""

from .controls import (
    encode_rs485_ate,
    power_limit_from_register_101c,
    power_limit_to_register_101c,
)
from .faults import decode_plus_r5_faults, decode_r6_3k_faults
from .models import (
    DEVTYPE_FAMILY,
    DEVTYPE_MODELS,
    C6_DEVTYPES,
    Family,
    UnsupportedInverterError,
    detect_family,
    register_devtype,
)

try:  # requires modbus-connection at runtime; pure helpers work without it
    from .connection import create_serial_connection, create_tcp_connection
    from .device import SajInverter, UpdateReport

    _HAS_MODBUS = True
except ImportError:  # pragma: no cover
    _HAS_MODBUS = False

__all__ = [
    "C6_DEVTYPES",
    "DEVTYPE_FAMILY",
    "DEVTYPE_MODELS",
    "Family",
    "SajInverter",
    "UnsupportedInverterError",
    "UpdateReport",
    "create_serial_connection",
    "create_tcp_connection",
    "decode_plus_r5_faults",
    "decode_r6_3k_faults",
    "detect_family",
    "encode_rs485_ate",
    "power_limit_from_register_101c",
    "power_limit_to_register_101c",
    "register_devtype",
]

__version__ = "0.4.0"
