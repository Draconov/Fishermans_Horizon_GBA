from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil


def _verify_m4_module():
    path = Path("scripts/verify_m4.py")
    assert path.is_file(), "M4 verification gate is missing"
    spec = importlib.util.spec_from_file_location("verify_m4_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verify_m4_allows_explicitly_unavailable_rom_build(reference_apk: Path, monkeypatch, capsys):
    verify_m4 = _verify_m4_module()
    monkeypatch.setattr(verify_m4, "_verify_m3_gate", lambda _apk: True)
    monkeypatch.setattr(verify_m4, "_verify_m4_recovery", lambda _apk: True)
    monkeypatch.setattr(verify_m4, "_verify_m4_assets", lambda _apk: True)
    monkeypatch.setattr(verify_m4, "_run_host_tests", lambda _apk: True)
    monkeypatch.setattr(
        verify_m4,
        "_build_rom_if_available",
        lambda: (None, "arm-none-eabi-g++ missing, Butano missing"),
    )

    assert verify_m4.main(["--apk", str(reference_apk)]) == 0
    output = capsys.readouterr().out
    assert "[PASS] M0-M3 deterministic reference gate" in output
    assert "[PASS] M4 recovered progression content" in output
    assert "[PASS] M4 deterministic progression assets" in output
    assert "[INFO] ROM build unavailable locally" in output
    assert "[PASS] ROM build" not in output


def test_verify_m4_recovery_detects_stale_or_malformed_frozen_json(reference_apk: Path, tmp_path: Path):
    verify_m4 = _verify_m4_module()
    stale = tmp_path / "m4_progression_content.json"
    stale.write_text("{}\n", encoding="utf-8")
    assert not verify_m4._verify_m4_recovery(reference_apk, stale)

    frozen = json.loads(Path("reference/m4_progression_content.json").read_text(encoding="utf-8"))
    frozen["shop"]["prices"][0] = 999
    stale.write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
    assert not verify_m4._verify_m4_recovery(reference_apk, stale)


def test_verify_m4_assets_detect_byte_and_manifest_mismatch(reference_apk: Path, tmp_path: Path):
    verify_m4 = _verify_m4_module()
    graphics = tmp_path / "graphics"
    graphics.mkdir()
    for name in verify_m4.M4_ASSET_FILES:
        shutil.copy2(Path("graphics") / name, graphics / name)

    (graphics / "m4_catalog_anim.bmp").write_bytes(b"stale")
    assert not verify_m4._verify_m4_assets(reference_apk, graphics)

    for name in verify_m4.M4_ASSET_FILES:
        shutil.copy2(Path("graphics") / name, graphics / name)
    stale_manifest = tmp_path / "manifest.tsv"
    stale_manifest.write_text("output_path\toutput_sha256\n", encoding="utf-8")
    assert not verify_m4._verify_m4_assets(reference_apk, graphics, stale_manifest)


def test_verify_m4_propagates_host_test_failure(reference_apk: Path, monkeypatch, capsys):
    verify_m4 = _verify_m4_module()
    monkeypatch.setattr(verify_m4, "_verify_m3_gate", lambda _apk: True)
    monkeypatch.setattr(verify_m4, "_verify_m4_recovery", lambda _apk: True)
    monkeypatch.setattr(verify_m4, "_verify_m4_assets", lambda _apk: True)
    monkeypatch.setattr(verify_m4, "_run_host_tests", lambda _apk: False)

    assert verify_m4.main(["--apk", str(reference_apk)]) == 1
    assert "[FAIL] host test suite" in capsys.readouterr().err


def test_readme_documents_m4_progression_and_fresh_save_path():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "## M4 status" in text
    assert "16 one-time shop items" in text
    assert "44-entry catalog" in text
    assert "Cecil prologue" in text
    assert "fresh-save" in text
    assert "scripts/verify_m4.py" in text
