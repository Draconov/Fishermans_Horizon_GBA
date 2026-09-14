from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil


def _verify_m3_module():
    path = Path("scripts/verify_m3.py")
    assert path.is_file(), "M3 verification gate is missing"
    spec = importlib.util.spec_from_file_location("verify_m3_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verify_m3_allows_explicitly_unavailable_rom_build(reference_apk: Path, monkeypatch, capsys):
    verify_m3 = _verify_m3_module()
    monkeypatch.setattr(verify_m3, "_verify_m2_gate", lambda _apk: True)
    monkeypatch.setattr(verify_m3, "_verify_m3_recovery", lambda _apk: True)
    monkeypatch.setattr(verify_m3, "_verify_m3_assets", lambda _apk: True)
    monkeypatch.setattr(verify_m3, "_run_host_tests", lambda _apk: True)
    monkeypatch.setattr(
        verify_m3,
        "_build_rom_if_available",
        lambda: (None, "arm-none-eabi-g++ missing, Butano missing"),
    )

    assert verify_m3.main(["--apk", str(reference_apk)]) == 0
    output = capsys.readouterr().out
    assert "[PASS] M0-M2 deterministic reference gate" in output
    assert "[PASS] M3 recovered full fishing content" in output
    assert "[PASS] M3 deterministic all-area fishing assets" in output
    assert "[INFO] ROM build unavailable locally" in output
    assert "[PASS] ROM build" not in output


def test_verify_m3_recovery_detects_stale_frozen_json(reference_apk: Path, tmp_path: Path):
    verify_m3 = _verify_m3_module()
    stale = tmp_path / "m3_fishing_content.json"
    stale.write_text("{}\n", encoding="utf-8")
    assert not verify_m3._verify_m3_recovery(reference_apk, stale)


def test_verify_m3_assets_detect_byte_and_mapping_mismatch(reference_apk: Path, tmp_path: Path):
    verify_m3 = _verify_m3_module()
    graphics = tmp_path / "graphics"
    graphics.mkdir()
    for name in verify_m3.M3_ASSET_FILES:
        shutil.copy2(Path("graphics") / name, graphics / name)

    (graphics / "fishing_area_ocean.bmp").write_bytes(b"stale")
    assert not verify_m3._verify_m3_assets(reference_apk, graphics)

    for name in verify_m3.M3_ASSET_FILES:
        shutil.copy2(Path("graphics") / name, graphics / name)
    (graphics / "fishing_m3_sprite_map.json").write_text("{}\n", encoding="utf-8")
    assert not verify_m3._verify_m3_assets(reference_apk, graphics)


def test_verify_m3_propagates_host_test_failure(reference_apk: Path, monkeypatch, capsys):
    verify_m3 = _verify_m3_module()
    monkeypatch.setattr(verify_m3, "_verify_m2_gate", lambda _apk: True)
    monkeypatch.setattr(verify_m3, "_verify_m3_recovery", lambda _apk: True)
    monkeypatch.setattr(verify_m3, "_verify_m3_assets", lambda _apk: True)
    monkeypatch.setattr(verify_m3, "_run_host_tests", lambda _apk: False)

    assert verify_m3.main(["--apk", str(reference_apk)]) == 1
    assert "[FAIL] host test suite" in capsys.readouterr().err


def test_readme_documents_m3_full_fishing_content_and_audio_boundary():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "## M3 status" in text
    assert "all five fishing areas" in text
    assert "44 unique catalog fish" in text
    assert "three rod variants" in text
    assert "semantic sound events" in text
    assert "sample conversion/playback" in text
    assert "scripts/verify_m3.py" in text
