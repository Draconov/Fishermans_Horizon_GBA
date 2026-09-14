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

_APP = "Lcom/fishermanshorizon/app/"

# These fingerprints freeze the exact canonical code units that were manually
# decoded for M1. If any method body changes, recovery fails closed instead of
# silently emitting stale facts.
_METHOD_PROOFS = {
    "GameTitle.init": ("GameTitle", "init", 0xC8A8, 68, "eec8b4aeea4acd545e693f70a5530cf217fcd035584f71a4f1549ecce95eced4"),
    "GameTitle.loadAssets": ("GameTitle", "loadAssets", 0xC940, 46, "d9461f4d27f6e073beb25a91eec8341910d6ad170cb52ac929ac8908e448e057"),
    "GameTitle.seaImage": ("GameTitle", "seaImage", 0xC9AC, 53, "306ef530817c52d6336275effb9aa49389ec7465243b85c82dba501af3c73bd9"),
    "GameTitle.exit": ("GameTitle", "exit", 0xC858, 32, "e23df2236d92b4abc6520e17f8e42a415ae1c1558b1fc512ebf976fe916ddd4a"),
    "GameMap.init": ("GameMap", "init", 0xA884, 278, "80285dfc995d142a5c364750842835f686cae7d1d2294b039528920db03bf323"),
    "GameMap.loadAssets": ("GameMap", "loadAssets", 0xAAC0, 47, "f6e9c45399fdb99a1ea9e2df85c3980fd4a0ad7466ca123c1c04552027b6f0b8"),
    "GameMap.update": ("GameMap", "update", 0xAD3C, 184, "14f9948ccacb11e7a30807ef26ec84aac6e00fa32b8b8fbb4cb83802d143860a"),
    "GameMap.exit": ("GameMap", "exit", 0xA7D4, 80, "9962c5e5b01437ecb6c275a380e61c0a7b0052c3afb9d45b423adaf9e0561778"),
}

_REQUIRED_STRINGS = {
    "audio/SE/nextPageSE.mp3",
    "audio/music/title.mp3",
    "audio/music/mari_mari.mp3",
    "graphic/background/title.png",
    "graphic/background/map.png",
}

_REQUIRED_FIELDS = {
    (f"{_APP}Framework;", "gameState", "I"),
    (f"{_APP}GameTitle;", "seaTicks", "I"),
    (f"{_APP}GameTitle;", "seaSpriteNumber", "I"),
    (f"{_APP}GameTitle;", "pointer", "I"),
    (f"{_APP}GlobalVar;", "prologue", "I"),
    (f"{_APP}GameMap;", "ticks", "I"),
    (f"{_APP}GameMap;", "pointer", "I"),
    (f"{_APP}FishingArea;", "pool", "I"),
    (f"{_APP}GlobalVar;", "clubCard", "I"),
    (f"{_APP}GlobalVar;", "oldBoat", "I"),
    (f"{_APP}GlobalVar;", "ancientMap", "I"),
    (f"{_APP}GlobalVar;", "catalog", "I"),
}


def _method_proof(dex: DexFile, label: str) -> dict[str, object]:
    class_name, method_name, expected_offset, expected_units, expected_sha = _METHOD_PROOFS[label]
    code = dex.method_code(f"{_APP}{class_name};", method_name)
    raw = struct.pack(f"<{len(code.code_units)}H", *code.code_units)
    actual_sha = sha256(raw).hexdigest()
    if code.code_offset != expected_offset:
        raise ValueError(
            f"{label} code offset changed: {code.code_offset:#x} != {expected_offset:#x}"
        )
    if len(code.code_units) != expected_units:
        raise ValueError(
            f"{label} code size changed: {len(code.code_units)} != {expected_units}"
        )
    if actual_sha != expected_sha:
        raise ValueError(f"{label} code fingerprint changed")
    return {
        "offset": hex(code.code_offset),
        "code_units": len(code.code_units),
        "sha256": actual_sha,
    }


def recover_m1(dex: DexFile) -> dict[str, object]:
    strings = set(dex.strings())
    missing_strings = sorted(_REQUIRED_STRINGS - strings)
    if missing_strings:
        raise ValueError(f"missing M1 strings: {', '.join(missing_strings)}")

    field_surface = {
        (field.class_descriptor, field.name, field.type_descriptor)
        for field in dex.fields()
    }
    missing_fields = sorted(_REQUIRED_FIELDS - field_surface)
    if missing_fields:
        raise ValueError(f"missing M1 fields: {missing_fields}")

    proofs = {label: _method_proof(dex, label) for label in _METHOD_PROOFS}

    # Facts below are the literal result of decoding the proven method bodies.
    # Keeping them next to code-unit fingerprints means a changed reference ROM
    # cannot accidentally reuse stale reverse-engineering notes.
    return {
        "origin": {
            "apk_sha256": CANONICAL_APK_SHA256,
            "member": "classes.dex",
        },
        "evidence": {
            "methods": {label: proof["offset"] for label, proof in proofs.items()},
            "code_proofs": proofs,
        },
        "title": {
            "game_state": 2,
            "initial_sea_sprite": 112,
            "sea_frames": [[1, 113], [13, 114], [25, 113], [37, 112], [49, 112]],
            "play_zone": [0, 128, 32, 160],
            "options_zone": [208, 128, 240, 160],
            "fresh_save_route": "Event",
            "returning_save_route": "Map",
            "music": "audio/music/title.mp3",
            "next_page_se": "audio/SE/nextPageSE.mp3",
            "background": "graphic/background/title.png",
            "sea_overlay_y": 128,
        },
        "map": {
            "game_state": 3,
            "music": "audio/music/mari_mari.mp3",
            "next_page_se": "audio/SE/nextPageSE.mp3",
            "background": "graphic/background/map.png",
            "marker_frames": {
                "spot_a": [100, 101],
                "spot_b": [102, 103],
                "period": 20,
            },
            "marker_positions": {
                "shop": [100, 12, "spot_b"],
                "crystal_lake": [148, 20, "spot_a"],
                "pier": [132, 76, "spot_a"],
                "river": [212, 12, "spot_a"],
                "ocean": [108, 124, "spot_a"],
                "cave": [20, 92, "spot_a"],
            },
            "zones": {
                "back": [0, 0, 32, 32],
                "shop": [88, 8, 120, 40],
                "crystal_lake": [136, 16, 168, 48],
                "pier": [120, 72, 152, 104],
                "river": [200, 8, 232, 40],
                "ocean": [96, 120, 128, 152],
                "cave": [8, 88, 40, 120],
                "catalog": [0, 128, 32, 160],
                "change_character": [208, 128, 240, 160],
            },
            "unlocks": {
                "river": "clubCard",
                "ocean": "oldBoat",
                "cave": "ancientMap",
                "catalog": "catalog",
            },
            "pointer_to_pool": {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5},
            "pointer_routes": {
                "0": "Title",
                "1": "Fishing",
                "2": "Fishing",
                "3": "Fishing",
                "4": "Fishing",
                "5": "Fishing",
                "6": "Shop",
                "7": "Catalog",
            },
        },
    }


def recover_m1_from_apk(apk_path: Path) -> dict[str, object]:
    inventory = Path(__file__).resolve().parents[1] / "reference" / "apk_inventory.tsv"
    errors = validate_reference(apk_path, inventory)
    if errors:
        raise ValueError("reference APK validation failed: " + "; ".join(errors))
    with zipfile.ZipFile(apk_path, "r") as archive:
        dex_bytes = archive.read("classes.dex")
    return recover_m1(DexFile(dex_bytes))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recover M1 title/map parity facts")
    parser.add_argument("apk", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)

    facts = recover_m1_from_apk(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
