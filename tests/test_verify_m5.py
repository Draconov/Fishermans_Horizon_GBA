from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil


def _module():
    path = Path("scripts/verify_m5.py")
    assert path.is_file(), "M5 verification gate is missing"
    spec = importlib.util.spec_from_file_location("verify_m5_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verify_m5_allows_unavailable_rom_build(reference_apk: Path, monkeypatch, capsys):
    m = _module()
    monkeypatch.setattr(m, "_verify_m4_gate", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_m5_recovery", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_m5_audio", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_m5_parity", lambda _apk: True)
    monkeypatch.setattr(m, "_run_host_tests", lambda _apk: True)
    monkeypatch.setattr(m, "_build_rom_if_available", lambda: (None, "toolchain missing"))
    assert m.main(["--apk", str(reference_apk)]) == 0
    out = capsys.readouterr().out
    assert "[PASS] M0-M4 deterministic reference gate" in out
    assert "[PASS] M5 deterministic audio assets" in out
    assert "[PASS] M5 GBA resource and visual parity" in out
    assert "[INFO] ROM build unavailable locally" in out


def test_verify_m5_recovery_detects_stale_json(reference_apk: Path, tmp_path: Path):
    m = _module()
    stale = tmp_path / "m5.json"
    data = json.loads(Path("reference/m5_audio_presentation.json").read_text())
    data["conversion"]["sample_rate"] = 12345
    stale.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    assert not m._verify_m5_recovery(reference_apk, stale)


def test_verify_m5_audio_detects_changed_wav(reference_apk: Path, tmp_path: Path):
    m = _module()
    audio = tmp_path / "audio"
    shutil.copytree("audio", audio)
    path = audio / "coin.wav"
    data = bytearray(path.read_bytes()); data[-1] ^= 1; path.write_bytes(data)
    assert not m._verify_m5_audio(reference_apk, audio, Path("reference/m5_audio_assets.json"))


def test_verify_m5_propagates_parity_and_host_failures(reference_apk: Path, monkeypatch, capsys):
    m = _module()
    monkeypatch.setattr(m, "_verify_m4_gate", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_m5_recovery", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_m5_audio", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_m5_parity", lambda _apk: False)
    assert m.main(["--apk", str(reference_apk)]) == 1
    assert "[FAIL] M5 GBA resource or visual parity" in capsys.readouterr().err

    monkeypatch.setattr(m, "_verify_m5_parity", lambda _apk: True)
    monkeypatch.setattr(m, "_run_host_tests", lambda _apk: False)
    assert m.main(["--apk", str(reference_apk)]) == 1
    assert "[FAIL] host test suite" in capsys.readouterr().err


def test_readme_documents_m5_persistence_audio_and_hardening():
    text = Path("README.md").read_text()
    assert "## M5 status" in text
    assert "32-byte" in text
    assert "SRAM" in text
    assert "16 kHz" in text
    assert "textSE.mp3" in text
    assert "scripts/verify_m5.py" in text
