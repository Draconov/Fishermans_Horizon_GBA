from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.dex import DexFile
from tools.reference_apk import CANONICAL_APK_SHA256, validate_reference

_APP = 'Lcom/fishermanshorizon/app/'
_INVENTORY = ROOT / 'reference/apk_inventory.tsv'

_METHOD_PROOFS = {
    'GameIntro.draw': ('GameIntro', 'draw', 0xA54C, 20, '8a6b95516a588ff22aa0989009cae986dc63ca74428ffe1af8d72049f3524a67'),
    'GameIntro.exit': ('GameIntro', 'exit', 0xA584, 9, '8d5a0c8c93c13427c27c155d64cd4acfcc112030f314cf9ed362c4d45abf5433'),
    'GameIntro.init': ('GameIntro', 'init', 0xA5A8, 50, '5ae2985bb22f0901df6d554cc1cbafde1e4fdcc7c8a458aa2c2f60a782b33f93'),
    'GameIntro.update': ('GameIntro', 'update', 0xA61C, 34, '7b36a62abacb7a9ae5210c36f668d5f97383d50a18177ebe93cf0c2b74e99184'),
    'DialogBox.drawDialog': ('DialogBox', 'drawDialog', 0x36F0, 669, '81e419b86b356b8ef04294774ce5e8480a6f1b1bd932ecbc3633839aebf02caf'),
    'DialogBox.getChar': ('DialogBox', 'getChar', 0x3C60, 2196, '7d53dfe9cd305b74f2f923b9fff1a5190cccd61b68da77f7d68605b3eadfd1e7'),
    'DialogBox.exit': ('DialogBox', 'exit', 0x3C3C, 10, 'd114cb423526ea368b95af0e646f31d649ed42be8b8c1adfae3043a9e362f790'),
    'DialogBox.init': ('DialogBox', 'init', 0x4D98, 45, 'b7556b0812503cd03f697fbc1958e095af2468a28f6a012274be48b106876c81'),
    'DialogBox.newText': ('DialogBox', 'newText', 0x4E78, 10, 'c4a7543cef38b1a11bece2b3e7a6e9bc9fd4782c550917a7d36ab48356f8683a'),
    'DialogBox.setNewPage': ('DialogBox', 'setNewPage', 0x4E9C, 37, '93d352fd21049c202d056bfa6c1d386b48735060e74007f1fc2a1ab8fa09206a'),
    'DialogBox.update': ('DialogBox', 'update', 0x4EF8, 86, '27f7a6d4737fccddea0a19d71dbc5e84f174d881a3cf9c3ec69b058e9324e394'),
    'DrawText.getChar': ('DrawText', 'getChar', 0x5074, 1862, '852e876241bc8808f199d7fc192eed7d26839740b7bcf1c112813349a9a26fc9'),
    'ScreenFlash.draw': ('ScreenFlash', 'draw', 0xE744, 15, '97b09d35d31a598ac52e85e1d20ee314502c7a8397c9ec3b87b41125cad6f853'),
    'ScreenFlash.init': ('ScreenFlash', 'init', 0xE774, 42, 'b24012e23429e1f2ddce15fecd6e3f947a8ad1eda44df2b4b09ae602adeb0161'),
    'ScreenFlash.update': ('ScreenFlash', 'update', 0xE7D8, 149, 'a27579989e4357ec2eea7e3e08855a11a8f11561a82700a4ed3e9927b0051e39'),
    'Framework.draw': ('Framework', 'draw', 0x7290, 72, '3315768ae19cc2de1d80e0828f73da5adb3dfcbd7a571c11f426a8b15b1bb9dc'),
    'Framework.init': ('Framework', 'init', 0x7330, 10, 'ce5c09a8693fee9dcd99c9d57e8183f65fe35bf08f2e38296f5462318fa5bcdd'),
    'Framework.update': ('Framework', 'update', 0x7384, 72, '4370f1c4be35cdccc8f65753067ed5a6a1e64ab69fa1372a0ba8239b29ea216b'),
    'GameEvent.update': ('GameEvent', 'update', 0x91B0, 69, '26fb05778780b1f66faa599f18380d6e78255992e4245d945f614beb9fac55c6'),
    'Fish.lure': ('Fish', 'lure', 0x6168, 125, 'a18438e9d56503654fbfcb7ad21adfcdf9b50452bc057904821c7514f926c93d'),
    'GameFishing.stateFishCatch': ('GameFishing', 'stateFishCatch', 0x9BC4, 136, '4ee8245ea960a0326c570f5e2003b03357426ce5aa34db9299f427d4f4319296'),
    'GameFishing.stateLineBreak': ('GameFishing', 'stateLineBreak', 0x9F98, 45, '4bc58c6fa19229489aca0374b99c1b9e3a05c04eb8a184e98f3bd91e90a33a70'),
}

_SCREEN_FLASH_REACHABLE_FROM = [
    'Framework.init',
    'Framework.update',
    'Framework.draw',
    'GameCatalog.init',
    'GameCatalog.update',
    'GameCatalog.exit',
    'GameEvent.init',
    'GameEvent.update',
    'GameEvent.exit',
    'GameFishing.init',
    'GameFishing.update',
    'GameFishing.stateLineBreak',
    'GameFishing.exit',
    'GameIntro.update',
    'GameIntro.exit',
    'GameMap.init',
    'GameMap.update',
    'GameMap.exit',
    'GameOptions.init',
    'GameOptions.update',
    'GameOptions.exit',
    'GameShop.init',
    'GameShop.update',
    'GameShop.exit',
    'GameTitle.init',
    'GameTitle.update',
    'GameTitle.exit',
]


def _method_proof(dex: DexFile, label: str) -> dict[str, object]:
    class_name, method_name, expected_offset, expected_units, expected_sha = _METHOD_PROOFS[label]
    code = dex.method_code(f'{_APP}{class_name};', method_name)
    raw = struct.pack(f'<{len(code.code_units)}H', *code.code_units)
    actual_sha = sha256(raw).hexdigest()
    if code.code_offset != expected_offset or len(code.code_units) != expected_units or actual_sha != expected_sha:
        raise ValueError(f'{label} DEX fingerprint changed')
    return {'offset': hex(code.code_offset), 'code_units': len(code.code_units), 'sha256': actual_sha}


def recover_from_apk(apk_path: Path) -> dict[str, object]:
    errors = validate_reference(apk_path, _INVENTORY, expected_sha256=CANONICAL_APK_SHA256)
    if errors:
        raise ValueError('; '.join(errors))

    with zipfile.ZipFile(apk_path, 'r') as archive:
        dex = DexFile(archive.read('classes.dex'))
        credit = archive.read('assets/graphic/background/introCredit.png')
        intro_sfx = archive.read('assets/audio/SE/introSE.mp3')

    # The behavior below was decoded instruction-for-instruction from the
    # fingerprinted methods. Keeping it next to the hashes makes drift fail
    # before any recovered constants are trusted by the port.
    return {
        'origin': {
            'apk_sha256': CANONICAL_APK_SHA256,
            'member': 'classes.dex',
            'dex_classes': ['GameIntro', 'DialogBox', 'DrawText', 'ScreenFlash', 'Framework', 'GameEvent', 'GameFishing', 'Fish'],
            'intro_credit_sha256': sha256(credit).hexdigest(),
            'intro_sfx_sha256': sha256(intro_sfx).hexdigest(),
        },
        'evidence': {label: _method_proof(dex, label) for label in _METHOD_PROOFS},
        'intro': {
            'background_argb': [255, 25, 5, 36],
            'credit_asset': 'assets/graphic/background/introCredit.png',
            'credit_position': [48, 48],
            'credit_size': [144, 64],
            'fade_in_tick': 25,
            'fade_out_tick': 175,
            'intro_sfx': 'assets/audio/SE/introSE.mp3',
            'skippable': False,
            'transition_after_black': 'Title',
        },
        'dialog': {
            'text_speed': 4,
            'box_hidden_y': 160,
            'box_visible_y': 136,
            'slide_pixels_per_frame': 2,
            'text_origin': [8, 4],
            'glyph_advance': 7,
            'line_advance': 9,
            'line_width_cutoff': 210,
            'visible_lines_per_page': 2,
            'explicit_newline': '#',
            'paragraph_break': '@',
            'paragraph_advance': 18,
            'base_tile': 96,
            'advance_tile': 98,
            'touch_zone': [208, 128, 240, 160],
            'gba_advance_button': 'A',
            'effective_reveal_source_chars_per_frame': 1,
            'next_page_sfx': 'nextPage',
        },
        'event_dialog': {
            'open_tick': 100,
            'after_dialog': ['fade_out', 'fade_music', 'return_to_map_after_black'],
        },
        'fishing_dialog': {
            'catch_open_tick': 43,
            'catch_template': '<fish> was caught!#You got <reward>$!',
            'line_break_flash_tick': 1,
            'line_break_open_tick': 15,
            'line_break_text': 'The line broke...',
        },
        'presentation_audit': {
            'ScreenFlash': {
                'classification': 'reachable_used',
                'reachable_from': _SCREEN_FLASH_REACHABLE_FROM,
                'implemented_behavior': 'global black fade in/out plus pale-green line-break flash',
            },
        },
        'screen_flash': {
            'classification': 'reachable_used',
            'speed': 15,
            'base_argb': [255, 25, 5, 36],
            'flash_argb': [255, 235, 255, 237],
            'modes': {
                'FADE_NONE': 0,
                'FADE_IN': 1,
                'FADE_OUT': 2,
                'FLASH_IN': 3,
                'FLASH_OUT': 4,
            },
            'fade_in_delta': -15,
            'fade_out_delta': 15,
            'flash_delta': 150,
            'flash_hold_ticks': 4,
            'reachable_from': _SCREEN_FLASH_REACHABLE_FROM,
        },
    }


def recover_m7(dex: DexFile) -> dict[str, object]:
    """Recover M7 facts from a canonical classes.dex payload."""
    proofs = {label: _method_proof(dex, label) for label in _METHOD_PROOFS}
    # Public helper is intentionally evidence-only; APK-bound asset hashes live in recover_m7_from_apk.
    return {'evidence': {'code_proofs': proofs}}


def recover_m7_from_apk(apk_path: Path) -> dict[str, object]:
    return recover_from_apk(apk_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'reference/m7_final_parity.json')
    args = parser.parse_args(argv)
    data = recover_from_apk(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
