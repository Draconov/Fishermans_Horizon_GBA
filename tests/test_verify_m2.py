from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil


def _verify_m2_module():
    path = Path("scripts/verify_m2.py")
    assert path.is_file(), "M2 verification gate is missing"
    spec = importlib.util.spec_from_file_location("verify_m2_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verify_m2_allows_explicitly_unavailable_rom_build(reference_apk: Path, monkeypatch, capsys):
    verify_m2 = _verify_m2_module()
    monkeypatch.setattr(verify_m2, "_verify_m1_gate", lambda _apk: True)
    monkeypatch.setattr(verify_m2, "_verify_m2_recovery", lambda _apk: True)
    monkeypatch.setattr(verify_m2, "_verify_m2_assets", lambda _apk: True)
    monkeypatch.setattr(verify_m2, "_run_host_tests", lambda _apk: True)
    monkeypatch.setattr(
        verify_m2,
        "_build_rom_if_available",
        lambda: (None, "arm-none-eabi-g++ missing, Butano missing"),
    )

    assert verify_m2.main(["--apk", str(reference_apk)]) == 0
    output = capsys.readouterr().out
    assert "[PASS] M2 recovered Crystal Lake fishing facts" in output
    assert "[PASS] M2 deterministic fishing assets" in output
    assert "[INFO] ROM build unavailable locally" in output
    assert "[PASS] ROM build" not in output


def test_verify_m2_recovery_detects_stale_frozen_json(reference_apk: Path, tmp_path: Path):
    verify_m2 = _verify_m2_module()
    stale = tmp_path / "m2_fishing.json"
    stale.write_text("{}\n", encoding="utf-8")
    assert not verify_m2._verify_m2_recovery(reference_apk, stale)


def test_verify_m2_assets_detect_byte_and_mapping_mismatch(reference_apk: Path, tmp_path: Path):
    verify_m2 = _verify_m2_module()
    graphics = tmp_path / "graphics"
    graphics.mkdir()
    for name in verify_m2.M2_ASSET_FILES:
        shutil.copy2(Path("graphics") / name, graphics / name)
    (graphics / "fishing_lake.bmp").write_bytes(b"stale")
    assert not verify_m2._verify_m2_assets(reference_apk, graphics)

    for name in verify_m2.M2_ASSET_FILES:
        shutil.copy2(Path("graphics") / name, graphics / name)
    (graphics / "fishing_sprite_map.json").write_text("{}\n", encoding="utf-8")
    assert not verify_m2._verify_m2_assets(reference_apk, graphics)


def test_verify_m2_propagates_host_test_failure(reference_apk: Path, monkeypatch, capsys):
    verify_m2 = _verify_m2_module()
    monkeypatch.setattr(verify_m2, "_verify_m1_gate", lambda _apk: True)
    monkeypatch.setattr(verify_m2, "_verify_m2_recovery", lambda _apk: True)
    monkeypatch.setattr(verify_m2, "_verify_m2_assets", lambda _apk: True)
    monkeypatch.setattr(verify_m2, "_run_host_tests", lambda _apk: False)

    assert verify_m2.main(["--apk", str(reference_apk)]) == 1
    assert "[FAIL] host test suite" in capsys.readouterr().err


def test_readme_documents_m2_fishing_vertical_slice_and_limitations():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "## M2 status" in text
    assert "Crystal Lake fishing loop" in text
    assert "A = hold/release rod" in text
    assert "Select = cycle owned bait" in text
    assert "scripts/verify_m2.py" in text
    assert "dialog typography" in text
    assert "audio" in text
