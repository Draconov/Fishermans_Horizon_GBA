from __future__ import annotations

import json
from pathlib import Path

from tools.recover_m2 import recover_m2_from_apk


def test_recover_m2_state_machine_and_core_constants(reference_apk: Path):
    facts = recover_m2_from_apk(reference_apk)
    fishing = facts["fishing"]
    assert fishing["states"] == {
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
    }
    assert fishing["update_increments_ticks_first"] is True
    assert fishing["minimal_throw_distance"] == 100
    assert fishing["meter"] == {"min": 37, "max": 111}
    assert fishing["rod_strengths"] == [10, 12, 14]
    assert fishing["line"] == {"initial_distance": 50.0, "catch_x": 48, "break_distance": 280.0}
    assert fishing["money_cap"] == 999
    assert fishing["throw_delay_buckets"] == [
        {"max_charge_delta": 25, "delay": 0},
        {"max_charge_delta": 50, "delay": 6},
        {"max_charge_delta": None, "delay": 12},
    ]
    assert fishing["sea_frames"] == [
        [1, 113], [13, 114], [25, 113], [37, 112], [49, 112]
    ]


def test_recover_m2_bait_and_difficulty_rules(reference_apk: Path):
    facts = recover_m2_from_apk(reference_apk)
    assert facts["bait"]["types"] == {
        "WORM": 0,
        "BREAD": 1,
        "CANDY": 2,
        "BITTER_GUM": 3,
        "STEAK": 4,
        "RAINBOWORM": 5,
        "BAIT_X": 6,
        "ANY": 7,
    }
    assert facts["bait"]["movement"] == {
        "0": 0,
        "1-9": 1,
        "10": 2,
        "held_step_period": 12,
        "released_step_period": 24,
        "max_points": 10,
    }
    assert facts["fish_difficulty"] == {
        "0": {"strength": 4, "stamina": 1, "critical_stamina": 1, "rest_count": 0},
        "1": {"strength": 7, "stamina": 600, "critical_stamina": 150, "rest_count": 3},
        "2": {"strength": 8, "stamina": 700, "critical_stamina": 200, "rest_count": 4},
        "3": {"strength": 9, "stamina": 1000, "critical_stamina": 250, "rest_count": 6},
        "4": {"strength": 10, "stamina": 1200, "critical_stamina": 300, "rest_count": 8},
    }


def test_recover_m2_crystal_lake_roll_mapping_is_one_indexed(reference_apk: Path):
    facts = recover_m2_from_apk(reference_apk)
    lake = facts["crystal_lake"]
    assert lake["pool"] == 1
    assert lake["random_roll_to_fish"] == {
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
    expected = [
        ("BOOT", 3, 0, 7, 2, 40, 119, 1),
        ("BABY UNICUDA", 40, 1, 0, 1, 80, 122, 5),
        ("ANGELINE", 11, 1, 1, 1, 80, 129, 5),
        ("BLEH", 6, 1, 0, 1, 80, 131, 5),
        ("PUG", 24, 2, 3, 1, 80, 142, 10),
        ("WHITESTRIPE", 19, 2, 2, 1, 80, 137, 10),
        ("NUMKITE", 34, 2, 3, 1, 80, 144, 10),
        ("NUMEART", 35, 2, 2, 1, 80, 150, 10),
        ("UNICUDA", 41, 3, 5, 1, 80, 160, 25),
    ]
    actual = [
        (
            fish["name"], fish["number"], fish["difficulty"], fish["bait"],
            fish["movement"], fish["distance"], fish["sprite"], fish["reward"],
        )
        for fish in lake["fish"]
    ]
    assert actual == expected
    assert lake["catalog_indices"] == {
        "BOOT": 2,
        "BABY UNICUDA": 39,
        "ANGELINE": 10,
        "BLEH": 5,
        "PUG": 23,
        "WHITESTRIPE": 18,
        "NUMKITE": 33,
        "NUMEART": 34,
        "UNICUDA": 40,
    }


def test_recover_m2_timing_and_lure_predicate(reference_apk: Path):
    facts = recover_m2_from_apk(reference_apk)
    assert facts["fishing"]["get_ready_ticks"] == {
        "pose_1": 1,
        "pose_2_hide_bait": 4,
        "pose_3": 7,
        "release_after": 9,
        "charge_step": 2,
    }
    assert facts["fishing"]["bait_in_water"] == {
        "random_window": 30,
        "lure_starts_after_tick": 50,
        "reel_distance_step": 1.0,
        "reel_period": 3,
        "hook_animation_end_tick": 10,
    }
    assert facts["fish_lure"] == {
        "required_consecutive_ticks": 10,
        "bait_x_matches_all": True,
        "fish_bait_any_value": 7,
        "distance_relation": "line_distance > fish_distance",
        "mismatch_resets_timer": True,
    }
    assert facts["progression"] == {
        "catalog_index": "fish_number - 1",
        "money_cap": 999,
        "reward_applied_at_reward_tick": 25,
    }


def test_recover_m2_records_exact_method_proofs(reference_apk: Path):
    facts = recover_m2_from_apk(reference_apk)
    proofs = facts["evidence"]["code_proofs"]
    assert proofs["GameFishing.stateFishInLine"] == {
        "offset": "0x9ce4",
        "code_units": 193,
        "sha256": "067b0bb506fe6c65e32aaa954765514a52fe7bb0b4fbe9005e3fc3fe9a6e89ec",
    }
    assert proofs["FishingArea.loadArea"] == {
        "offset": "0x6784",
        "code_units": 926,
        "sha256": "31ed268e54d4c899c7edeb600e68e8e9fb093e9db0f03568001e12973fb0df3e",
    }
    assert proofs["Fish.lure"] == {
        "offset": "0x6168",
        "code_units": 125,
        "sha256": "a18438e9d56503654fbfcb7ad21adfcdf9b50452bc057904821c7514f926c93d",
    }
    assert proofs["GameFishing.seaImage"] == {
        "offset": "0x9898",
        "code_units": 53,
        "sha256": "4ef13d7c33a40bdb658d9fdc506b6277665557c5fb27759d9a76aeb7ee8e06f1",
    }
    assert proofs["GameFishing.setEquipedBait"] == {
        "offset": "0x9964",
        "code_units": 64,
        "sha256": "756e0196e31c13bb73d46ab065da4a3bd1e21aacc6189dee12ca5c4e8715a462",
    }
    assert proofs["GameFishing.checkNextBait"] == {
        "offset": "0x9280",
        "code_units": 203,
        "sha256": "41e3f89b858c975eb4917cc9907a4b78f91b50334c29df517b40013abb4b6299",
    }


def test_frozen_m2_json_matches_recovery(reference_apk: Path):
    expected = recover_m2_from_apk(reference_apk)
    frozen = json.loads(Path("reference/m2_fishing.json").read_text(encoding="utf-8"))
    assert frozen == expected


def test_recover_m2_visual_line_and_draw_anchors(reference_apk: Path):
    facts = recover_m2_from_apk(reference_apk)
    visual = facts["visual"]
    assert visual["fishing_line_argb"] == [255, 235, 255, 237]
    assert visual["anchors"] == {
        "sea_y": 128,
        "character": [16, 72],
        "rod": [0, 48],
        "meter_y": 128,
        "back_icon": [4, 4],
        "bait_icon": [192, 4],
        "coin_x": 48,
    }
    proofs = facts["evidence"]["code_proofs"]
    assert proofs["GameFishing.draw"] == {
        "offset": "0x9428",
        "code_units": 184,
        "sha256": "f94ceeff7d67e935777253c42e3a5be3d9ed580b608d8775fc9d53cea8ae1528",
    }
    assert proofs["GameFishing.loadAssets"] == {
        "offset": "0x96dc",
        "code_units": 122,
        "sha256": "05f9802ce2c748523b13e5348cf96c0109b8a54d700ad6e6fea35f8ad19f1451",
    }
