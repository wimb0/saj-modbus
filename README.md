# saj-modbus

Standalone Python package for **SAJ solar inverters over Modbus**, built from:

- your `saj_modbus` HA custom component (`custom_components/saj_modbus/`, R5-focused), and
- the three PDFs in `www/saj/`:
  - `saj-plus-series-inverter-modbus-protocal.pdf` (2017, Sununo Plus / Suntrio Plus)
  - `SAJ Modbus Protocol_EN_R5.pdf` (2019, R5 series)
  - `map-modbus-communication-protocol-saj-r5-r6-c6.pdf` (2022 v7.2, PLUS / R5 / R6 / C6)

Goal: **read data from all supported inverters** with one API, plus the
control writes your component already proves (power on/off, power limit, clock).

**C6 is excluded on purpose** — Modbus control is known to cause issues on
those units, so C6 types fail closed at setup instead of polling a
look-alike map.

## Supported families (auto-detected from the reported device type)

| Family | Reported `devtype` (`0x8F00`) | Realtime base | Notes |
|---|---|---|---|
| PLUS (Sununo Plus / Suntrio Plus) | 0x11 / 0x12 / 0x21 | `0x0100` | Classic map, 6-reg `FaultMSG`, energy `0x012C-0x0136`, clock `0x0137` |
| R5 (single/three-phase) | 0x13 / 0x14 / 0x15 / 0x22 | `0x0100` | Same as PLUS + PV string currents `0x013B-0x014A`, info `0x8F1D` |
| R6 3-15K (hybrid / storage) | register yours (unpublished) | `0x4000` | Battery, grid/inv/output, flows, extended energy `0x40BC-0x40FD`, faults `0x4005/0x4007/0x4009` |
| R6 17-50K | register yours (unpublished) | `0x6000` | `TodayEnergy` is `UInt32` here, PV1-12 + strings, faults `0x6014` (6 regs) |

Detection in `SajInverter.async_setup()` is type-driven only:

1. Read the info block (`0x8F00-0x8F1C`) — required, not optional.
2. Map the reported type via `models.detect_family()`.
3. Poll that family's map. C6, unknown, or unreadable types raise
   `UnsupportedInverterError` instead of guessing.

There is no address probing: polling the wrong family's registers against
the wrong hardware is what mis-controls inverters.

## Register maps (from the PDFs)

- Info (all): `0x8F00` Type, `0x8F01` SubType, `0x8F02` CommVer (-3),
  `0x8F03` SN (10 regs), `0x8F0D` PC (10), `0x8F17` DV, `0x8F18` MCV,
  `0x8F19` SCV, `0x8F1A` DispHW, `0x8F1B` CtrlHW, `0x8F1C` PowerHW,
  optional `0x8F1D` RS485 baud/slave (R5 doc only).
- PLUS/R5 realtime `0x0100-0x014B`: MPVMode, FaultMSG x6, PV1-3, Bus, Temp,
  GFCI, Power/QPower/PF, L1-L3, ISO1-4, Today/Month/Year/Total energy,
  Today/Total hours, ErrorCount, clock, PV string currents.
- R6 3-15K `0x4000-0x40FD`: clock, MPVMode (0-9), HFault/MFault/MFault2/BMS,
  temps, ISO, DRM, battery set/points, R/S/T grid, R/S/T inv, R/S/T out,
  bus/battery, PV1-4 + strings, on-grid side, flow directions, PV/grid/battery
  flow watts, totals, hours + full energy ledger (PV, BatChg, BatDis, InvGen,
  Load, Backup, Sell, FeedIn).
- R6 17-50K `0x6000-0x6080`: clock, Total/Year/Month/Today energy
  (`UInt32`!), hours, ErrorCount/SN, MPVMode, FaultMSG x6, ConnTime, Energy,
  Power (`UInt32`), QPower (`Int32`), PF, L1-L3, NE volt, GFCI, bus, temps,
  ISO, PV1-12 + string currents. (C6 shares this section of the PDF map but
  is excluded from this package.)
- Settings:
  - Classic: `0x1008` SafetyType, `0x1009` FunMask, `0x1019` ISOLimit,
    `0x101C` PowerLimited (-3, 0-1100 = 0-110%), `0x101D/0x101E` reactive,
    `0x1037` remote on/off (0/1), `0x1046` PVInputMode,
    R6-3K equivalents at `0x3408/0x340B/0x340C/0x3410/0x3416/0x3417/0x3421/0x343A`
    (`0x340C` is **inverted**: 1 = off, 0 = on),
    legacy `0x801F` LimitPower (kept for your existing installs),
    `0x8014` RS485 baud/slave, `0x8015` clear faults, `0x801B` clear energy,
    `0x8020` clock (W, 4 regs).

Unconnected inputs (spare phases, missing MPPT strings) answer `0xFFFF` /
`0xFFFFFFFF`; those decode to `None` (unavailable) rather than phantom
readings like 6553.5 V. The CLI/snapshot likewise only contains declared
register fields, never Modbus planner internals.

On-demand history (PLUS/R5 only — the newer maps don't republish these
blocks): `async_read_energy_history()` for the daily/monthly/yearly ledger
(`0x0A00-0x0ABE`) and `async_read_fault_history()` for the 100-slot fault
record (`0x0B00-0x0EE6`, empty slots skipped). Both are slow (~1200 registers
total), so they stay out of the poll loop; other families raise
`UnsupportedInverterError`. Firmware that serves fewer than the documented
100 fault slots (or none) is handled: refused windows fall back to
slot-by-slot reads, and a fully unserved area raises instead of returning
a lying empty list.

Fault text tables live in `saj_modbus/faults.py` (classic 81-code map,
2022 unified PLUS/R5/R6 map, and R6-3K bit-tag maps for
`0x4005/0x4007/0x4009`).

## Registering an R6 type code

The PDFs do not publish R6 `devtype` values, so only PLUS/R5 codes work out
of the box. To add your R6:

```python
from saj_modbus import SajInverter, register_devtype

# 1. read back what your unit reports (needs modbus-connection + the inverter):
# raw = await SajInverter.probe_devtype(unit)  # -> e.g. 0x31
# 2. register it once at startup:
register_devtype(0x31, "r6_3k", "R6 8K-T2")
```

Unknown types raise `UnsupportedInverterError` carrying the raw value — send
that value back so the table grows. C6 codes are never registrable.

## Usage

```python
import asyncio
from saj_modbus import SajInverter

async def main():
    inv = SajInverter.tcp("192.168.1.50", 502, slave_id=1)
    await inv.async_setup()          # auto-detect family
    print(inv.family, inv.model_name, inv.serial_number)
    await inv.async_update()         # poll realtime (+power where served)
    print(inv.snapshot())            # plain dict of everything decoded
    await inv.async_close()

asyncio.run(main())
```

Serial:

```python
inv = SajInverter.serial("/dev/ttyUSB0", baudrate=9600, slave_id=1)
```

Control writes (same semantics as your HA component):

```python
await inv.async_set_power_on_off(True)
await inv.async_set_power_limit(50.0)   # percent, 0-110
await inv.async_set_datetime()          # sync clock to now
```

CLI dump:

```bash
python -m saj_modbus.cli --tcp 192.168.1.50 --port 502 --slave 1
python -m saj_modbus.cli --serial /dev/ttyUSB0 --baudrate 9600 --slave 1
# plus on-demand history (slow):
python -m saj_modbus.cli --tcp 192.168.1.50 --history
```

## Layout

- `models.py` — devtype → family/model (`detect_family`,
  `register_devtype`, `UnsupportedInverterError`), MPVMode maps.
- `faults.py` — fault tables + `translate_*` helpers (pure, tested).
- `fields.py` — `DateTimeField` (clock `yyyy/MMdd/HHmm/ss__`) + pure
  `decode_clock_words` / `encode_clock_words` (pure, tested).
- `info.py`, `realtime_plus_r5.py`, `realtime_r6_3k.py`, `realtime_r6_50k.py`,
  `history.py`, `settings.py` — `modbus-connection` Components.
- `measure.py` — `mgauge`/`minteger`/`muint32`: measurement factories with the
  `0xFFFF` → `None` sentinel wired in.
- `device.py` — `SajInverter` (type-driven detect + poll + snapshot + writes).
- `connection.py` — TCP / serial constructors.
- `cli.py` — JSON dump.

## Testing without hardware

`tests/test_decode.py` covers only pure helpers (clock, fault translate,
power-limit scales) so it runs without `modbus-connection` or an inverter:

```bash
python -m pytest tests/ -q
```
