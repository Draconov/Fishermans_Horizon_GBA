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

_METHOD_PROOFS = {
    "GameShop.<clinit>": ("GameShop", "<clinit>", 0xB370, 49, "7d6294eab5146db5cfc4249c54eb5ddb731ab919ce054387c2ba78d45c6ed0eb"),
    "GameShop.itemChecker": ("GameShop", "itemChecker", 0xB894, 98, "c0073af2fd47182b5410fb5ba2e485f3b4ff1bf82b4ff87d22c466de896c2eff"),
    "GameShop.itemGetter": ("GameShop", "itemGetter", 0xB968, 197, "512c1d5c2dfde8ad4b932b9de88229e55bc03663090f356f08be47855946aa22"),
    "GameShop.itemSetter": ("GameShop", "itemSetter", 0xBB04, 1389, "a8438118cb243d2852279bfb2ca828790be7451192d45d70dab5011b7956ba48"),
    "GameShop.update": ("GameShop", "update", 0xC710, 111, "7a36f9aeae33c7fe4082d27082be0a05554d4a383df8569c7e39f215199f54bd"),
    "GameCatalog.ending": ("GameCatalog", "ending", 0x7A54, 186, "16adfe31cf90234c5a27a8b68cbcf4fb15556f29735b80bed5484ea4582ce77f"),
    "GameCatalog.setFish": ("GameCatalog", "setFish", 0x7DC8, 2149, "64eba0fd6300ab63c8fc60b2a5de985725248722ee0c06bfd04b33fe93fd9a87"),
    "GameCatalog.update": ("GameCatalog", "update", 0x8EA4, 94, "732c1cd6aa2d891d9646952cb40841cccea83ca0da4858c4a46ec66be0196e6a"),
    "GameCatalog.exit": ("GameCatalog", "exit", 0x7BD8, 18, "346765cee47411a0a02d3c49bfc4915a4383f23b36dd88f3ac92f55e439c10b0"),
    "GameOptions.loadAssets": ("GameOptions", "loadAssets", 0xB074, 119, "27ab8254adb3ab54304a55fe982ebbdba3851ed9b9f05df0f9273536ad4d5938"),
    "GameOptions.update": ("GameOptions", "update", 0xB1F0, 176, "15bc0fed8e71700696fa22b4c8869d535e1561c66eb003204861bf6a683425b2"),
    "GameOptions.exit": ("GameOptions", "exit", 0xAF28, 12, "9cb5d89d8c3956139151c573df7dca4a5b96382799879fd5b3f1be0f4ed0f567"),
    "GameEvent.update": ("GameEvent", "update", 0x91B0, 69, "26fb05778780b1f66faa599f18380d6e78255992e4245d945f614beb9fac55c6"),
    "GameEvent.exit": ("GameEvent", "exit", 0x8FE0, 12, "685da90bda5ef0571f0037ed0ce87dac156da20d8e0e555df7680756c828d4ee"),
    "GlobalVar.saveData": ("GlobalVar", "saveData", 0xCB08, 366, "1fd17d749e23b4a6dc40baf0cd01aa31f331426ee5f156a245c50fdee387769f"),
    "GlobalVar.loadData": ("GlobalVar", "loadData", 0xCE04, 561, "4b37c8dfe55b6b28bac5e929ef6b62b5d3fe7ce5060a5969b1d1d84bfecc3220"),
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


def _signed4(value: int) -> int:
    return value - 16 if value & 0x8 else value


def _signed16(value: int) -> int:
    return value - 65536 if value & 0x8000 else value


def _signed32(value: int) -> int:
    return value - 4294967296 if value & 0x80000000 else value


def _instruction_width(code: tuple[int, ...], pc: int) -> int:
    unit = code[pc]
    opcode = unit & 0xFF
    high = unit >> 8

    if opcode == 0 and high:
        if high == 1:  # packed-switch-payload
            size = code[pc + 1]
            return 4 + size * 2
        if high == 2:  # sparse-switch-payload
            size = code[pc + 1]
            return 2 + size * 4
        if high == 3:  # fill-array-data-payload
            element_width = code[pc + 1]
            size = code[pc + 2] | (code[pc + 3] << 16)
            return 4 + ((element_width * size + 1) // 2)
        raise ValueError(f"unknown DEX payload type {high:#x}")

    if opcode in {0x00, 0x01, 0x04, 0x07, *range(0x0A, 0x13), 0x1D, 0x1E, 0x21, 0x27, 0x28, *range(0x7B, 0x90), *range(0xB0, 0xD0)}:
        return 1
    if opcode in {0x02, 0x05, 0x08, 0x13, 0x15, 0x16, 0x19, 0x1A, 0x1C, 0x1F, 0x20, 0x22, 0x23, 0x29, *range(0x2D, 0x3E), *range(0x44, 0x6E), *range(0xD0, 0xE3)}:
        return 2
    if opcode in {0x03, 0x06, 0x09, 0x14, 0x17, 0x1B, 0x24, 0x25, 0x26, 0x2A, 0x2B, 0x2C, *range(0x6E, 0x73), *range(0x74, 0x79)}:
        return 3
    if opcode == 0x18:
        return 5
    raise ValueError(f"unsupported DEX opcode {opcode:#x} at code unit {pc:#x}")


def _walk(code: tuple[int, ...]):
    pc = 0
    while pc < len(code):
        width = _instruction_width(code, pc)
        yield pc, code[pc] & 0xFF, code[pc:pc + width]
        pc += width


def _assign_constant(registers: dict[int, int], opcode: int, insn: tuple[int, ...]) -> None:
    unit = insn[0]
    if opcode == 0x12:
        registers[(unit >> 8) & 0xF] = _signed4((unit >> 12) & 0xF)
    elif opcode == 0x13:
        registers[(unit >> 8) & 0xFF] = _signed16(insn[1])
    elif opcode == 0x14:
        registers[(unit >> 8) & 0xFF] = _signed32(insn[1] | (insn[2] << 16))
    elif opcode == 0x15:
        registers[(unit >> 8) & 0xFF] = _signed16(insn[1]) << 16


def _recover_shop_prices(dex: DexFile) -> list[int]:
    code = dex.method_code(f"{_APP}GameShop;", "<clinit>").code_units
    fields = dex.fields()
    registers: dict[int, int] = {}
    values: dict[str, int] = {}

    for _pc, opcode, insn in _walk(code):
        if opcode in (0x12, 0x13, 0x14, 0x15):
            _assign_constant(registers, opcode, insn)
        elif opcode == 0x67:  # sput
            register = (insn[0] >> 8) & 0xFF
            field = fields[insn[1]]
            if field.class_descriptor == f"{_APP}GameShop;" and field.name.startswith("priceItem"):
                if register not in registers:
                    raise ValueError(f"shop price register v{register} has no constant")
                values[field.name] = registers[register]

    names = [f"priceItem{index:X}" for index in range(16)]
    if set(values) != set(names):
        raise ValueError(f"unexpected shop price fields: {sorted(values)}")
    return [values[name] for name in names]


def _recover_shop_progress_fields(dex: DexFile) -> list[str]:
    code = dex.method_code(f"{_APP}GameShop;", "itemChecker").code_units
    fields = dex.fields()
    last_progress: str | None = None
    mapping: dict[int, str] = {}

    for _pc, opcode, insn in _walk(code):
        if opcode == 0x60:  # sget
            field = fields[insn[1]]
            if field.class_descriptor == f"{_APP}GlobalVar;":
                last_progress = field.name
        elif opcode == 0x6A:  # sput-boolean
            field = fields[insn[1]]
            if field.class_descriptor == f"{_APP}GameShop;" and field.name.startswith("soldOutItem"):
                if last_progress is None:
                    raise ValueError("sold-out field was not preceded by a GlobalVar progress field")
                suffix = field.name.removeprefix("soldOutItem")
                slot = int(suffix, 16)
                mapping[slot] = last_progress
                last_progress = None

    if set(mapping) != set(range(16)):
        raise ValueError(f"unexpected shop sold-out mapping: {mapping}")
    return [mapping[index] for index in range(16)]


def _recover_catalog_field_order(dex: DexFile) -> list[str]:
    code = dex.method_code(f"{_APP}GameCatalog;", "setFish").code_units
    fields = dex.fields()
    cursor_field_index = next(
        index for index, field in enumerate(fields)
        if field.class_descriptor == f"{_APP}GameCatalog;" and field.name == "cursorPosition"
    )
    result: list[str] = []
    waiting_for_fish = False

    for _pc, opcode, insn in _walk(code):
        if opcode != 0x60:  # sget
            continue
        field_index = insn[1]
        field = fields[field_index]
        if field_index == cursor_field_index:
            waiting_for_fish = True
            continue
        if waiting_for_fish and field.class_descriptor == f"{_APP}GlobalVar;" and field.name.startswith("fish"):
            result.append(field.name)
            waiting_for_fish = False

    if len(result) != 44 or len(set(result)) != 44:
        raise ValueError(f"unexpected catalog field order: {len(result)} entries")
    return result


def _recover_save_field_order(dex: DexFile) -> list[str]:
    code = dex.method_code(f"{_APP}GlobalVar;", "saveData").code_units
    fields = dex.fields()
    result: list[str] = []
    for _pc, opcode, insn in _walk(code):
        if opcode == 0x60:  # sget
            field = fields[insn[1]]
            if field.class_descriptor == f"{_APP}GlobalVar;":
                result.append(field.name)
    if len(result) != 68 or len(set(result)) != 68:
        raise ValueError(f"unexpected GlobalVar save field order: {len(result)} entries")
    return result


def _recover_load_defaults(dex: DexFile) -> dict[str, int]:
    code = dex.method_code(f"{_APP}GlobalVar;", "loadData").code_units
    fields = dex.fields()
    registers: dict[int, int] = {}
    in_exception_defaults = False
    result: dict[str, int] = {}

    for _pc, opcode, insn in _walk(code):
        if opcode in (0x12, 0x13, 0x14, 0x15):
            _assign_constant(registers, opcode, insn)
        elif opcode == 0x0D:  # move-exception starts FileNotFound fallback
            in_exception_defaults = True
        elif in_exception_defaults and opcode == 0x67:  # sput
            register = (insn[0] >> 8) & 0xFF
            field = fields[insn[1]]
            if field.class_descriptor == f"{_APP}GlobalVar;":
                if register not in registers:
                    raise ValueError(f"default register v{register} has no constant")
                result[field.name] = registers[register]

    if len(result) != 68:
        raise ValueError(f"unexpected GlobalVar default count: {len(result)}")
    return result


def recover_m4(dex: DexFile) -> dict[str, object]:
    proofs = {label: _method_proof(dex, label) for label in _METHOD_PROOFS}
    string_seed = dex.static_field_values(f"{_APP}StringSeed;")
    event_constants = dex.static_field_values(f"{_APP}GameEvent;")
    global_static = dex.static_field_values(f"{_APP}GlobalVar;")

    prices = _recover_shop_prices(dex)
    progress_fields = _recover_shop_progress_fields(dex)
    shop_items: list[dict[str, object]] = []
    for slot in range(16):
        if slot < 6:
            name = string_seed[f"b_{slot + 1}"]
            description = string_seed[f"bd_{slot + 1}"]
        else:
            name = string_seed[f"i_{slot:X}"]
            description = string_seed[f"id_{slot - 6}"]
        item: dict[str, object] = {
            "slot": slot,
            "name": name,
            "description": description,
            "price": prices[slot],
            "progress_field": progress_fields[slot],
            "one_time": True,
        }
        if slot == 6:
            item["equip_rod"] = 1
        elif slot == 7:
            item["equip_rod"] = 2
        shop_items.append(item)

    catalog_fields = _recover_catalog_field_order(dex)
    catalog_entries = []
    for cursor, fish_field in enumerate(catalog_fields):
        suffix = fish_field.removeprefix("fish")
        catalog_entries.append({
            "cursor": cursor,
            "fish_field": fish_field,
            "number": int(suffix, 16) + 1,
            "name": string_seed[f"f_{suffix}"],
            "description": string_seed[f"fd_{suffix}"],
        })

    save_order = _recover_save_field_order(dex)
    defaults = _recover_load_defaults(dex)
    default_money = defaults["moneyC"] * 100 + defaults["moneyD"] * 10 + defaults["moneyU"]

    return {
        "origin": {"apk_sha256": CANONICAL_APK_SHA256, "member": "classes.dex"},
        "evidence": {
            "methods": {label: proof["offset"] for label, proof in proofs.items()},
            "code_proofs": proofs,
        },
        "shop": {
            "prices": prices,
            "items": shop_items,
        },
        "catalog": {
            "entries": catalog_entries,
            "completion_requires_all_44": True,
            "completion_event": 2,
        },
        "options": {
            "sound_default": defaults["sound"],
            "sound_values": [0, 1],
            "sound_labels": {"0": string_seed["s_04"], "1": string_seed["s_03"]},
            "image_default": defaults["image"],
            "image_labels": {"0": string_seed["s_06"], "1": string_seed["s_05"], "2": string_seed["s_07"]},
            "image_touch_cycle": [1, 2, 1],
            "save_file_touch_present_but_unused_in_update": True,
        },
        "events": {
            "constants": event_constants,
            "prologue": {
                "event": int(event_constants["BEGIN"]),
                "text": string_seed["s_0E"],
                "sets_prologue": 1,
                "next_state": "Map",
            },
            "ending": {
                "event": int(event_constants["END"]),
                "text": string_seed["s_11"],
                "completed_event": int(event_constants["NULL"]),
                "next_state": "Map",
            },
        },
        "save": {
            "file_name": global_static["fileName"],
            "field_order": save_order,
            "defaults": defaults,
            "default_money": default_money,
        },
    }


def recover_m4_from_apk(apk_path: Path) -> dict[str, object]:
    errors = validate_reference(apk_path, ROOT / "reference" / "apk_inventory.tsv")
    if errors:
        raise ValueError("reference APK validation failed: " + "; ".join(errors))
    with zipfile.ZipFile(apk_path, "r") as archive:
        dex_bytes = archive.read("classes.dex")
    return recover_m4(DexFile(dex_bytes))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recover M4 progression content from the canonical APK")
    parser.add_argument("apk", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)

    facts = recover_m4_from_apk(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
