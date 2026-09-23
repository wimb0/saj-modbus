"""Transport constructors (TCP + serial RTU) over modbus-connection."""

from __future__ import annotations

from modbus_connection import ModbusSerialParams, ModbusTcpParams
from modbus_connection.tmodbus import ModbusConnection

MODBUS_TIMEOUT = 5
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1


def create_tcp_connection(
    host: str, port: int = DEFAULT_PORT, timeout: int = MODBUS_TIMEOUT
) -> ModbusConnection:
    """Create a TCP inverter connection."""
    return ModbusConnection(ModbusTcpParams(host=host, port=port), timeout=timeout)


def create_serial_connection(
    device: str,
    baudrate: int = 9600,
    bytesize: int = 8,
    parity: str = "N",
    stopbits: int = 1,
    timeout: int = MODBUS_TIMEOUT,
) -> ModbusConnection:
    """Create a serial (RTU) inverter connection.

    ``device`` is a local port (``/dev/ttyUSB0``) or a serial-over-network
    URL (``socket://host:port``, ``rfc2217://host:port``). Framing is fixed
    to RTU: that is what the SAJ RS485 port speaks.
    """
    return ModbusConnection(
        ModbusSerialParams(
            device=device,
            baudrate=baudrate,
            bytesize=bytesize,  # type: ignore[arg-type]
            parity=parity,  # type: ignore[arg-type]
            stopbits=stopbits,  # type: ignore[arg-type]
            framer="rtu",
        ),
        timeout=timeout,
    )
