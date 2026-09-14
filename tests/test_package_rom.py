from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from scripts.package_rom import PackageError, package_rom


def _rom_bytes(*, title: bytes = b"FISH HORIZON", code: bytes = b"FHGA", size: int = 1024) -> bytes:
    data = bytearray(size)
    data[0xA0:0xAC] = title.ljust(12, b" ")[:12]
    data[0xAC:0xB0] = code.ljust(4, b" ")[:4]
    return bytes(data)


def test_package_rom_rejects_missing_and_too_small_rom(tmp_path: Path):
    with pytest.raises(PackageError, match="not found"):
        package_rom(tmp_path / "missing.gba", tmp_path / "dist")

    small = tmp_path / "small.gba"
    small.write_bytes(b"x" * 0xAF)
    with pytest.raises(PackageError, match="too small"):
        package_rom(small, tmp_path / "dist")


def test_package_rom_rejects_wrong_title_or_game_code(tmp_path: Path):
    wrong_title = tmp_path / "wrong_title.gba"
    wrong_title.write_bytes(_rom_bytes(title=b"OTHER GAME"))
    with pytest.raises(PackageError, match="ROM title"):
        package_rom(wrong_title, tmp_path / "dist")

    wrong_code = tmp_path / "wrong_code.gba"
    wrong_code.write_bytes(_rom_bytes(code=b"NOPE"))
    with pytest.raises(PackageError, match="game code"):
        package_rom(wrong_code, tmp_path / "dist")


def test_package_rom_writes_exact_release_files_and_checksum(tmp_path: Path):
    rom = tmp_path / "input.gba"
    payload = _rom_bytes()
    rom.write_bytes(payload)

    result = package_rom(rom, tmp_path / "dist")
    assert result.rom.name == "Fishermans_Horizon_GBA.gba"
    assert result.checksum.name == "Fishermans_Horizon_GBA.gba.sha256"
    assert result.sha256 == sha256(payload).hexdigest()
    assert result.rom.read_bytes() == payload
    assert result.checksum.read_text() == f"{result.sha256}  Fishermans_Horizon_GBA.gba\n"
    assert sorted(path.name for path in result.rom.parent.iterdir()) == [
        "Fishermans_Horizon_GBA.gba",
        "Fishermans_Horizon_GBA.gba.sha256",
    ]


def test_package_rom_is_idempotent_and_cleans_stale_output(tmp_path: Path):
    rom = tmp_path / "input.gba"
    rom.write_bytes(_rom_bytes())
    out = tmp_path / "dist"
    out.mkdir()
    (out / "stale.txt").write_text("stale")

    first = package_rom(rom, out)
    first_rom = first.rom.read_bytes()
    first_sum = first.checksum.read_bytes()
    second = package_rom(rom, out)

    assert second.rom.read_bytes() == first_rom
    assert second.checksum.read_bytes() == first_sum
    assert sorted(path.name for path in out.iterdir()) == [
        "Fishermans_Horizon_GBA.gba",
        "Fishermans_Horizon_GBA.gba.sha256",
    ]
