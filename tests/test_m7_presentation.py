from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_presentation_effects_host_contract(tmp_path: Path):
    compiler = shutil.which("g++") or shutil.which("c++")
    if compiler is None:
        pytest.skip("host C++ compiler unavailable")
    executable = tmp_path / "presentation_effects_test"
    result = subprocess.run(
        [
            compiler, "-std=c++17", "-Wall", "-Wextra", "-pedantic", "-Iinclude",
            "tests/host/test_presentation_effects.cpp", "src/presentation_effects.cpp", "-o", str(executable),
        ],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True, check=False)
    assert run.returncode == 0, run.stderr


def test_m7_presentation_runtime_matches_recovery_audit():
    facts = json.loads((ROOT / "reference/m7_final_parity.json").read_text())
    audit = facts["presentation_audit"]["ScreenFlash"]
    runtime = (ROOT / "src/presentation_effects.cpp").read_text() if (ROOT / "src/presentation_effects.cpp").exists() else ""
    assert audit["classification"] == "reachable_used"
    assert "PresentationEffects" in runtime
    assert "15" in runtime
    assert "150" in runtime
    assert "235" in runtime and "255" in runtime and "237" in runtime


def test_fishing_scene_uses_shared_dialog_and_exact_result_copy():
    header = (ROOT / "include/fishing_scene.h").read_text()
    source = (ROOT / "src/fishing_scene.cpp").read_text()
    assert '#include "dialog_model.h"' in header
    assert '#include "dialog_renderer.h"' in header
    assert "DialogModel _dialog" in header
    assert "DialogRenderer _dialog_renderer" in header
    assert "_dialog.update(bn::keypad::a_pressed())" in source
    assert "was caught!#You got " in source
    assert "The line broke..." in source
    assert "input.confirm_dialog = true" in source
    assert "input.confirm_dialog = bn::keypad::a_pressed()" not in source


def test_app_owns_recovered_global_presentation_adapter():
    header = (ROOT / "include/app.h").read_text()
    source = (ROOT / "src/app.cpp").read_text()
    assert '#include "presentation_effects.h"' in header
    assert "PresentationEffects _presentation" in header
    assert "bn::bg_palettes::set_fade_color" in source
    assert "bn::sprite_palettes::set_fade_color" in source
    assert "bn::bg_palettes::set_fade_intensity" in source
    assert "bn::sprite_palettes::set_fade_intensity" in source
    assert "take_flash_request" in source
    assert "take_presentation_event" in source
