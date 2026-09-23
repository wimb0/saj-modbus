"""Auto-detecting SAJ inverter: PLUS / R5 / R6 3-15K / R6 17-50K.

C6 is NOT supported (Modbus control is known to cause issues on those units)
and fails closed at setup.

Detection is driven only by the Type register (info ``0x8F00``) that the
inverter itself reports: setup reads the info block, maps the reported type
via :func:`models.detect_family`, and polls that family's map. There is no
address probing — polling the wrong family's registers is what mis-controls
hardware. Unknown or unreadable types raise
:class:`models.UnsupportedInverterError` instead of guessing.

Polling and the optional-block pattern build on upstream
:mod:`modbus_connection.model.device` (``Device`` / ``async_poll`` /
``read_optional``) rather than reimplementing them.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from modbus_connection import (
    IllegalDataAddressError,
    IllegalFunctionError,
    ModbusError,
    ModbusTimeoutError,
    ModbusUnit,
)
from modbus_connection.model import Component
from modbus_connection.model.device import Device, UpdateReport, read_optional
from modbus_connection.tmodbus import ModbusConnection

from .connection import (
    DEFAULT_SLAVE_ID,
    create_serial_connection,
    create_tcp_connection,
)
from .faults import (
    decode_plus_r5_faults,
    decode_r6_3k_faults,
    fault_messages_to_state,
)
from .history import (
    FAULT_BLOCKS,
    HistoryDailyEnergy,
    HistoryMonthlyEnergy,
    _fault_block_class,
    build_fault_history,
)
from .info import InverterInfo, decode_rs485_ate
from .models import (
    DEVTYPE_MODELS,
    Family,
    UnsupportedInverterError,
    describe_plus_r5_mode,
    describe_r6_3k_mode,
    detect_family,
)
from .realtime_plus_r5 import PlusR5Realtime
from .realtime_r6_3k import (
    R6_3KBattery,
    R6_3KBusBatPv,
    R6_3KEnergy,
    R6_3KFlows,
    R6_3KGrid,
    R6_3KHeader,
    R6_3KInv,
    R6_3KOutput,
    R6_3KStrings,
)
from .realtime_r6_50k import R6_50KHead, R6_50KPv
from .settings import (
    ClassicSettings,
    LegacySettings,
    PlusR5Power,
    R6_3KPower,
    R6_3KSettings,
)

_LOGGER = logging.getLogger(__name__)

UNIT_ID = DEFAULT_SLAVE_ID

# Refusals meaning "not in this inverter's map", for the on-demand history
# reads below. Setup/poll refusals go through upstream read_optional instead.
_NOT_SERVED = (IllegalFunctionError, IllegalDataAddressError)


def _plain_items(comp: Component) -> dict[str, Any]:
    """Declared register fields of one component, datetimes as ISO strings."""
    out: dict[str, Any] = {}
    for name in getattr(type(comp), "declared_fields", ()):
        value = getattr(comp, name)
        out[name] = value.isoformat() if isinstance(value, datetime) else value
    return out


def _component_snapshot(components: list[tuple[str, Component]]) -> dict[str, Any]:
    """Dump every *declared register field* of the components into a dict.

    Only ``declared_fields`` (the register/coil words from the PDF maps) are
    included — never the planner internals (``coil_ranges``, ``max_gap``,
    ``register_space``, ...) that also live on the instance.
    """
    out: dict[str, Any] = {}
    for prefix, comp in components:
        for name, value in _plain_items(comp).items():
            out[f"{prefix}.{name}"] = value
    return out


class SajInverter(Device):
    """One SAJ inverter on a Modbus unit, family detected from its type."""

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit)
        self.info = InverterInfo(unit)
        # PLUS/R5
        self.plus_r5 = PlusR5Realtime(unit)
        self.power = PlusR5Power(unit)
        # R6 3-15K
        self.r6_3k_header = R6_3KHeader(unit)
        self.r6_3k_battery = R6_3KBattery(unit)
        self.r6_3k_grid = R6_3KGrid(unit)
        self.r6_3k_inv = R6_3KInv(unit)
        self.r6_3k_output = R6_3KOutput(unit)
        self.r6_3k_busbatpv = R6_3KBusBatPv(unit)
        self.r6_3k_strings = R6_3KStrings(unit)
        self.r6_3k_flows = R6_3KFlows(unit)
        self.r6_3k_energy = R6_3KEnergy(unit)
        self.r6_3k_power = R6_3KPower(unit)
        # R6 17-50K (C6 excluded: setup refuses C6 types before reaching here)
        self.r6_50k_head = R6_50KHead(unit)
        self.r6_50k_pv = R6_50KPv(unit)
        # Settings (never polled)
        self.classic_settings = ClassicSettings(unit)
        self.r6_3k_settings = R6_3KSettings(unit)
        self.legacy = LegacySettings(unit)
        # History (PLUS/R5 only, never polled — read on demand)
        self.history_daily = HistoryDailyEnergy(unit)
        self.history_monthly = HistoryMonthlyEnergy(unit)
        self.history_faults: list[tuple[int, int, Component]] = [
            (first, last, cls(unit)) for first, last, cls in FAULT_BLOCKS
        ]

        self.family: Family | None = None
        self.absent: frozenset[str] = frozenset()
        self._polled: list[str] | None = None
        self._power_limit: float = 110.0

    # -- constructors ------------------------------------------------------
    @classmethod
    def tcp(cls, host: str, port: int = 502, slave_id: int = UNIT_ID) -> SajInverter:
        """Build an inverter over TCP (keeps the connection open)."""
        conn = create_tcp_connection(host, port)
        inv = cls(conn.for_unit(slave_id))
        inv._connection: ModbusConnection | None = conn
        return inv

    @classmethod
    def serial(
        cls,
        device: str,
        baudrate: int = 9600,
        slave_id: int = UNIT_ID,
    ) -> SajInverter:
        """Build an inverter over serial RTU (or serial-over-network URL)."""
        conn = create_serial_connection(device, baudrate)
        inv = cls(conn.for_unit(slave_id))
        inv._connection = conn
        return inv

    @classmethod
    async def probe_devtype(cls, unit: ModbusUnit) -> int | None:
        """Read back just the reported Type register (info ``0x8F00``).

        Helper for classifying hardware whose type code is not listed yet
        (R6 codes are unpublished): returns the raw value to pass to
        :func:`models.register_devtype`, or ``None`` if unreadable.
        """
        info = InverterInfo(unit)
        try:
            await info.async_update()
        except ModbusError:
            return None
        return info.devtype

    # -- identity ----------------------------------------------------------
    @property
    def components(self) -> dict[str, Component]:
        return {
            "info": self.info,
            "plus_r5": self.plus_r5,
            "power": self.power,
            "r6_3k_header": self.r6_3k_header,
            "r6_3k_battery": self.r6_3k_battery,
            "r6_3k_grid": self.r6_3k_grid,
            "r6_3k_inv": self.r6_3k_inv,
            "r6_3k_output": self.r6_3k_output,
            "r6_3k_busbatpv": self.r6_3k_busbatpv,
            "r6_3k_strings": self.r6_3k_strings,
            "r6_3k_flows": self.r6_3k_flows,
            "r6_3k_energy": self.r6_3k_energy,
            "r6_50k_head": self.r6_50k_head,
            "r6_50k_pv": self.r6_50k_pv,
            "history_daily": self.history_daily,
            "history_monthly": self.history_monthly,
        }

    @property
    def devtype(self) -> int | None:
        """The raw Type value the inverter reports (info ``0x8F00``)."""
        return self.info.devtype

    @property
    def serial_number(self) -> str | None:
        return self.info.sn or None

    @property
    def model_name(self) -> str | None:
        if self.family == "r6_3k":
            return "R6 3-15K (hybrid)"
        if self.family == "r6_50k":
            return "R6 17-50K"
        return DEVTYPE_MODELS.get(self.info.devtype)

    @property
    def mpvmode_raw(self) -> int | None:
        if self.family == "r6_3k":
            return self.r6_3k_header.mpvmode
        if self.family == "r6_50k":
            return self.r6_50k_head.mpvmode
        return self.plus_r5.mpvmode

    @property
    def status(self) -> str:
        if self.family == "r6_3k":
            return describe_r6_3k_mode(self.mpvmode_raw)
        return describe_plus_r5_mode(self.mpvmode_raw)

    @property
    def fault_messages(self) -> list[str]:
        if self.family == "r6_3k":
            h = self.r6_3k_header
            return decode_r6_3k_faults(h.hfaultmsg, h.mfaultmsg, h.mfaultmsg2)
        if self.family == "r6_50k":
            h = self.r6_50k_head
            return decode_plus_r5_faults(h.faultmsg0, h.faultmsg1, h.faultmsg2)
        r = self.plus_r5
        return decode_plus_r5_faults(r.faultmsg0, r.faultmsg1, r.faultmsg2)

    @property
    def faultmsg(self) -> str:
        return fault_messages_to_state(self.fault_messages)

    # -- setup / polling (upstream Device pattern) -----------------------------
    async def _async_setup(self) -> None:
        """Read the static info, detect the family, learn optional blocks.

        The info block is required: without the reported type there is no
        safe family to pick, so an unreadable info block raises instead of
        guessing. C6 and unknown types raise
        :class:`UnsupportedInverterError`.
        """
        try:
            await self.info.async_update()
        except ModbusError as ex:
            raise UnsupportedInverterError(
                None,
                f"Device type unreadable; refusing to guess the inverter family: {ex}",
            ) from ex

        self.family = detect_family(self.info.devtype)
        _LOGGER.info(
            "Detected SAJ family %s (reported type=0x%04X)",
            self.family,
            self.info.devtype,
        )

        absent = set()
        if self.family == "plus_r5":
            if await read_optional(self.power) is None:
                absent.add("power")
                _LOGGER.info("Optional block power not served; switch unavailable")
            self._polled = [n for n in ("plus_r5", "power") if n not in absent]
        elif self.family == "r6_3k":
            # Battery/strings/flows are optional on some firmware; the header
            # + grid + energy are the core. Probe the rest best-effort.
            core = ["r6_3k_header", "r6_3k_grid", "r6_3k_energy"]
            optional = [
                "r6_3k_battery",
                "r6_3k_inv",
                "r6_3k_output",
                "r6_3k_busbatpv",
                "r6_3k_strings",
                "r6_3k_flows",
                "r6_3k_power",
            ]
            for name in optional:
                if await read_optional(getattr(self, name)) is None:
                    absent.add(name)
            self._polled = core + [n for n in optional if n not in absent]
        else:
            self._polled = ["r6_50k_head", "r6_50k_pv"]

        self.absent = frozenset(absent)

    async def async_setup(self) -> Family:
        """Detect the family (idempotent; failed setups retry next call)."""
        await self.async_ensure_setup()
        assert self.family is not None
        return self.family

    async def async_update(self) -> UpdateReport:
        """Poll the detected family's components (setup first if needed)."""
        return await self.async_poll(self._polled or ())

    async def async_close(self) -> None:
        conn: ModbusConnection | None = getattr(self, "_connection", None)
        if conn is not None:
            await conn.close()

    # -- history (on demand, PLUS/R5 only) -----------------------------------
    def _require_history_family(self) -> None:
        """History blocks are only mapped for PLUS/R5; anything else raises."""
        if self._require_family() != "plus_r5":
            raise UnsupportedInverterError(
                self.devtype,
                "History blocks are only mapped for PLUS/R5 inverters",
            )

    @staticmethod
    def _plain(comp: Component) -> dict[str, Any]:
        """Declared fields of one component, datetimes as ISO strings."""
        return _plain_items(comp)

    async def async_read_energy_history(self) -> dict[str, dict[str, Any]]:
        """Read the energy ledger: daily (3 months) + monthly/yearly totals.

        Slow (a few hundred registers) — call on demand, not every poll.
        A refused block is skipped; if neither answers the inverter does not
        serve history at all and this raises.
        """
        self._require_history_family()
        out: dict[str, dict[str, Any]] = {}
        for key, comp in (
            ("daily_kwh", self.history_daily),
            ("monthly_kwh", self.history_monthly),
        ):
            try:
                await comp.async_update()
            except _NOT_SERVED:
                continue
            out[key] = self._plain(comp)
        if not out:
            raise UnsupportedInverterError(
                self.devtype,
                "energy history not served by this inverter (0x0A00 refused)",
            )
        return out

    async def _read_fault_slots_fallback(
        self,
        first: int,
        last: int,
        slots: dict[int, tuple[datetime | None, int | None, int | None, int | None]],
    ) -> int:
        """Read one 25-slot window slot by slot after its block read refused.

        Some firmware serves fewer than the documented 100 slots and rejects
        any read covering the missing tail, so fall back to 10-register reads
        and keep whatever answers. Aborts on 3 consecutive timeouts (dead link
        rather than missing registers).
        """
        count = 0
        timeouts = 0
        for slot in range(first, last + 1):
            comp = _fault_block_class(slot, slot)(self.modbus_unit)
            try:
                await comp.async_update()
            except _NOT_SERVED:
                continue
            except ModbusTimeoutError:
                timeouts += 1
                if timeouts >= 3:
                    raise
                continue
            timeouts = 0
            slots[slot] = (
                getattr(comp, f"herror_time{slot:03d}"),
                getattr(comp, f"herror{slot:03d}_0"),
                getattr(comp, f"herror{slot:03d}_1"),
                getattr(comp, f"herror{slot:03d}_2"),
            )
            count += 1
        return count

    async def async_read_fault_history(self) -> list[dict[str, Any]]:
        """Read the 100-slot fault record; empty slots are skipped.

        Slow (~1000 registers over several reads) — call on demand. Windows
        the inverter refuses fall back to slot-by-slot reads; if nothing
        answers at all this raises instead of returning a lying empty list.

        Timestamps are naive datetimes (the inverter reports no zone);
        contrast the timezone-aware realtime clock.
        """
        self._require_history_family()
        slots: dict[int, tuple[datetime | None, int | None, int | None, int | None]] = {}
        for first, last, block in self.history_faults:
            try:
                await block.async_update()
            except _NOT_SERVED:
                await self._read_fault_slots_fallback(first, last, slots)
                continue
            for slot in range(first, last + 1):
                slots[slot] = (
                    getattr(block, f"herror_time{slot:03d}"),
                    getattr(block, f"herror{slot:03d}_0"),
                    getattr(block, f"herror{slot:03d}_1"),
                    getattr(block, f"herror{slot:03d}_2"),
                )
        if not slots:
            raise UnsupportedInverterError(
                self.devtype,
                "fault history not served by this inverter (0x0B00 refused)",
            )
        return build_fault_history(slots)

    # -- snapshot ----------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        """Everything decoded, as a plain JSON-able dict."""
        if self.family == "plus_r5":
            blocks = [("info", self.info), ("realtime", self.plus_r5)]
            extra: dict[str, Any] = {"power_on_off": self.power.poweronoff}
        elif self.family == "r6_3k":
            h = self.r6_3k_header
            blocks = [
                ("info", self.info),
                ("header", h),
                ("battery", self.r6_3k_battery),
                ("grid", self.r6_3k_grid),
                ("inv", self.r6_3k_inv),
                ("output", self.r6_3k_output),
                ("busbatpv", self.r6_3k_busbatpv),
                ("strings", self.r6_3k_strings),
                ("flows", self.r6_3k_flows),
                ("energy", self.r6_3k_energy),
            ]
            extra = {"inverter_stopped": self.r6_3k_power.inverterstop}
        else:
            blocks = [("info", self.info), ("head", self.r6_50k_head), ("pv", self.r6_50k_pv)]
            extra = {}
        out = _component_snapshot(blocks)
        out["family"] = self.family
        out["devtype"] = self.devtype
        out["model"] = self.model_name
        out["serial"] = self.serial_number
        out["rs485"] = decode_rs485_ate(self.info.rs485_ate)
        out["status"] = self.status
        out["mpvmode"] = self.mpvmode_raw
        out["faults"] = self.fault_messages
        out["faultmsg"] = self.faultmsg
        out.update(extra)
        return out

    # -- control writes ----------------------------------------------------
    def _require_family(self) -> Family:
        if self.family is None:
            raise UnsupportedInverterError(None, "Setup has not detected a family yet")
        return self.family

    async def async_set_power_on_off(self, value: bool) -> bool:
        """Remote on/off. R6 3-15K uses the inverted 0x340C register."""
        family = self._require_family()
        try:
            if family == "r6_3k":
                await self.r6_3k_power.write("inverterstop", not value)
            else:
                await self.power.write("poweronoff", value)
        except ModbusError as ex:
            _LOGGER.error("Failed to set power on/off: %s", ex)
            return False
        return True

    async def async_set_power_limit(self, percent: float) -> bool:
        """Active power limit in percent (0-110).

        Tries the modern register first (0x101C classic / 0x340B R6-3K),
        falls back to the legacy 0x801F your component uses.
        """
        family = self._require_family()
        if not 0 <= percent <= 110:
            raise ValueError(f"power limit must be 0-110 %, got {percent}")
        try:
            if family == "r6_3k":
                try:
                    await self.r6_3k_settings.write("powerlimited", percent / 100)
                except _NOT_SERVED:
                    await self.legacy.write("limitpower", percent)
            else:
                try:
                    await self.classic_settings.write("powerlimited", percent / 100)
                except _NOT_SERVED:
                    await self.legacy.write("limitpower", percent)
        except ModbusError as ex:
            _LOGGER.error("Failed to set power limit: %s", ex)
            return False
        self._power_limit = percent
        return True

    @property
    def power_limit(self) -> float:
        """Last power limit written (write-only on the inverter)."""
        return self._power_limit

    async def async_set_datetime(self, value: datetime | None = None) -> None:
        """Sync the inverter clock (0x8020).

        Defaults to the machine-local wall time (the inverter keeps no zone);
        ``.astimezone()`` preserves that across timezones where a bare UTC
        ``now()`` would shift the wall clock.
        """
        await self.legacy.write("datetime", value or datetime.now(timezone.utc).astimezone())
