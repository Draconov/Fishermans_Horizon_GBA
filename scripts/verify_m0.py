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
from scripts.stage_reference_assets import stage_title
from tools.recover_surface import recover_from_apk
from tools.reference_apk import validate_reference


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _verify_recovery(apk: Path) -> bool:
    generated = json.dumps(recover_from_apk(apk), indent=2, ensure_ascii=False) + "\n"
    expected_path = ROOT / "reference" / "recovered_surface.json"
    return expected_path.read_text(encoding="utf-8") == generated


def _manifest_record(manifest: Path | None = None) -> dict[str, str]:
    manifest = manifest or (ROOT / "reference" / "reference_asset_manifest.tsv")
    with manifest.open("r", encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    matches = [row for row in rows if row.get("output_path") == "graphics/title.bmp"]
    if len(matches) != 1:
        raise ValueError("reference asset manifest must contain exactly one M0 title asset")
    return matches[0]


def _verify_staged_title(apk: Path) -> bool:
    with tempfile.TemporaryDirectory(prefix="fh-m0-assets-") as temp_dir:
        temp_graphics = Path(temp_dir) / "graphics"
        record = stage_title(apk, temp_graphics)
        if (temp_graphics / "title.bmp").read_bytes() != (ROOT / "graphics" / "title.bmp").read_bytes():
            return False
        if (temp_graphics / "title.json").read_bytes() != (ROOT / "graphics" / "title.json").read_bytes():
            return False

        frozen = _manifest_record()
        for key, value in record.items():
            if frozen.get(key) != str(value):
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
    parser = argparse.ArgumentParser(description="Run the Fisherman's Horizon GBA M0 verification gate")
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

    if not _verify_recovery(args.apk):
        return _fail("[FAIL] recovered_surface.json is stale")
    print("[PASS] deterministic DEX recovery output")

    if not _verify_staged_title(args.apk):
        return _fail("[FAIL] staged title asset or manifest is stale")
    print("[PASS] deterministic title asset staging")

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
