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
from tools.recover_m4 import _walk
from tools.reference_apk import CANONICAL_APK_SHA256, validate_reference

_APP = "Lcom/fishermanshorizon/app/"
_INVENTORY = ROOT / "reference/apk_inventory.tsv"

_METHOD_PROOFS = {
    "GameTitle.loadAssets": ("GameTitle", "loadAssets", 0xC940, 46, "d9461f4d27f6e073beb25a91eec8341910d6ad170cb52ac929ac8908e448e057"),
    "GameMap.loadAssets": ("GameMap", "loadAssets", 0xAAC0, 47, "f6e9c45399fdb99a1ea9e2df85c3980fd4a0ad7466ca123c1c04552027b6f0b8"),
    "GameFishing.loadAssets": ("GameFishing", "loadAssets", 0x96DC, 122, "05f9802ce2c748523b13e5348cf96c0109b8a54d700ad6e6fea35f8ad19f1451"),
    "GameShop.loadAssets": ("GameShop", "loadAssets", 0xC5F0, 72, "18c333b4032e5551d2cb02fdbb5867f7036c7ea9c5f18cbde374a6f5d9b67bc3"),
    "GameCatalog.loadAssets": ("GameCatalog", "loadAssets", 0x7CD8, 50, "cf7e6cfdf818cd6b5e5c93c32a898836d95f9b3dd0c4b82241d03ab6362266d6"),
    "GameEvent.loadAssets": ("GameEvent", "loadAssets", 0x9048, 45, "1c89149b748a9ccb14bd802830e3646bb860ccc1c0faa7609103fb66e9bd1d01"),
    "GameIntro.init": ("GameIntro", "init", 0xA5A8, 50, "5ae2985bb22f0901df6d554cc1cbafde1e4fdcc7c8a458aa2c2f60a782b33f93"),
    "GameOptions.update": ("GameOptions", "update", 0xB1F0, 176, "15bc0fed8e71700696fa22b4c8869d535e1561c66eb003204861bf6a683425b2"),
    "SoundEngine.loadMusic": ("SoundEngine", "loadMusic", 0xE9F0, 50, "438e6271209bf4315928386ccc3d9a9e7d3125ae91c6cc75c6cf77da59e36194"),
    "SoundEngine.loadSE": ("SoundEngine", "loadSE", 0xEA70, 23, "63da9e44bfe800d85eb22e28505cc96560afb72aea1cde91aa1969f717b71852"),
    "SoundEngine.run": ("SoundEngine", "run", 0xEBC8, 400, "35cb707c8bd675fd4fe4655c118c3905731ed7d21d9040cf96df968522e8b597"),
}

_EXPECTED_AUDIO = {
    "assets/audio/SE/coilSE.mp3": (4249, "78e6824e64827878a11c11e308947d09f1bf6401f9a42ee75f0f16a25d437c75"),
    "assets/audio/SE/coinSE.mp3": (10880, "3c9e5525c5c1a04cb5ceaae83b43d1746d5f75b16ec624906e22e1978b1651e5"),
    "assets/audio/SE/fanfareSE.mp3": (7593, "c5d711aa3281e89115e6f0cde4e6cb703a7b87c0bcd0d6c9da1d8ff6067d4582"),
    "assets/audio/SE/fishCatchBaitSE.mp3": (9856, "aaea09e2ae5470bcdc78a7507aaa0ebe262f777ef17083ffd2455ad4dc6e642a"),
    "assets/audio/SE/introSE.mp3": (14280, "af7dbf8582eaa8ac986c676cfc5fee267bb27e2b6a52ee60e5be2afc284f91c5"),
    "assets/audio/SE/lineBreakSE.mp3": (9344, "272084e2e9bd1035b9dd46248003162bdcfe1f2797c23dc644a429c4e907fa25"),
    "assets/audio/SE/nextPageSE.mp3": (3712, "e5bd4a08e2d2bf3c78b4cb857dab5a4a9ba070dc35a704062c18ec93eedc482d"),
    "assets/audio/SE/throwSE.mp3": (9856, "0444df841d4642aae0093cbfb4069344763c6ab61bcca5a4d2091e6a70ff75a4"),
    "assets/audio/SE/waterSE.mp3": (10368, "c9b00c6473db6e7d6f5a602af964ffc06a2c02e6bde7bd61da877d5d3551a637"),
    "assets/audio/music/mari_mari.mp3": (55657, "fd042d8c8a8130b6791450778df5b3be0f5c672058cb0813267f3c3d42192374"),
    "assets/audio/music/select.mp3": (55657, "520052ada7adf9c4b3789b877aa4e33ae4b9b2d797b3e4411e109537799b1541"),
    "assets/audio/music/title.mp3": (659190, "3280ceae2511c6343bc94df5cb9ca0a08c2587e458f72a74f0ab3a2c290b2a80"),
    "assets/audio/music/welcome.mp3": (110410, "897ed2ef8b55d6dcf900b80c5a45a37b78f330b8ae6556fe0a366eae42c7bca7"),
}

AUDIO_OUTPUTS = {
    "assets/audio/music/title.mp3": "title.wav",
    "assets/audio/music/welcome.mp3": "welcome.wav",
    "assets/audio/music/mari_mari.mp3": "mari_mari.wav",
    "assets/audio/music/select.mp3": "select.wav",
    "assets/audio/SE/coilSE.mp3": "coil.wav",
    "assets/audio/SE/coinSE.mp3": "coin.wav",
    "assets/audio/SE/fanfareSE.mp3": "fanfare.wav",
    "assets/audio/SE/fishCatchBaitSE.mp3": "fish_catch_bait.wav",
    "assets/audio/SE/introSE.mp3": "intro.wav",
    "assets/audio/SE/lineBreakSE.mp3": "line_break.wav",
    "assets/audio/SE/nextPageSE.mp3": "next_page.wav",
    "assets/audio/SE/throwSE.mp3": "throw_sfx.wav",
    "assets/audio/SE/waterSE.mp3": "water.wav",
}


def _method_proof(dex: DexFile, label: str) -> dict[str, object]:
    class_name, method_name, expected_offset, expected_units, expected_sha = _METHOD_PROOFS[label]
    code = dex.method_code(f"{_APP}{class_name};", method_name)
    raw = struct.pack(f"<{len(code.code_units)}H", *code.code_units)
    actual_sha = sha256(raw).hexdigest()
    if code.code_offset != expected_offset or len(code.code_units) != expected_units or actual_sha != expected_sha:
        raise ValueError(f"{label} DEX fingerprint changed")
    return {"offset": hex(code.code_offset), "code_units": len(code.code_units), "sha256": actual_sha}


def _audio_string_refs(dex: DexFile, class_name: str, method_name: str) -> list[str]:
    code = dex.method_code(f"{_APP}{class_name};", method_name).code_units
    strings = dex.strings()
    result: list[str] = []
    for _pc, opcode, insn in _walk(code):
        string_index: int | None = None
        if opcode == 0x1A:
            string_index = insn[1]
        elif opcode == 0x1B:
            string_index = insn[1] | (insn[2] << 16)
        if string_index is not None:
            value = strings[string_index]
            if value.startswith("audio/") and value.endswith(".mp3"):
                result.append("assets/" + value)
    return result


def recover_from_apk(apk_path: Path) -> dict[str, object]:
    errors = validate_reference(apk_path, _INVENTORY, expected_sha256=CANONICAL_APK_SHA256)
    if errors:
        raise ValueError("; ".join(errors))

    with zipfile.ZipFile(apk_path, "r") as archive:
        dex = DexFile(archive.read("classes.dex"))
        archive_names = set(archive.namelist())
        assets: list[dict[str, object]] = []
        for path, (expected_size, expected_sha) in sorted(_EXPECTED_AUDIO.items()):
            raw = archive.read(path)
            actual_sha = sha256(raw).hexdigest()
            if len(raw) != expected_size or actual_sha != expected_sha:
                raise ValueError(f"audio source changed: {path}")
            assets.append({"apk_path": path, "bytes": len(raw), "sha256": actual_sha, "output": AUDIO_OUTPUTS[path]})

    refs = {
        "Title": _audio_string_refs(dex, "GameTitle", "loadAssets"),
        "Map": _audio_string_refs(dex, "GameMap", "loadAssets"),
        "Fishing": _audio_string_refs(dex, "GameFishing", "loadAssets"),
        "Shop": _audio_string_refs(dex, "GameShop", "loadAssets"),
        "Catalog": _audio_string_refs(dex, "GameCatalog", "loadAssets"),
        "Event": _audio_string_refs(dex, "GameEvent", "loadAssets"),
        "Intro": _audio_string_refs(dex, "GameIntro", "init"),
        "Options": _audio_string_refs(dex, "GameOptions", "update"),
    }
    referenced = {path for values in refs.values() for path in values}
    missing = sorted(path for path in referenced if path not in archive_names)
    if missing != ["assets/audio/SE/textSE.mp3"]:
        raise ValueError(f"unexpected missing audio references: {missing}")

    music = {
        "Title": "assets/audio/music/title.mp3",
        "Map": "assets/audio/music/mari_mari.mp3",
        "Shop": "assets/audio/music/select.mp3",
        "Catalog": "assets/audio/music/select.mp3",
        "Event": "assets/audio/music/welcome.mp3",
    }
    fishing_sfx = [
        "assets/audio/SE/nextPageSE.mp3",
        "assets/audio/SE/throwSE.mp3",
        "assets/audio/SE/lineBreakSE.mp3",
        "assets/audio/SE/coinSE.mp3",
        "assets/audio/SE/fishCatchBaitSE.mp3",
        "assets/audio/SE/waterSE.mp3",
        "assets/audio/SE/fanfareSE.mp3",
        "assets/audio/SE/coilSE.mp3",
    ]

    return {
        "origin": {
            "apk_sha256": CANONICAL_APK_SHA256,
            "dex_classes": ["GameTitle", "GameMap", "GameFishing", "GameShop", "GameCatalog", "GameEvent", "GameIntro", "GameOptions", "SoundEngine"],
        },
        "evidence": {label: _method_proof(dex, label) for label in _METHOD_PROOFS},
        "audio": {
            "present_count": len(assets),
            "assets": assets,
            "missing_references": missing,
        },
        "scene_audio": {
            "Title": {"music": music["Title"], "sfx": ["assets/audio/SE/nextPageSE.mp3"]},
            "Map": {"music": music["Map"], "sfx": ["assets/audio/SE/nextPageSE.mp3"]},
            "Fishing": {"music": None, "inherits_previous_music": True, "sfx": fishing_sfx},
            "Shop": {
                "music": music["Shop"],
                "sfx": ["assets/audio/SE/nextPageSE.mp3", "assets/audio/SE/coinSE.mp3"],
                "referenced_missing_sfx": ["assets/audio/SE/textSE.mp3"],
            },
            "Catalog": {"music": music["Catalog"], "sfx": ["assets/audio/SE/nextPageSE.mp3"]},
            "Event": {"music": music["Event"], "sfx": ["assets/audio/SE/nextPageSE.mp3"]},
            "Options": {"music": None, "return_music": "assets/audio/music/title.mp3", "sfx": []},
            "Intro": {"music": None, "sfx": ["assets/audio/SE/introSE.mp3"]},
        },
        "conversion": {
            "sample_rate": 16000,
            "channels": 1,
            "sample_width_bits": 8,
            "backend": "Butano 21.7.1 / Maxmod Direct Sound",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "reference/m5_audio_presentation.json")
    args = parser.parse_args(argv)
    data = recover_from_apk(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
