# Changelog

All notable changes to `saj-modbus` are recorded here. Dates are release dates
of the corresponding zip drops / git tags.

## 0.7.0 — 2026-09-23

- SubType (`0x8F01`) decodes as rated watts (verified: 2500 = 2.5 kW):
  `SajInverter.rated_power`,   `snapshot["rated_power_w"]`, and power-suffixed `model_name`
  (e.g. `R5 (single-phase), 2.5K`).

## 0.6.0 — 2026-09-23

- End-to-end tests against the in-memory mock backend (`MockModbusConnection`):
  detect/poll/snapshot, unknown-type refusal, write round-trip, partial and
  unserved fault history, raw-word reads. Needs `pytest-asyncio`
  (`asyncio_mode = "auto"`).
- CLI `--raw ADDRESS COUNT` escape hatch dumping raw holding-register words
  (`SajInverter.async_read_raw_words`); works even when setup refuses.
- CLI `--timeout` and `timeout=` on `tcp()`/`serial()` (was fixed at 5 s).
- Fault-history fallback reads refused windows concurrently.
- PyPI trusted-publishing workflow (needs a `pypi` environment + project setup).

## 0.5.0 — 2026-09-23

- Yearly energy ledger split out of `monthly_kwh` into its own `yearly_kwh`
  block (`HistoryYearlyEnergy`, `0x0A8D-0x0ABE`).

## 0.4.1 — 2026-09-23

- Ruff-clean tree (imports, `datetime.UTC`, `functools.cache`, naive-datetime
  `noqa` with reasons, test-only `DTZ001` ignore).

## 0.4.0 — 2026-09-23

- `SajInverter` builds on upstream `modbus_connection.model.device`
  (`Device` / `async_poll` / `read_optional`); own poll loop removed.
- Snapshot decodes `rs485_ate` into `{"baudrate", "slave"}`.
- Fault slot classes memoized; `_plain`/`snapshot` dump unified.
- CI lint step; fault timestamps documented as naive, realtime as aware.

## 0.3.3 — 2026-09-23

- Fault timestamps decode binary-first (observed on R5 despite the "BCD"
  docs) with BCD fallback; verified against a live `0x0B00` slot dump.

## 0.3.2 — 2026-09-23

- Removed `SajInverter.async_read_raw` (no public raw API on the installed
  backend; it could only raise `AttributeError`).

## 0.3.1 — 2026-09-23

- Refused fault-history windows fall back to slot-by-slot reads; fully
  unserved areas raise `UnsupportedInverterError` instead of tracebacks.

## 0.3.0 — 2026-09-23

- On-demand history: energy ledger (`0x0A00-0x0ABE`) and 100-slot fault
  record (`0x0B00-0x0EE6`); CLI `--history`.
- `0xFFFF` sentinels decode to `None` via library-native `nan=` on every
  measurement field; snapshot only dumps declared fields.

## 0.2.1 — 2026-09-23

- `requirements.txt`; `requires-python >= 3.12`.

## 0.2.0 — 2026-09-23

- C6 excluded (fails closed); type-driven family detection (`detect_family`,
  `register_devtype`, `UnsupportedInverterError`); renamed to `saj-modbus` /
  `saj_modbus`; MIT license; CI on Python 3.12+.

## 0.1.0 — 2026-09-23

- Initial package: PLUS/R5/R6 maps from the three SAJ PDFs, auto-detection,
  snapshot, control writes, CLI dump.
