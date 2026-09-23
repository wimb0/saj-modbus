"""On-demand history: energy ledger + fault records (PLUS/R5 only).

Register layout from the PLUS (2017) and R5 (2019) PDFs; the 2022 map does
not republish history blocks, so other families raise instead of guessing:

- Energy (``0x0A00-0x0ABE``): daily readings for the current, last, and
  second-to-last month (``UInt16``, -2 kWh), then monthly/yearly ``UInt32``
  totals. Split into two components so no poll exceeds one Modbus read span
  by more than the planner chunks.
- Faults (``0x0B00-0x0EE6``): 100 slots of 4 BCD time words + 6 fault words
  (the same three 32-bit masks as realtime ``0x0101``). Split into four
  25-slot blocks; each block is read only when requested.

Nothing here is polled — read it through
:meth:`device.SajInverter.async_read_energy_history` and
:meth:`device.SajInverter.async_read_fault_history`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from modbus_connection.model import Component, RegisterField

from .faults import decode_plus_r5_faults
from .fields import decode_bcd_clock_words
from .measure import mgauge, muint32


class HistoryTimeField(RegisterField[datetime | None]):
    """BCD history timestamp: year word, month/day, hour/minute, second bytes."""

    def decode(
        self, words: list[int], scale_exponent: int | None = None
    ) -> datetime | None:
        return decode_bcd_clock_words(words)


def _daily_energy_class() -> type[Component]:
    """31 daily readings x3 months (0x0A00-0x0A5C, UInt16 -2 kWh)."""
    namespace: dict[str, Any] = {}
    for i in range(1, 32):
        namespace[f"etoday{i}"] = mgauge(0x0A00 + i - 1, 0.01, signed=False)
        namespace[f"letoday{i}"] = mgauge(0x0A1F + i - 1, 0.01, signed=False)
        namespace[f"lletoday{i}"] = mgauge(0x0A3E + i - 1, 0.01, signed=False)
    namespace["__doc__"] = "Daily energy: current/last/second-to-last month."
    return type("HistoryDailyEnergy", (Component,), namespace)


def _monthly_energy_class() -> type[Component]:
    """Monthly + yearly totals (0x0A5D-0x0ABE, UInt32 -2 kWh)."""
    namespace: dict[str, Any] = {}
    for i in range(1, 13):
        namespace[f"emonth{i}"] = muint32(0x0A5D + (i - 1) * 2, scale=0.01)
        namespace[f"lemonth{i}"] = muint32(0x0A75 + (i - 1) * 2, scale=0.01)
    namespace["eyear"] = muint32(0x0A8D, scale=0.01)
    for i in range(1, 25):
        namespace[f"eyear{i}"] = muint32(0x0A8F + (i - 1) * 2, scale=0.01)
    namespace["__doc__"] = "Monthly energy (this/last year) + yearly archive."
    return type("HistoryMonthlyEnergy", (Component,), namespace)


def _fault_block_class(first: int, last: int) -> type[Component]:
    """One 25-slot fault window; slot i lives at 0x0B00+(i-1)*10."""
    namespace: dict[str, Any] = {}
    for i in range(first, last + 1):
        base = 0x0B00 + (i - 1) * 10
        namespace[f"herror_time{i:03d}"] = HistoryTimeField(base, count=4)
        namespace[f"herror{i:03d}_0"] = muint32(base + 4)
        namespace[f"herror{i:03d}_1"] = muint32(base + 6)
        namespace[f"herror{i:03d}_2"] = muint32(base + 8)
    namespace["__doc__"] = f"Fault slots {first}-{last}."
    return type(f"HistoryFaults{first:03d}_{last:03d}", (Component,), namespace)


HistoryDailyEnergy = _daily_energy_class()
HistoryMonthlyEnergy = _monthly_energy_class()

HistoryFaults001_025 = _fault_block_class(1, 25)
HistoryFaults026_050 = _fault_block_class(26, 50)
HistoryFaults051_075 = _fault_block_class(51, 75)
HistoryFaults076_100 = _fault_block_class(76, 100)

#: (first slot, last slot, block class) in read order.
FAULT_BLOCKS: tuple[tuple[int, int, type[Component]], ...] = (
    (1, 25, HistoryFaults001_025),
    (26, 50, HistoryFaults026_050),
    (51, 75, HistoryFaults051_075),
    (76, 100, HistoryFaults076_100),
)


def build_fault_history(
    slots: dict[int, tuple[datetime | None, int | None, int | None, int | None]],
) -> list[dict[str, Any]]:
    """Result list from per-slot readings; empty slots skipped, ordered by slot.

    Pure (no Modbus): ``slots`` maps slot number to ``(time, word0, word1,
    word2)`` with ``None`` for sentinel/unread words.
    """
    out: list[dict[str, Any]] = []
    for slot in sorted(slots):
        time, word0, word1, word2 = slots[slot]
        faults = decode_plus_r5_faults(word0, word1, word2)
        if time is not None or faults:
            out.append(
                {
                    "slot": slot,
                    "time": time.isoformat() if time is not None else None,
                    "faults": faults,
                }
            )
    return out
