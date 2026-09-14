from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_save_storage_uses_butano_sram_and_codec():
    header = (ROOT / "include/save_storage.h").read_text()
    source = (ROOT / "src/save_storage.cpp").read_text()
    assert "class SaveStorage" in header
    assert '#include "bn_sram.h"' in source
    assert "bn::sram::read" in source
    assert "bn::sram::write" in source
    assert "decode_save" in source
    assert "encode_save" in source


def test_app_loads_before_first_scene_and_revision_gates_saves():
    header = (ROOT / "include/app.h").read_text()
    source = (ROOT / "src/app.cpp").read_text()
    assert '#include "save_storage.h"' in header or '#include "save_storage.h"' in source
    assert "SaveStorage::load()" in source
    assert "progress_revision()" in source
    assert "SaveStorage::save" in source
    assert "_saved_progress_revision" in header
    assert source.index("SaveStorage::load()") < source.index("_sync_scene()")
