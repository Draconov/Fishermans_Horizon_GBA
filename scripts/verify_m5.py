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

from scripts.stage_audio_assets import stage_audio_assets
from scripts.verify_m1 import _build_rom_if_available, _run_host_tests
from scripts.verify_m4 import _verify_m3_gate, _verify_m4_assets, _verify_m4_recovery
from tools.m5_validation import validate_graphics_resources, validate_visual_parity
from tools.recover_m5 import recover_from_apk
from tools.reference_apk import validate_reference


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _verify_m4_gate(apk: Path) -> bool:
    return _verify_m3_gate(apk) and _verify_m4_recovery(apk) and _verify_m4_assets(apk)


def _verify_m5_recovery(apk: Path, expected_path: Path | None = None) -> bool:
    expected_path = expected_path or (ROOT / "reference" / "m5_audio_presentation.json")
    try:
        generated = json.dumps(recover_from_apk(apk), indent=2, sort_keys=True) + "\n"
        return expected_path.is_file() and expected_path.read_text(encoding="utf-8") == generated
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return False


def _verify_m5_audio(
    apk: Path,
    expected_audio: Path | None = None,
    expected_manifest: Path | None = None,
) -> bool:
    expected_audio = expected_audio or (ROOT / "audio")
    expected_manifest = expected_manifest or (ROOT / "reference" / "m5_audio_assets.json")
    try:
        with tempfile.TemporaryDirectory(prefix="fh-m5-audio-") as temp_dir:
            temp = Path(temp_dir)
            generated_audio = temp / "audio"
            generated_manifest = temp / "manifest.json"
            manifest = stage_audio_assets(apk, generated_audio, generated_manifest)
            if not expected_manifest.is_file():
                return False
            if generated_manifest.read_bytes() != expected_manifest.read_bytes():
                return False
            expected_names = {str(item["output"]) for item in manifest["assets"]}
            actual_names = {path.name for path in expected_audio.glob("*.wav")}
            if actual_names != expected_names:
                return False
            for name in expected_names:
                if (generated_audio / name).read_bytes() != (expected_audio / name).read_bytes():
                    return False
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError):
        return False
    return True


def _verify_m5_parity(apk: Path, graphics_dir: Path | None = None) -> bool:
    graphics_dir = graphics_dir or (ROOT / "graphics")
    try:
        return not validate_graphics_resources(graphics_dir) and not validate_visual_parity(apk, graphics_dir)
    except (OSError, ValueError, KeyError):
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Fisherman's Horizon GBA M5 verification gate")
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

    if not _verify_m4_gate(args.apk):
        return _fail("[FAIL] M0-M4 deterministic recovery or assets are stale")
    print("[PASS] M0-M4 deterministic reference gate")

    if not _verify_m5_recovery(args.apk):
        return _fail("[FAIL] M5 recovered audio/presentation evidence is stale")
    print("[PASS] M5 recovered audio/presentation evidence")

    if not _verify_m5_audio(args.apk):
        return _fail("[FAIL] M5 deterministic audio assets are stale")
    print("[PASS] M5 deterministic audio assets")

    if not _verify_m5_parity(args.apk):
        return _fail("[FAIL] M5 GBA resource or visual parity")
    print("[PASS] M5 GBA resource and visual parity")

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
