"""End-to-end tests against the in-memory mock backend.

Needs modbus-connection (a test dependency, not a pure-logic environment):
CI installs it, hardware-test VMs have it. The ``pytest.importorskip`` below
skips this module cleanly where it is missing.
"""

import pytest

pytest.importorskip("modbus_connection")

from modbus_connection import IllegalDataAddressError
from modbus_connection.mock import MockModbusConnection

from saj_modbus import SajInverter, UnsupportedInverterError


def _pack_ascii(text: str, words: int) -> list[int]:
    """ASCII string to big-endian words, null-padded to ``words`` registers."""
    data = text.encode("ascii")[: words * 2].ljust(words * 2, b"\x00")
    return [(data[i] << 8) + data[i + 1] for i in range(0, len(data), 2)]


def make_r5_unit(overrides: dict[int, int] | None = None) -> object:
    """A mock unit answering as an R5 single-phase (devtype 0x15) inverter."""
    holding: dict[int, int] = {
        0x8F00: 0x15,
        0x8F01: 2500,  # 2.5 kW rated, like the real R5
        0x8F02: 2000,  # comms 2.000
        0x8F17: 3039,
        0x8F18: 1227,
        0x8F19: 0xFFFF,  # unpopulated version reads as None
        0x0100: 2,  # NORMAL
        0x0113: 509,
        0x012C: 510,  # today 5.10 kWh
        0x0131: 6,  # total 429656 x 0.01 = 4296.56 kWh over 0x131-0x132
        0x0132: 36440,
        0x1037: 1,
    }
    for addr, word in zip(
        range(0x8F03, 0x8F03 + 10), _pack_ascii("R5X1252J2340E53422", 10), strict=True
    ):
        holding[addr] = word
    if overrides:
        holding.update(overrides)
    conn = MockModbusConnection()
    unit = conn.for_unit(1)
    unit.holding.update(holding)
    return unit


async def test_r5_detect_poll_snapshot() -> None:
    inv = SajInverter(make_r5_unit())  # type: ignore[arg-type]
    assert await inv.async_setup() == "plus_r5"
    report = await inv.async_update()
    assert report.complete
    assert inv.model_name == "R5 (single-phase), 2.5K"
    assert inv.rated_power == 2500
    assert inv.serial_number == "R5X1252J2340E53422"
    assert inv.status == "Normal"
    assert inv.fault_messages == []
    assert inv.plus_r5.power == 509
    assert inv.plus_r5.todayenergy == 5.1
    assert inv.plus_r5.totalenergy == 4296.56
    assert inv.info.scv is None  # 0xFFFF sentinel
    snap = inv.snapshot()
    assert snap["family"] == "plus_r5"
    assert snap["rated_power_w"] == 2500
    assert snap["realtime.power"] == 509
    assert snap["power_on_off"] is True
    await inv.async_close()


async def test_unknown_devtype_raises() -> None:
    inv = SajInverter(make_r5_unit({0x8F00: 0xDEAD}))  # type: ignore[arg-type]
    with pytest.raises(UnsupportedInverterError):
        await inv.async_setup()
    await inv.async_close()


async def test_power_write_roundtrip() -> None:
    inv = SajInverter(make_r5_unit())  # type: ignore[arg-type]
    await inv.async_setup()
    assert await inv.async_set_power_on_off(False) is True
    await inv.async_update()
    assert inv.power.poweronoff is False
    assert await inv.async_set_power_limit(50.0) is True
    await inv.async_close()


async def test_fault_history_partial_record() -> None:
    unit = make_r5_unit()  # type: ignore[assignment]
    # slots 1-2 populated (binary clock words + one fault word each)
    unit.holding.update(
        {
            0x0B00: 0x07E9,
            0x0B01: 0x030C,
            0x0B02: 0x0A2A,
            0x0B03: 0x1C00,
            0x0B04: 0x0000,
            0x0B05: 0x0000,
            0x0B06: 0x0000,
            0x0B07: 0x0000,
            0x0B08: 0x0080,
            0x0B09: 0x0000,
        }
    )
    # everything from slot 3 on is unserved: fail each covered address
    for addr in range(0x0B0A, 0x0EE7):
        unit.fail_read(addr, IllegalDataAddressError())
    inv = SajInverter(unit)  # type: ignore[arg-type]
    await inv.async_setup()
    faults = await inv.async_read_fault_history()
    assert len(faults) == 1
    assert faults[0]["slot"] == 1
    assert faults[0]["time"] == "2025-03-12T10:42:28"
    await inv.async_close()


async def test_fault_history_unserved_raises() -> None:
    unit = make_r5_unit()  # type: ignore[assignment]
    for addr in range(0x0B00, 0x0EE7):
        unit.fail_read(addr, IllegalDataAddressError())
    inv = SajInverter(unit)  # type: ignore[arg-type]
    await inv.async_setup()
    with pytest.raises(UnsupportedInverterError):
        await inv.async_read_fault_history()
    await inv.async_close()


async def test_raw_words_escape_hatch() -> None:
    inv = SajInverter(make_r5_unit())  # type: ignore[arg-type]
    await inv.async_setup()
    assert await inv.async_read_raw_words(0x0100, 2) == [0x0002, 0x0000]
    await inv.async_close()


async def test_energy_history_blocks() -> None:
    unit = make_r5_unit()  # type: ignore[assignment]
    unit.holding.update(
        {
            0x0A00: 100,  # etoday1 = 1.00 kWh
            0x0A5D: 0x0000,  # emonth1 = 178.94 kWh over 0x0A5D-0x0A5E
            0x0A5E: 17894,
            0x0A8D: 0x0002,  # eyear = 1350.71 kWh over 0x0A8D-0x0A8E
            0x0A8E: 3999,
        }
    )
    inv = SajInverter(unit)  # type: ignore[arg-type]
    await inv.async_setup()
    energy = await inv.async_read_energy_history()
    assert energy["daily_kwh"]["etoday1"] == 1.0
    assert energy["monthly_kwh"]["emonth1"] == 178.94
    assert energy["monthly_kwh"]["lemonth1"] == 0.0
    assert energy["yearly_kwh"]["eyear"] == 1350.71
    assert energy["yearly_kwh"]["eyear1"] == 0.0
    await inv.async_close()
