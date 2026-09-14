from pathlib import Path
import shutil


def test_visible_background_pixels_match_canonical_apk(reference_apk: Path):
    from tools.m5_validation import validate_visual_parity

    assert validate_visual_parity(reference_apk, Path("graphics")) == []


def test_visual_parity_detects_a_changed_visible_pixel(reference_apk: Path, tmp_path: Path):
    from tools.m5_validation import validate_visual_parity

    graphics = tmp_path / "graphics"
    graphics.mkdir()
    for stem in (
        "title_anim", "map", "fishing_area_crystal", "fishing_area_pier",
        "fishing_area_river", "fishing_area_ocean", "fishing_area_cave",
        "m4_shop", "m4_catalog_anim", "m4_options_anim", "m4_event_anim",
    ):
        shutil.copy2(Path("graphics") / f"{stem}.bmp", graphics / f"{stem}.bmp")

    path = graphics / "map.bmp"
    data = bytearray(path.read_bytes())
    pixel_offset = int.from_bytes(data[10:14], "little")
    width = int.from_bytes(data[18:22], "little", signed=True)
    height = int.from_bytes(data[22:26], "little", signed=True)
    row_stride = (width + 3) & ~3
    x, y = 8 + 120, 48 + 80
    raw_y = height - 1 - y
    data[pixel_offset + raw_y * row_stride + x] ^= 1
    path.write_bytes(data)
    assert validate_visual_parity(reference_apk, graphics)
