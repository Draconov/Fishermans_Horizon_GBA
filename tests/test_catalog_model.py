from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_model_host_contract(tmp_path: Path):
    compiler = shutil.which("g++") or shutil.which("c++")
    if compiler is None:
        pytest.skip("host C++ compiler unavailable")

    executable = tmp_path / "catalog_model_test"
    result = subprocess.run(
        [
            compiler,
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-pedantic",
            "-Iinclude",
            "tests/host/test_catalog_model.cpp",
            "src/catalog_model.cpp",
            "src/catalog_content.cpp",
            "src/flow_model.cpp",
            "src/progression_content.cpp",
            "src/game_state.cpp",
            "-o",
            str(executable),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True, check=False)
    assert run.returncode == 0, run.stderr
