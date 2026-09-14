from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import sys

from scripts.check_toolchain import check_toolchain


def test_toolchain_status_reports_missing_arm_compiler(monkeypatch):
    monkeypatch.setenv("PATH", "")
    monkeypatch.delenv("LIBBUTANO", raising=False)
    status = check_toolchain()
    assert status.arm_compiler is None
    assert not status.can_build_rom


def test_toolchain_status_accepts_complete_fake_toolchain(tmp_path: Path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    compiler = bin_dir / "arm-none-eabi-g++"
    compiler.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    compiler.chmod(compiler.stat().st_mode | stat.S_IXUSR)
    make = bin_dir / "make"
    make.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    make.chmod(make.stat().st_mode | stat.S_IXUSR)

    butano = tmp_path / "butano" / "butano"
    butano.mkdir(parents=True)
    (butano / "butano.mak").write_text("# fake\n", encoding="utf-8")

    monkeypatch.setenv("PATH", str(bin_dir))
    monkeypatch.setenv("LIBBUTANO", str(butano))
    status = check_toolchain()
    assert status.arm_compiler == str(compiler)
    assert status.make == str(make)
    assert status.butano_mak == butano / "butano.mak"
    assert status.can_build_rom


def test_verify_m0_requires_reference_apk(tmp_path: Path):
    missing = tmp_path / "missing.apk"
    result = subprocess.run(
        [sys.executable, "scripts/verify_m0.py", "--apk", str(missing)],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "reference APK not found" in result.stderr


def test_m0_manifest_lookup_ignores_additional_milestone_assets(tmp_path: Path):
    from scripts.verify_m0 import _manifest_record

    manifest = tmp_path / "manifest.tsv"
    manifest.write_text(
        "source_member\tsource_sha256\tsource_bytes\tsource_width\tsource_height\toutput_path\toutput_sha256\toutput_bytes\toutput_width\toutput_height\toffset_x\toffset_y\n"
        "title\thash0\t1\t240\t160\tgraphics/title.bmp\tout0\t2\t256\t256\t8\t48\n"
        "map\thash1\t1\t240\t160\tgraphics/map.bmp\tout1\t2\t256\t256\t8\t48\n",
        encoding="utf-8",
    )

    record = _manifest_record(manifest)
    assert record["output_path"] == "graphics/title.bmp"
    assert record["source_member"] == "title"
