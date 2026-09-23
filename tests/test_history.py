"""History support tests: pure BCD logic + structural checks via a model stub.

history.py needs modbus-connection at runtime, so these tests inject a tiny
stub for modbus_connection.model (factories just record their arguments)
before importing it. That verifies addresses, counts, and sentinel wiring
without hardware.
"""

import sys
import types
from datetime import datetime

from saj_modbus.fields import decode_bcd_clock_words


def _install_model_stub() -> None:
    mod = types.ModuleType("modbus_connection")
    model = types.ModuleType("modbus_connection.model")

    class RegisterField:
        def __init__(self, address, *args, **kwargs):
            self.address = address
            self.args = args
            self.kwargs = kwargs

        def __class_getitem__(cls, item):
            return cls

    class Component:
        pass

    def _factory(name):
        def make(address, *args, **kwargs):
            return (name, address, args, kwargs)

        return make

    model.RegisterField = RegisterField
    model.Component = Component
    model.gauge = _factory("gauge")
    model.integer = _factory("integer")
    model.uint32 = _factory("uint32")
    mod.model = model
    sys.modules.setdefault("modbus_connection", mod)
    sys.modules.setdefault("modbus_connection.model", model)


_install_model_stub()

from saj_modbus import history  # noqa: E402


def test_bcd_clock_valid():
    assert decode_bcd_clock_words([0x2015, 0x0102, 0x1011, 0x1200]) == datetime(
        2015, 1, 2, 10, 11, 12
    )


def test_bcd_clock_empty_slots_are_none():
    assert decode_bcd_clock_words([0, 0, 0, 0]) is None
    assert decode_bcd_clock_words([0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF]) is None


def test_bcd_clock_invalid_is_none():
    assert decode_bcd_clock_words([0x2015, 0x0113, 0x0A0B, 0x0C00]) is None  # month 13
    assert decode_bcd_clock_words([0x2015, 0x0102]) is None  # truncated


def test_daily_energy_addresses_and_sentinels():
    cls = history.HistoryDailyEnergy
    assert cls.etoday1[1] == 0x0A00
    assert cls.etoday31[1] == 0x0A1E
    assert cls.letoday1[1] == 0x0A1F
    assert cls.letoday31[1] == 0x0A3D
    assert cls.lletoday1[1] == 0x0A3E
    assert cls.lletoday31[1] == 0x0A5C
    fields = [v for v in vars(cls).values() if isinstance(v, tuple)]
    assert len(fields) == 93
    assert all(v[3].get("nan") == 0xFFFF for v in fields)


def test_monthly_energy_addresses_and_sentinels():
    cls = history.HistoryMonthlyEnergy
    assert cls.emonth1[1] == 0x0A5D
    assert cls.emonth12[1] == 0x0A73
    assert cls.lemonth1[1] == 0x0A75
    assert cls.lemonth12[1] == 0x0A8B
    assert cls.eyear[1] == 0x0A8D
    assert cls.eyear1[1] == 0x0A8F
    assert cls.eyear24[1] == 0x0ABD
    fields = [v for v in vars(cls).values() if isinstance(v, tuple)]
    assert len(fields) == 12 + 12 + 1 + 24
    assert all(v[3].get("nan") == 0xFFFFFFFF for v in fields)


def test_fault_blocks_cover_100_slots():
    assert [b[:2] for b in history.FAULT_BLOCKS] == [
        (1, 25),
        (26, 50),
        (51, 75),
        (76, 100),
    ]
    first = history.HistoryFaults001_025
    assert first.herror_time001.address == 0x0B00
    last = history.HistoryFaults076_100
    assert last.herror100_2[1] == 0x0EE6
    assert last.herror100_2[3].get("nan") == 0xFFFFFFFF
    for _, _, cls in history.FAULT_BLOCKS:
        members = [
            v
            for v in vars(cls).values()
            if isinstance(v, tuple) or isinstance(v, history.HistoryTimeField)
        ]
        assert len(members) == 100  # 25 slots x (time + 3 fault words)
