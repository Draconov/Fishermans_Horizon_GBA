#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_toolchain import check_toolchain
from scripts.stage_reference_assets import stage_m1_assets
from scripts.verify_m0 import _verify_recovery, _verify_staged_title
from tools.recover_m1 import recover_m1_from_apk
from tools.reference_apk import validate_reference

M1_ASSET_FILES = (
    "title_anim.bmp",
    "title_anim.json",
    "map.bmp",
    "map.json",
    "map_spots.bmp",
    "map_spots.json",
    "crystal_lake.bmp",
    "crystal_lake.json",
)


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _verify_m0_recovery(apk: Path) -> bool:
    return _verify_recovery(apk)


def _verify_m0_title(apk: Path) -> bool:
    return _verify_staged_title(apk)


def _verify_m1_recovery(apk: Path, expected_path: Path | None = None) -> bool:
    expected_path = expected_path or (ROOT / "reference" / "m1_title_map.json")
    generated = json.dumps(recover_m1_from_apk(apk), indent=2) + "\n"
    return expected_path.is_file() and expected_path.read_text(encoding="utf-8") == generated


def _manifest_records(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    return {row["output_path"]: row for row in rows}


def _verify_m1_assets(
    apk: Path,
    expected_graphics: Path | None = None,
    manifest_path: Path | None = None,
) -> bool:
    expected_graphics = expected_graphics or (ROOT / "graphics")
    manifest_path = manifest_path or (ROOT / "reference" / "reference_asset_manifest.tsv")

    with tempfile.TemporaryDirectory(prefix="fh-m1-assets-") as temp_dir:
        generated_graphics = Path(temp_dir) / "graphics"
        records = stage_m1_assets(apk, generated_graphics)

        for name in M1_ASSET_FILES:
            expected = expected_graphics / name
            generated = generated_graphics / name
            if not expected.is_file() or expected.read_bytes() != generated.read_bytes():
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


def _run_host_tests(apk: Path) -> bool:
    env = os.environ.copy()
    env["FH_REFERENCE_APK"] = str(apk)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT,
        env=env,
        check=False,
    )
    return result.returncode == 0


def _build_rom_if_available() -> tuple[bool | None, str]:
    status = check_toolchain()
    if not status.can_build_rom:
        reasons = []
        if not status.arm_compiler:
            reasons.append("arm-none-eabi-g++ missing")
        if not status.make:
            reasons.append("make missing")
        if not status.butano_mak.is_file():
            reasons.append(f"Butano missing at {status.butano_dir}")
        return None, ", ".join(reasons)

    rom = ROOT / "Fishermans_Horizon_GBA.gba"
    rom.unlink(missing_ok=True)
    env = os.environ.copy()
    env["LIBBUTANO"] = str(status.butano_dir)
    result = subprocess.run(
        [status.make or "make", "-j2"],
        cwd=ROOT,
        env=env,
        check=False,
    )
    return result.returncode == 0 and rom.is_file(), str(rom)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Fisherman's Horizon GBA M1 verification gate")
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

    if not _verify_m0_recovery(args.apk):
        return _fail("[FAIL] M0 recovered_surface.json is stale")
    print("[PASS] M0 deterministic DEX surface")

    if not _verify_m0_title(args.apk):
        return _fail("[FAIL] M0 staged title asset is stale")
    print("[PASS] M0 deterministic title staging")

    if not _verify_m1_recovery(args.apk):
        return _fail("[FAIL] M1 recovered title/map facts are stale")
    print("[PASS] M1 recovered title/map facts")

    if not _verify_m1_assets(args.apk):
        return _fail("[FAIL] M1 staged assets or manifest are stale")
    print("[PASS] M1 deterministic title/map/Crystal Lake assets")

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
