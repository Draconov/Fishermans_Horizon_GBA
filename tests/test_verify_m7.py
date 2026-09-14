from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def _module():
    import scripts.verify_m7 as module
    return module


def test_verify_m7_rejects_stale_recovery_json(reference_apk: Path, tmp_path: Path):
    m = _module()
    stale = tmp_path / "m7.json"
    stale.write_text("{}\n", encoding="utf-8")
    assert not m._verify_m7_recovery(reference_apk, stale)


def test_verify_m7_rejects_intro_asset_drift(reference_apk: Path, tmp_path: Path):
    m = _module()
    graphics = tmp_path / "graphics"
    graphics.mkdir()
    for name in m.M7_ASSET_FILES:
        source = Path("graphics") / name
        (graphics / name).write_bytes(source.read_bytes())
    intro = graphics / "m7_intro_credit.bmp"
    data = bytearray(intro.read_bytes())
    data[-1] ^= 1
    intro.write_bytes(data)
    assert not m._verify_m7_assets(reference_apk, graphics, Path("reference/reference_asset_manifest.tsv"))


def test_verify_m7_rejects_image_mode_runtime_surface(tmp_path: Path):
    m = _module()
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "include").mkdir()
    (root / "src" / "bad.cpp").write_text("int image_option = 2; // stretched\n", encoding="utf-8")
    assert not m._verify_no_image_mode_runtime(root)


def test_verify_m7_propagates_host_failures(reference_apk: Path, monkeypatch, capsys):
    m = _module()
    monkeypatch.setattr(m, "_verify_m6_source_gate", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_m7_recovery", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_m7_assets", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_no_image_mode_runtime", lambda: True)
    monkeypatch.setattr(m, "_run_host_tests", lambda _apk: False)
    assert m.main(["--apk", str(reference_apk)]) == 1
    assert "[FAIL] host test suite" in capsys.readouterr().err


def test_verify_m7_allows_missing_local_toolchain_as_info(reference_apk: Path, monkeypatch, capsys):
    m = _module()
    monkeypatch.setattr(m, "_verify_m6_source_gate", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_m7_recovery", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_m7_assets", lambda _apk: True)
    monkeypatch.setattr(m, "_verify_no_image_mode_runtime", lambda: True)
    monkeypatch.setattr(m, "_run_host_tests", lambda _apk: True)
    monkeypatch.setattr(m, "_build_rom_if_available", lambda: (None, "toolchain missing"))
    assert m.main(["--apk", str(reference_apk)]) == 0
    out = capsys.readouterr().out
    assert "[PASS] M7 recovered final-parity evidence" in out
    assert "[INFO] ROM build unavailable locally" in out


def test_verify_m7_can_be_launched_as_a_script():
    result = subprocess.run(
        [sys.executable, "scripts/verify_m7.py", "--help"],
        cwd=".", text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "M7 final-parity gate" in result.stdout


def test_verify_m7_self_run_excludes_only_its_own_test_file():
    text = Path("scripts/verify_m7.py").read_text() if Path("scripts/verify_m7.py").exists() else ""
    assert "--ignore=tests/test_verify_m7.py" in text
    assert "verify_m6_main" not in text


def test_readme_documents_m7_final_parity_gate():
    text = Path("README.md").read_text()
    assert "scripts/verify_m7.py" in text
    assert "image mode" in text.lower()
    assert "GameIntro" in text
    assert "DialogBox" in text
