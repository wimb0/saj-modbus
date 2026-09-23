"""Fault decoding for every SAJ family.

Three sources, all kept (they disagree on several codes):

- ``CLASSIC_FAULT_MESSAGES`` — your existing ``const.py`` table (2017/2019
  PLUS + R5 docs). Used for PLUS/R5 realtime ``0x0101`` (6 regs).
- ``UNIFIED_FAULT_MESSAGES`` — the 2022 map (PLUS / R5 / R6, section 4.5.1).
  Same 6-reg layout, several codes redefined
  (43/42/41/37/36/35, new 87/86/84/83/44). C6 is excluded from this
  package, so C6-only rows are not carried.
- ``R6_3K_*`` — R6 3-15K bit-tag tables for ``0x4005`` / ``0x4007`` / ``0x4009``
  (section 4.5.2). Each set bit is a fault; reserved bits decode to nothing.

All helpers are pure (no Modbus import) so tests run without hardware.
"""

from __future__ import annotations

# --- Classic table (your const.py, verbatim) ---------------------------------
CLASSIC_FAULT_MESSAGES: dict[int, dict[int, str]] = {
    0: {
        0x80000000: "Code 81: Lost Communication D<->C",
        0x00080000: "Code 48: Master Fan4 Error",
        0x00040000: "Code 47: Master Fan3 Error",
        0x00020000: "Code 46: Master Fan2 Error",
        0x00010000: "Code 45: Master Fan1 Error",
        0x00002000: "Code 43: Master HW Phase3 Current High",
        0x00001000: "Code 42: Master HW Phase2 Current High",
        0x00000800: "Code 41: Master HW Phase1 Current High",
        0x00000400: "Code 40: Master HWPV2 Current High",
        0x00000200: "Code 39: Master HWPV1 Current High",
        0x00000100: "Code 38: Master HWBus Voltage High",
        0x00000010: "Code 37: Master Phase3 Current High",
        0x00000008: "Code 36: Master Phase2 Current High",
        0x00000004: "Code 35: Master Phase1 Current High",
        0x00000002: "Code 34: Master Bus Voltage Low",
        0x00000001: "Code 33: Master Bus Voltage High",
    },
    1: {
        0x80000000: "Code 32: Master Bus Voltage Balance Error",
        0x40000000: "Code 31: Master ISO Error",
        0x20000000: "Code 30: Master Phase3 DCI Error",
        0x10000000: "Code 29: Master Phase2 DCI Error",
        0x08000000: "Code 28: Master Phase1 DCI Error",
        0x04000000: "Code 27: Master GFCI Error",
        0x02000000: "Code 26: Master Phase3 No Grid Error",
        0x01000000: "Code 25: Master Phase2 No Grid Error",
        0x00800000: "Code 24: Master Phase1 No Grid Error",
        0x00400000: "Code 23: Master Phase3 Frequency Low",
        0x00200000: "Code 22: Master Phase3 Frequency High",
        0x00100000: "Code 21: Master Phase2 Frequency Low",
        0x00080000: "Code 20: Master Phase2 Frequency High",
        0x00040000: "Code 19: Master Phase1 Frequency Low",
        0x00020000: "Code 18: Master Phase1 Frequency High",
        0x00010000: "Code 17: Master Phase3 Voltage 10Min High",
        0x00008000: "Code 16: Master Phase2 Voltage 10Min High",
        0x00004000: "Code 15: Master Phase1 Voltage 10Min High",
        0x00002000: "Code 14: Master Phase3 Voltage Low",
        0x00001000: "Code 13: Master Phase3 Voltage High",
        0x00000800: "Code 12: Master Phase2 Voltage Low",
        0x00000400: "Code 11: Master Phase2 Voltage High",
        0x00000200: "Code 10: Master Phase1 Voltage Low",
        0x00000100: "Code 09: Master Phase1 Voltage High",
        0x00000080: "Code 08: Master Current Sensor Error",
        0x00000040: "Code 07: Master DCI Device Error",
        0x00000020: "Code 06: Master GFCI Device Error",
        0x00000010: "Code 05: Master Lost Communication M<->S",
        0x00000008: "Code 04: Master Temperature Low Error",
        0x00000004: "Code 03: Master Temperature High Error",
        0x00000002: "Code 02: Master EEPROM Error",
        0x00000001: "Code 01: Master Relay Error",
    },
    2: {
        0x40000000: "Code 80: Slave PV Voltage High Error",
        0x20000000: "Code 79: Slave PV2 Current High Error",
        0x10000000: "Code 78: Slave PV1 Current High Error",
        0x08000000: "Code 77: Slave PV2 Voltage High Error",
        0x04000000: "Code 76: Slave PV1 Voltage High Error",
        0x02000000: "Code 75: Slave Phase3 No Grid Error",
        0x01000000: "Code 74: Slave Phase2 No Grid Error",
        0x00800000: "Code 73: Slave Phase1 No Grid Error",
        0x00400000: "Code 72: Slave Phase3 Frequency Low",
        0x00200000: "Code 71: Slave Phase3 Frequency High",
        0x00100000: "Code 70: Slave Phase2 Frequency Low",
        0x00080000: "Code 69: Slave Phase2 Frequency High",
        0x00040000: "Code 68: Slave Phase1 Frequency Low",
        0x00020000: "Code 67: Slave Phase1 Frequency High",
        0x00010000: "Code 66: Slave Phase3 Voltage Low",
        0x00008000: "Code 65: Slave Phase3 Voltage High",
        0x00004000: "Code 64: Slave Phase2 Voltage Low",
        0x00002000: "Code 63: Slave Phase2 Voltage High",
        0x00001000: "Code 62: Slave Phase1 Voltage Low",
        0x00000800: "Code 61: Slave Phase1 Voltage High",
        0x00000400: "Code 60: Slave Phase3 DCI Consis Error",
        0x00000200: "Code 59: Slave Phase2 DCI Consis Error",
        0x00000100: "Code 58: Slave Phase1 DCI Consis Error",
        0x00000080: "Code 57: Slave GFCI Consis Error",
        0x00000040: "Code 56: Slave Phase3 Frequency Consis Error",
        0x00000020: "Code 55: Slave Phase2 Frequency Consis Error",
        0x00000010: "Code 54: Slave Phase1 Frequency Consis Error",
        0x00000008: "Code 53: Slave Phase3 Voltage Consis Error",
        0x00000004: "Code 52: Slave Phase2 Voltage Consis Error",
        0x00000002: "Code 51: Slave Phase1 Voltage Consis Error",
        0x00000001: "Code 50: Slave Lost Communication between M<->S",
    },
}

# --- Unified 2022 table (PLUS/R5/R6, map PDF 4.5.1, C6 rows omitted) ----------
UNIFIED_FAULT_MESSAGES: dict[int, dict[int, str]] = {
    0: {
        0x80000000: "Code 81: Lost Communication D<->C",
        0x00100000: "Code 87: Master Arc Error",
        0x00080000: "Code 48: Master Fan4 Error",
        0x00040000: "Code 47: Master Fan3 Error",
        0x00020000: "Code 46: Master Fan2 Error",
        0x00010000: "Code 45: Master Fan1 Error",
        0x00008000: "Code 86: Master DRM0 Error",
        0x00004000: "Code 44: Master Grid NE Voltage Error",
        0x00002000: "Code 43: Master DC SPD Error",
        0x00001000: "Code 42: Master AC SPD Error",
        0x00000800: "Code 41: Master HW Current High",
        0x00000200: "Code 39: Master HWPV Current High",
        0x00000100: "Code 38: Master HWBus Voltage High",
        0x00000040: "Code 84: Master PVInput Error",
        0x00000020: "Code 83: Master Arc Device Error",
        0x00000010: "Code 37: Master Islanding Error",
        0x00000008: "Code 36: Master PV Voltage High Error",
        0x00000004: "Code 35: Master Grid Phase Error",
        0x00000002: "Code 34: Master Bus Voltage Low",
        0x00000001: "Code 33: Master Bus Voltage High",
    },
    1: {
        0x80000000: "Code 32: Master Bus Voltage Balance Error",
        0x40000000: "Code 31: Master ISO Error",
        0x20000000: "Code 30: Master Phase3 DCI Error",
        0x10000000: "Code 29: Master Phase2 DCI Error",
        0x08000000: "Code 28: Master Phase1 DCI Error",
        0x04000000: "Code 27: Master GFCI Error",
        0x00800000: "Code 24: Master No Grid Error",
        0x00040000: "Code 19: Master Frequency Low",
        0x00020000: "Code 18: Master Frequency High",
        0x00004000: "Code 15: Master Voltage 10Min High",
        0x00002000: "Code 14: Master Phase3 Voltage Low",
        0x00001000: "Code 13: Master Phase3 Voltage High",
        0x00000800: "Code 12: Master Phase2 Voltage Low",
        0x00000400: "Code 11: Master Phase2 Voltage High",
        0x00000200: "Code 10: Master Phase1 Voltage Low",
        0x00000100: "Code 09: Master Phase1 Voltage High",
        0x00000080: "Code 08: Master Current Sensor Error",
        0x00000040: "Code 07: Master DCI Device Error",
        0x00000020: "Code 06: Master GFCI Device Error",
        0x00000008: "Code 04: Master Temperature Low Error",
        0x00000004: "Code 03: Master Temperature High Error",
        0x00000002: "Code 02: Master EEPROM Error",
        0x00000001: "Code 01: Master Relay Error",
    },
    2: {
        0x04000000: "Code 76: Slave PV Voltage High Error",
        0x02000000: "Code 75: HW PV Curr High Error",
        0x01000000: "Code 74: PV Input Mode Error",
        0x00800000: "Code 73: Slave No Grid Error",
        0x00040000: "Code 68: Slave Frequency Low",
        0x00020000: "Code 67: Slave Frequency High",
        0x00010000: "Code 66: Slave Phase3 Voltage Low",
        0x00008000: "Code 65: Slave Phase3 Voltage High",
        0x00004000: "Code 64: Slave Phase2 Voltage Low",
        0x00002000: "Code 63: Slave Phase2 Voltage High",
        0x00001000: "Code 62: Slave Phase1 Voltage Low",
        0x00000800: "Code 61: Slave Phase1 Voltage High",
    },
}

# --- R6 3-15K bit-tag tables (map PDF 4.5.2) ----------------------------------
# Bit index -> message. Reserved bits are absent on purpose.
R6_3K_HFAULT: dict[int, str] = {  # 0x4005 display/slave
    0: "Code 50: Lost Com H<->M",
    1: "Code 51: Meter Lost Com Warn",
    2: "Code 52: HMI Eeprom Err",
    3: "Code 53: HMI RTC Err",
    4: "Code 54: BMS Device Err",
    5: "Code 55: BMS Lost Conn Warn",
    6: "Code 56: CT Device Err",
    7: "Code 57: AFCI Lost Com Err",
    11: "Code 61: R Volt High Fault",
    12: "Code 62: R Volt Low Fault",
    13: "Code 63: S Volt High Fault",
    14: "Code 64: S Volt Low Fault",
    15: "Code 65: T Volt High Fault",
    16: "Code 66: T Volt Low Fault",
    17: "Code 67: Freq High Fault",
    18: "Code 68: Freq Low Fault",
    23: "Code 73: No Grid Fault",
    24: "Code 74: PV Input Mode Fault",
    25: "Code 75: HW PV Curr High Fault",
    26: "Code 76: PV Vol High Fault",
    27: "Code 77: HW Bus Volt High Fault",
}

R6_3K_MFAULT: dict[int, str] = {  # 0x4007 master
    0: "Code 33: Master Bus Voltage High",
    1: "Code 34: Master Bus Voltage Low",
    2: "Code 35: Master Grid Phase Error",
    3: "Code 36: Master PV Voltage High Error",
    4: "Code 37: Master Islanding Error",
    5: "Code 83: Master Arc Device Error",
    6: "Code 84: Master PVInput Error",
    7: "Code 49: Lost Communication DSP<->PowerMeter",
    8: "Code 38: Master HW Bus Voltage High",
    9: "Code 39: Master HW PV Current High",
    11: "Code 41: Master HW Inv Current High",
    14: "Code 44: Master Grid NE Voltage Error",
    15: "Code 86: Master DRM0 Error",
    16: "Code 45: Master Fan1 Error",
    17: "Code 46: Master Fan2 Error",
    18: "Code 47: Master Fan3 Error",
    19: "Code 48: Master Fan4 Error",
    20: "Code 87: Master Arc Error",
    21: "Code 88: Master SW PV Current High",
    22: "Code 89: Master Battery Voltage High",
    23: "Code 90: Master Battery Current High",
    24: "Code 91: Master Battery Charge Voltage High",
    25: "Code 92: Master Battery OverLoad",
    26: "Code 93: Master Battery SoftConnect TimeOut",
    27: "Code 94: Master Output OverLoad",
    28: "Code 95: Master Battery Open Circuit Error",
    29: "Code 96: Master Battery Discharge Voltage Low",
    30: "Code 85: Authority expires",
    31: "Code 81: Lost Communication D<->C",
}

R6_3K_MFAULT2: dict[int, str] = {  # 0x4009 master-2
    0: "Code 01: Master Relay Error",
    1: "Code 02: Master EEPROM Error",
    2: "Code 03: Master Temperature High Error",
    3: "Code 04: Master Temperature Low Error",
    4: "Code 05: Master Lost Communication M<->S",
    5: "Code 06: Master GFCI Device Error",
    6: "Code 07: Master DCI Device Error",
    7: "Code 08: Master Current Sensor Error",
    8: "Code 09: Master Phase1 Voltage High",
    9: "Code 10: Master Phase1 Voltage Low",
    10: "Code 11: Master Phase2 Voltage High",
    11: "Code 12: Master Phase2 Voltage Low",
    12: "Code 13: Master Phase3 Voltage High",
    13: "Code 14: Master Phase3 Voltage Low",
    14: "Code 15: Master Voltage 10Min High",
    15: "Code 16: Master OffGrid Voltage Low",
    17: "Code 18: Master Grid Frequency High",
    18: "Code 19: Master Grid Frequency Low",
    20: "Code 21: Master Phase1 DCV Error",
    21: "Code 22: Master Phase2 DCV Error",
    22: "Code 23: Master Phase3 DCV Error",
    23: "Code 24: Master No Grid Error",
    26: "Code 27: Master GFCI Error",
    27: "Code 28: Master Phase1 DCI Error",
    28: "Code 29: Master Phase2 DCI Error",
    29: "Code 30: Master Phase3 DCI Error",
    30: "Code 31: Master ISO Error",
    31: "Code 32: Master Bus Voltage Balance Error",
}


def translate_mask_to_messages(fault_code: int, table: dict[int, str]) -> list[str]:
    """Translate one 32-bit fault mask with a {bit: message} table."""
    if not fault_code:
        return []
    return [msg for bit, msg in sorted(table.items()) if fault_code & (1 << bit)]


def translate_code_to_messages(
    fault_code: int, fault_messages: dict[int, str]
) -> list[str]:
    """Translate one 32-bit fault word with a {mask: message} table."""
    if not fault_code:
        return []
    return [msg for code, msg in fault_messages.items() if fault_code & code]


def decode_plus_r5_faults(
    fault0: int | None,
    fault1: int | None,
    fault2: int | None,
    unified: bool = True,
) -> list[str]:
    """Decode the 6-reg PLUS/R5/R6-50K fault block.

    ``unified=True`` uses the 2022 table; ``False`` keeps your component's
    original 2017/2019 wording for backwards compatibility.
    """
    table = UNIFIED_FAULT_MESSAGES if unified else CLASSIC_FAULT_MESSAGES
    out: list[str] = []
    for value, idx in ((fault0, 0), (fault1, 1), (fault2, 2)):
        out.extend(translate_code_to_messages(value or 0, table[idx]))
    return out


def decode_r6_3k_faults(
    hfault: int | None, mfault: int | None, mfault2: int | None
) -> list[str]:
    """Decode the R6 3-15K fault registers 0x4005 / 0x4007 / 0x4009."""
    out: list[str] = []
    out.extend(translate_mask_to_messages(hfault or 0, R6_3K_HFAULT))
    out.extend(translate_mask_to_messages(mfault or 0, R6_3K_MFAULT))
    out.extend(translate_mask_to_messages(mfault2 or 0, R6_3K_MFAULT2))
    return out


def fault_messages_to_state(messages: list[str], limit: int = 254) -> str:
    """Join fault messages the way your HA sensor does (capped)."""
    return ", ".join(messages).strip()[:limit]
