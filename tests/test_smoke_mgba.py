from __future__ import annotations

from pathlib import Path
import subprocess

from scripts.smoke_mgba import smoke_rom


def _rom(tmp_path: Path) -> Path:
    path = tmp_path / "game.gba"
    path.write_bytes(b"rom")
    return path


def test_smoke_rom_reports_missing_emulator_as_unavailable(tmp_path: Path):
    result = smoke_rom(_rom(tmp_path), which=lambda _name: None)
    assert not result.available
    assert not result.passed
    assert "not found" in result.detail


def test_smoke_rom_passes_when_emulator_remains_alive_until_timeout(tmp_path: Path):
    def runner(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(["mgba"], 0.01, output="boot ok\n", stderr="")

    result = smoke_rom(_rom(tmp_path), timeout_seconds=0.01, which=lambda _name: "/usr/bin/mgba", runner=runner)
    assert result.available
    assert result.passed
    assert "alive" in result.detail


def test_smoke_rom_fails_when_emulator_exits_early(tmp_path: Path):
    completed = subprocess.CompletedProcess(["mgba"], 3, stdout="", stderr="crash")
    result = smoke_rom(
        _rom(tmp_path),
        which=lambda _name: "/usr/bin/mgba",
        runner=lambda *_args, **_kwargs: completed,
    )
    assert result.available
    assert not result.passed
    assert "exited early" in result.detail


def test_smoke_rom_fails_on_fatal_or_error_log_even_if_timeout_occurs(tmp_path: Path):
    def runner(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(["mgba"], 0.01, output="FATAL: bad opcode\n", stderr="")

    result = smoke_rom(_rom(tmp_path), which=lambda _name: "/usr/bin/mgba", runner=runner)
    assert result.available
    assert not result.passed
    assert "fatal/error" in result.detail


def test_smoke_rom_rejects_missing_rom_before_launch(tmp_path: Path):
    result = smoke_rom(tmp_path / "missing.gba", which=lambda _name: "/usr/bin/mgba")
    assert result.available
    assert not result.passed
    assert "ROM not found" in result.detail
