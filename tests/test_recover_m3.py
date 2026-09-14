from __future__ import annotations

import json
import os
from pathlib import Path
import zipfile

import pytest

from tools.dex import DexFile
from tools.recover_m3 import recover_m3, recover_m3_from_apk


ROOT = Path(__file__).resolve().parents[1]
APK = Path(os.environ.get("FH_REFERENCE_APK", "/mnt/data/fishermans-horizon-1-1.apk"))


def _dex() -> DexFile:
    with zipfile.ZipFile(APK, "r") as archive:
        return DexFile(archive.read("classes.dex"))


def test_recovers_five_complete_fishing_pools_from_dalvik() -> None:
    facts = recover_m3(_dex())
    pools = facts["areas"]

    assert [pool["pool"] for pool in pools] == [1, 2, 3, 4, 5]
    assert [pool["background"] for pool in pools] == [
        "graphic/background/crystalLake.png",
        "graphic/background/pier.png",
        "graphic/background/river.png",
        "graphic/background/ocean.png",
        "graphic/background/cave.png",
    ]
    assert all(len(pool["fish"]) == 9 for pool in pools)
    assert sum(len(pool["fish"]) for pool in pools) == 45
    assert len({fish["number"] for pool in pools for fish in pool["fish"]}) == 44


def test_lure_roll_mapping_matches_control_flow_for_every_pool() -> None:
    facts = recover_m3(_dex())
    pools = {pool["pool"]: pool for pool in facts["areas"]}

    assert pools[1]["random_roll_to_fish"] == {
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
    }
    assert pools[2]["random_roll_to_fish"]["9"] == "TROLLSHARK"
    assert pools[3]["random_roll_to_fish"]["9"] == "PINKSHARK"
    assert pools[4]["random_roll_to_fish"]["9"] == "HAMMERHEAD"
    assert pools[5]["random_roll_to_fish"]["9"] == "???"


def test_cross_pool_constructor_sentinels_are_recovered_not_hand_normalized() -> None:
    facts = recover_m3(_dex())
    by_pool = {pool["pool"]: pool["fish"] for pool in facts["areas"]}

    assert by_pool[2][0] == {
        "field": "can", "name": "CAN", "number": 4, "difficulty": 0,
        "bait": 7, "movement": 2, "distance": 40, "sprite": 120, "reward": 1,
    }
    assert by_pool[3][-1] == {
        "field": "gayshark", "name": "PINKSHARK", "number": 38, "difficulty": 4,
        "bait": 4, "movement": 1, "distance": 80, "sprite": 158, "reward": 50,
    }
    assert by_pool[5][-1] == {
        "field": "glitish", "name": "???", "number": 44, "difficulty": 4,
        "bait": 6, "movement": 1, "distance": 80, "sprite": 148, "reward": 1,
    }


def test_duplicate_siriridine_constructor_is_preserved_in_pier_and_ocean() -> None:
    facts = recover_m3(_dex())
    occurrences = [
        (pool["pool"], fish)
        for pool in facts["areas"]
        for fish in pool["fish"]
        if fish["number"] == 1
    ]
    assert [pool for pool, _ in occurrences] == [2, 4]
    assert all(fish["name"] == "SIRIRIDINE" for _, fish in occurrences)


def test_m3_code_fingerprints_lock_complete_area_and_bait_selection_methods() -> None:
    facts = recover_m3(_dex())
    proofs = facts["evidence"]["code_proofs"]
    assert proofs["FishingArea.loadArea"] == {
        "offset": "0x6784", "code_units": 926,
        "sha256": "31ed268e54d4c899c7edeb600e68e8e9fb093e9db0f03568001e12973fb0df3e",
    }
    assert proofs["FishingArea.lurePool"] == {
        "offset": "0x6ed0", "code_units": 440,
        "sha256": "ee35cdd08133323c276832519c86259a878aa361d816c3e5f950935b07181c12",
    }
    assert proofs["GameFishing.checkNextBait"] == {
        "offset": "0x9280", "code_units": 203,
        "sha256": "41e3f89b858c975eb4917cc9907a4b78f91b50334c29df517b40013abb4b6299",
    }
    assert proofs["GameFishing.setEquipedBait"] == {
        "offset": "0x9964", "code_units": 64,
        "sha256": "756e0196e31c13bb73d46ab065da4a3bd1e21aacc6189dee12ca5c4e8715a462",
    }


def test_canonical_json_is_reproducible() -> None:
    facts = recover_m3_from_apk(APK)
    committed = json.loads((ROOT / "reference" / "m3_fishing_content.json").read_text(encoding="utf-8"))
    assert facts == committed


def test_game_fishing_sound_channels_and_state_flags_are_recovered_from_dalvik() -> None:
    facts = recover_m3(_dex())
    audio = facts["audio"]
    assert audio["channels"] == [
        {"flag": "playSE0", "channel": 2, "asset": "audio/SE/nextPageSE.mp3"},
        {"flag": "playSE1", "channel": 3, "asset": "audio/SE/throwSE.mp3"},
        {"flag": "playSE2", "channel": 4, "asset": "audio/SE/lineBreakSE.mp3"},
        {"flag": "playSE3", "channel": 5, "asset": "audio/SE/coinSE.mp3"},
        {"flag": "playSE4", "channel": 6, "asset": "audio/SE/fishCatchBaitSE.mp3"},
        {"flag": "playSE5", "channel": 7, "asset": "audio/SE/waterSE.mp3"},
        {"flag": "playSE6", "channel": 8, "asset": "audio/SE/fanfareSE.mp3"},
        {"flag": "playSE7", "channel": 9, "asset": "audio/SE/coilSE.mp3"},
    ]
    assert audio["state_flags"] == {
        "stateStand": ["playSE0"],
        "stateThrow": ["playSE1", "playSE5"],
        "stateBaitInWater": ["playSE4", "playSE7"],
        "stateFishInLine": ["playSE7"],
        "stateFishCatch": ["playSE5", "playSE6"],
        "stateLineBreak": ["playSE2"],
        "stateReward": ["playSE3"],
    }
