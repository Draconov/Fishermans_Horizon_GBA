from __future__ import annotations

from tools.recover_surface import recover_surface


def test_recovered_surface_has_all_catalog_slots(reference_dex_file):
    surface = recover_surface(reference_dex_file)
    assert surface["catalog_fields"] == [f"fish{i:02X}" for i in range(0x2C)]


def test_recovered_surface_has_fishing_state_contract(reference_dex_file):
    surface = recover_surface(reference_dex_file)
    assert surface["fishing_states"] == [
        "INIT",
        "STAND",
        "GET_READY_TO_THROW",
        "THROW",
        "BAIT_IN_WATER",
        "FISH_IN_LINE",
        "RECOIL",
        "FISH_CATCH",
        "LINE_BREAK",
        "REWARD",
    ]


def test_recovered_surface_has_five_area_symbols(reference_dex_file):
    assert recover_surface(reference_dex_file)["area_symbols"] == [
        "CRYSTAL_LAKE",
        "PIER",
        "RIVER",
        "OCEAN",
        "CAVE",
    ]


def test_recovered_surface_records_game_classes_and_methods(reference_dex_file):
    surface = recover_surface(reference_dex_file)
    assert "Lcom/fishermanshorizon/app/GameFishing;" in surface["classes"]
    methods = {
        (method["class"], method["name"])
        for method in surface["methods"]
    }
    assert ("Lcom/fishermanshorizon/app/GameFishing;", "stateReward") in methods
    assert ("Lcom/fishermanshorizon/app/FishingArea;", "loadArea") in methods


def test_recovered_surface_records_canonical_origin(reference_dex_file):
    surface = recover_surface(reference_dex_file)
    assert surface["origin"] == {
        "apk_sha256": "581aeb20073592905b5a82ddc38a54f522f2f369330ae92f025ae7d52ca0d137",
        "member": "classes.dex",
    }
