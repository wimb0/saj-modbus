"""Type-driven family detection: no hardware, no modbus-connection needed."""

import pytest

from saj_modbus.models import (
    C6_DEVTYPES,
    UnsupportedInverterError,
    detect_family,
    register_devtype,
)


def test_known_plus_r5_types():
    for devtype in (0x11, 0x12, 0x13, 0x14, 0x15, 0x21, 0x22):
        assert detect_family(devtype) == "plus_r5"


def test_unreadable_type_refuses_to_guess():
    with pytest.raises(UnsupportedInverterError):
        detect_family(None)


def test_unknown_type_fails_closed():
    with pytest.raises(UnsupportedInverterError) as exc_info:
        detect_family(0x9999)
    assert exc_info.value.devtype == 0x9999


def test_c6_is_rejected_with_dedicated_message():
    C6_DEVTYPES.add(0xC600)
    try:
        with pytest.raises(UnsupportedInverterError, match="C6"):
            detect_family(0xC600)
        with pytest.raises(UnsupportedInverterError, match="C6"):
            register_devtype(0xC600, "r6_50k", "C6 must never register")
    finally:
        C6_DEVTYPES.discard(0xC600)


def test_register_r6_type_then_detect():
    register_devtype(0x30, "r6_3k", "R6 test unit")
    try:
        assert detect_family(0x30) == "r6_3k"
    finally:
        from saj_modbus.models import DEVTYPE_FAMILY, DEVTYPE_MODELS

        DEVTYPE_FAMILY.pop(0x30, None)
        DEVTYPE_MODELS.pop(0x30, None)
