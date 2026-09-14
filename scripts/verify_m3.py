#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.stage_reference_assets import stage_m3_assets
from scripts.verify_m1 import _build_rom_if_available, _manifest_records, _run_host_tests
from scripts.verify_m2 import _verify_m1_gate, _verify_m2_assets, _verify_m2_recovery
from tools.recover_m3 import recover_m3_from_apk
from tools.reference_apk import validate_reference

M3_ASSET_FILES = (
    "fishing_area_crystal.bmp", "fishing_area_crystal.json",
    "fishing_area_pier.bmp", "fishing_area_pier.json",
    "fishing_area_river.bmp", "fishing_area_river.json",
    "fishing_area_ocean.bmp", "fishing_area_ocean.json",
    "fishing_area_cave.bmp", "fishing_area_cave.json",
    "fishing_fish_m3_0.bmp", "fishing_fish_m3_0.json",
    "fishing_fish_m3_1.bmp", "fishing_fish_m3_1.json",
    "fishing_m3_sprite_map.json",
    "fishing_rods_left.bmp", "fishing_rods_left.json",
    "fishing_rods_right.bmp", "fishing_rods_right.json",
)


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _verify_m2_gate(apk: Path) -> bool:
    return _verify_m1_gate(apk) and _verify_m2_recovery(apk) and _verify_m2_assets(apk)


def _verify_m3_recovery(apk: Path, expected_path: Path | None = None) -> bool:
    expected_path = expected_path or (ROOT / "reference" / "m3_fishing_content.json")
    generated = json.dumps(recover_m3_from_apk(apk), indent=2) + "\n"
    return expected_path.is_file() and expected_path.read_text(encoding="utf-8") == generated


def _verify_m3_assets(
    apk: Path,
    expected_graphics: Path | None = None,
    manifest_path: Path | None = None,
) -> bool:
    expected_graphics = expected_graphics or (ROOT / "graphics")
    manifest_path = manifest_path or (ROOT / "reference" / "reference_asset_manifest.tsv")

    with tempfile.TemporaryDirectory(prefix="fh-m3-assets-") as temp_dir:
        generated_graphics = Path(temp_dir) / "graphics"
        records = stage_m3_assets(apk, generated_graphics)

        for name in M3_ASSET_FILES:
            expected = expected_graphics / name
            generated = generated_graphics / name
            if not expected.is_file() or not generated.is_file():
                return False
            if expected.read_bytes() != generated.read_bytes():
                return False

        frozen = _manifest_records(manifest_path)
        for record in records:
            output_path = str(record["output_path"])
            frozen_record = frozen.get(output_path)
            if frozen_record is None:
                return False
            for key, value in record.items():
                if frozen_record.get(key) != str(value):
                    return False

    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Fisherman's Horizon GBA M3 verification gate")
    parser.add_argument("--apk", required=True, type=Path)
    args = parser.parse_args(argv)

    if not args.apk.is_file():
        print(f"reference APK not found: {args.apk}", file=sys.stderr)
        return 2

    reference_errors = validate_reference(args.apk, ROOT / "reference" / "apk_inventory.tsv")
    if reference_errors:
        for error in reference_errors:
            print(error, file=sys.stderr)
        return 1
    print("[PASS] canonical APK hash + inventory")

    if not _verify_m2_gate(args.apk):
        return _fail("[FAIL] M0-M2 deterministic recovery or assets are stale")
    print("[PASS] M0-M2 deterministic reference gate")

    if not _verify_m3_recovery(args.apk):
        return _fail("[FAIL] M3 recovered full fishing content is stale")
    print("[PASS] M3 recovered full fishing content")

    if not _verify_m3_assets(args.apk):
        return _fail("[FAIL] M3 staged all-area fishing assets or manifest are stale")
    print("[PASS] M3 deterministic all-area fishing assets")

    if not _run_host_tests(args.apk):
        return _fail("[FAIL] host test suite")
    print("[PASS] host test suite")

    built, detail = _build_rom_if_available()
    if built is None:
        print(f"[INFO] ROM build unavailable locally: {detail}")
    elif not built:
        return _fail(f"[FAIL] ROM build did not produce expected file: {detail}")
    else:
        print(f"[PASS] ROM build: {detail}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
