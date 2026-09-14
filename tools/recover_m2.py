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

# The facts below were decoded from these exact canonical method bodies.  The
# recovery step intentionally fails closed if any body changes, so a different
# APK cannot silently inherit the 1.1 gameplay table.
_METHOD_PROOFS = {
    "GameFishing.<clinit>": ("GameFishing", "<clinit>", 0x924C, 5, "de09f64e18e8c36db03d543e042f0d8d56c9c303eabdf5c8450a770d0f01f856"),
    "GameFishing.checkNextBait": ("GameFishing", "checkNextBait", 0x9280, 203, "41e3f89b858c975eb4917cc9907a4b78f91b50334c29df517b40013abb4b6299"),
    "GameFishing.draw": ("GameFishing", "draw", 0x9428, 184, "f94ceeff7d67e935777253c42e3a5be3d9ed580b608d8775fc9d53cea8ae1528"),
    "GameFishing.init": ("GameFishing", "init", 0x95CC, 128, "190dcaf94950e10c74bc190073edad198b47301d71aa5b3b25c0782b4d6c2cd4"),
    "GameFishing.loadAssets": ("GameFishing", "loadAssets", 0x96DC, 122, "05f9802ce2c748523b13e5348cf96c0109b8a54d700ad6e6fea35f8ad19f1451"),
    "GameFishing.resetVar": ("GameFishing", "resetVar", 0x97E0, 83, "da06977a7704e510e36f9f3a9efaeab6c844e4d244e78c07657c61ad3b911f16"),
    "GameFishing.seaImage": ("GameFishing", "seaImage", 0x9898, 53, "4ef13d7c33a40bdb658d9fdc506b6277665557c5fb27759d9a76aeb7ee8e06f1"),
    "GameFishing.setDelay": ("GameFishing", "setDelay", 0x9914, 31, "481198e0c487e3a2ddc2e08ee53568225efd8e60a2f540622dbf2c6032178f81"),
    "GameFishing.setEquipedBait": ("GameFishing", "setEquipedBait", 0x9964, 64, "756e0196e31c13bb73d46ab065da4a3bd1e21aacc6189dee12ca5c4e8715a462"),
    "GameFishing.stateStand": ("GameFishing", "stateStand", 0xA270, 59, "f1f8a707c9f74487a8ac8452aea4fbef96c9df38e00fad8f0c2f178c1dd7457f"),
    "GameFishing.stateGetReadyToThrow": ("GameFishing", "stateGetReadyToThrow", 0x9E78, 83, "d818065981c732fb7564dcf90a61599e738c983e44e472d8fe437dcf3e695659"),
    "GameFishing.stateThrow": ("GameFishing", "stateThrow", 0xA2F8, 164, "98f22fec863daebcb584b6ba162e2cc9aa30fca8866d470356b53ba028f3524d"),
    "GameFishing.stateBaitInWater": ("GameFishing", "stateBaitInWater", 0x99F4, 223, "3a92168ffaa275d5f83656d4acc83a9a33225992633305a03857b9f966dd7372"),
    "GameFishing.stateFishInLine": ("GameFishing", "stateFishInLine", 0x9CE4, 193, "067b0bb506fe6c65e32aaa954765514a52fe7bb0b4fbe9005e3fc3fe9a6e89ec"),
    "GameFishing.stateRecoil": ("GameFishing", "stateRecoil", 0xA004, 120, "e02fdca05ad166ad49b3ba206f2abc02807cd7e30ab6d9b727a9611aefaea44a"),
    "GameFishing.stateFishCatch": ("GameFishing", "stateFishCatch", 0x9BC4, 136, "4ee8245ea960a0326c570f5e2003b03357426ce5aa34db9299f427d4f4319296"),
    "GameFishing.stateLineBreak": ("GameFishing", "stateLineBreak", 0x9F98, 45, "4bc58c6fa19229489aca0374b99c1b9e3a05c04eb8a184e98f3bd91e90a33a70"),
    "GameFishing.stateReward": ("GameFishing", "stateReward", 0xA104, 173, "4382fcc9f43c6c12d5fd727465a441b9239845c722041e7c5ef5c2755b2030cd"),
    "GameFishing.update": ("GameFishing", "update", 0xA450, 106, "e26f13e6d195a04213aedcca0e1308be22632affc5c81682c63c02bae358e8ce"),
    "FishingArea.loadArea": ("FishingArea", "loadArea", 0x6784, 926, "31ed268e54d4c899c7edeb600e68e8e9fb093e9db0f03568001e12973fb0df3e"),
    "FishingArea.lurePool": ("FishingArea", "lurePool", 0x6ED0, 440, "ee35cdd08133323c276832519c86259a878aa361d816c3e5f950935b07181c12"),
    "FishingArea.inLinePool": ("FishingArea", "inLinePool", 0x6470, 386, "2deeb4298defe7369a36432e41da368c46f1953bc9d69c0b506da66e0cce52aa"),
    "FishingArea.addCatalog": ("FishingArea", "addCatalog", 0x628C, 234, "ee4dbdf6472b5d8720e4919b9e742afc71ff65a35704f3a0992bf6fded927a9c"),
    "Fish.<init>": ("Fish", "<init>", 0x5FA0, 101, "adc5f2ffd12c5621aa86e00e78ddd7e6739426c564dfcf68b98d4a5077c6fed3"),
    "Fish.lure": ("Fish", "lure", 0x6168, 125, "a18438e9d56503654fbfcb7ad21adfcdf9b50452bc057904821c7514f926c93d"),
    "Fish.inLine": ("Fish", "inLine", 0x607C, 110, "31f9c1b8087385518e3d62d9cb5d96ebb2947b52c6cf96dcc46e9c543a70bae7"),
    "Bait.set": ("Bait", "set", 0x357C, 130, "6fd0f016bf0e91741b56a60635af97f5107694022bb0b4b94d272a9ee42ebfab"),
    "Bait.lure": ("Bait", "lure", 0x34B8, 90, "cbab8495f7c0238881369aacb1d26fbdbb0cba7450f87cfdec5516b8efa03f01"),
}

_REQUIRED_FIELDS = {
    (f"{_APP}GameFishing;", "gameFishingState", "I"),
    (f"{_APP}GameFishing;", "ticks", "I"),
    (f"{_APP}GameFishing;", "meterX", "I"),
    (f"{_APP}GameFishing;", "lineDistance", "F"),
    (f"{_APP}GameFishing;", "stickSTR", "I"),
    (f"{_APP}GameFishing;", "fishSTR", "I"),
    (f"{_APP}Fish;", "currentSTA", "I"),
    (f"{_APP}GameFishing;", "reward", "I"),
    (f"{_APP}FishingArea;", "pool", "I"),
    (f"{_APP}Bait;", "movementType", "I"),
    (f"{_APP}Framework;", "money", "I"),
}


def _method_proof(dex: DexFile, label: str) -> dict[str, object]:
    class_name, method_name, expected_offset, expected_units, expected_sha = _METHOD_PROOFS[label]
    code = dex.method_code(f"{_APP}{class_name};", method_name)
    raw = struct.pack(f"<{len(code.code_units)}H", *code.code_units)
    actual_sha = sha256(raw).hexdigest()
    if code.code_offset != expected_offset:
        raise ValueError(f"{label} code offset changed: {code.code_offset:#x} != {expected_offset:#x}")
    if len(code.code_units) != expected_units:
        raise ValueError(f"{label} code size changed: {len(code.code_units)} != {expected_units}")
    if actual_sha != expected_sha:
        raise ValueError(f"{label} code fingerprint changed")
    return {"offset": hex(code.code_offset), "code_units": len(code.code_units), "sha256": actual_sha}


def recover_m2(dex: DexFile) -> dict[str, object]:
    field_surface = {(field.class_descriptor, field.name, field.type_descriptor) for field in dex.fields()}
    missing_fields = sorted(_REQUIRED_FIELDS - field_surface)
    if missing_fields:
        raise ValueError(f"missing M2 fields: {missing_fields}")

    proofs = {label: _method_proof(dex, label) for label in _METHOD_PROOFS}

    fish = [
        {"name": "BOOT", "number": 3, "difficulty": 0, "bait": 7, "movement": 2, "distance": 40, "sprite": 119, "reward": 1},
        {"name": "BABY UNICUDA", "number": 40, "difficulty": 1, "bait": 0, "movement": 1, "distance": 80, "sprite": 122, "reward": 5},
        {"name": "ANGELINE", "number": 11, "difficulty": 1, "bait": 1, "movement": 1, "distance": 80, "sprite": 129, "reward": 5},
        {"name": "BLEH", "number": 6, "difficulty": 1, "bait": 0, "movement": 1, "distance": 80, "sprite": 131, "reward": 5},
        {"name": "PUG", "number": 24, "difficulty": 2, "bait": 3, "movement": 1, "distance": 80, "sprite": 142, "reward": 10},
        {"name": "WHITESTRIPE", "number": 19, "difficulty": 2, "bait": 2, "movement": 1, "distance": 80, "sprite": 137, "reward": 10},
        {"name": "NUMKITE", "number": 34, "difficulty": 2, "bait": 3, "movement": 1, "distance": 80, "sprite": 144, "reward": 10},
        {"name": "NUMEART", "number": 35, "difficulty": 2, "bait": 2, "movement": 1, "distance": 80, "sprite": 150, "reward": 10},
        {"name": "UNICUDA", "number": 41, "difficulty": 3, "bait": 5, "movement": 1, "distance": 80, "sprite": 160, "reward": 25},
    ]

    return {
        "origin": {"apk_sha256": CANONICAL_APK_SHA256, "member": "classes.dex"},
        "visual": {
            "fishing_line_argb": [255, 235, 255, 237],
            "anchors": {
                "sea_y": 128,
                "character": [16, 72],
                "rod": [0, 48],
                "meter_y": 128,
                "back_icon": [4, 4],
                "bait_icon": [192, 4],
                "coin_x": 48,
            },
        },
        "evidence": {
            "methods": {label: proof["offset"] for label, proof in proofs.items()},
            "code_proofs": proofs,
        },
        "fishing": {
            "states": {
                "INIT": 0,
                "STAND": 1,
                "RECOIL": 2,
                "GET_READY_TO_THROW": 3,
                "THROW": 4,
                "BAIT_IN_WATER": 5,
                "FISH_IN_LINE": 6,
                "LINE_BREAK": 7,
                "FISH_CATCH": 8,
                "REWARD": 9,
            },
            "update_increments_ticks_first": True,
            "minimal_throw_distance": 100,
            "meter": {"min": 37, "max": 111},
            "rod_strengths": [10, 12, 14],
            "line": {"initial_distance": 50.0, "catch_x": 48, "break_distance": 280.0},
            "money_cap": 999,
            "throw_delay_buckets": [
                {"max_charge_delta": 25, "delay": 0},
                {"max_charge_delta": 50, "delay": 6},
                {"max_charge_delta": None, "delay": 12},
            ],
            # GameFishing.seaImage is instruction-for-instruction equivalent to
            # GameTitle.seaImage except for the owning static field references.
            "sea_frames": [[1, 113], [13, 114], [25, 113], [37, 112], [49, 112]],
            "get_ready_ticks": {
                "pose_1": 1,
                "pose_2_hide_bait": 4,
                "pose_3": 7,
                "release_after": 9,
                "charge_step": 2,
            },
            "throw_ticks": {
                "pose_1": 1,
                "pose_2": 4,
                "pose_3": 7,
                "set_delay": 10,
                "splash_offset": 19,
                "landed_offset": 37,
            },
            "bait_in_water": {
                "random_window": 30,
                "lure_starts_after_tick": 50,
                "reel_distance_step": 1.0,
                "reel_period": 3,
                "hook_animation_end_tick": 10,
            },
            "line_break_dialog_tick": 15,
            "catch_dialog_tick": 43,
            "reward_commit_tick": 25,
        },
        "bait": {
            "types": {
                "WORM": 0,
                "BREAD": 1,
                "CANDY": 2,
                "BITTER_GUM": 3,
                "STEAK": 4,
                "RAINBOWORM": 5,
                "BAIT_X": 6,
                "ANY": 7,
            },
            "movement": {
                "0": 0,
                "1-9": 1,
                "10": 2,
                "held_step_period": 12,
                "released_step_period": 24,
                "max_points": 10,
            },
            "base_sprites": [11, 75, 13, 77, 88, 90, 92],
        },
        "fish_difficulty": {
            "0": {"strength": 4, "stamina": 1, "critical_stamina": 1, "rest_count": 0},
            "1": {"strength": 7, "stamina": 600, "critical_stamina": 150, "rest_count": 3},
            "2": {"strength": 8, "stamina": 700, "critical_stamina": 200, "rest_count": 4},
            "3": {"strength": 9, "stamina": 1000, "critical_stamina": 250, "rest_count": 6},
            "4": {"strength": 10, "stamina": 1200, "critical_stamina": 300, "rest_count": 8},
        },
        "fish_lure": {
            "required_consecutive_ticks": 10,
            "bait_x_matches_all": True,
            "fish_bait_any_value": 7,
            "distance_relation": "line_distance > fish_distance",
            "mismatch_resets_timer": True,
        },
        "fish_in_line": {
            "exhausted_strength_delta": -3,
            "rest_early_end_distance_bonus": 80,
            "rest_early_end_ticks": 160,
            "held_meter_period": 2,
            "held_meter_step": -1,
            "released_meter_step": 1,
            "strength_distance_scale": 0.1,
        },
        "crystal_lake": {
            "pool": 1,
            "random_roll_to_fish": {
                "0": None,
                "1": "BOOT",
                "2": "BABY UNICUDA",
                "3": "ANGELINE",
                "4": "BLEH",
                "5": "PUG",
                "6": "WHITESTRIPE",
                "7": "NUMKITE",
                "8": "NUMEART",
                "9": "UNICUDA",
            },
            "fish": fish,
            "catalog_indices": {item["name"]: item["number"] - 1 for item in fish},
        },
        "progression": {
            "catalog_index": "fish_number - 1",
            "money_cap": 999,
            "reward_applied_at_reward_tick": 25,
        },
        "input": {
            "back_zone": [0, 0, 32, 32],
            "stick_zone": [0, 128, 32, 160],
            "bait_zone": [208, 0, 240, 32],
        },
    }


def recover_m2_from_apk(apk_path: Path) -> dict[str, object]:
    inventory = ROOT / "reference" / "apk_inventory.tsv"
    errors = validate_reference(apk_path, inventory)
    if errors:
        raise ValueError("reference APK validation failed: " + "; ".join(errors))
    with zipfile.ZipFile(apk_path, "r") as archive:
        dex_bytes = archive.read("classes.dex")
    return recover_m2(DexFile(dex_bytes))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recover M2 Crystal Lake fishing parity facts")
    parser.add_argument("apk", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)

    facts = recover_m2_from_apk(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
