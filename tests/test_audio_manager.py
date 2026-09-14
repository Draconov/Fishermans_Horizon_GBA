from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_audio_policy_host_contract(tmp_path: Path):
    compiler = shutil.which('g++') or shutil.which('c++')
    if compiler is None:
        pytest.skip('host C++ compiler unavailable')
    exe = tmp_path / 'audio_policy_test'
    result = subprocess.run([
        compiler, '-std=c++17', '-Wall', '-Wextra', '-pedantic', '-Iinclude',
        'tests/host/test_audio_policy.cpp', 'src/audio_policy.cpp', '-o', str(exe),
    ], cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True, check=False)
    assert run.returncode == 0, run.stderr


def test_audio_manager_uses_staged_sound_items_and_never_missing_text_se():
    header = (ROOT / 'include/audio_manager.h').read_text()
    source = (ROOT / 'src/audio_manager.cpp').read_text()
    assert 'class AudioManager' in header
    assert '#include "bn_sound_items.h"' in source
    assert source.count('#include "bn_sound_items') == 1
    for item in ['title', 'welcome', 'mari_mari', 'select', 'next_page', 'coin', 'throw_sfx', 'line_break', 'fish_catch_bait', 'water', 'fanfare', 'coil']:
        assert f'bn::sound_items::{item}' in source
    assert 'bn::sound_items::throw.' not in source
    assert 'text_se' not in source.lower()
    assert 'sound_option == 0' in source
    assert 'stop()' in source
    assert 'active()' in source


def test_scenes_emit_audio_cues_and_app_routes_them():
    app_h = (ROOT / 'include/app.h').read_text()
    app_cpp = (ROOT / 'src/app.cpp').read_text()
    assert 'AudioManager _audio' in app_h
    assert '_audio.update(' in app_cpp
    assert '_audio.play(' in app_cpp
    assert 'take_audio_event()' in app_cpp

    for scene in ['title', 'map', 'shop', 'catalog', 'options', 'event', 'fishing']:
        header = (ROOT / f'include/{scene}_scene.h').read_text()
        source = (ROOT / f'src/{scene}_scene.cpp').read_text()
        assert 'AudioCue take_audio_event()' in header
        assert f'{scene.capitalize()}Scene::take_audio_event()' in source if scene != 'fishing' else 'FishingScene::take_audio_event()' in source


def test_fishing_scene_consumes_semantic_model_sound_events():
    source = (ROOT / 'src/fishing_scene.cpp').read_text()
    assert 'audio_cue_from_fishing(_model.take_sound_event())' in source
    assert '_last_sound_event' not in source
