#!/usr/bin/env python3
from __future__ import annotations

import argparse
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

from scripts.package_rom import OUTPUT_ROM, OUTPUT_SUM, PackageError, package_rom
from scripts.smoke_mgba import SmokeResult, smoke_rom
from scripts.verify_m1 import _build_rom_if_available
from scripts.verify_m5 import _verify_m4_gate, _verify_m5_audio, _verify_m5_parity, _verify_m5_recovery

WORKFLOW = ROOT / ".github" / "workflows" / "gba.yml"


def _fail(message: str) -> int:
    print(message, file=__import__("sys").stderr)
    return 1


def _verify_m5_gate(apk: Path) -> bool:
    return (
        _verify_m4_gate(apk)
        and _verify_m5_recovery(apk)
        and _verify_m5_audio(apk)
        and _verify_m5_parity(apk)
    )




def _run_host_tests(apk: Path) -> bool:
    env = os.environ.copy()
    env["FH_REFERENCE_APK"] = str(apk)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--ignore=tests/test_verify_m6.py"],
        cwd=ROOT,
        env=env,
        check=False,
    )
    return result.returncode == 0

def _verify_workflow_contract(workflow: Path | None = None) -> bool:
    workflow = workflow or WORKFLOW
    try:
        text = workflow.read_text(encoding="utf-8")
        parsed = yaml.safe_load(text)
    except (OSError, yaml.YAMLError):
        return False
    if not isinstance(parsed, dict) or not isinstance(parsed.get("jobs"), dict):
        return False
    required = (
        "devkitpro/devkitarm:20260610",
        "--branch 21.7.1",
        "python -m pytest -q",
        "scripts/package_rom.py",
        "scripts/smoke_mgba.py",
        "--require-available",
        "publish_release:",
        "release_tag:",
        "actions/upload-artifact@v4",
        "actions/download-artifact@v4",
        "Fishermans_Horizon_GBA.gba.sha256",
    )
    if any(item not in text for item in required):
        return False
    guard = "github.event_name == 'workflow_dispatch' && inputs.publish_release == true && inputs.release_tag != ''"
    if text.count(guard) < 2:
        return False
    if "permissions:\n  contents: read" not in text:
        return False
    release = parsed["jobs"].get("release")
    if not isinstance(release, dict) or release.get("permissions", {}).get("contents") != "write":
        return False
    return True


def _synthetic_rom() -> bytes:
    data = bytearray(1024)
    data[0xA0:0xAC] = b"FISH HORIZON"
    data[0xAC:0xB0] = b"FHGA"
    return bytes(data)


def _verify_package_contract(
    *,
    packager: Callable[[Path, Path], object] = package_rom,
) -> bool:
    try:
        with tempfile.TemporaryDirectory(prefix="fh-m6-package-") as td:
            temp = Path(td)
            source = temp / "source.gba"
            source.write_bytes(_synthetic_rom())
            out = temp / "dist"
            packager(source, out)
            names = sorted(path.name for path in out.iterdir() if path.is_file())
            if names != [OUTPUT_ROM, OUTPUT_SUM]:
                return False
            rom = out / OUTPUT_ROM
            checksum = out / OUTPUT_SUM
            if rom.read_bytes() != source.read_bytes():
                return False
            digest = sha256(source.read_bytes()).hexdigest()
            if checksum.read_text(encoding="ascii") != f"{digest}  {OUTPUT_ROM}\n":
                return False
    except (OSError, PackageError, AttributeError, TypeError):
        return False
    return True


def _package_built_rom(rom: Path) -> Path:
    result = package_rom(rom, ROOT / "dist")
    return result.rom


def _smoke_built_rom(rom: Path) -> SmokeResult:
    return smoke_rom(rom)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Fisherman's Horizon GBA M6 release-hardening gate")
    parser.add_argument("--apk", required=True, type=Path)
    args = parser.parse_args(argv)

    if not args.apk.is_file():
        print(f"reference APK not found: {args.apk}", file=__import__("sys").stderr)
        return 2

    if not _verify_m5_gate(args.apk):
        return _fail("[FAIL] M5 canonical parity gate")
    print("[PASS] M5 canonical parity gate")

    if not _verify_workflow_contract():
        return _fail("[FAIL] M6 release workflow contract")
    print("[PASS] M6 release workflow contract")

    if not _verify_package_contract():
        return _fail("[FAIL] M6 deterministic package contract")
    print("[PASS] M6 deterministic package contract")

    if not _run_host_tests(args.apk):
        return _fail("[FAIL] host test suite")
    print("[PASS] host test suite")

    built, detail = _build_rom_if_available()
    if built is None:
        print(f"[INFO] local ROM build unavailable: {detail}")
        print("[INFO] release eligibility not claimed locally")
        return 0
    if not built:
        return _fail(f"[FAIL] local ROM build did not produce expected file: {detail}")

    rom = Path(detail)
    print(f"[PASS] local ROM build: {rom}")
    try:
        packaged_rom = _package_built_rom(rom)
    except (OSError, PackageError) as exc:
        return _fail(f"[FAIL] package built ROM: {exc}")
    print(f"[PASS] packaged ROM: {packaged_rom}")

    smoke = _smoke_built_rom(packaged_rom)
    if not smoke.available:
        print(f"[INFO] local mGBA unavailable: {smoke.detail}")
        print("[INFO] release eligibility not claimed locally")
        return 0
    if not smoke.passed:
        return _fail(f"[FAIL] mGBA smoke test: {smoke.detail}")
    print(f"[PASS] mGBA smoke test: {smoke.detail}")
    print("[PASS] release eligibility: ROM built, packaged, and smoke-tested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
