#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.stage_reference_assets import stage_m7_assets
from scripts.verify_m1 import _build_rom_if_available, _manifest_records
from scripts.verify_m6 import _verify_m5_gate, _verify_package_contract, _verify_workflow_contract
from tools.recover_m7 import recover_m7_from_apk
from tools.reference_apk import validate_reference

_M7_STEMS = (
    "m7_intro_credit",
    "m7_options_anim",
    "m7_dialog_panel",
    "m7_dialog_markers",
    "m7_dialog_dollar",
)
M7_ASSET_FILES = tuple(f"{stem}.{suffix}" for stem in _M7_STEMS for suffix in ("bmp", "json"))


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _verify_m6_source_gate(apk: Path) -> bool:
    return _verify_m5_gate(apk) and _verify_workflow_contract() and _verify_package_contract()


def _verify_m7_recovery(apk: Path, expected_path: Path | None = None) -> bool:
    expected_path = expected_path or (ROOT / "reference" / "m7_final_parity.json")
    try:
        generated = json.dumps(recover_m7_from_apk(apk), indent=2, sort_keys=True) + "\n"
        return expected_path.is_file() and expected_path.read_text(encoding="utf-8") == generated
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return False


def _verify_m7_assets(
    apk: Path,
    expected_graphics: Path | None = None,
    manifest_path: Path | None = None,
) -> bool:
    expected_graphics = expected_graphics or (ROOT / "graphics")
    manifest_path = manifest_path or (ROOT / "reference" / "reference_asset_manifest.tsv")
    try:
        with tempfile.TemporaryDirectory(prefix="fh-m7-assets-") as td:
            generated_graphics = Path(td) / "graphics"
            records = stage_m7_assets(apk, generated_graphics)
            for name in M7_ASSET_FILES:
                expected = expected_graphics / name
                generated = generated_graphics / name
                if not expected.is_file() or not generated.is_file() or expected.read_bytes() != generated.read_bytes():
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
    except (OSError, ValueError, KeyError):
        return False
    return True


def _verify_no_image_mode_runtime(root: Path | None = None) -> bool:
    root = root or ROOT
    forbidden = ("image_option", "image mode", "image_mode", "stretched")
    try:
        for folder in (root / "include", root / "src"):
            for path in folder.rglob("*"):
                if path.suffix not in (".h", ".cpp") or not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8").lower()
                if any(token in text for token in forbidden):
                    return False
    except OSError:
        return False
    return True


def _run_host_tests(apk: Path) -> bool:
    env = os.environ.copy()
    env["FH_REFERENCE_APK"] = str(apk)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--ignore=tests/test_verify_m7.py"],
        cwd=ROOT,
        env=env,
        check=False,
    )
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Fisherman's Horizon GBA M7 final-parity gate")
    parser.add_argument("--apk", required=True, type=Path)
    args = parser.parse_args(argv)

    if not args.apk.is_file():
        print(f"reference APK not found: {args.apk}", file=sys.stderr)
        return 2

    errors = validate_reference(args.apk, ROOT / "reference" / "apk_inventory.tsv")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("[PASS] canonical APK hash + inventory")

    if not _verify_m6_source_gate(args.apk):
        return _fail("[FAIL] M0-M6 deterministic source/release contracts")
    print("[PASS] M0-M6 deterministic source/release contracts")

    if not _verify_m7_recovery(args.apk):
        return _fail("[FAIL] M7 recovered final-parity evidence is stale")
    print("[PASS] M7 recovered final-parity evidence")

    if not _verify_m7_assets(args.apk):
        return _fail("[FAIL] M7 deterministic assets or manifest are stale")
    print("[PASS] M7 deterministic assets")

    if not _verify_no_image_mode_runtime():
        return _fail("[FAIL] Android image-mode runtime surface remains")
    print("[PASS] native 240x160 presentation only; no image mode runtime")

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
