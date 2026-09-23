"""JSON dump CLI: python -m saj_modbus.cli --tcp HOST [--port 502] [--slave 1]."""

from __future__ import annotations

import argparse
import asyncio
import json

from .connection import DEFAULT_PORT, DEFAULT_SLAVE_ID
from .device import SajInverter


async def _run(args: argparse.Namespace) -> int:
    if args.serial:
        inv = SajInverter.serial(args.serial, baudrate=args.baudrate, slave_id=args.slave)
    else:
        inv = SajInverter.tcp(args.tcp, port=args.port, slave_id=args.slave)
    try:
        await inv.async_setup()
        await inv.async_update()
    finally:
        pass
    print(json.dumps(inv.snapshot(), indent=2, default=str))
    await inv.async_close()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Dump a SAJ inverter as JSON")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tcp", help="inverter host/IP")
    group.add_argument("--serial", help="serial port or URL (socket://host:port)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--slave", type=int, default=DEFAULT_SLAVE_ID)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
