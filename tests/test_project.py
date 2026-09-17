from __future__ import annotations

from hashlib import sha256
import json
import re
from pathlib import Path
import shutil
import struct
import subprocess

import pytest

from scripts.package_rom import PackageError, package_rom

ROOT = Path(__file__).resolve().parents[1]

RUNTIME_SOURCES = [
    "src/audio_policy.cpp",
    "src/catalog_content.cpp",
    "src/catalog_model.cpp",
    "src/dialog_model.cpp",
    "src/event_model.cpp",
    "src/fishing_content.cpp",
    "src/fishing_model.cpp",
    "src/flow_model.cpp",
    "src/game_state.cpp",
    "src/intro_model.cpp",
    "src/ui_font.cpp",
    "src/options_model.cpp",
    "src/presentation_effects.cpp",
    "src/progression_content.cpp",
    "src/save_codec.cpp",
    "src/shop_model.cpp",
]


def _bmp_info(path: Path) -> tuple[int, int, int]:
    data = path.read_bytes()
    assert data[:2] == b"BM", path
    assert len(data) >= 54, path
    width = struct.unpack_from("<i", data, 18)[0]
    height = abs(struct.unpack_from("<i", data, 22)[0])
    bpp = struct.unpack_from("<H", data, 28)[0]
    return width, height, bpp


def _rom_bytes(*, title: bytes = b"FISH HORIZON", code: bytes = b"FHGA", size: int = 1024) -> bytes:
    data = bytearray(size)
    data[0xA0:0xAC] = title.ljust(12, b" ")[:12]
    data[0xAC:0xB0] = code.ljust(4, b" ")[:4]
    return bytes(data)


def test_runtime_contract(tmp_path: Path):
    compiler = shutil.which("g++") or shutil.which("c++")
    if compiler is None:
        pytest.skip("host C++ compiler unavailable")

    exe = tmp_path / "runtime_tests"
    result = subprocess.run(
        [
            compiler,
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-pedantic",
            "-Iinclude",
            "tests/runtime_tests.cpp",
            *RUNTIME_SOURCES,
            "-o",
            str(exe),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True, check=False)
    assert run.returncode == 0, run.stderr


def test_graphics_are_well_formed():
    graphics = ROOT / "graphics"
    bmps = {path.stem: path for path in graphics.glob("*.bmp")}
    configs = {path.stem: path for path in graphics.glob("*.json")}
    assert bmps.keys() == configs.keys()

    for stem, bmp in bmps.items():
        width, height, bpp = _bmp_info(bmp)
        assert width > 0 and height > 0, stem
        assert bpp == 8, stem
        config = json.loads(configs[stem].read_text(encoding="utf-8"))
        assert config["type"] in {"sprite", "regular_bg"}, stem



def test_waterfall_background_asset_contract():
    bmp = ROOT / "graphics" / "fishing_bg_waterfall.bmp"
    config_path = ROOT / "graphics" / "fishing_bg_waterfall.json"
    assert bmp.exists()
    assert config_path.exists()
    assert _bmp_info(bmp) == (256, 768, 8)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config == {
        "type": "regular_bg",
        "bpp_mode": "bpp_8",
        "tiles_compression": "auto_no_huffman",
        "palette_compression": "auto_no_huffman",
        "map_compression": "none",
        "height": 256,
    }

def test_generated_asset_references_have_matching_graphics():
    include_pattern = re.compile(r'#include "bn_(?:regular_bg|sprite)_items_([a-z0-9_]+)\.h"')
    item_pattern = re.compile(r'bn::(?:regular_bg|sprite)_items::([a-z0-9_]+)')
    available = {path.stem for path in (ROOT / "graphics").glob("*.json")}
    missing: list[tuple[str, str]] = []
    for source in (ROOT / "src").glob("*.cpp"):
        text = source.read_text(encoding="utf-8")
        for stem in include_pattern.findall(text) + item_pattern.findall(text):
            if stem not in available:
                missing.append((source.name, stem))
    assert missing == []


def test_graphics_use_logical_names():
    stems = {path.stem for path in (ROOT / "graphics").iterdir() if path.is_file()}
    assert "shop_bg" in stems
    assert "m4_shop" not in stems
    assert not any(stem.startswith(("m3_", "m4_", "m7_")) for stem in stems)


def test_repo_is_standalone_and_tests_are_minimal():
    assert not (ROOT / "reference").exists()
    assert not (ROOT / "tools").exists()

    forbidden = ("recover_", "verify_m", "reference_apk", "stage_reference")
    names = [path.name for path in ROOT.rglob("*") if path.is_file()]
    assert not any(any(token in name for token in forbidden) for name in names)

    test_files = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "tests").rglob("*")
        if path.is_file() and path.suffix in {".cpp", ".py"}
    )
    assert test_files == ["tests/runtime_tests.cpp", "tests/test_project.py"]


def test_package_rom_contract(tmp_path: Path):
    rom = tmp_path / "input.gba"
    payload = _rom_bytes()
    rom.write_bytes(payload)

    result = package_rom(rom, tmp_path / "dist")
    assert result.rom.name == "Fishermans_Horizon_GBA.gba"
    assert result.checksum.name == "Fishermans_Horizon_GBA.gba.sha256"
    assert result.sha256 == sha256(payload).hexdigest()
    assert result.rom.read_bytes() == payload
    assert result.checksum.read_text(encoding="ascii") == (
        f"{result.sha256}  Fishermans_Horizon_GBA.gba\n"
    )

    bad = tmp_path / "bad.gba"
    bad.write_bytes(_rom_bytes(title=b"OTHER GAME"))
    with pytest.raises(PackageError, match="ROM title"):
        package_rom(bad, tmp_path / "bad-dist")
