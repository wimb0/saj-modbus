"""Pure-logic tests: run without Modbus hardware or modbus-connection."""

from datetime import datetime

from saj_modbus.controls import encode_rs485_ate, power_limit_to_register_101c
from saj_modbus.faults import (
    CLASSIC_FAULT_MESSAGES,
    R6_3K_HFAULT,
    R6_3K_MFAULT,
    decode_plus_r5_faults,
    decode_r6_3k_faults,
    translate_code_to_messages,
    translate_mask_to_messages,
)
from saj_modbus.fields import decode_clock_words, encode_clock_words
from saj_modbus.models import (
    describe_model,
    describe_plus_r5_mode,
    describe_r6_3k_mode,
    rated_power_w,
)


def test_clock_roundtrip():
    dt = datetime(2015, 1, 2, 10, 11, 12)
    words = encode_clock_words(dt)
    assert words == [0x07DF, 0x0102, 0x0A0B, 0x0C00]
    back = decode_clock_words(words)
    assert back is not None
    assert (back.year, back.month, back.day, back.hour, back.minute, back.second) == (
        2015, 1, 2, 10, 11, 12,
    )


def test_clock_invalid_returns_none():
    assert decode_clock_words([0, 0x0000, 0x0000, 0x0000]) is None


def test_classic_fault_example_from_pdf():
    # PLUS doc 4.5 example: 00 08 00 00 83 80 00 04 00 00 00 00
    # -> words 0x0008,0x0000,0x8380,0x0004,0x0000,0x0000
    # -> fault0 = 0x00080000, fault1 = 0x83800004, fault2 = 0
    msgs = decode_plus_r5_faults(0x00080000, 0x83800004, 0x00000000, unified=False)
    assert "Code 48: Master Fan4 Error" in msgs
    assert "Code 32: Master Bus Voltage Balance Error" in msgs
    assert "Code 03: Master Temperature High Error" in msgs


def test_unified_differs_on_redefined_codes():
    # 0x00002000 is Phase3 Current High (classic) vs DC SPD Error (unified)
    classic = translate_code_to_messages(0x00002000, CLASSIC_FAULT_MESSAGES[0])
    assert classic == ["Code 43: Master HW Phase3 Current High"]
    unified = decode_plus_r5_faults(0x00002000, 0, 0, unified=True)
    assert unified == ["Code 43: Master DC SPD Error"]


def test_r6_3k_bit_tables():
    assert translate_mask_to_messages(0b1, R6_3K_HFAULT) == ["Code 50: Lost Com H<->M"]
    assert "Code 81: Lost Communication D<->C" in translate_mask_to_messages(
        1 << 31, R6_3K_MFAULT
    )
    msgs = decode_r6_3k_faults(0, 0, 0)
    assert msgs == []


def test_modes():
    assert describe_plus_r5_mode(2) == "Normal"
    assert describe_plus_r5_mode(99) == "Unknown"
    assert describe_r6_3k_mode(2) == "Operate"
    assert describe_r6_3k_mode(5) == "Fault"


def test_model_power():
    assert rated_power_w(2500) == 2500
    assert rated_power_w(None) is None
    assert describe_model("R5 (single-phase)", 2500) == "R5 (single-phase), 2.5K"
    assert describe_model("R5 (single-phase)", 5000) == "R5 (single-phase), 5K"
    assert describe_model("R5 (single-phase)", 800) == "R5 (single-phase), 800W"
    assert describe_model("R5 (single-phase)", None) == "R5 (single-phase)"
    assert describe_model(None, 2500) is None


def test_power_limit_helpers():
    assert power_limit_to_register_101c(0) == 0
    assert power_limit_to_register_101c(110) == 1100
    assert power_limit_to_register_101c(50.0) == 500
    try:
        power_limit_to_register_101c(111)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_rs485_ate():
    assert encode_rs485_ate(9600, 1) == 0x0104
    try:
        encode_rs485_ate(19200, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
