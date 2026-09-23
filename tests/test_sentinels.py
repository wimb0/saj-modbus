"""Sentinel coverage: every numeric measurement must decode 0xFFFF* as None.

Runs on source text (ast) so it needs neither modbus-connection nor hardware.
Measurement fields must use the m-versions from saj_modbus.measure (which set
the library-native nan= sentinel); only enum/mode/fault/direction words and
identity fields may use the raw factories.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "saj_modbus"

# field names allowed to use the raw gauge/integer/uint32 factories per file
# (modes, fault words, config/state enums, directions, identity words).
RAW_ALLOWED: dict[str, set[str]] = {
    "info.py": {"devtype", "subtype", "rs485_ate"},
    "realtime_plus_r5.py": {"mpvmode", "faultmsg0", "faultmsg1", "faultmsg2"},
    "realtime_r6_3k.py": {
        "mpvmode",
        "hfaultmsg",
        "mfaultmsg",
        "mfaultmsg2",
        "bmsfaultmsg",
        "setappmode",
        "batstatus",
        "batprotocol",
        "metermodeset",
        "pv_direction",
        "battery_direction",
        "grid_direction",
        "output_direction",
    },
    "realtime_r6_50k.py": {"mpvmode", "faultmsg0", "faultmsg1", "faultmsg2"},
    "history.py": set(),  # energy + fault words are all sentinel-wrapped
}

RAW_FACTORIES = {"gauge", "integer", "uint32"}
MEASURE_FACTORIES = {"mgauge", "minteger", "muint32"}


def _calls(path: Path) -> list[tuple[str, str]]:
    """(field name, factory name) for every `name = factory(...)` in a file."""
    tree = ast.parse(path.read_text())
    out = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
        ):
            out.append((node.targets[0].id, node.value.func.id))
    return out


def test_measurements_use_sentinel_factories():
    for filename, allowed in RAW_ALLOWED.items():
        for field, factory in _calls(ROOT / filename):
            if factory in MEASURE_FACTORIES:
                continue
            if factory in RAW_FACTORIES:
                assert field in allowed, (
                    f"{filename}:{field} uses raw {factory}() without nan sentinel; "
                    f"use m{factory}() from .measure or extend RAW_ALLOWED with justification"
                )


def test_each_map_has_sentinel_fields():
    for filename in RAW_ALLOWED:
        tree = ast.parse((ROOT / filename).read_text())
        factories = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert factories & MEASURE_FACTORIES, f"{filename} has no sentinel fields left"
