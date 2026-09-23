"""PLUS / R5 realtime block (0x0100-0x014B).

Covers the 2017 PLUS doc, the 2019 R5 doc (adds 0x8F1D info + 0x013B-0x014B
string currents), and the 2022 PLUS/R5 table. One component so the classic
single-poll behaviour of your component is preserved (76 regs < 125 limit).
"""

from __future__ import annotations

from modbus_connection.model import Component, gauge, integer, uint32

from .fields import DateTimeField


class PlusR5Realtime(Component):
    """Realtime inverter data, polled every update cycle."""

    mpvmode = integer(0x100, signed=False)
    faultmsg0 = uint32(0x101)
    faultmsg1 = uint32(0x103)
    faultmsg2 = uint32(0x105)
    pv1volt = gauge(0x107, 0.1, signed=False)
    pv1curr = gauge(0x108, 0.01, signed=False)
    pv1power = integer(0x109, signed=False)
    pv2volt = gauge(0x10A, 0.1, signed=False)
    pv2curr = gauge(0x10B, 0.01, signed=False)
    pv2power = integer(0x10C, signed=False)
    pv3volt = gauge(0x10D, 0.1, signed=False)
    pv3curr = gauge(0x10E, 0.01, signed=False)
    pv3power = integer(0x10F, signed=False)
    busvolt = gauge(0x110, 0.1, signed=False)
    invtempc = gauge(0x111, 0.1)
    gfci = integer(0x112)
    power = integer(0x113, signed=False)
    qpower = integer(0x114)
    pf = gauge(0x115, 0.001)
    l1volt = gauge(0x116, 0.1, signed=False)
    l1curr = gauge(0x117, 0.01, signed=False)
    l1freq = gauge(0x118, 0.01, signed=False)
    l1dci = integer(0x119)
    l1power = integer(0x11A, signed=False)
    l1pf = gauge(0x11B, 0.001)
    l2volt = gauge(0x11C, 0.1, signed=False)
    l2curr = gauge(0x11D, 0.01, signed=False)
    l2freq = gauge(0x11E, 0.01, signed=False)
    l2dci = integer(0x11F)
    l2power = integer(0x120, signed=False)
    l2pf = gauge(0x121, 0.001)
    l3volt = gauge(0x122, 0.1, signed=False)
    l3curr = gauge(0x123, 0.01, signed=False)
    l3freq = gauge(0x124, 0.01, signed=False)
    l3dci = integer(0x125)
    l3power = integer(0x126, signed=False)
    l3pf = gauge(0x127, 0.001)
    iso1 = integer(0x128, signed=False)
    iso2 = integer(0x129, signed=False)
    iso3 = integer(0x12A, signed=False)
    iso4 = integer(0x12B, signed=False)
    todayenergy = gauge(0x12C, 0.01, signed=False)
    monthenergy = uint32(0x12D, scale=0.01)
    yearenergy = uint32(0x12F, scale=0.01)
    totalenergy = uint32(0x131, scale=0.01)
    todayhour = gauge(0x133, 0.1, signed=False)
    totalhour = uint32(0x134, scale=0.1)
    errorcount = integer(0x136, signed=False)
    datetime = DateTimeField(0x137, count=4)
    # R5 string currents (2019 doc 0x013B-0x014A + reserved 0x014B).
    # PLUS firmware without them refuses this tail; device.py treats that
    # as "strings absent", not as a failed poll.
    pv1strcurr1 = gauge(0x13B, 0.01, signed=False)
    pv1strcurr2 = gauge(0x13C, 0.01, signed=False)
    pv1strcurr3 = gauge(0x13D, 0.01, signed=False)
    pv1strcurr4 = gauge(0x13E, 0.01, signed=False)
    pv2strcurr1 = gauge(0x13F, 0.01, signed=False)
    pv2strcurr2 = gauge(0x140, 0.01, signed=False)
    pv2strcurr3 = gauge(0x141, 0.01, signed=False)
    pv2strcurr4 = gauge(0x142, 0.01, signed=False)
    pv3strcurr1 = gauge(0x143, 0.01, signed=False)
    pv3strcurr2 = gauge(0x144, 0.01, signed=False)
    pv3strcurr3 = gauge(0x145, 0.01, signed=False)
    pv3strcurr4 = gauge(0x146, 0.01, signed=False)
    pv4strcurr1 = gauge(0x147, 0.01, signed=False)
    pv4strcurr2 = gauge(0x148, 0.01, signed=False)
    pv4strcurr3 = gauge(0x149, 0.01, signed=False)
    pv4strcurr4 = gauge(0x14A, 0.01, signed=False)
