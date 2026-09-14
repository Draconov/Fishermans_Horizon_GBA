from __future__ import annotations

from tools.dex import DexFile
from tools.recover_m4 import recover_m4


def test_recover_m4_shop_table_from_reference_dex(reference_dex: bytes):
    facts = recover_m4(DexFile(reference_dex))
    shop = facts["shop"]

    assert shop["prices"] == [15, 15, 30, 45, 100, 100, 45, 120, 30, 60, 120, 20, 30, 30, 50, 100]
    assert len(shop["items"]) == 16
    assert [item["slot"] for item in shop["items"]] == list(range(16))
    assert [item["progress_field"] for item in shop["items"]] == [
        "baitBread", "baitCandy", "baitBitter", "baitSteak", "baitRainbow", "baitX",
        "hardRod", "proRod", "oldBoat", "clubCard", "ancientMap", "catalog",
        "hugo", "sgtJoe", "itemE", "itemF",
    ]
    assert shop["items"][0]["name"] == "Bread"
    assert shop["items"][5]["name"] == "Bait X"
    assert shop["items"][6]["name"] == "Pro Rod"
    assert shop["items"][7]["name"] == "Nova Rod"
    assert shop["items"][15]["name"] == "Shadow"
    assert shop["items"][6]["equip_rod"] == 1
    assert shop["items"][7]["equip_rod"] == 2
    assert all(item["one_time"] for item in shop["items"])


def test_recover_m4_catalog_order_and_text(reference_dex: bytes):
    facts = recover_m4(DexFile(reference_dex))
    entries = facts["catalog"]["entries"]

    assert len(entries) == 44
    assert [entry["name"] for entry in entries[:5]] == [
        "BOOT", "CAN", "PLASTIC BAG", "SIRIRIDINE", "DRAGFISH"
    ]
    assert [entry["fish_field"] for entry in entries[:5]] == [
        "fish02", "fish03", "fish04", "fish00", "fish01"
    ]
    assert entries[-1]["name"] == "???"
    assert entries[-1]["fish_field"] == "fish2B"
    assert entries[0]["description"] == "An old boot. Please, discard it properly."
    assert facts["catalog"]["completion_requires_all_44"] is True
    assert facts["catalog"]["completion_event"] == 2


def test_recover_m4_options_events_and_save_layout(reference_dex: bytes):
    facts = recover_m4(DexFile(reference_dex))

    assert facts["options"] == {
        "sound_default": 1,
        "sound_values": [0, 1],
        "sound_labels": {"0": "off", "1": "on"},
        "image_default": 1,
        "image_labels": {"0": "   half", "1": "  original", "2": "stretched"},
        "image_touch_cycle": [1, 2, 1],
        "save_file_touch_present_but_unused_in_update": True,
    }

    assert facts["events"]["constants"] == {"BEGIN": 1, "END": 2, "NULL": 3}
    assert facts["events"]["prologue"]["event"] == 1
    assert facts["events"]["prologue"]["sets_prologue"] == 1
    assert facts["events"]["prologue"]["text"].startswith("Hya! I<m Cecil!")
    assert facts["events"]["ending"]["event"] == 2
    assert facts["events"]["ending"]["completed_event"] == 3
    assert "caught all the known sea creatures" in facts["events"]["ending"]["text"]

    save = facts["save"]
    assert save["file_name"] == "horizon.fish"
    assert len(save["field_order"]) == 68
    assert save["field_order"][:6] == ["sound", "image", "prologue", "moneyU", "moneyD", "moneyC"]
    assert save["field_order"][-1] == "fish2B"
    assert save["defaults"]["sound"] == 1
    assert save["defaults"]["image"] == 1
    assert save["defaults"]["prologue"] == 0
    assert [save["defaults"][key] for key in ("moneyU", "moneyD", "moneyC")] == [0, 1, 0]
    assert save["default_money"] == 10
    assert all(save["defaults"][f"fish{index:02X}"] == 0 for index in range(44))


def test_recover_m4_fingerprints_exact_behavior_methods(reference_dex: bytes):
    facts = recover_m4(DexFile(reference_dex))
    proofs = facts["evidence"]["code_proofs"]

    assert proofs["GameShop.<clinit>"]["offset"] == "0xb370"
    assert proofs["GameCatalog.setFish"]["code_units"] == 2149
    assert proofs["GameOptions.update"]["sha256"] == "15bc0fed8e71700696fa22b4c8869d535e1561c66eb003204861bf6a683425b2"
    assert proofs["GlobalVar.saveData"]["code_units"] == 366
    assert proofs["GlobalVar.loadData"]["code_units"] == 561


def test_canonical_m4_json_is_reproducible(reference_dex: bytes):
    import json
    from pathlib import Path

    facts = recover_m4(DexFile(reference_dex))
    committed = json.loads((Path(__file__).resolve().parents[1] / "reference" / "m4_progression_content.json").read_text(encoding="utf-8"))
    assert facts == committed
