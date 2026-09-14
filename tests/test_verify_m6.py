from __future__ import annotations

from pathlib import Path

from scripts.smoke_mgba import SmokeResult


def _module():
    import scripts.verify_m6 as module
    return module


def test_verify_m6_allows_unavailable_local_build(reference_apk: Path, monkeypatch, capsys):
    m = _module()
    monkeypatch.setattr(m, '_verify_m5_gate', lambda _apk: True)
    monkeypatch.setattr(m, '_verify_workflow_contract', lambda: True)
    monkeypatch.setattr(m, '_verify_package_contract', lambda: True)
    monkeypatch.setattr(m, '_run_host_tests', lambda _apk: True)
    monkeypatch.setattr(m, '_build_rom_if_available', lambda: (None, 'toolchain missing'))
    assert m.main(['--apk', str(reference_apk)]) == 0
    out = capsys.readouterr().out
    assert '[PASS] M5 canonical parity gate' in out
    assert '[PASS] M6 release workflow contract' in out
    assert '[INFO] local ROM build unavailable' in out
    assert 'release eligibility not claimed' in out


def test_verify_m6_allows_unavailable_local_emulator_after_real_build(reference_apk: Path, monkeypatch, tmp_path: Path, capsys):
    m = _module()
    rom = tmp_path / 'Fishermans_Horizon_GBA.gba'; rom.write_bytes(b'x')
    monkeypatch.setattr(m, '_verify_m5_gate', lambda _apk: True)
    monkeypatch.setattr(m, '_verify_workflow_contract', lambda: True)
    monkeypatch.setattr(m, '_verify_package_contract', lambda: True)
    monkeypatch.setattr(m, '_run_host_tests', lambda _apk: True)
    monkeypatch.setattr(m, '_build_rom_if_available', lambda: (True, str(rom)))
    monkeypatch.setattr(m, '_package_built_rom', lambda _rom: tmp_path / 'dist' / 'Fishermans_Horizon_GBA.gba')
    monkeypatch.setattr(m, '_smoke_built_rom', lambda _rom: SmokeResult(False, False, 'mGBA missing'))
    assert m.main(['--apk', str(reference_apk)]) == 0
    out = capsys.readouterr().out
    assert '[PASS] local ROM build' in out
    assert '[INFO] local mGBA unavailable' in out
    assert 'release eligibility not claimed' in out


def test_verify_m6_detects_malformed_workflow(tmp_path: Path):
    m = _module()
    workflow = tmp_path / 'gba.yml'
    workflow.write_text('name: nope\njobs: {}\n')
    assert not m._verify_workflow_contract(workflow)


def test_verify_m6_detects_package_contract_drift():
    m = _module()

    def bad_packager(_rom, out):
        out.mkdir(parents=True, exist_ok=True)
        (out / 'wrong.bin').write_bytes(b'x')
        return object()

    assert not m._verify_package_contract(packager=bad_packager)


def test_verify_m6_propagates_m5_and_smoke_failures(reference_apk: Path, monkeypatch, tmp_path: Path, capsys):
    m = _module()
    monkeypatch.setattr(m, '_verify_m5_gate', lambda _apk: False)
    assert m.main(['--apk', str(reference_apk)]) == 1
    assert '[FAIL] M5 canonical parity gate' in capsys.readouterr().err

    rom = tmp_path / 'Fishermans_Horizon_GBA.gba'; rom.write_bytes(b'x')
    monkeypatch.setattr(m, '_verify_m5_gate', lambda _apk: True)
    monkeypatch.setattr(m, '_verify_workflow_contract', lambda: True)
    monkeypatch.setattr(m, '_verify_package_contract', lambda: True)
    monkeypatch.setattr(m, '_run_host_tests', lambda _apk: True)
    monkeypatch.setattr(m, '_build_rom_if_available', lambda: (True, str(rom)))
    monkeypatch.setattr(m, '_package_built_rom', lambda _rom: tmp_path / 'dist' / 'Fishermans_Horizon_GBA.gba')
    monkeypatch.setattr(m, '_smoke_built_rom', lambda _rom: SmokeResult(True, False, 'fatal/error'))
    assert m.main(['--apk', str(reference_apk)]) == 1
    assert '[FAIL] mGBA smoke test: fatal/error' in capsys.readouterr().err


def test_readme_documents_final_m6_gate():
    text = Path('README.md').read_text()
    assert 'scripts/verify_m6.py' in text
    assert 'release eligibility' in text
    assert 'CI is strict' in text


def test_verify_m6_can_be_launched_as_a_script():
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, 'scripts/verify_m6.py', '--help'],
        cwd='.',
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert 'M6 release-hardening gate' in result.stdout


def test_verify_m6_runs_host_suite_once_without_calling_m5_cli():
    text = Path('scripts/verify_m6.py').read_text()
    assert 'verify_m5_main' not in text
    assert 'from scripts.verify_m1 import _build_rom_if_available' in text
    assert 'def _run_host_tests(apk: Path) -> bool:' in text
    assert 'if not _run_host_tests(args.apk):' in text


def test_verify_m6_host_gate_excludes_its_own_recursive_test_file():
    text = Path('scripts/verify_m6.py').read_text()
    assert '--ignore=tests/test_verify_m6.py' in text
