from __future__ import annotations

import json
from pathlib import Path

from tools.recover_m5 import recover_from_apk

ROOT = Path(__file__).resolve().parents[1]
APK = Path('/mnt/data/fishermans-horizon-1-1.apk')


def test_recover_m5_audio_contract():
    data = recover_from_apk(APK)
    assert data['audio']['present_count'] == 13
    assert data['audio']['missing_references'] == ['assets/audio/SE/textSE.mp3']

    assets = {item['apk_path']: item for item in data['audio']['assets']}
    assert len(assets) == 13
    assert assets['assets/audio/music/title.mp3']['sha256'] == '3280ceae2511c6343bc94df5cb9ca0a08c2587e458f72a74f0ab3a2c290b2a80'
    assert assets['assets/audio/SE/introSE.mp3']['sha256'] == 'af7dbf8582eaa8ac986c676cfc5fee267bb27e2b6a52ee60e5be2afc284f91c5'

    scenes = data['scene_audio']
    assert scenes['Title']['music'] == 'assets/audio/music/title.mp3'
    assert scenes['Map']['music'] == 'assets/audio/music/mari_mari.mp3'
    assert scenes['Shop']['music'] == 'assets/audio/music/select.mp3'
    assert scenes['Catalog']['music'] == 'assets/audio/music/select.mp3'
    assert scenes['Event']['music'] == 'assets/audio/music/welcome.mp3'
    assert scenes['Fishing']['music'] is None
    assert scenes['Fishing']['inherits_previous_music'] is True
    assert scenes['Options']['return_music'] == 'assets/audio/music/title.mp3'
    assert scenes['Intro']['sfx'] == ['assets/audio/SE/introSE.mp3']

    assert scenes['Fishing']['sfx'] == [
        'assets/audio/SE/nextPageSE.mp3',
        'assets/audio/SE/throwSE.mp3',
        'assets/audio/SE/lineBreakSE.mp3',
        'assets/audio/SE/coinSE.mp3',
        'assets/audio/SE/fishCatchBaitSE.mp3',
        'assets/audio/SE/waterSE.mp3',
        'assets/audio/SE/fanfareSE.mp3',
        'assets/audio/SE/coilSE.mp3',
    ]
    assert 'assets/audio/SE/textSE.mp3' in scenes['Shop']['referenced_missing_sfx']

    evidence = data['evidence']
    assert evidence['GameTitle.loadAssets']['offset'] == '0xc940'
    assert evidence['GameFishing.loadAssets']['code_units'] == 122
    assert evidence['SoundEngine.run']['sha256'] == '35cb707c8bd675fd4fe4655c118c3905731ed7d21d9040cf96df968522e8b597'


def test_recover_m5_matches_committed_reference():
    recovered = recover_from_apk(APK)
    committed = json.loads((ROOT / 'reference/m5_audio_presentation.json').read_text())
    assert recovered == committed
