"""JSON dump CLI: python -m saj_modbus.cli --tcp HOST [--port 502] [--slave 1]."""

from __future__ import annotations

import argparse
import asyncio
import json

from .connection import DEFAULT_PORT, DEFAULT_SLAVE_ID, MODBUS_TIMEOUT
from .device import SajInverter
from .models import UnsupportedInverterError


async def _run(args: argparse.Namespace) -> int:
    if args.serial:
        inv = SajInverter.serial(
            args.serial,
            baudrate=args.baudrate,
            slave_id=args.slave,
            timeout=args.timeout,
        )
    else:
        inv = SajInverter.tcp(args.tcp, port=args.port, slave_id=args.slave, timeout=args.timeout)
    snap: dict = {}
    try:
        await inv.async_setup()
        await inv.async_update()
        snap = inv.snapshot()
        if args.history:
            try:
                snap["history"] = {
                    "energy": await inv.async_read_energy_history(),
                    "faults": await inv.async_read_fault_history(),
                }
            except UnsupportedInverterError as ex:
                snap["history_error"] = str(ex)
    except UnsupportedInverterError as ex:
        if not args.raw:
            raise
        snap["setup_error"] = str(ex)
    if args.raw:
        address = int(args.raw[0], 0)
        count = int(args.raw[1], 0)
        words = await inv.async_read_raw_words(address, count)
        snap["raw"] = {
            "address": f"0x{address:04X}",
            "words": [f"0x{word:04X}" for word in words],
        }
    print(json.dumps(snap, indent=2, default=str))
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
    parser.add_argument("--timeout", type=int, default=MODBUS_TIMEOUT)
    parser.add_argument(
        "--history",
        action="store_true",
        help="also read energy + fault history (PLUS/R5 only, slow: ~1200 registers)",
    )
    parser.add_argument(
        "--raw",
        nargs=2,
        metavar=("ADDRESS", "COUNT"),
        help="dump raw holding-register words, e.g. --raw 0x0B00 10",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
