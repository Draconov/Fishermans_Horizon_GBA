from __future__ import annotations

from pathlib import Path
import shutil

import scripts.verify_m1 as verify_m1


def test_verify_m1_allows_explicitly_unavailable_rom_build(reference_apk: Path, monkeypatch, capsys):
    monkeypatch.setattr(verify_m1, "_verify_m0_recovery", lambda _apk: True)
    monkeypatch.setattr(verify_m1, "_verify_m0_title", lambda _apk: True)
    monkeypatch.setattr(verify_m1, "_verify_m1_recovery", lambda _apk: True)
    monkeypatch.setattr(verify_m1, "_verify_m1_assets", lambda _apk: True)
    monkeypatch.setattr(verify_m1, "_run_host_tests", lambda _apk: True)
    monkeypatch.setattr(
        verify_m1,
        "_build_rom_if_available",
        lambda: (None, "arm-none-eabi-g++ missing, Butano missing"),
    )

    assert verify_m1.main(["--apk", str(reference_apk)]) == 0
    output = capsys.readouterr().out
    assert "[PASS] M1 recovered title/map facts" in output
    assert "[INFO] ROM build unavailable locally" in output
    assert "[PASS] ROM build" not in output


def test_verify_m1_recovery_detects_stale_frozen_json(reference_apk: Path, tmp_path: Path):
    stale = tmp_path / "m1_title_map.json"
    stale.write_text("{}\n", encoding="utf-8")
    assert not verify_m1._verify_m1_recovery(reference_apk, stale)


def test_verify_m1_assets_detects_byte_mismatch(reference_apk: Path, tmp_path: Path):
    graphics = tmp_path / "graphics"
    graphics.mkdir()
    for name in verify_m1.M1_ASSET_FILES:
        shutil.copy2(Path("graphics") / name, graphics / name)
    (graphics / "map.bmp").write_bytes(b"stale")

    assert not verify_m1._verify_m1_assets(reference_apk, graphics)


def test_verify_m1_propagates_host_test_failure(reference_apk: Path, monkeypatch, capsys):
    monkeypatch.setattr(verify_m1, "_verify_m0_recovery", lambda _apk: True)
    monkeypatch.setattr(verify_m1, "_verify_m0_title", lambda _apk: True)
    monkeypatch.setattr(verify_m1, "_verify_m1_recovery", lambda _apk: True)
    monkeypatch.setattr(verify_m1, "_verify_m1_assets", lambda _apk: True)
    monkeypatch.setattr(verify_m1, "_run_host_tests", lambda _apk: False)

    assert verify_m1.main(["--apk", str(reference_apk)]) == 1
    assert "[FAIL] host test suite" in capsys.readouterr().err


def test_readme_documents_m1_vertical_slice_and_limitations():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "## M1 status" in text
    assert "animated title" in text
    assert "Crystal Lake" in text
    assert "fresh-save" in text
    assert "fishing mechanics" in text
