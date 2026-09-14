#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import shutil

EXPECTED_TITLE = b"FISH HORIZON"
EXPECTED_CODE = b"FHGA"
OUTPUT_ROM = "Fishermans_Horizon_GBA.gba"
OUTPUT_SUM = "Fishermans_Horizon_GBA.gba.sha256"


class PackageError(RuntimeError):
    pass


@dataclass(frozen=True)
class PackageResult:
    rom: Path
    checksum: Path
    sha256: str


def _clean_ascii(raw: bytes) -> bytes:
    return raw.rstrip(b"\x00 ")


def _validate_rom(data: bytes) -> None:
    if len(data) < 0xB0:
        raise PackageError(f"ROM is too small for a GBA header: {len(data)} bytes")
    title = _clean_ascii(data[0xA0:0xAC])
    code = _clean_ascii(data[0xAC:0xB0])
    if title != EXPECTED_TITLE:
        raise PackageError(f"unexpected ROM title: {title!r}")
    if code != EXPECTED_CODE:
        raise PackageError(f"unexpected ROM game code: {code!r}")


def package_rom(rom: Path, output_dir: Path) -> PackageResult:
    rom = Path(rom)
    output_dir = Path(output_dir)
    if not rom.is_file():
        raise PackageError(f"ROM not found: {rom}")

    data = rom.read_bytes()
    _validate_rom(data)

    if output_dir.exists():
        for child in output_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        output_dir.mkdir(parents=True)

    digest = sha256(data).hexdigest()
    output_rom = output_dir / OUTPUT_ROM
    output_sum = output_dir / OUTPUT_SUM
    output_rom.write_bytes(data)
    output_sum.write_text(f"{digest}  {OUTPUT_ROM}\n", encoding="ascii", newline="\n")
    return PackageResult(output_rom, output_sum, digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and package the Fisherman's Horizon GBA ROM")
    parser.add_argument("--rom", type=Path, default=Path("Fishermans_Horizon_GBA.gba"))
    parser.add_argument("--out", type=Path, default=Path("dist"))
    args = parser.parse_args(argv)
    try:
        result = package_rom(args.rom, args.out)
    except PackageError as exc:
        parser.error(str(exc))
    print(f"ROM: {result.rom}")
    print(f"SHA-256: {result.sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
