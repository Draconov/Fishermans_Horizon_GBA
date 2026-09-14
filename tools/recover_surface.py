from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import zipfile

from tools.dex import DexFile
from tools.reference_apk import CANONICAL_APK_SHA256

_APP_PREFIX = "Lcom/fishermanshorizon/app/"
_FISH_FIELD = re.compile(r"^fish([0-9A-F]{2})$")
_FISHING_STATE_ORDER = (
    "INIT",
    "STAND",
    "GET_READY_TO_THROW",
    "THROW",
    "BAIT_IN_WATER",
    "FISH_IN_LINE",
    "RECOIL",
    "FISH_CATCH",
    "LINE_BREAK",
    "REWARD",
)
_AREA_ORDER = ("CRYSTAL_LAKE", "PIER", "RIVER", "OCEAN", "CAVE")


def _require_symbols(strings: set[str], symbols: tuple[str, ...], label: str) -> list[str]:
    missing = [symbol for symbol in symbols if symbol not in strings]
    if missing:
        raise ValueError(f"missing {label} symbols: {', '.join(missing)}")
    return list(symbols)


def recover_surface(dex: DexFile) -> dict[str, object]:
    strings = dex.strings()
    string_set = set(strings)

    catalog_pairs = []
    for value in strings:
        match = _FISH_FIELD.fullmatch(value)
        if match:
            catalog_pairs.append((int(match.group(1), 16), value))
    catalog_fields = [value for index, value in sorted(catalog_pairs) if index < 0x2C]
    expected_catalog = [f"fish{index:02X}" for index in range(0x2C)]
    if catalog_fields != expected_catalog:
        raise ValueError("catalog field sequence fish00..fish2B is incomplete")

    classes = [
        descriptor
        for descriptor in dex.class_descriptors()
        if descriptor.startswith(_APP_PREFIX)
    ]
    methods = [
        {
            "class": method.class_descriptor,
            "name": method.name,
            "prototype": method.prototype,
        }
        for method in dex.methods()
        if method.class_descriptor.startswith(_APP_PREFIX)
    ]

    return {
        "origin": {
            "apk_sha256": CANONICAL_APK_SHA256,
            "member": "classes.dex",
        },
        "dex_counts": {
            "strings": dex.string_ids_size,
            "methods": dex.method_ids_size,
            "classes": dex.class_defs_size,
        },
        "catalog_fields": catalog_fields,
        "fishing_states": _require_symbols(
            string_set, _FISHING_STATE_ORDER, "fishing state"
        ),
        "area_symbols": _require_symbols(string_set, _AREA_ORDER, "area"),
        "classes": classes,
        "methods": methods,
    }


def recover_from_apk(apk_path: Path) -> dict[str, object]:
    with zipfile.ZipFile(apk_path, "r") as archive:
        dex_bytes = archive.read("classes.dex")
    return recover_surface(DexFile(dex_bytes))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recover Fisherman's Horizon DEX symbol surface")
    parser.add_argument("apk", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)

    surface = recover_from_apk(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(surface, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
