from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_native_compile_checker_covers_every_production_translation_unit():
    result = subprocess.run(
        [sys.executable, "scripts/check_native_compile.py"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    expected = sorted(path.as_posix() for path in Path("src").glob("*.cpp"))
    for source in expected:
        assert f"[PASS] {source}" in result.stdout
    assert f"[PASS] {len(expected)} native translation units" in result.stdout
    assert "[PASS] no unsupported libc symbols" in result.stdout
