from __future__ import annotations

import json
import math
from pathlib import Path
import shutil
import wave

import pytest

from scripts.stage_audio_assets import stage_audio_assets

APK = Path('/mnt/data/fishermans-horizon-1-1.apk')

EXPECTED_OUTPUTS = {
    'title.s3m', 'welcome.wav', 'mari_mari.wav', 'select.wav',
    'coil.wav', 'coin.wav', 'fanfare.wav', 'fish_catch_bait.wav',
    'intro.wav', 'line_break.wav', 'next_page.wav', 'throw_sfx.wav', 'water.wav',
}


def test_stage_audio_assets_are_deterministic_gba_pcm(tmp_path: Path):
    if shutil.which('ffmpeg') is None:
        pytest.skip('ffmpeg unavailable')

    a = tmp_path / 'a'
    b = tmp_path / 'b'
    manifest_a = tmp_path / 'a.json'
    manifest_b = tmp_path / 'b.json'
    stage_audio_assets(APK, a, manifest_a)
    stage_audio_assets(APK, b, manifest_b)

    assert {p.name for p in a.iterdir() if p.is_file()} == EXPECTED_OUTPUTS
    assert manifest_a.read_bytes() == manifest_b.read_bytes()
    for name in EXPECTED_OUTPUTS:
        assert (a / name).read_bytes() == (b / name).read_bytes()
        if name.endswith('.wav'):
            with wave.open(str(a / name), 'rb') as wav:
                assert wav.getnchannels() == 1
                assert wav.getsampwidth() == 1
                assert wav.getframerate() == 16000
                assert wav.getnframes() > 0

    manifest = json.loads(manifest_a.read_text())
    assert manifest['sample_rate'] == 16000
    assert manifest['sample_width_bits'] == 8
    assert len(manifest['assets']) == 13
    title = next(item for item in manifest['assets'] if item['output'] == 'title.s3m')
    assert title['source'] == 'assets/audio/music/title.mp3'
    assert 658000 <= title['frames'] <= 661000
    assert title['format'] == 's3m'
    assert title['chunk_count'] >= 2
    assert title['sha256'] == __import__('hashlib').sha256((a / 'title.s3m').read_bytes()).hexdigest()


def test_makefile_imports_staged_audio():
    text = Path('Makefile').read_text()
    assert 'AUDIO := audio' in text


def test_staged_audio_names_are_safe_butano_cpp_identifiers():
    import keyword
    import re

    cpp_keywords = {
        'alignas','alignof','and','and_eq','asm','auto','bitand','bitor','bool','break','case','catch',
        'char','char8_t','char16_t','char32_t','class','compl','concept','const','consteval','constexpr',
        'constinit','const_cast','continue','co_await','co_return','co_yield','decltype','default','delete','do',
        'double','dynamic_cast','else','enum','explicit','export','extern','false','float','for','friend','goto',
        'if','inline','int','long','mutable','namespace','new','noexcept','not','not_eq','nullptr','operator','or',
        'or_eq','private','protected','public','register','reinterpret_cast','requires','return','short','signed',
        'sizeof','static','static_assert','static_cast','struct','switch','template','this','thread_local','throw',
        'true','try','typedef','typeid','typename','union','unsigned','using','virtual','void','volatile','wchar_t',
        'while','xor','xor_eq',
    }
    for name in EXPECTED_OUTPUTS:
        stem = Path(name).stem
        assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', stem), stem
        assert stem not in cpp_keywords, stem
        assert not keyword.iskeyword(stem), stem


def test_title_music_is_staged_as_chunked_s3m(tmp_path: Path):
    if shutil.which('ffmpeg') is None:
        pytest.skip('ffmpeg unavailable')

    out = tmp_path / 'audio'
    manifest_path = tmp_path / 'manifest.json'
    manifest = stage_audio_assets(APK, out, manifest_path)
    title = next(item for item in manifest['assets'] if item['output'] == 'title.s3m')
    data = (out / 'title.s3m').read_bytes()

    assert title['format'] == 's3m'
    assert title['source'] == 'assets/audio/music/title.mp3'
    assert title['sample_rate'] == 16000
    assert title['chunk_count'] == 11
    assert title['frames'] >= 658000
    assert data[44:48] == b'SCRM'
    assert b'SCRS' in data
    assert not (out / 'title.wav').exists()
