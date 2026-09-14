from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from scripts.bootstrap_m8_toolchain import BUTANO_TAG, ToolchainError, inspect_toolchain


def _fake_tree(tmp_path: Path) -> tuple[Path, Path]:
    devkitpro = tmp_path / "devkitpro"
    compiler = devkitpro / "devkitARM" / "bin" / "arm-none-eabi-g++"
    compiler.parent.mkdir(parents=True)
    compiler.write_text("#!/bin/sh\n")
    butano = tmp_path / "butano"
    butano.mkdir()
    (butano / "butano.mak").write_text("# fake\n")
    (butano / ".git").mkdir()
    return devkitpro, butano


def test_inspect_toolchain_requires_exact_butano_tag_and_reports_versions(tmp_path: Path):
    devkitpro, butano = _fake_tree(tmp_path)

    def runner(command, **_kwargs):
        if command[-1] == "-dumpfullversion":
            return subprocess.CompletedProcess(command, 0, stdout="15.2.0\n", stderr="")
        if command[:3] == ["git", "-C", str(butano)] and command[3:] == ["describe", "--tags", "--exact-match"]:
            return subprocess.CompletedProcess(command, 0, stdout=f"{BUTANO_TAG}\n", stderr="")
        if command[:3] == ["git", "-C", str(butano)] and command[3:] == ["rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, stdout="112a1827c9c6d9e6041a7e93e66f04c4561a6415\n", stderr="")
        raise AssertionError(command)

    report = inspect_toolchain(devkitpro=devkitpro, butano_dir=butano, runner=runner)
    assert report.devkitarm_release == "67"
    assert report.compiler_version == "15.2.0"
    assert report.butano_tag == "21.7.1"
    assert report.butano_commit == "112a1827c9c6d9e6041a7e93e66f04c4561a6415"
    assert report.compiler == devkitpro / "devkitARM" / "bin" / "arm-none-eabi-g++"


def test_inspect_toolchain_rejects_unpinned_devkitarm_gcc_version(tmp_path: Path):
    devkitpro, butano = _fake_tree(tmp_path)

    def runner(command, **_kwargs):
        if command[-1] == "-dumpfullversion":
            return subprocess.CompletedProcess(command, 0, stdout="15.1.0\n", stderr="")
        if command[:3] == ["git", "-C", str(butano)] and command[3:] == ["describe", "--tags", "--exact-match"]:
            return subprocess.CompletedProcess(command, 0, stdout=f"{BUTANO_TAG}\n", stderr="")
        if command[:3] == ["git", "-C", str(butano)] and command[3:] == ["rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, stdout="0123456789abcdef\n", stderr="")
        raise AssertionError(command)

    with pytest.raises(ToolchainError, match="devkitARM GCC"):
        inspect_toolchain(devkitpro=devkitpro, butano_dir=butano, runner=runner)


def test_inspect_toolchain_rejects_wrong_butano_commit(tmp_path: Path):
    devkitpro, butano = _fake_tree(tmp_path)

    def runner(command, **_kwargs):
        if command[-1] == "-dumpfullversion":
            return subprocess.CompletedProcess(command, 0, stdout="15.2.0\n", stderr="")
        if command[:3] == ["git", "-C", str(butano)] and command[3:] == ["describe", "--tags", "--exact-match"]:
            return subprocess.CompletedProcess(command, 0, stdout=f"{BUTANO_TAG}\n", stderr="")
        if command[:3] == ["git", "-C", str(butano)] and command[3:] == ["rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, stdout="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef\n", stderr="")
        raise AssertionError(command)

    with pytest.raises(ToolchainError, match="Butano commit"):
        inspect_toolchain(devkitpro=devkitpro, butano_dir=butano, runner=runner)


def test_inspect_toolchain_rejects_wrong_butano_tag(tmp_path: Path):
    devkitpro, butano = _fake_tree(tmp_path)

    def runner(command, **_kwargs):
        if command[-1] == "-dumpfullversion":
            return subprocess.CompletedProcess(command, 0, stdout="15.2.0\n", stderr="")
        if command[:3] == ["git", "-C", str(butano)] and command[3:] == ["describe", "--tags", "--exact-match"]:
            return subprocess.CompletedProcess(command, 0, stdout="21.7.0\n", stderr="")
        raise AssertionError(command)

    with pytest.raises(ToolchainError, match="Butano tag"):
        inspect_toolchain(devkitpro=devkitpro, butano_dir=butano, runner=runner)


def test_inspect_toolchain_rejects_missing_compiler_or_butano_make(tmp_path: Path):
    devkitpro, butano = _fake_tree(tmp_path)
    (devkitpro / "devkitARM" / "bin" / "arm-none-eabi-g++").unlink()
    with pytest.raises(ToolchainError, match="compiler"):
        inspect_toolchain(devkitpro=devkitpro, butano_dir=butano)

    devkitpro, butano = _fake_tree(tmp_path / "second")
    (butano / "butano.mak").unlink()
    with pytest.raises(ToolchainError, match="butano.mak"):
        inspect_toolchain(devkitpro=devkitpro, butano_dir=butano)
