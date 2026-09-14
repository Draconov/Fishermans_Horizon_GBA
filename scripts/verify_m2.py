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

from scripts.stage_reference_assets import stage_m2_assets
from scripts.verify_m1 import (
    _build_rom_if_available,
    _manifest_records,
    _run_host_tests,
    _verify_m0_recovery,
    _verify_m0_title,
    _verify_m1_assets,
    _verify_m1_recovery,
)
from tools.recover_m2 import recover_m2_from_apk
from tools.reference_apk import validate_reference

M2_ASSET_FILES = (
    "fishing_char.bmp",
    "fishing_char.json",
    "fishing_rod_left.bmp",
    "fishing_rod_left.json",
    "fishing_rod_right.bmp",
    "fishing_rod_right.json",
    "fishing_lake.bmp",
    "fishing_lake.json",
    "fishing_bait.bmp",
    "fishing_bait.json",
    "fishing_fish_a.bmp",
    "fishing_fish_a.json",
    "fishing_fish_b.bmp",
    "fishing_fish_b.json",
    "fishing_sprite_map.json",
    "fishing_splash.bmp",
    "fishing_splash.json",
    "fishing_coin.bmp",
    "fishing_coin.json",
    "fishing_hud.bmp",
    "fishing_hud.json",
    "fishing_meter.bmp",
    "fishing_meter.json",
    "fishing_line_dot.bmp",
    "fishing_line_dot.json",
)


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _verify_m1_gate(apk: Path) -> bool:
    return (
        _verify_m0_recovery(apk)
        and _verify_m0_title(apk)
        and _verify_m1_recovery(apk)
        and _verify_m1_assets(apk)
    )


def _verify_m2_recovery(apk: Path, expected_path: Path | None = None) -> bool:
    expected_path = expected_path or (ROOT / "reference" / "m2_fishing.json")
    generated = json.dumps(recover_m2_from_apk(apk), indent=2) + "\n"
    return expected_path.is_file() and expected_path.read_text(encoding="utf-8") == generated


def _verify_m2_assets(
    apk: Path,
    expected_graphics: Path | None = None,
    manifest_path: Path | None = None,
) -> bool:
    expected_graphics = expected_graphics or (ROOT / "graphics")
    manifest_path = manifest_path or (ROOT / "reference" / "reference_asset_manifest.tsv")

    with tempfile.TemporaryDirectory(prefix="fh-m2-assets-") as temp_dir:
        generated_graphics = Path(temp_dir) / "graphics"
        records = stage_m2_assets(apk, generated_graphics)

        for name in M2_ASSET_FILES:
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
    parser = argparse.ArgumentParser(description="Run the Fisherman's Horizon GBA M2 verification gate")
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

    if not _verify_m1_gate(args.apk):
        return _fail("[FAIL] M0/M1 deterministic recovery or assets are stale")
    print("[PASS] M0/M1 deterministic reference gate")

    if not _verify_m2_recovery(args.apk):
        return _fail("[FAIL] M2 recovered Crystal Lake fishing facts are stale")
    print("[PASS] M2 recovered Crystal Lake fishing facts")

    if not _verify_m2_assets(args.apk):
        return _fail("[FAIL] M2 staged fishing assets or manifest are stale")
    print("[PASS] M2 deterministic fishing assets")

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
