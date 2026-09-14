from __future__ import annotations

import pytest

from tools.dex import DexFile


def test_reference_dex_exposes_game_title_update_code(reference_dex: bytes):
    dex = DexFile(reference_dex)
    code = dex.method_code("Lcom/fishermanshorizon/app/GameTitle;", "update")
    assert code.registers_size == 3
    assert code.ins_size == 0
    assert code.outs_size == 1
    assert len(code.code_units) == 43
    assert code.code_offset == 0xCA28


def test_reference_dex_exposes_fields(reference_dex: bytes):
    dex = DexFile(reference_dex)
    fields = {
        (field.class_descriptor, field.name, field.type_descriptor)
        for field in dex.fields()
    }
    assert ("Lcom/fishermanshorizon/app/GameTitle;", "pointer", "I") in fields
    assert ("Lcom/fishermanshorizon/app/GameMap;", "crystalLakeTouchZone", "Lcom/fishermanshorizon/app/TouchZone;") in fields
    assert len(dex.fields()) == 650


def test_reference_dex_exposes_encoded_method_identity(reference_dex: bytes):
    dex = DexFile(reference_dex)
    encoded = [
        method
        for method in dex.encoded_methods()
        if method.method.class_descriptor == "Lcom/fishermanshorizon/app/GameTitle;"
        and method.method.name == "seaImage"
    ]
    assert len(encoded) == 1
    assert encoded[0].code_offset == 0xC9AC
    assert encoded[0].access_flags & 0x8  # static


def test_method_code_rejects_ambiguous_or_missing_method(reference_dex: bytes):
    dex = DexFile(reference_dex)
    with pytest.raises(KeyError, match="method not found"):
        dex.method_code("Lcom/fishermanshorizon/app/GameTitle;", "notARealMethod")
