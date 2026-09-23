"""JSON dump CLI: python -m saj_modbus.cli --tcp HOST [--port 502] [--slave 1]."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from modbus_connection import ModbusError

from .connection import DEFAULT_PORT, DEFAULT_SLAVE_ID, MODBUS_TIMEOUT
from .device import SajInverter
from .models import UnsupportedInverterError


class _CliError(Exception):
    """Expected CLI failure (bad input, dead link, unsupported unit)."""


async def _dump(inv: SajInverter, args: argparse.Namespace) -> dict:
    """Run the requested reads; raises _CliError for expected failures."""
    snap: dict = {}
    try:
        await inv.async_setup()
        await inv.async_update()
    except UnsupportedInverterError as ex:
        if not args.raw:
            raise
        snap["setup_error"] = str(ex)
    else:
        snap = inv.snapshot()
        if args.history:
            try:
                snap["history"] = {
                    "energy": await inv.async_read_energy_history(),
                    "faults": await inv.async_read_fault_history(),
                }
            except UnsupportedInverterError as ex:
                snap["history_error"] = str(ex)
    if args.raw:
        try:
            address = int(args.raw[0], 0)
            count = int(args.raw[1], 0)
        except ValueError:
            raise _CliError(f"invalid --raw ADDRESS/COUNT: {args.raw}") from None
        words = await inv.async_read_raw_words(address, count)
        snap["raw"] = {
            "address": f"0x{address:04X}",
            "words": [f"0x{word:04X}" for word in words],
        }
    return snap


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
    try:
        snap = await _dump(inv, args)
    except (ModbusError, UnsupportedInverterError, ValueError, _CliError) as ex:
        print(f"error: {ex}", file=sys.stderr)
        await inv.async_close()
        return 2
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
