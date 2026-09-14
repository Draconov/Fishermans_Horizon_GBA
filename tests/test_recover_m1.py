from __future__ import annotations

import json
from pathlib import Path

from tools.recover_m1 import recover_m1_from_apk


def test_recover_m1_title_facts(reference_apk: Path):
    facts = recover_m1_from_apk(reference_apk)
    title = facts["title"]
    assert title["game_state"] == 2
    assert title["initial_sea_sprite"] == 112
    assert title["sea_frames"] == [[1, 113], [13, 114], [25, 113], [37, 112], [49, 112]]
    assert title["play_zone"] == [0, 128, 32, 160]
    assert title["options_zone"] == [208, 128, 240, 160]
    assert title["fresh_save_route"] == "Event"
    assert title["returning_save_route"] == "Map"
    assert title["music"] == "audio/music/title.mp3"
    assert title["next_page_se"] == "audio/SE/nextPageSE.mp3"


def test_recover_m1_map_facts(reference_apk: Path):
    facts = recover_m1_from_apk(reference_apk)
    game_map = facts["map"]
    assert game_map["game_state"] == 3
    assert game_map["music"] == "audio/music/mari_mari.mp3"
    assert game_map["marker_frames"] == {
        "spot_a": [100, 101],
        "spot_b": [102, 103],
        "period": 20,
    }
    assert game_map["zones"]["back"] == [0, 0, 32, 32]
    assert game_map["zones"]["shop"] == [88, 8, 120, 40]
    assert game_map["zones"]["crystal_lake"] == [136, 16, 168, 48]
    assert game_map["zones"]["pier"] == [120, 72, 152, 104]
    assert game_map["zones"]["river"] == [200, 8, 232, 40]
    assert game_map["zones"]["ocean"] == [96, 120, 128, 152]
    assert game_map["zones"]["cave"] == [8, 88, 40, 120]
    assert game_map["zones"]["catalog"] == [0, 128, 32, 160]
    assert game_map["zones"]["change_character"] == [208, 128, 240, 160]
    assert game_map["unlocks"] == {
        "river": "clubCard",
        "ocean": "oldBoat",
        "cave": "ancientMap",
        "catalog": "catalog",
    }
    assert game_map["pointer_to_pool"] == {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
    assert game_map["pointer_routes"] == {
        "0": "Title",
        "1": "Fishing",
        "2": "Fishing",
        "3": "Fishing",
        "4": "Fishing",
        "5": "Fishing",
        "6": "Shop",
        "7": "Catalog",
    }


def test_recover_m1_records_source_method_offsets(reference_apk: Path):
    facts = recover_m1_from_apk(reference_apk)
    assert facts["evidence"]["methods"] == {
        "GameTitle.init": "0xc8a8",
        "GameTitle.loadAssets": "0xc940",
        "GameTitle.seaImage": "0xc9ac",
        "GameTitle.exit": "0xc858",
        "GameMap.init": "0xa884",
        "GameMap.loadAssets": "0xaac0",
        "GameMap.update": "0xad3c",
        "GameMap.exit": "0xa7d4",
    }


def test_frozen_m1_json_matches_recovery(reference_apk: Path):
    expected = recover_m1_from_apk(reference_apk)
    frozen = json.loads(Path("reference/m1_title_map.json").read_text(encoding="utf-8"))
    assert frozen == expected
