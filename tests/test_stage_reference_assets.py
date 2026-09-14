from __future__ import annotations

import json
import struct
from pathlib import Path

from scripts.stage_reference_assets import read_apk_member, stage_title
from tools.png_asset import decode_rgba_png


def _read_bmp(path: Path):
    data = path.read_bytes()
    assert data[:2] == b"BM"
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    assert dib_size == 40
    width = struct.unpack_from("<i", data, 18)[0]
    height = struct.unpack_from("<i", data, 22)[0]
    bpp = struct.unpack_from("<H", data, 28)[0]
    colors_used = struct.unpack_from("<I", data, 46)[0]
    assert bpp == 8
    assert colors_used == 256
    palette = []
    palette_offset = 14 + dib_size
    for index in range(256):
        blue, green, red, _ = struct.unpack_from("<BBBB", data, palette_offset + index * 4)
        palette.append((red, green, blue))
    row_stride = (width + 3) & ~3

    def index_at(x: int, y: int) -> int:
        row_from_bottom = height - 1 - y
        return data[pixel_offset + row_from_bottom * row_stride + x]

    return width, height, palette, index_at


def test_reference_title_is_native_gba_viewport(reference_apk: Path):
    png = read_apk_member(reference_apk, "assets/graphic/background/title.png")
    image = decode_rgba_png(png)
    assert image.width == 240
    assert image.height == 160
    assert image.rgba_at(0, 0) == (80, 156, 204, 255)
    assert image.rgba_at(239, 159) == (62, 29, 112, 255)


def test_stage_title_center_pads_without_rescaling(tmp_path: Path, reference_apk: Path):
    out = tmp_path / "graphics"
    stage_title(reference_apk, out)

    width, height, palette, index_at = _read_bmp(out / "title.bmp")
    assert (width, height) == (256, 256)
    assert index_at(0, 0) == 0
    assert palette[index_at(8, 48)] == (80, 156, 204)
    assert palette[index_at(247, 207)] == (62, 29, 112)
    assert palette[index_at(128, 128)] == (114, 158, 138)


def test_stage_title_writes_butano_regular_bg_metadata(tmp_path: Path, reference_apk: Path):
    out = tmp_path / "graphics"
    stage_title(reference_apk, out)
    metadata = json.loads((out / "title.json").read_text(encoding="utf-8"))
    assert metadata == {
        "type": "regular_bg",
        "bpp_mode": "bpp_8",
        "compression": "auto_no_huffman",
    }


def test_stage_m1_title_animation_uses_exact_sea_tile_crops(tmp_path: Path, reference_apk: Path):
    from scripts.stage_reference_assets import stage_m1_assets

    out = tmp_path / "graphics"
    records = stage_m1_assets(reference_apk, out)

    width, height, palette, index_at = _read_bmp(out / "title_anim.bmp")
    assert (width, height) == (256, 256 * 3)

    # Original tile 112 starts at seaTiles (0, 0). Pixel (6, 0) is a white crest.
    assert palette[index_at(8 + 6, 48 + 128)] == (235, 255, 227)
    # Tile 113 starts at seaTiles (0, 4); the same source position is plain water.
    assert palette[index_at(8 + 6, 256 + 48 + 128)] == (80, 156, 204)
    # Tile 114 starts at seaTiles (0, 8). Its second row differs from tile 113.
    assert palette[index_at(8 + 4, 2 * 256 + 48 + 129)] == (58, 77, 186)

    metadata = json.loads((out / "title_anim.json").read_text(encoding="utf-8"))
    assert metadata == {
        "type": "regular_bg",
        "height": 256,
        "bpp_mode": "bpp_8",
        "compression": "auto_no_huffman",
    }
    assert {record["output_path"] for record in records} == {
        "graphics/title_anim.bmp",
        "graphics/map.bmp",
        "graphics/map_spots.bmp",
        "graphics/crystal_lake.bmp",
    }


def test_stage_m1_map_and_crystal_lake_preserve_native_viewport(tmp_path: Path, reference_apk: Path):
    from scripts.stage_reference_assets import stage_m1_assets

    out = tmp_path / "graphics"
    stage_m1_assets(reference_apk, out)

    map_width, map_height, map_palette, map_index_at = _read_bmp(out / "map.bmp")
    assert (map_width, map_height) == (256, 256)
    assert map_index_at(0, 0) == 0
    assert map_palette[map_index_at(8, 48)] == (62, 29, 112)
    assert map_palette[map_index_at(247, 207)] == (62, 29, 112)

    lake_width, lake_height, lake_palette, lake_index_at = _read_bmp(out / "crystal_lake.bmp")
    assert (lake_width, lake_height) == (256, 256)
    assert lake_index_at(0, 0) == 0
    assert lake_palette[lake_index_at(8, 48)] == (80, 156, 204)
    assert lake_palette[lake_index_at(247, 207)] == (62, 29, 112)

    for stem in ("map", "crystal_lake"):
        metadata = json.loads((out / f"{stem}.json").read_text(encoding="utf-8"))
        assert metadata == {
            "type": "regular_bg",
            "bpp_mode": "bpp_8",
            "compression": "auto_no_huffman",
        }


def test_stage_m1_map_spots_uses_recovered_tiles_100_through_103(tmp_path: Path, reference_apk: Path):
    from scripts.stage_reference_assets import stage_m1_assets

    out = tmp_path / "graphics"
    stage_m1_assets(reference_apk, out)

    width, height, palette, index_at = _read_bmp(out / "map_spots.bmp")
    assert (width, height) == (32, 16)
    # tile 100 source crop = (96,48)..(103,63)
    assert palette[index_at(0, 0)] == (25, 5, 36)
    # tile 101 source crop = (104,48)..(111,63)
    assert index_at(8, 0) == 0
    assert palette[index_at(8 + 3, 7)] == (235, 255, 227)
    # tile 102 source crop = (112,48)..(119,63)
    assert palette[index_at(16 + 3, 7)] == (235, 255, 227)
    # tile 103 source crop = (120,48)..(127,63)
    assert index_at(24, 0) == 0
    assert palette[index_at(24 + 3, 7)] == (235, 255, 227)

    metadata = json.loads((out / "map_spots.json").read_text(encoding="utf-8"))
    assert metadata == {
        "type": "sprite",
        "width": 8,
        "height": 16,
        "bpp_mode": "bpp_8",
        "compression": "auto_no_huffman",
    }


def _first_opaque_pixel(image, x0: int, y0: int, width: int, height: int):
    for y in range(height):
        for x in range(width):
            rgba = image.rgba_at(x0 + x, y0 + y)
            if rgba[3] == 255:
                return x, y, rgba[:3]
    raise AssertionError(f"no opaque pixel in crop {(x0, y0, width, height)}")


def test_stage_m2_character_and_rod_frames_preserve_exact_source_crops(tmp_path: Path, reference_apk: Path):
    from scripts.stage_reference_assets import stage_m2_assets

    out = tmp_path / "graphics"
    records = stage_m2_assets(reference_apk, out)
    outputs = {record["output_path"] for record in records}
    assert {
        "graphics/fishing_char.bmp",
        "graphics/fishing_rod_left.bmp",
        "graphics/fishing_rod_right.bmp",
    }.issubset(outputs)

    char_source = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/charSpriteSheet.png"))
    cw, ch, cpal, cidx = _read_bmp(out / "fishing_char.bmp")
    assert (cw, ch) == (32 * 16, 64)
    for frame, source_x, source_y in ((0, 0, 0), (7, 224, 0), (8, 0, 40), (15, 224, 40)):
        dx, dy, rgb = _first_opaque_pixel(char_source, source_x, source_y, 32, 40)
        assert cpal[cidx(frame * 32 + dx, dy)] == rgb
        assert cidx(frame * 32, 63) == 0

    rod_source = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/stickSpriteSheet.png"))
    lw, lh, lpal, lidx = _read_bmp(out / "fishing_rod_left.bmp")
    rw, rh, rpal, ridx = _read_bmp(out / "fishing_rod_right.bmp")
    assert (lw, lh) == (64 * 12, 64)
    assert (rw, rh) == (16 * 24, 32)
    for frame, source_x, source_y in ((0, 0, 0), (4, 0, 64), (11, 240, 128)):
        left_x = source_x
        dx, dy, rgb = _first_opaque_pixel(rod_source, left_x, source_y, 64, 64)
        assert lpal[lidx(frame * 64 + dx, dy)] == rgb
        right_x = source_x + 64
        try:
            dx, dy, rgb = _first_opaque_pixel(rod_source, right_x, source_y, 16, 64)
        except AssertionError:
            continue
        piece = dy // 32
        assert rpal[ridx((frame * 2 + piece) * 16 + dx, dy % 32)] == rgb

    assert json.loads((out / "fishing_char.json").read_text()) == {
        "type": "sprite", "width": 32, "height": 64,
        "bpp_mode": "bpp_4", "compression": "auto_no_huffman",
    }
    assert json.loads((out / "fishing_rod_left.json").read_text()) == {
        "type": "sprite", "width": 64, "height": 64,
        "bpp_mode": "bpp_4", "compression": "auto_no_huffman",
    }
    assert json.loads((out / "fishing_rod_right.json").read_text()) == {
        "type": "sprite", "width": 16, "height": 32,
        "bpp_mode": "bpp_4", "compression": "auto_no_huffman",
    }


def test_stage_m2_bait_and_fish_atlases_are_4bpp_safe_and_keep_source_mapping(tmp_path: Path, reference_apk: Path):
    from scripts.stage_reference_assets import stage_m2_assets

    out = tmp_path / "graphics"
    stage_m2_assets(reference_apk, out)
    mapping = json.loads((out / "fishing_sprite_map.json").read_text(encoding="utf-8"))
    assert mapping == {
        "11": ["fishing_bait", 0], "12": ["fishing_bait", 1],
        "75": ["fishing_bait", 2], "76": ["fishing_bait", 3],
        "13": ["fishing_bait", 4], "14": ["fishing_bait", 5],
        "77": ["fishing_bait", 6], "78": ["fishing_bait", 7],
        "88": ["fishing_bait", 8], "89": ["fishing_bait", 9],
        "90": ["fishing_bait", 10], "91": ["fishing_bait", 11],
        "92": ["fishing_bait", 12], "93": ["fishing_bait", 13],
        "124": ["fishing_bait", 14],
        "119": ["fishing_fish_a", 0], "122": ["fishing_fish_a", 1],
        "129": ["fishing_fish_a", 2], "131": ["fishing_fish_a", 3],
        "137": ["fishing_fish_b", 0], "142": ["fishing_fish_b", 1],
        "144": ["fishing_fish_b", 2], "150": ["fishing_fish_b", 3],
        "160": ["fishing_fish_b", 4],
    }

    tiles = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/tiles.png"))
    width, height, palette, index_at = _read_bmp(out / "fishing_bait.bmp")
    assert (width, height) == (16 * 15, 32)

    # Regular 8x8 source tile 11.
    dx, dy, rgb = _first_opaque_pixel(tiles, 88, 0, 8, 8)
    assert palette[index_at(dx, dy)] == rgb

    # Fish tile 160 is the unusual 16x24 crop at (48,152), now in fish bank B.
    width, height, palette, index_at = _read_bmp(out / "fishing_fish_b.bmp")
    assert (width, height) == (16 * 5, 32)
    frame160 = mapping["160"][1]
    dx, dy, rgb = _first_opaque_pixel(tiles, 48, 152, 16, 24)
    assert palette[index_at(frame160 * 16 + dx, dy)] == rgb
    assert index_at(frame160 * 16, 31) == 0

    for stem in ("fishing_bait", "fishing_fish_a", "fishing_fish_b"):
        metadata = json.loads((out / f"{stem}.json").read_text())
        assert metadata == {
            "type": "sprite", "width": 16, "height": 32,
            "bpp_mode": "bpp_4", "compression": "auto_no_huffman",
        }
        _w, _h, _palette, frame_index_at = _read_bmp(out / f"{stem}.bmp")
        assert len({frame_index_at(x, y) for y in range(_h) for x in range(_w)}) <= 16


def test_stage_m2_water_splash_coin_hud_and_meter_use_recovered_tiles(tmp_path: Path, reference_apk: Path):
    from scripts.stage_reference_assets import stage_m2_assets

    out = tmp_path / "graphics"
    stage_m2_assets(reference_apk, out)

    sea = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/seaTiles.png"))
    lake = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/background/crystalLake.png"))
    sw, sh, spal, sidx = _read_bmp(out / "fishing_lake.bmp")
    assert (sw, sh) == (256, 256 * 3)
    # Native background is preserved above the animated water strip.
    assert spal[sidx(8 + 20, 48 + 40)] == lake.rgba_at(20, 40)[:3]
    # GameFishing draws the same 4px sea frames over source y=128.
    assert spal[sidx(8 + 6, 48 + 128)] == sea.rgba_at(6, 0)[:3]
    assert spal[sidx(8 + 6, 256 + 48 + 128)] == sea.rgba_at(6, 4)[:3]
    assert spal[sidx(8 + 4, 2 * 256 + 48 + 129)] == sea.rgba_at(4, 9)[:3]
    assert json.loads((out / "fishing_lake.json").read_text()) == {
        "type": "regular_bg", "height": 256,
        "bpp_mode": "bpp_8", "compression": "auto_no_huffman",
    }

    dims = {
        "fishing_splash.bmp": (16 * 6, 8),
        "fishing_coin.bmp": (8 * 3, 8),
        "fishing_hud.bmp": (16 * 2, 16),
        "fishing_meter.bmp": (8, 8),
    }
    for name, expected in dims.items():
        width, height, _palette, _idx = _read_bmp(out / name)
        assert (width, height) == expected

    for stem, width, height in (
        ("fishing_splash", 16, 8),
        ("fishing_coin", 8, 8),
        ("fishing_hud", 16, 16),
        ("fishing_meter", 8, 8),
    ):
        assert json.loads((out / f"{stem}.json").read_text()) == {
            "type": "sprite", "width": width, "height": height,
            "bpp_mode": "bpp_4", "compression": "auto_no_huffman",
        }

    tiles = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/tiles.png"))
    # splash 104=(0,64,16,8), coin 116=(96,64,8,8), HUD 97=(16,48,16,16), meter 10=(80,0,8,8)
    for bmp, sx, sy, w, h in (
        ("fishing_splash.bmp", 0, 64, 16, 8),
        ("fishing_coin.bmp", 96, 64, 8, 8),
        ("fishing_hud.bmp", 16, 48, 16, 16),
        ("fishing_meter.bmp", 80, 0, 8, 8),
    ):
        _, _, palette, index_at = _read_bmp(out / bmp)
        dx, dy, rgb = _first_opaque_pixel(tiles, sx, sy, w, h)
        assert palette[index_at(dx, dy)] == rgb


def test_stage_m2_line_dot_uses_original_android_paint_color(tmp_path: Path, reference_apk: Path):
    from scripts.stage_reference_assets import stage_m2_assets

    out = tmp_path / "graphics"
    stage_m2_assets(reference_apk, out)
    width, height, palette, index_at = _read_bmp(out / "fishing_line_dot.bmp")
    assert (width, height) == (8, 8)
    assert palette[index_at(3, 3)] == (235, 255, 237)
    assert index_at(0, 0) == 0
    assert json.loads((out / "fishing_line_dot.json").read_text()) == {
        "type": "sprite", "width": 8, "height": 8,
        "bpp_mode": "bpp_4", "compression": "auto_no_huffman",
    }


def test_stage_m2_does_not_emit_palette_conflicting_legacy_items(tmp_path: Path, reference_apk: Path):
    from scripts.stage_reference_assets import stage_m2_assets

    out = tmp_path / "graphics"
    stage_m2_assets(reference_apk, out)
    assert not (out / "fishing_sea.bmp").exists()
    assert not (out / "fishing_bait_fish.bmp").exists()
    assert not (out / "fishing_bait_fish_map.json").exists()


def _m3_fish_source_rect(index: int) -> tuple[int, int, int, int]:
    if 110 <= index <= 111:
        return ((index - 110) * 16, 72, 16, 16)
    if 119 <= index <= 124:
        return ((index - 117) * 16, 72, 16, 16)
    if 125 <= index <= 156:
        offset = index - 125
        return ((offset % 8) * 16, 88 + (offset // 8) * 16, 16, 16)
    if 157 <= index <= 164:
        return ((index - 157) * 16, 152, 16, 24)
    raise AssertionError(f"unexpected M3 fish sprite index {index}")


def test_stage_m3_all_fishing_backgrounds_preserve_native_pixels_and_sea_frames(
    tmp_path: Path, reference_apk: Path
):
    from scripts.stage_reference_assets import stage_m3_assets

    out = tmp_path / "graphics"
    records = stage_m3_assets(reference_apk, out)
    outputs = {record["output_path"] for record in records}
    areas = (
        ("fishing_area_crystal", "assets/graphic/background/crystalLake.png"),
        ("fishing_area_pier", "assets/graphic/background/pier.png"),
        ("fishing_area_river", "assets/graphic/background/river.png"),
        ("fishing_area_ocean", "assets/graphic/background/ocean.png"),
        ("fishing_area_cave", "assets/graphic/background/cave.png"),
    )
    sea = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/seaTiles.png"))

    for stem, member in areas:
        assert f"graphics/{stem}.bmp" in outputs
        source = decode_rgba_png(read_apk_member(reference_apk, member))
        width, height, palette, index_at = _read_bmp(out / f"{stem}.bmp")
        assert (width, height) == (256, 256 * 3)
        assert index_at(0, 0) == 0
        # Pixels above the animated four-pixel strip are source-exact and unscaled.
        assert palette[index_at(8 + 20, 48 + 40)] == source.rgba_at(20, 40)[:3]
        # All three recovered GameFishing sea frames are composited at source y=128.
        assert palette[index_at(8 + 6, 48 + 128)] == sea.rgba_at(6, 0)[:3]
        assert palette[index_at(8 + 6, 256 + 48 + 128)] == sea.rgba_at(6, 4)[:3]
        assert palette[index_at(8 + 4, 2 * 256 + 48 + 129)] == sea.rgba_at(4, 9)[:3]
        assert json.loads((out / f"{stem}.json").read_text()) == {
            "type": "regular_bg", "height": 256,
            "bpp_mode": "bpp_8", "compression": "auto_no_huffman",
        }


def test_stage_m3_all_44_fish_use_exact_recovered_crops_and_4bpp_banks(
    tmp_path: Path, reference_apk: Path
):
    from scripts.stage_reference_assets import stage_m3_assets

    out = tmp_path / "graphics"
    stage_m3_assets(reference_apk, out)
    content = json.loads(Path("reference/m3_fishing_content.json").read_text(encoding="utf-8"))
    expected_sprites = sorted({fish["sprite"] for area in content["areas"] for fish in area["fish"]})
    assert len(expected_sprites) == 44

    mapping = json.loads((out / "fishing_m3_sprite_map.json").read_text(encoding="utf-8"))
    assert sorted(map(int, mapping)) == expected_sprites
    banks = sorted({entry[0] for entry in mapping.values()})
    assert banks == ["fishing_fish_m3_0", "fishing_fish_m3_1"]

    tiles = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/tiles.png"))
    for stem in banks:
        metadata = json.loads((out / f"{stem}.json").read_text())
        assert metadata == {
            "type": "sprite", "width": 16, "height": 32,
            "bpp_mode": "bpp_4", "compression": "auto_no_huffman",
        }
        width, height, _palette, index_at = _read_bmp(out / f"{stem}.bmp")
        assert height == 32
        # 4bpp has 16 palette entries total, including transparent index zero.
        assert len({index_at(x, y) for y in range(height) for x in range(width)}) <= 16

    # Every mapped sprite preserves at least one exact visible source pixel from its recovered crop.
    for sprite in expected_sprites:
        stem, frame = mapping[str(sprite)]
        sx, sy, sw, sh = _m3_fish_source_rect(sprite)
        dx, dy, rgb = _first_opaque_pixel(tiles, sx, sy, sw, sh)
        _width, _height, palette, index_at = _read_bmp(out / f"{stem}.bmp")
        assert palette[index_at(frame * 16 + dx, dy)] == rgb
        assert index_at(frame * 16, 31) == 0


def test_stage_m3_all_three_rods_are_staged_without_resampling(tmp_path: Path, reference_apk: Path):
    from scripts.stage_reference_assets import stage_m3_assets

    out = tmp_path / "graphics"
    stage_m3_assets(reference_apk, out)
    rod_source = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/stickSpriteSheet.png"))
    lw, lh, lpal, lidx = _read_bmp(out / "fishing_rods_left.bmp")
    rw, rh, rpal, ridx = _read_bmp(out / "fishing_rods_right.bmp")
    assert (lw, lh) == (64 * 36, 64)
    assert (rw, rh) == (16 * 72, 32)

    # One frame from each rod plus the last frame proves the source layout is preserved.
    for frame in (0, 12, 24, 35):
        source_x = (frame % 4) * 80
        source_y = (frame // 4) * 64
        dx, dy, rgb = _first_opaque_pixel(rod_source, source_x, source_y, 64, 64)
        assert lpal[lidx(frame * 64 + dx, dy)] == rgb
        try:
            dx, dy, rgb = _first_opaque_pixel(rod_source, source_x + 64, source_y, 16, 64)
        except AssertionError:
            continue
        piece = dy // 32
        assert rpal[ridx((frame * 2 + piece) * 16 + dx, dy % 32)] == rgb

    for stem, width in (("fishing_rods_left", 64), ("fishing_rods_right", 16)):
        expected_height = 32 if stem == "fishing_rods_right" else 64
        assert json.loads((out / f"{stem}.json").read_text()) == {
            "type": "sprite", "width": width, "height": expected_height,
            "bpp_mode": "bpp_4", "compression": "auto_no_huffman",
        }
        bw, bh, _palette, index_at = _read_bmp(out / f"{stem}.bmp")
        assert len({index_at(x, y) for y in range(bh) for x in range(bw)}) <= 16


def test_stage_m4_progression_backgrounds_and_sprites_are_exact(tmp_path: Path, reference_apk: Path):
    from scripts.stage_reference_assets import stage_m4_assets

    out = tmp_path / "graphics"
    records = stage_m4_assets(reference_apk, out)
    assert {record["output_path"] for record in records} == {
        "graphics/m4_shop.bmp",
        "graphics/m4_catalog_anim.bmp",
        "graphics/m4_options_anim.bmp",
        "graphics/m4_event_anim.bmp",
        "graphics/m4_font.bmp",
        "graphics/m4_shop_keeper.bmp",
        "graphics/m4_shop_cursor.bmp",
        "graphics/m4_catalog_cursor.bmp",
        "graphics/m4_shop_sold_out.bmp",
        "graphics/m4_event_cecil.bmp",
        *{f"graphics/fishing_char_m4_{index}.bmp" for index in range(6)},
    }

    shop = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/background/shop.png"))
    width, height, palette, index_at = _read_bmp(out / "m4_shop.bmp")
    assert (width, height) == (256, 256)
    assert palette[index_at(8 + 10, 48 + 10)] == shop.rgba_at(10, 10)[:3]

    sea = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/seaTiles.png"))
    for stem, member in (
        ("m4_catalog_anim", "assets/graphic/background/catalog.png"),
        ("m4_options_anim", "assets/graphic/background/options.png"),
        ("m4_event_anim", "assets/graphic/background/crystalLakeNoHud.png"),
    ):
        bg = decode_rgba_png(read_apk_member(reference_apk, member))
        w, h, pal, idx = _read_bmp(out / f"{stem}.bmp")
        assert (w, h) == (256, 256 * 3)
        assert pal[idx(8 + 20, 48 + 40)] == bg.rgba_at(20, 40)[:3]
        assert pal[idx(8 + 6, 48 + 128)] == sea.rgba_at(6, 0)[:3]
        assert pal[idx(8 + 6, 256 + 48 + 128)] == sea.rgba_at(6, 4)[:3]

    tiles = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/tiles.png"))
    # Shop keeper frame 166: source (24,176) 24x24 padded to a 32x32 sprite.
    w, h, pal, idx = _read_bmp(out / "m4_shop_keeper.bmp")
    assert (w, h) == (32 * 2, 32)
    assert pal[idx(4, 4)] == tiles.rgba_at(24 + 4, 176 + 4)[:3]
    # Catalog cursor frame 164: source (112,152) 16x24 padded to 16x32.
    w, h, pal, idx = _read_bmp(out / "m4_catalog_cursor.bmp")
    assert (w, h) == (16, 32)
    assert pal[idx(4, 4)] == tiles.rgba_at(112 + 4, 152 + 4)[:3]

    # Cecil frame 177: source (24,264) 24x40 padded to 32x64.
    w, h, pal, idx = _read_bmp(out / "m4_event_cecil.bmp")
    assert (w, h) == (32 * 2, 64)
    assert pal[idx(4, 4)] == tiles.rgba_at(24 + 4, 264 + 4)[:3]

    char_source = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/charSpriteSheet.png"))
    for character in range(6):
        w, h, pal, idx = _read_bmp(out / f"fishing_char_m4_{character}.bmp")
        assert (w, h) == (32 * 16, 64)
        source_index = character * 16
        source_x = (source_index % 8) * 32
        source_y = (source_index // 8) * 40
        dx, dy, rgb = _first_opaque_pixel(char_source, source_x, source_y, 32, 40)
        assert pal[idx(dx, dy)] == rgb
        assert len({idx(x, y) for y in range(h) for x in range(w)}) <= 16

    assert json.loads((out / "m4_font.json").read_text()) == {
        "type": "sprite", "width": 8, "height": 8,
        "bpp_mode": "bpp_4", "compression": "auto_no_huffman",
    }


def test_stage_m7_intro_and_native_options_assets(tmp_path: Path, reference_apk: Path):
    from scripts.stage_reference_assets import stage_m7_assets

    out = tmp_path / "graphics"
    records = stage_m7_assets(reference_apk, out)
    assert {record["output_path"] for record in records} == {
        "graphics/m7_intro_credit.bmp",
        "graphics/m7_options_anim.bmp",
        "graphics/m7_dialog_panel.bmp",
        "graphics/m7_dialog_markers.bmp",
        "graphics/m7_dialog_dollar.bmp",
    }

    width, height, palette, index_at = _read_bmp(out / "m7_intro_credit.bmp")
    assert (width, height) == (256, 256)
    # Original GameIntro fill color and credit placement, plus Butano 8/48 centering.
    assert palette[index_at(8 + 10, 48 + 10)] == (25, 5, 36)
    # First opaque source credit pixel is local (48,0), placed at (48,48).
    assert palette[index_at(8 + 48 + 48, 48 + 48)] == (235, 255, 227)

    width, height, palette, index_at = _read_bmp(out / "m7_options_anim.bmp")
    assert (width, height) == (256, 256 * 3)
    # The removed Android image row used to be dark UI at source (80,42).
    assert palette[index_at(8 + 80, 48 + 42)] == (80, 156, 204)
    # The sound row remains intact.
    assert palette[index_at(8 + 80, 48 + 10)] != (80, 156, 204)

    tiles = decode_rgba_png(read_apk_member(reference_apk, "assets/graphic/tile/tiles.png"))
    mw, mh, mpal, midx = _read_bmp(out / "m7_dialog_markers.bmp")
    assert (mw, mh) == (32, 16)
    for frame, sx in ((0, 0), (1, 32)):
        dx, dy, rgb = _first_opaque_pixel(tiles, sx, 48, 16, 16)
        assert mpal[midx(frame * 16 + dx, dy)] == rgb

    dw, dh, dpal, didx = _read_bmp(out / "m7_dialog_dollar.bmp")
    assert (dw, dh) == (8, 8)
    dx, dy, rgb = _first_opaque_pixel(tiles, 96, 64, 8, 8)
    assert dpal[didx(dx, dy)] == rgb

    pw, ph, ppal, pidx = _read_bmp(out / "m7_dialog_panel.bmp")
    assert (pw, ph) == (128, 32)
    assert ppal[pidx(0, 0)] == (25, 5, 36)
    assert pidx(63, 23) != 0
    assert pidx(64 + 39, 23) != 0
    assert pidx(64 + 40, 23) == 0
    assert pidx(0, 24) == 0
