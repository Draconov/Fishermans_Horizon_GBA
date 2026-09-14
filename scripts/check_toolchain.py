#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ToolchainStatus:
    arm_compiler: str | None
    make: str | None
    butano_dir: Path
    butano_mak: Path

    @property
    def can_build_rom(self) -> bool:
        return bool(self.arm_compiler and self.make and self.butano_mak.is_file())


def check_toolchain() -> ToolchainStatus:
    configured = os.environ.get("LIBBUTANO")
    butano_dir = Path(configured) if configured else ROOT.parent / "butano" / "butano"
    return ToolchainStatus(
        arm_compiler=shutil.which("arm-none-eabi-g++"),
        make=shutil.which("make"),
        butano_dir=butano_dir,
        butano_mak=butano_dir / "butano.mak",
    )


def main() -> int:
    status = check_toolchain()
    print(f"arm-none-eabi-g++: {status.arm_compiler or 'missing'}")
    print(f"make: {status.make or 'missing'}")
    print(f"Butano: {status.butano_dir}")
    print(f"butano.mak: {'found' if status.butano_mak.is_file() else 'missing'}")
    print(f"ROM build: {'available' if status.can_build_rom else 'unavailable locally'}")
    return 0 if status.can_build_rom else 1


if __name__ == "__main__":
    raise SystemExit(main())
