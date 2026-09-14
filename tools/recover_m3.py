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
from tools.recover_m2 import recover_m2
from tools.reference_apk import CANONICAL_APK_SHA256, validate_reference

_APP = "Lcom/fishermanshorizon/app/"

_METHOD_PROOFS = {
    "FishingArea.loadArea": ("FishingArea", "loadArea", 0x6784, 926, "31ed268e54d4c899c7edeb600e68e8e9fb093e9db0f03568001e12973fb0df3e"),
    "FishingArea.lurePool": ("FishingArea", "lurePool", 0x6ED0, 440, "ee35cdd08133323c276832519c86259a878aa361d816c3e5f950935b07181c12"),
    "GameFishing.checkNextBait": ("GameFishing", "checkNextBait", 0x9280, 203, "41e3f89b858c975eb4917cc9907a4b78f91b50334c29df517b40013abb4b6299"),
    "GameFishing.setEquipedBait": ("GameFishing", "setEquipedBait", 0x9964, 64, "756e0196e31c13bb73d46ab065da4a3bd1e21aacc6189dee12ca5c4e8715a462"),
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


def _signed8(value: int) -> int:
    return value - 256 if value & 0x80 else value


def _signed16(value: int) -> int:
    return value - 65536 if value & 0x8000 else value


def _extract_area_constructors(dex: DexFile) -> tuple[list[str], list[list[dict[str, object]]]]:
    code = dex.method_code(f"{_APP}FishingArea;", "loadArea").code_units
    strings = dex.strings()
    fields = dex.fields()
    methods = dex.methods()

    registers: dict[int, object] = {}
    backgrounds: list[str] = []
    areas: list[list[dict[str, object]]] = []
    current_area: list[dict[str, object]] | None = None
    pc = 0

    while pc < len(code):
        unit = code[pc]
        opcode = unit & 0xFF

        if opcode == 0x12:  # const/4 vA, #+B
            register = (unit >> 8) & 0xF
            registers[register] = _signed4((unit >> 12) & 0xF)
            pc += 1
        elif opcode == 0x13:  # const/16 vAA, #+BBBB
            register = (unit >> 8) & 0xFF
            registers[register] = _signed16(code[pc + 1])
            pc += 2
        elif opcode == 0x1A:  # const-string vAA, string@BBBB
            register = (unit >> 8) & 0xFF
            registers[register] = strings[code[pc + 1]]
            pc += 2
        elif opcode == 0x22:  # new-instance vAA, type@BBBB
            register = (unit >> 8) & 0xFF
            registers[register] = ("new-instance", code[pc + 1])
            pc += 2
        elif opcode == 0x60:  # sget vAA, field@BBBB
            pc += 2
        elif opcode == 0x33:  # if-ne vA, vB, +CCCC
            pc += 2
        elif opcode == 0x71:  # invoke-static {vC...}, meth@BBBB
            count = (unit >> 12) & 0xF
            method = methods[code[pc + 1]]
            reg_word = code[pc + 2]
            first_register = reg_word & 0xF
            if method.class_descriptor == f"{_APP}GraphicLoader;" and method.name == "loadBackground":
                if count != 1:
                    raise ValueError("unexpected GraphicLoader.loadBackground argument count")
                background = registers.get(first_register)
                if not isinstance(background, str):
                    raise ValueError("background path was not loaded from a string constant")
                backgrounds.append(background)
                current_area = []
                areas.append(current_area)
            pc += 3
        elif opcode == 0x76:  # invoke-direct/range {vCCCC..}, meth@BBBB
            count = (unit >> 8) & 0xFF
            method = methods[code[pc + 1]]
            first_register = code[pc + 2]
            if method.class_descriptor == f"{_APP}Fish;" and method.name == "<init>":
                if count != 9 or current_area is None:
                    raise ValueError("unexpected Fish constructor placement")
                args = [registers.get(first_register + index) for index in range(1, count)]
                if len(args) != 8 or not isinstance(args[0], str) or not all(isinstance(value, int) for value in args[1:]):
                    raise ValueError("Fish constructor arguments were not constant-loaded as expected")
                next_pc = pc + 3
                if next_pc + 1 >= len(code) or (code[next_pc] & 0xFF) != 0x69:
                    raise ValueError("Fish constructor is not followed by sput-object")
                field = fields[code[next_pc + 1]]
                if field.class_descriptor != f"{_APP}FishingArea;" or field.type_descriptor != f"{_APP}Fish;":
                    raise ValueError("Fish constructor stored into unexpected field")
                current_area.append({
                    "field": field.name,
                    "name": args[0],
                    "number": args[1],
                    "difficulty": args[2],
                    "bait": args[3],
                    "movement": args[4],
                    "distance": args[5],
                    "sprite": args[6],
                    "reward": args[7],
                })
                pc = next_pc + 2
            else:
                pc += 3
        elif opcode == 0x69:  # sput-object handled with constructor when relevant
            pc += 2
        elif opcode == 0x0E:  # return-void
            pc += 1
        else:
            raise ValueError(f"unexpected FishingArea.loadArea opcode {opcode:#x} at code unit {pc:#x}")

    if len(backgrounds) != 5 or len(areas) != 5 or any(len(area) != 9 for area in areas):
        raise ValueError(f"unexpected fishing area layout: backgrounds={len(backgrounds)}, sizes={[len(area) for area in areas]}")
    return backgrounds, areas


def _lure_field_for(dex: DexFile, pool: int, roll: int) -> str | None:
    code = dex.method_code(f"{_APP}FishingArea;", "lurePool").code_units
    fields = dex.fields()
    methods = dex.methods()
    registers: list[object] = [0] * 7
    registers[6] = roll  # one static int argument; p0 aliases v6 in this method
    pc = 0
    selected_field: str | None = None

    for _ in range(600):
        if pc < 0 or pc >= len(code):
            raise ValueError("FishingArea.lurePool control flow escaped code item")
        unit = code[pc]
        opcode = unit & 0xFF

        if opcode == 0x12:  # const/4
            register = (unit >> 8) & 0xF
            registers[register] = _signed4((unit >> 12) & 0xF)
            pc += 1
        elif opcode == 0x13:  # const/16
            register = (unit >> 8) & 0xFF
            registers[register] = _signed16(code[pc + 1])
            pc += 2
        elif opcode == 0x60:  # sget int
            register = (unit >> 8) & 0xFF
            field = fields[code[pc + 1]]
            if field.class_descriptor != f"{_APP}FishingArea;":
                raise ValueError("unexpected sget owner in lurePool")
            if field.name == "pool":
                registers[register] = pool
            elif field.name == "randomLure":
                registers[register] = roll
            else:
                raise ValueError(f"unexpected int field in lurePool: {field.name}")
            pc += 2
        elif opcode == 0x62:  # sget-object
            register = (unit >> 8) & 0xFF
            field = fields[code[pc + 1]]
            if field.class_descriptor != f"{_APP}FishingArea;" or field.type_descriptor != f"{_APP}Fish;":
                raise ValueError("unexpected object field in lurePool")
            registers[register] = field.name
            pc += 2
        elif opcode == 0x33:  # if-ne vA, vB, +CCCC
            register_a = (unit >> 8) & 0xF
            register_b = (unit >> 12) & 0xF
            offset = _signed16(code[pc + 1])
            pc = pc + offset if registers[register_a] != registers[register_b] else pc + 2
        elif opcode == 0x6E:  # invoke-virtual {vC}, Fish.lure
            method = methods[code[pc + 1]]
            register_word = code[pc + 2]
            register_c = register_word & 0xF
            if method.class_descriptor != f"{_APP}Fish;" or method.name != "lure":
                raise ValueError("unexpected virtual invocation in lurePool")
            value = registers[register_c]
            if not isinstance(value, str):
                raise ValueError("Fish.lure receiver was not a recovered field")
            selected_field = value
            pc += 3
        elif opcode == 0x28:  # goto +AA
            pc += _signed8((unit >> 8) & 0xFF)
        elif opcode == 0x29:  # goto/16 +AAAA
            pc += _signed16(code[pc + 1])
        elif opcode == 0x0E:  # return-void
            return selected_field
        else:
            raise ValueError(f"unexpected FishingArea.lurePool opcode {opcode:#x} at code unit {pc:#x}")

    raise ValueError("FishingArea.lurePool interpreter exceeded step budget")



def _recover_game_fishing_audio(dex: DexFile) -> dict[str, object]:
    methods = dex.methods()
    fields = dex.fields()
    strings = dex.strings()
    load_se_index = next(
        index for index, method in enumerate(methods)
        if method.class_descriptor == f"{_APP}SoundEngine;" and method.name == "loadSE"
    )
    code = dex.method_code(f"{_APP}GameFishing;", "loadAssets").code_units
    channels: list[dict[str, object]] = []

    for pc in range(len(code) - 2):
        unit = code[pc]
        if (unit & 0xFF) != 0x71 or code[pc + 1] != load_se_index:
            continue
        count = (unit >> 12) & 0xF
        register_word = code[pc + 2]
        registers = [
            register_word & 0xF,
            (register_word >> 4) & 0xF,
            (register_word >> 8) & 0xF,
            (register_word >> 12) & 0xF,
            (unit >> 8) & 0xF,
        ][:count]
        if len(registers) != 2:
            raise ValueError("unexpected SoundEngine.loadSE register count")
        string_reg, channel_reg = registers
        asset: str | None = None
        channel: int | None = None
        for cursor in range(pc - 1, max(-1, pc - 6), -1):
            op = code[cursor] & 0xFF
            reg = (code[cursor] >> 8) & 0xFF
            if op == 0x1A and reg == string_reg and cursor + 1 < pc:
                asset = strings[code[cursor + 1]]
            elif op == 0x12 and ((code[cursor] >> 8) & 0xF) == channel_reg:
                literal = (code[cursor] >> 12) & 0xF
                channel = literal - 16 if literal & 0x8 else literal
            elif op == 0x13 and reg == channel_reg and cursor + 1 < pc:
                literal = code[cursor + 1]
                channel = literal - 65536 if literal & 0x8000 else literal
        if asset is None or channel is None:
            raise ValueError("could not recover GameFishing.loadSE constant arguments")
        channels.append({"channel": channel, "asset": asset})

    channels.sort(key=lambda item: int(item["channel"]))
    if [item["channel"] for item in channels] != list(range(2, 10)):
        raise ValueError(f"unexpected GameFishing SE channels: {channels}")
    for index, item in enumerate(channels):
        item["flag"] = f"playSE{index}"
    channels = [
        {"flag": item["flag"], "channel": item["channel"], "asset": item["asset"]}
        for item in channels
    ]

    state_flags: dict[str, list[str]] = {}
    for state_name in (
        "stateStand", "stateThrow", "stateBaitInWater", "stateFishInLine",
        "stateFishCatch", "stateLineBreak", "stateReward",
    ):
        state_code = dex.method_code(f"{_APP}GameFishing;", state_name).code_units
        flags: set[str] = set()
        for pc in range(len(state_code) - 1):
            if (state_code[pc] & 0xFF) != 0x6A:  # sput-boolean
                continue
            field_index = state_code[pc + 1]
            if field_index >= len(fields):
                continue
            field = fields[field_index]
            if field.class_descriptor == f"{_APP}SoundEngine;" and field.name.startswith("playSE"):
                flags.add(field.name)
        state_flags[state_name] = sorted(flags, key=lambda value: int(value[6:]))

    return {"channels": channels, "state_flags": state_flags}

def recover_m3(dex: DexFile) -> dict[str, object]:
    proofs = {label: _method_proof(dex, label) for label in _METHOD_PROOFS}
    backgrounds, constructor_areas = _extract_area_constructors(dex)
    m2 = recover_m2(dex)

    areas = []
    for pool_index, (background, constructors) in enumerate(zip(backgrounds, constructor_areas), start=1):
        by_field = {fish["field"]: fish for fish in constructors}
        mapping: dict[str, str | None] = {"0": None}
        ordered_fish = []
        for roll in range(1, 10):
            field_name = _lure_field_for(dex, pool_index, roll)
            if field_name is None or field_name not in by_field:
                raise ValueError(f"pool {pool_index} roll {roll} did not resolve to a constructed Fish")
            fish = by_field[field_name]
            mapping[str(roll)] = str(fish["name"])
            ordered_fish.append(fish)
        if {fish["field"] for fish in ordered_fish} != set(by_field):
            raise ValueError(f"pool {pool_index} lure mapping does not cover its constructor set")
        areas.append({
            "pool": pool_index,
            "background": background,
            "random_roll_to_fish": mapping,
            "fish": ordered_fish,
        })

    unique_numbers = {fish["number"] for area in areas for fish in area["fish"]}
    if len(unique_numbers) != 44:
        raise ValueError(f"expected 44 unique catalog fish numbers, got {len(unique_numbers)}")

    return {
        "origin": {"apk_sha256": CANONICAL_APK_SHA256, "member": "classes.dex"},
        "evidence": {
            "methods": {label: proof["offset"] for label, proof in proofs.items()},
            "code_proofs": proofs,
        },
        "areas": areas,
        "unique_catalog_fish": 44,
        "constructor_instances": 45,
        "rods": {"strengths": m2["fishing"]["rod_strengths"]},
        "bait": {
            "types": m2["bait"]["types"],
            "base_sprites": m2["bait"]["base_sprites"],
            "movement": m2["bait"]["movement"],
        },
        "audio": _recover_game_fishing_audio(dex),
    }


def recover_m3_from_apk(apk_path: Path) -> dict[str, object]:
    errors = validate_reference(apk_path, ROOT / "reference" / "apk_inventory.tsv")
    if errors:
        raise ValueError("reference APK validation failed: " + "; ".join(errors))
    with zipfile.ZipFile(apk_path, "r") as archive:
        dex_bytes = archive.read("classes.dex")
    return recover_m3(DexFile(dex_bytes))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recover complete M3 fishing content from the canonical APK")
    parser.add_argument("apk", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)

    facts = recover_m3_from_apk(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
