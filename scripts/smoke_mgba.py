#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
from typing import Callable


@dataclass(frozen=True)
class SmokeResult:
    available: bool
    passed: bool
    detail: str
    log: str = ""


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _has_fatal_log(log: str) -> bool:
    return re.search(r"\b(?:fatal|error)\b", log, flags=re.IGNORECASE) is not None


def smoke_rom(
    rom: Path,
    *,
    emulator: str = "mgba",
    timeout_seconds: float = 5.0,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> SmokeResult:
    rom = Path(rom)
    emulator_path = which(emulator)
    if not emulator_path:
        return SmokeResult(False, False, f"mGBA emulator not found: {emulator}")
    if not rom.is_file():
        return SmokeResult(True, False, f"ROM not found: {rom}")

    command = [emulator_path, "-l", "71", str(rom)]
    try:
        completed = runner(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        log = _as_text(exc.stdout) + _as_text(exc.stderr)
        if _has_fatal_log(log):
            return SmokeResult(True, False, "mGBA logged fatal/error before timeout", log)
        return SmokeResult(True, True, f"mGBA remained alive for {timeout_seconds:g}s", log)
    except OSError as exc:
        return SmokeResult(True, False, f"failed to launch mGBA: {exc}")

    log = _as_text(completed.stdout) + _as_text(completed.stderr)
    if _has_fatal_log(log):
        return SmokeResult(True, False, "mGBA logged fatal/error before exiting", log)
    return SmokeResult(True, False, f"mGBA exited early with code {completed.returncode}", log)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a bounded Fisherman's Horizon ROM smoke test in mGBA")
    parser.add_argument("--rom", type=Path, default=Path("dist/Fishermans_Horizon_GBA.gba"))
    parser.add_argument("--emulator", default="mgba")
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--require-available", action="store_true")
    args = parser.parse_args(argv)

    result = smoke_rom(args.rom, emulator=args.emulator, timeout_seconds=args.seconds)
    if result.log:
        print(result.log, end="" if result.log.endswith("\n") else "\n")
    if not result.available:
        prefix = "[FAIL]" if args.require_available else "[INFO]"
        print(f"{prefix} {result.detail}")
        return 2 if args.require_available else 0
    if result.passed:
        print(f"[PASS] {result.detail}")
        return 0
    print(f"[FAIL] {result.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
