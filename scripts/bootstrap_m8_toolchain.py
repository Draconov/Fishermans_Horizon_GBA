#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
from typing import Callable

BUTANO_TAG = "21.7.1"
BUTANO_COMMIT = "112a1827c9c6d9e6041a7e93e66f04c4561a6415"
DEVKITARM_RELEASE = "67"
DEVKITARM_GCC_VERSION = "15.2.0"


class ToolchainError(RuntimeError):
    pass


@dataclass(frozen=True)
class ToolchainReport:
    devkitpro: Path
    devkitarm_release: str
    compiler: Path
    compiler_version: str
    butano_dir: Path
    butano_tag: str
    butano_commit: str

    def to_json_dict(self) -> dict[str, str]:
        data = asdict(self)
        return {key: str(value) for key, value in data.items()}


def _run_text(command: list[str], runner: Callable[..., subprocess.CompletedProcess[str]]) -> str:
    completed = runner(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "command failed").strip()
        raise ToolchainError(f"command failed ({' '.join(command)}): {detail}")
    return completed.stdout.strip()


def inspect_toolchain(
    *,
    devkitpro: Path = Path("/opt/devkitpro"),
    butano_dir: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> ToolchainReport:
    devkitpro = Path(devkitpro)
    butano_dir = Path(butano_dir)
    compiler = devkitpro / "devkitARM" / "bin" / "arm-none-eabi-g++"
    if not compiler.is_file():
        raise ToolchainError(f"devkitARM compiler not found: {compiler}")
    butano_mak = butano_dir / "butano.mak"
    if not butano_mak.is_file():
        raise ToolchainError(f"Butano butano.mak not found: {butano_mak}")

    compiler_version = _run_text([str(compiler), "-dumpfullversion"], runner)
    if compiler_version != DEVKITARM_GCC_VERSION:
        raise ToolchainError(
            f"unexpected devkitARM GCC: {compiler_version!r}; "
            f"expected release r{DEVKITARM_RELEASE} / GCC {DEVKITARM_GCC_VERSION!r}"
        )
    butano_tag = _run_text(["git", "-C", str(butano_dir), "describe", "--tags", "--exact-match"], runner)
    if butano_tag != BUTANO_TAG:
        raise ToolchainError(f"unexpected Butano tag: {butano_tag!r}; expected {BUTANO_TAG!r}")
    butano_commit = _run_text(["git", "-C", str(butano_dir), "rev-parse", "HEAD"], runner)
    if butano_commit != BUTANO_COMMIT:
        raise ToolchainError(f"unexpected Butano commit: {butano_commit!r}; expected {BUTANO_COMMIT!r}")
    return ToolchainReport(
        devkitpro=devkitpro,
        devkitarm_release=DEVKITARM_RELEASE,
        compiler=compiler,
        compiler_version=compiler_version,
        butano_dir=butano_dir,
        butano_tag=butano_tag,
        butano_commit=butano_commit,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect the pinned M8 GBA toolchain")
    parser.add_argument("--devkitpro", type=Path, default=Path("/opt/devkitpro"))
    parser.add_argument("--butano", type=Path, required=True)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)
    try:
        report = inspect_toolchain(devkitpro=args.devkitpro, butano_dir=args.butano)
    except ToolchainError as exc:
        parser.error(str(exc))
    print(f"devkitARM release: r{report.devkitarm_release}")
    print(f"devkitARM compiler: {report.compiler}")
    print(f"devkitARM GCC: {report.compiler_version}")
    print(f"Butano: {report.butano_tag} @ {report.butano_commit}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Report: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
