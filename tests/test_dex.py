from __future__ import annotations

import pytest

from tools.dex import DexFile


def test_reference_dex_header_counts(reference_dex: bytes):
    dex = DexFile(reference_dex)
    assert dex.string_ids_size == 1039
    assert dex.method_ids_size == 253
    assert dex.class_defs_size == 29


def test_reference_dex_exposes_gameplay_classes(reference_dex: bytes):
    dex = DexFile(reference_dex)
    classes = dex.class_descriptors()
    assert "Lcom/fishermanshorizon/app/GameFishing;" in classes
    assert "Lcom/fishermanshorizon/app/GlobalVar;" in classes
    assert len(classes) == 29


def test_reference_dex_exposes_gameplay_methods(reference_dex: bytes):
    dex = DexFile(reference_dex)
    names = {(method.class_descriptor, method.name) for method in dex.methods()}
    assert ("Lcom/fishermanshorizon/app/GameFishing;", "stateFishInLine") in names
    assert ("Lcom/fishermanshorizon/app/GlobalVar;", "saveData") in names


def test_reference_dex_builds_method_prototypes(reference_dex: bytes):
    dex = DexFile(reference_dex)
    methods = [method for method in dex.methods() if method.name == "saveData"]
    assert methods
    assert all(method.prototype.startswith("(") and ")" in method.prototype for method in methods)


def test_dex_rejects_non_dex_bytes():
    with pytest.raises(ValueError, match="DEX magic"):
        DexFile(b"not a dex")


def test_reference_dex_decodes_static_field_values(reference_dex: bytes):
    dex = DexFile(reference_dex)

    strings = dex.static_field_values("Lcom/fishermanshorizon/app/StringSeed;")
    assert strings["b_0"] == "Worm"
    assert strings["f_2B"] == "???"
    assert strings["s_0E"].startswith("Hya! I<m Cecil!")
    assert len(strings) == 146

    event = dex.static_field_values("Lcom/fishermanshorizon/app/GameEvent;")
    assert event == {"BEGIN": 1, "END": 2, "NULL": 3}

    global_values = dex.static_field_values("Lcom/fishermanshorizon/app/GlobalVar;")
    assert global_values["fileName"] == "horizon.fish"
