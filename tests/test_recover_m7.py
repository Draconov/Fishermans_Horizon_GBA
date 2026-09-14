from __future__ import annotations

import json
from pathlib import Path

from tools.recover_m7 import recover_from_apk

ROOT = Path(__file__).resolve().parents[1]
APK = Path('/mnt/data/fishermans-horizon-1-1.apk')


def test_recover_m7_intro_dialog_and_effect_contract():
    data = recover_from_apk(APK)

    intro = data['intro']
    assert intro == {
        'background_argb': [255, 25, 5, 36],
        'credit_asset': 'assets/graphic/background/introCredit.png',
        'credit_position': [48, 48],
        'credit_size': [144, 64],
        'fade_in_tick': 25,
        'fade_out_tick': 175,
        'intro_sfx': 'assets/audio/SE/introSE.mp3',
        'skippable': False,
        'transition_after_black': 'Title',
    }

    dialog = data['dialog']
    assert dialog['text_speed'] == 4
    assert dialog['box_hidden_y'] == 160
    assert dialog['box_visible_y'] == 136
    assert dialog['slide_pixels_per_frame'] == 2
    assert dialog['text_origin'] == [8, 4]
    assert dialog['glyph_advance'] == 7
    assert dialog['line_advance'] == 9
    assert dialog['line_width_cutoff'] == 210
    assert dialog['visible_lines_per_page'] == 2
    assert dialog['explicit_newline'] == '#'
    assert dialog['paragraph_break'] == '@'
    assert dialog['paragraph_advance'] == 18
    assert dialog['base_tile'] == 96
    assert dialog['advance_tile'] == 98
    assert dialog['touch_zone'] == [208, 128, 240, 160]
    assert dialog['gba_advance_button'] == 'A'
    assert dialog['effective_reveal_source_chars_per_frame'] == 1
    assert dialog['next_page_sfx'] == 'nextPage'

    events = data['event_dialog']
    assert events['open_tick'] == 100
    assert events['after_dialog'] == ['fade_out', 'fade_music', 'return_to_map_after_black']

    fishing = data['fishing_dialog']
    assert fishing['catch_open_tick'] == 43
    assert fishing['catch_template'] == '<fish> was caught!#You got <reward>$!'
    assert fishing['line_break_open_tick'] == 15
    assert fishing['line_break_text'] == 'The line broke...'
    assert fishing['line_break_flash_tick'] == 1

    flash = data['screen_flash']
    assert flash['classification'] == 'reachable_used'
    assert flash['speed'] == 15
    assert flash['base_argb'] == [255, 25, 5, 36]
    assert flash['flash_argb'] == [255, 235, 255, 237]
    assert flash['modes'] == {
        'FADE_NONE': 0,
        'FADE_IN': 1,
        'FADE_OUT': 2,
        'FLASH_IN': 3,
        'FLASH_OUT': 4,
    }
    assert flash['fade_in_delta'] == -15
    assert flash['fade_out_delta'] == 15
    assert flash['flash_delta'] == 150
    assert flash['flash_hold_ticks'] == 4
    assert 'Framework.update' in flash['reachable_from']
    assert 'GameFishing.stateLineBreak' in flash['reachable_from']
    assert 'GameIntro.update' in flash['reachable_from']

    assert data['origin']['member'] == 'classes.dex'
    assert data['presentation_audit']['ScreenFlash']['classification'] == 'reachable_used'
    assert data['presentation_audit']['ScreenFlash']['implemented_behavior']
    evidence = data['evidence']
    assert evidence['GameIntro.update']['offset'] == '0xa61c'
    assert evidence['DialogBox.drawDialog']['code_units'] == 669
    assert evidence['DialogBox.getChar']['code_units'] == 2196
    assert evidence['DrawText.getChar']['code_units'] == 1862
    assert evidence['ScreenFlash.update']['sha256'] == 'a27579989e4357ec2eea7e3e08855a11a8f11561a82700a4ed3e9927b0051e39'
    assert evidence['GameFishing.stateFishCatch']['offset'] == '0x9bc4'


def test_recover_m7_matches_committed_reference():
    recovered = recover_from_apk(APK)
    committed = json.loads((ROOT / 'reference/m7_final_parity.json').read_text())
    assert recovered == committed
