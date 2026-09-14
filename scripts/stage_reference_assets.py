#!/usr/bin/env python3
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.png_asset import (
    RgbaImage,
    center_rgba,
    composite_rgba,
    crop_rgba,
    place_rgba,
    decode_rgba_png,
    stack_rgba_horizontal,
    stack_rgba_vertical,
    write_centered_indexed_bmp,
    write_indexed_bmp,
)
from tools.recover_m3 import recover_m3_from_apk
from tools.reference_apk import validate_reference

TITLE_MEMBER = "assets/graphic/background/title.png"
SEA_TILES_MEMBER = "assets/graphic/tile/seaTiles.png"
MAP_MEMBER = "assets/graphic/background/map.png"
CRYSTAL_LAKE_MEMBER = "assets/graphic/background/crystalLake.png"
PIER_MEMBER = "assets/graphic/background/pier.png"
RIVER_MEMBER = "assets/graphic/background/river.png"
OCEAN_MEMBER = "assets/graphic/background/ocean.png"
CAVE_MEMBER = "assets/graphic/background/cave.png"
SHOP_MEMBER = "assets/graphic/background/shop.png"
CATALOG_MEMBER = "assets/graphic/background/catalog.png"
OPTIONS_MEMBER = "assets/graphic/background/options.png"
EVENT_MEMBER = "assets/graphic/background/crystalLakeNoHud.png"
INTRO_CREDIT_MEMBER = "assets/graphic/background/introCredit.png"
TILES_MEMBER = "assets/graphic/tile/tiles.png"
CHAR_SHEET_MEMBER = "assets/graphic/tile/charSpriteSheet.png"
STICK_SHEET_MEMBER = "assets/graphic/tile/stickSpriteSheet.png"
DEX_MEMBER = "classes.dex"

_REGULAR_BG_METADATA = {
    "type": "regular_bg",
    "bpp_mode": "bpp_8",
    "compression": "auto_no_huffman",
}

_ANIMATED_REGULAR_BG_METADATA = {
    "type": "regular_bg",
    "bpp_mode": "bpp_8",
    "height": 256,
    "tiles_compression": "auto_no_huffman",
    "palette_compression": "auto_no_huffman",
    "map_compression": "none",
}


_DRAWTEXT_FILL = (25, 5, 36, 255)
_SHOP_TEXT_FIELDS = ((126, 8, 92, 8), (24, 144, 32, 8), (193, 144, 22, 8))
_FISHING_TEXT_FIELDS = ((126, 8, 92, 8), (193, 144, 22, 8))


def _fill_rects(image: RgbaImage, rects: tuple[tuple[int, int, int, int], ...]) -> RgbaImage:
    pixels = bytearray(image.pixels)
    color = bytes(_DRAWTEXT_FILL)
    for x, y, width, height in rects:
        if x < 0 or y < 0 or x + width > image.width or y + height > image.height:
            raise ValueError("DrawText backing rectangle outside source image")
        for row in range(y, y + height):
            start = (row * image.width + x) * 4
            for column in range(width):
                pos = start + column * 4
                pixels[pos:pos + 4] = color
    return RgbaImage(image.width, image.height, bytes(pixels))


def read_apk_member(apk_path: Path, member: str) -> bytes:
    with zipfile.ZipFile(apk_path, "r") as archive:
        return archive.read(member)


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _record(
    *,
    source_member: str,
    source_bytes: bytes,
    source_width: int,
    source_height: int,
    output_path: str,
    output_file: Path,
    output_width: int,
    output_height: int,
    offset_x: int,
    offset_y: int,
) -> dict[str, object]:
    output = output_file.read_bytes()
    return {
        "source_member": source_member,
        "source_sha256": sha256(source_bytes).hexdigest(),
        "source_bytes": len(source_bytes),
        "source_width": source_width,
        "source_height": source_height,
        "output_path": output_path,
        "output_sha256": sha256(output).hexdigest(),
        "output_bytes": len(output),
        "output_width": output_width,
        "output_height": output_height,
        "offset_x": offset_x,
        "offset_y": offset_y,
    }


def stage_title(apk_path: Path, graphics_dir: Path) -> dict[str, object]:
    source = read_apk_member(apk_path, TITLE_MEMBER)
    image = decode_rgba_png(source)
    if (image.width, image.height) != (240, 160):
        raise ValueError(
            f"unexpected title dimensions: {image.width}x{image.height}, expected 240x160"
        )

    graphics_dir.mkdir(parents=True, exist_ok=True)
    bmp_path = graphics_dir / "title.bmp"
    offset_x, offset_y = write_centered_indexed_bmp(bmp_path, image)
    _write_json(graphics_dir / "title.json", _REGULAR_BG_METADATA)

    return _record(
        source_member=TITLE_MEMBER,
        source_bytes=source,
        source_width=image.width,
        source_height=image.height,
        output_path="graphics/title.bmp",
        output_file=bmp_path,
        output_width=256,
        output_height=256,
        offset_x=offset_x,
        offset_y=offset_y,
    )


def _stage_regular_bg(
    apk_path: Path,
    graphics_dir: Path,
    *,
    member: str,
    stem: str,
    drawtext_fields: tuple[tuple[int, int, int, int], ...] = (),
) -> dict[str, object]:
    source = read_apk_member(apk_path, member)
    image = decode_rgba_png(source)
    if (image.width, image.height) != (240, 160):
        raise ValueError(
            f"unexpected {stem} dimensions: {image.width}x{image.height}, expected 240x160"
        )
    if drawtext_fields:
        image = _fill_rects(image, drawtext_fields)
    bmp_path = graphics_dir / f"{stem}.bmp"
    offset_x, offset_y = write_centered_indexed_bmp(bmp_path, image)
    _write_json(graphics_dir / f"{stem}.json", _REGULAR_BG_METADATA)
    return _record(
        source_member=member,
        source_bytes=source,
        source_width=image.width,
        source_height=image.height,
        output_path=f"graphics/{stem}.bmp",
        output_file=bmp_path,
        output_width=256,
        output_height=256,
        offset_x=offset_x,
        offset_y=offset_y,
    )


def _stage_title_animation(apk_path: Path, graphics_dir: Path) -> dict[str, object]:
    title_source = read_apk_member(apk_path, TITLE_MEMBER)
    sea_source = read_apk_member(apk_path, SEA_TILES_MEMBER)
    title = decode_rgba_png(title_source)
    sea = decode_rgba_png(sea_source)
    if (title.width, title.height) != (240, 160):
        raise ValueError("title animation requires a 240x160 title source")
    if (sea.width, sea.height) != (240, 16):
        raise ValueError("title animation requires a 240x16 seaTiles source")

    # GameTitle.seaImage() only selects tiles 112, 113 and 114. Tile 115 is present
    # in the sheet but never selected by the canonical title update routine.
    maps = []
    for source_y in (0, 4, 8):
        sea_frame = crop_rgba(sea, 0, source_y, 240, 4)
        composited = composite_rgba(title, sea_frame, 0, 128)
        canvas, offset_x, offset_y = center_rgba(composited)
        maps.append(canvas)

    stacked = stack_rgba_vertical(maps)
    bmp_path = graphics_dir / "title_anim.bmp"
    write_indexed_bmp(bmp_path, stacked)
    metadata = dict(_ANIMATED_REGULAR_BG_METADATA)
    _write_json(graphics_dir / "title_anim.json", metadata)

    combined_source = title_source + sea_source
    return _record(
        source_member=f"{TITLE_MEMBER}+{SEA_TILES_MEMBER}",
        source_bytes=combined_source,
        source_width=240,
        source_height=176,
        output_path="graphics/title_anim.bmp",
        output_file=bmp_path,
        output_width=256,
        output_height=256 * 3,
        offset_x=offset_x,
        offset_y=offset_y,
    )


def _stage_map_spots(apk_path: Path, graphics_dir: Path) -> dict[str, object]:
    source = read_apk_member(apk_path, TILES_MEMBER)
    tiles = decode_rgba_png(source)
    if (tiles.width, tiles.height) != (128, 304):
        raise ValueError("map spot extraction requires the canonical 128x304 tile sheet")

    frames = [crop_rgba(tiles, x, 48, 8, 16) for x in (96, 104, 112, 120)]
    sheet = stack_rgba_horizontal(frames)
    bmp_path = graphics_dir / "map_spots.bmp"
    write_indexed_bmp(bmp_path, sheet)
    _write_json(
        graphics_dir / "map_spots.json",
        _sprite_metadata(8, 16, bpp_mode="bpp_4", graphics_count=len(frames)),
    )
    return _record(
        source_member=TILES_MEMBER,
        source_bytes=source,
        source_width=tiles.width,
        source_height=tiles.height,
        output_path="graphics/map_spots.bmp",
        output_file=bmp_path,
        output_width=sheet.width,
        output_height=sheet.height,
        offset_x=96,
        offset_y=48,
    )


def stage_m1_assets(apk_path: Path, graphics_dir: Path) -> list[dict[str, object]]:
    graphics_dir.mkdir(parents=True, exist_ok=True)
    return [
        _stage_title_animation(apk_path, graphics_dir),
        _stage_regular_bg(apk_path, graphics_dir, member=MAP_MEMBER, stem="map"),
        _stage_map_spots(apk_path, graphics_dir),
        _stage_regular_bg(
            apk_path,
            graphics_dir,
            member=CRYSTAL_LAKE_MEMBER,
            stem="crystal_lake",
        ),
    ]



def _sprite_metadata(
    width: int,
    height: int,
    *,
    bpp_mode: str = "bpp_8",
    graphics_count: int = 1,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "type": "sprite",
        "width": width,
        "height": height,
        "bpp_mode": bpp_mode,
    }
    if graphics_count > 1:
        # Butano can only index individual graphics from an uncompressed tile sheet.
        metadata["tiles_compression"] = "none"
        metadata["palette_compression"] = "auto_no_huffman"
    else:
        metadata["compression"] = "auto_no_huffman"
    return metadata


def _pad_rgba(image: RgbaImage, width: int, height: int) -> RgbaImage:
    return place_rgba(image, canvas_width=width, canvas_height=height, x=0, y=0)


def _tile_rect(index: int) -> tuple[int, int, int, int]:
    if 0 <= index < 96:
        return (index % 16 * 8, index // 16 * 8, 8, 8)

    explicit = {
        96: (0, 48, 16, 16),
        97: (16, 48, 16, 16),
        98: (32, 48, 16, 16),
        104: (0, 64, 16, 8),
        105: (16, 64, 16, 8),
        106: (32, 64, 16, 8),
        107: (48, 64, 16, 8),
        108: (64, 64, 16, 8),
        109: (80, 64, 16, 8),
        110: (0, 72, 16, 16),
        111: (16, 72, 16, 16),
        116: (96, 64, 8, 8),
        117: (104, 64, 8, 8),
        118: (112, 64, 8, 8),
        119: (32, 72, 16, 16),
        120: (48, 72, 16, 16),
        121: (64, 72, 16, 16),
        122: (80, 72, 16, 16),
        123: (96, 72, 16, 16),
        124: (112, 72, 16, 16),
    }
    if index in explicit:
        return explicit[index]
    if 125 <= index <= 156:
        offset = index - 125
        return ((offset % 8) * 16, 88 + (offset // 8) * 16, 16, 16)
    if 157 <= index <= 164:
        return ((index - 157) * 16, 152, 16, 24)
    if 165 <= index <= 169:
        return ((index - 165) * 24, 176, 24, 24)
    if 171 <= index <= 175:
        return ((index - 171) * 24, 224, 24, 40)
    if 176 <= index <= 178:
        return ((index - 176) * 24, 264, 24, 40)
    raise ValueError(f"no recovered source rectangle for tile {index}")


def _crop_tile(tiles: RgbaImage, index: int) -> RgbaImage:
    return crop_rgba(tiles, *_tile_rect(index))


def _write_sprite_sheet(
    graphics_dir: Path,
    stem: str,
    frames: list[RgbaImage],
    *,
    frame_width: int,
    frame_height: int,
    bpp_mode: str = "bpp_8",
) -> Path:
    padded = [_pad_rgba(frame, frame_width, frame_height) for frame in frames]
    sheet = stack_rgba_horizontal(padded)
    bmp_path = graphics_dir / f"{stem}.bmp"
    write_indexed_bmp(bmp_path, sheet)
    _write_json(
        graphics_dir / f"{stem}.json",
        _sprite_metadata(
            frame_width, frame_height, bpp_mode=bpp_mode, graphics_count=len(frames)
        ),
    )
    return bmp_path


def stage_m2_assets(apk_path: Path, graphics_dir: Path) -> list[dict[str, object]]:
    """Stage the exact canonical sprites needed by the first Crystal Lake loop."""
    graphics_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []

    char_bytes = read_apk_member(apk_path, CHAR_SHEET_MEMBER)
    char = decode_rgba_png(char_bytes)
    if (char.width, char.height) != (256, 480):
        raise ValueError("character extraction requires the canonical 256x480 sheet")
    char_frames = [
        crop_rgba(char, (frame % 8) * 32, (frame // 8) * 40, 32, 40)
        for frame in range(16)
    ]
    char_path = _write_sprite_sheet(
        graphics_dir, "fishing_char", char_frames,
        frame_width=32, frame_height=64, bpp_mode="bpp_4",
    )
    records.append(_record(
        source_member=CHAR_SHEET_MEMBER, source_bytes=char_bytes,
        source_width=char.width, source_height=char.height,
        output_path="graphics/fishing_char.bmp", output_file=char_path,
        output_width=32 * 16, output_height=64, offset_x=0, offset_y=0,
    ))

    stick_bytes = read_apk_member(apk_path, STICK_SHEET_MEMBER)
    stick = decode_rgba_png(stick_bytes)
    if (stick.width, stick.height) != (320, 576):
        raise ValueError("rod extraction requires the canonical 320x576 sheet")
    rod_frames = [
        crop_rgba(stick, (frame % 4) * 80, (frame // 4) * 64, 80, 64)
        for frame in range(12)
    ]
    left_frames = [crop_rgba(frame, 0, 0, 64, 64) for frame in rod_frames]
    right_frames = [
        piece
        for frame in rod_frames
        for piece in (crop_rgba(frame, 64, 0, 16, 32), crop_rgba(frame, 64, 32, 16, 32))
    ]
    left_path = _write_sprite_sheet(
        graphics_dir, "fishing_rod_left", left_frames,
        frame_width=64, frame_height=64, bpp_mode="bpp_4",
    )
    right_path = _write_sprite_sheet(
        graphics_dir, "fishing_rod_right", right_frames,
        frame_width=16, frame_height=32, bpp_mode="bpp_4",
    )
    for stem, path, width in (
        ("fishing_rod_left", left_path, 64 * 12),
        ("fishing_rod_right", right_path, 16 * 24),
    ):
        records.append(_record(
            source_member=STICK_SHEET_MEMBER, source_bytes=stick_bytes,
            source_width=stick.width, source_height=stick.height,
            output_path=f"graphics/{stem}.bmp", output_file=path,
            output_width=width, output_height=(32 if stem == "fishing_rod_right" else 64), offset_x=0, offset_y=0,
        ))

    lake_bytes = read_apk_member(apk_path, CRYSTAL_LAKE_MEMBER)
    lake = decode_rgba_png(lake_bytes)
    if (lake.width, lake.height) != (240, 160):
        raise ValueError("fishing lake extraction requires the canonical 240x160 background")

    sea_bytes = read_apk_member(apk_path, SEA_TILES_MEMBER)
    sea = decode_rgba_png(sea_bytes)
    if (sea.width, sea.height) != (240, 16):
        raise ValueError("fishing sea extraction requires the canonical 240x16 sheet")
    lake_maps = []
    for source_y in (0, 4, 8):
        strip = crop_rgba(sea, 0, source_y, 240, 4)
        composited = composite_rgba(lake, strip, 0, 128)
        canvas, offset_x, offset_y = center_rgba(composited)
        lake_maps.append(canvas)
    lake_sheet = stack_rgba_vertical(lake_maps)
    lake_path = graphics_dir / "fishing_lake.bmp"
    write_indexed_bmp(lake_path, lake_sheet)
    lake_metadata = dict(_ANIMATED_REGULAR_BG_METADATA)
    _write_json(graphics_dir / "fishing_lake.json", lake_metadata)
    records.append(_record(
        source_member=f"{CRYSTAL_LAKE_MEMBER}+{SEA_TILES_MEMBER}",
        source_bytes=lake_bytes + sea_bytes,
        source_width=240, source_height=176,
        output_path="graphics/fishing_lake.bmp", output_file=lake_path,
        output_width=256, output_height=256 * 3, offset_x=offset_x, offset_y=offset_y,
    ))

    tiles_bytes = read_apk_member(apk_path, TILES_MEMBER)
    tiles = decode_rgba_png(tiles_bytes)
    if (tiles.width, tiles.height) != (128, 304):
        raise ValueError("fishing tile extraction requires the canonical 128x304 sheet")

    sprite_groups = (
        ("fishing_bait", [11, 12, 75, 76, 13, 14, 77, 78, 88, 89, 90, 91, 92, 93, 124]),
        ("fishing_fish_a", [119, 122, 129, 131]),
        ("fishing_fish_b", [137, 142, 144, 150, 160]),
    )
    sprite_mapping: dict[str, list[object]] = {}
    for stem, indices in sprite_groups:
        frames = [_crop_tile(tiles, index) for index in indices]
        path = _write_sprite_sheet(
            graphics_dir, stem, frames,
            frame_width=16, frame_height=32, bpp_mode="bpp_4",
        )
        for frame, source in enumerate(indices):
            sprite_mapping[str(source)] = [stem, frame]
        records.append(_record(
            source_member=TILES_MEMBER, source_bytes=tiles_bytes,
            source_width=tiles.width, source_height=tiles.height,
            output_path=f"graphics/{stem}.bmp", output_file=path,
            output_width=16 * len(indices), output_height=32, offset_x=0, offset_y=0,
        ))
    _write_json(graphics_dir / "fishing_sprite_map.json", sprite_mapping)

    for stem, indices, frame_width, frame_height in (
        ("fishing_splash", list(range(104, 110)), 16, 8),
        ("fishing_coin", [116, 117, 118], 8, 8),
        ("fishing_hud", [97, 98], 16, 16),
        ("fishing_meter", [10], 8, 8),
    ):
        frames = [_crop_tile(tiles, index) for index in indices]
        path = _write_sprite_sheet(
            graphics_dir, stem, frames,
            frame_width=frame_width, frame_height=frame_height, bpp_mode="bpp_4",
        )
        records.append(_record(
            source_member=TILES_MEMBER, source_bytes=tiles_bytes,
            source_width=tiles.width, source_height=tiles.height,
            output_path=f"graphics/{stem}.bmp", output_file=path,
            output_width=frame_width * len(indices), output_height=frame_height,
            offset_x=0, offset_y=0,
        ))

    # Android GameFishing.loadAssets(): Paint.setARGB(255, 235, 255, 237).
    line_pixels = bytearray(8 * 8 * 4)
    line_offset = (3 * 8 + 3) * 4
    line_pixels[line_offset:line_offset + 4] = bytes((235, 255, 237, 255))
    line_image = RgbaImage(8, 8, bytes(line_pixels))
    line_path = graphics_dir / "fishing_line_dot.bmp"
    write_indexed_bmp(line_path, line_image)
    _write_json(
        graphics_dir / "fishing_line_dot.json",
        _sprite_metadata(8, 8, bpp_mode="bpp_4"),
    )
    dex_bytes = read_apk_member(apk_path, DEX_MEMBER)
    records.append(_record(
        source_member=f"{DEX_MEMBER}:GameFishing.loadAssets", source_bytes=dex_bytes,
        source_width=0, source_height=0,
        output_path="graphics/fishing_line_dot.bmp", output_file=line_path,
        output_width=8, output_height=8, offset_x=3, offset_y=3,
    ))

    return records


def _opaque_colors(image: RgbaImage) -> set[tuple[int, int, int, int]]:
    result: set[tuple[int, int, int, int]] = set()
    for offset in range(0, len(image.pixels), 4):
        color = tuple(image.pixels[offset:offset + 4])
        if color[3] == 0:
            continue
        if color[3] != 255:
            raise ValueError("semi-transparent sprite pixels are not supported")
        result.add(color)
    return result


def _first_fit_4bpp_banks(
    frames: list[tuple[int, RgbaImage]],
) -> list[list[tuple[int, RgbaImage]]]:
    # Deterministic first-fit-decreasing: packing the palette-heavy sprites first
    # avoids a third bank while preserving every source pixel exactly.
    prepared = [(source_index, frame, _opaque_colors(frame)) for source_index, frame in frames]
    prepared.sort(key=lambda item: (-len(item[2]), item[0]))

    banks: list[list[tuple[int, RgbaImage]]] = []
    bank_colors: list[set[tuple[int, int, int, int]]] = []
    for source_index, frame, frame_colors in prepared:
        if len(frame_colors) > 15:
            raise ValueError(f"sprite tile {source_index} alone exceeds a 4bpp palette")
        for bank_index, colors in enumerate(bank_colors):
            combined = colors | frame_colors
            if len(combined) <= 15:  # palette index zero is reserved for transparency
                banks[bank_index].append((source_index, frame))
                bank_colors[bank_index] = combined
                break
        else:
            banks.append([(source_index, frame)])
            bank_colors.append(set(frame_colors))
    return banks


def _stage_fishing_area_background(
    apk_path: Path,
    graphics_dir: Path,
    *,
    member: str,
    stem: str,
    sea_bytes: bytes,
    sea: RgbaImage,
    drawtext_fields: tuple[tuple[int, int, int, int], ...] = _FISHING_TEXT_FIELDS,
) -> dict[str, object]:
    background_bytes = read_apk_member(apk_path, member)
    background = decode_rgba_png(background_bytes)
    if (background.width, background.height) != (240, 160):
        raise ValueError(f"{stem} requires a canonical 240x160 fishing background")
    if drawtext_fields:
        background = _fill_rects(background, drawtext_fields)

    maps = []
    for source_y in (0, 4, 8):
        strip = crop_rgba(sea, 0, source_y, 240, 4)
        composited = composite_rgba(background, strip, 0, 128)
        canvas, offset_x, offset_y = center_rgba(composited)
        maps.append(canvas)
    sheet = stack_rgba_vertical(maps)
    bmp_path = graphics_dir / f"{stem}.bmp"
    write_indexed_bmp(bmp_path, sheet)
    metadata = dict(_ANIMATED_REGULAR_BG_METADATA)
    _write_json(graphics_dir / f"{stem}.json", metadata)
    return _record(
        source_member=f"{member}+{SEA_TILES_MEMBER}",
        source_bytes=background_bytes + sea_bytes,
        source_width=240,
        source_height=176,
        output_path=f"graphics/{stem}.bmp",
        output_file=bmp_path,
        output_width=256,
        output_height=256 * 3,
        offset_x=offset_x,
        offset_y=offset_y,
    )


def stage_m3_assets(apk_path: Path, graphics_dir: Path) -> list[dict[str, object]]:
    """Stage all five recovered fishing areas, 44 fish and three rod variants."""
    graphics_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    facts = recover_m3_from_apk(apk_path)

    sea_bytes = read_apk_member(apk_path, SEA_TILES_MEMBER)
    sea = decode_rgba_png(sea_bytes)
    if (sea.width, sea.height) != (240, 16):
        raise ValueError("M3 fishing backgrounds require the canonical 240x16 sea sheet")

    stems = (
        "fishing_area_crystal",
        "fishing_area_pier",
        "fishing_area_river",
        "fishing_area_ocean",
        "fishing_area_cave",
    )
    for area, stem in zip(facts["areas"], stems, strict=True):
        member = "assets/" + str(area["background"])
        records.append(_stage_fishing_area_background(
            apk_path, graphics_dir, member=member, stem=stem, sea_bytes=sea_bytes, sea=sea
        ))

    tiles_bytes = read_apk_member(apk_path, TILES_MEMBER)
    tiles = decode_rgba_png(tiles_bytes)
    if (tiles.width, tiles.height) != (128, 304):
        raise ValueError("M3 fish extraction requires the canonical 128x304 tile sheet")
    fish_indices = sorted({
        int(fish["sprite"])
        for area in facts["areas"]
        for fish in area["fish"]
    })
    if len(fish_indices) != 44:
        raise ValueError(f"expected 44 unique M3 fish sprites, got {len(fish_indices)}")
    fish_frames = [(index, _crop_tile(tiles, index)) for index in fish_indices]
    fish_banks = _first_fit_4bpp_banks(fish_frames)
    mapping: dict[str, list[object]] = {}
    for bank_index, bank in enumerate(fish_banks):
        stem = f"fishing_fish_m3_{bank_index}"
        path = _write_sprite_sheet(
            graphics_dir, stem, [frame for _source, frame in bank],
            frame_width=16, frame_height=32, bpp_mode="bpp_4",
        )
        for frame_index, (source_index, _frame) in enumerate(bank):
            mapping[str(source_index)] = [stem, frame_index]
        records.append(_record(
            source_member=TILES_MEMBER, source_bytes=tiles_bytes,
            source_width=tiles.width, source_height=tiles.height,
            output_path=f"graphics/{stem}.bmp", output_file=path,
            output_width=16 * len(bank), output_height=32, offset_x=0, offset_y=0,
        ))
    _write_json(graphics_dir / "fishing_m3_sprite_map.json", mapping)

    stick_bytes = read_apk_member(apk_path, STICK_SHEET_MEMBER)
    stick = decode_rgba_png(stick_bytes)
    if (stick.width, stick.height) != (320, 576):
        raise ValueError("M3 rod extraction requires the canonical 320x576 sheet")
    rod_frames = [
        crop_rgba(stick, (frame % 4) * 80, (frame // 4) * 64, 80, 64)
        for frame in range(36)
    ]
    left_frames = [crop_rgba(frame, 0, 0, 64, 64) for frame in rod_frames]
    right_frames = [
        piece
        for frame in rod_frames
        for piece in (crop_rgba(frame, 64, 0, 16, 32), crop_rgba(frame, 64, 32, 16, 32))
    ]
    for stem, frames, frame_width in (
        ("fishing_rods_left", left_frames, 64),
        ("fishing_rods_right", right_frames, 16),
    ):
        frame_height = 32 if stem == "fishing_rods_right" else 64
        path = _write_sprite_sheet(
            graphics_dir, stem, frames, frame_width=frame_width, frame_height=frame_height, bpp_mode="bpp_4"
        )
        records.append(_record(
            source_member=STICK_SHEET_MEMBER, source_bytes=stick_bytes,
            source_width=stick.width, source_height=stick.height,
            output_path=f"graphics/{stem}.bmp", output_file=path,
            output_width=frame_width * len(frames), output_height=frame_height, offset_x=0, offset_y=0,
        ))

    return records


def _stage_m4_animated_background(
    apk_path: Path,
    graphics_dir: Path,
    *,
    member: str,
    stem: str,
    sea_bytes: bytes,
    sea: RgbaImage,
) -> dict[str, object]:
    return _stage_fishing_area_background(
        apk_path, graphics_dir, member=member, stem=stem, sea_bytes=sea_bytes, sea=sea, drawtext_fields=()
    )


def stage_m4_assets(apk_path: Path, graphics_dir: Path) -> list[dict[str, object]]:
    """Stage additive Shop/Catalog/Options/Event graphics recovered for M4."""
    graphics_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []

    records.append(_stage_regular_bg(
        apk_path, graphics_dir, member=SHOP_MEMBER, stem="m4_shop", drawtext_fields=_SHOP_TEXT_FIELDS
    ))

    sea_bytes = read_apk_member(apk_path, SEA_TILES_MEMBER)
    sea = decode_rgba_png(sea_bytes)
    if (sea.width, sea.height) != (240, 16):
        raise ValueError("M4 animated backgrounds require the canonical 240x16 sea sheet")
    for member, stem in (
        (CATALOG_MEMBER, "m4_catalog_anim"),
        (OPTIONS_MEMBER, "m4_options_anim"),
        (EVENT_MEMBER, "m4_event_anim"),
    ):
        records.append(_stage_m4_animated_background(
            apk_path, graphics_dir, member=member, stem=stem, sea_bytes=sea_bytes, sea=sea
        ))

    tiles_bytes = read_apk_member(apk_path, TILES_MEMBER)
    tiles = decode_rgba_png(tiles_bytes)
    if (tiles.width, tiles.height) != (128, 304):
        raise ValueError("M4 sprite extraction requires the canonical 128x304 tile sheet")

    # DrawText/getChar uses the first 96 8x8 tiles as the original game font.
    font_frames = [crop_rgba(tiles, (index % 16) * 8, (index // 16) * 8, 8, 8) for index in range(96)]
    font_path = _write_sprite_sheet(
        graphics_dir, "m4_font", font_frames, frame_width=8, frame_height=8, bpp_mode="bpp_4"
    )
    records.append(_record(
        source_member=TILES_MEMBER, source_bytes=tiles_bytes,
        source_width=tiles.width, source_height=tiles.height,
        output_path="graphics/m4_font.bmp", output_file=font_path,
        output_width=8 * 96, output_height=8, offset_x=0, offset_y=0,
    ))

    sprite_specs = (
        ("m4_shop_keeper", (166, 167), 32, 32),
        ("m4_shop_cursor", (165,), 32, 32),
        ("m4_catalog_cursor", (164,), 16, 32),
        ("m4_shop_sold_out", (156,), 16, 16),
        ("m4_event_cecil", (177, 178), 32, 64),
    )
    for stem, indices, width, height in sprite_specs:
        frames = [_crop_tile(tiles, index) for index in indices]
        path = _write_sprite_sheet(
            graphics_dir, stem, frames, frame_width=width, frame_height=height, bpp_mode="bpp_4"
        )
        records.append(_record(
            source_member=TILES_MEMBER, source_bytes=tiles_bytes,
            source_width=tiles.width, source_height=tiles.height,
            output_path=f"graphics/{stem}.bmp", output_file=path,
            output_width=width * len(indices), output_height=height, offset_x=0, offset_y=0,
        ))

    # GameMap.setSprite selects tiles 171..176 for the current character,
    # while GameMap.draw places that 24x40 portrait at (183, 91). Keep the
    # source crop exact and only pad it to a legal GBA OBJ size.
    for character, index in enumerate(range(171, 177)):
        frame = _crop_tile(tiles, index)
        stem = f"map_character_{character}"
        path = _write_sprite_sheet(
            graphics_dir,
            stem,
            [frame],
            frame_width=32,
            frame_height=64,
            bpp_mode="bpp_4",
        )
        records.append(_record(
            source_member=TILES_MEMBER, source_bytes=tiles_bytes,
            source_width=tiles.width, source_height=tiles.height,
            output_path=f"graphics/{stem}.bmp", output_file=path,
            output_width=32, output_height=64, offset_x=0, offset_y=0,
        ))

    # GameMap.draw uses tile 170 at (0, 136) when Catalog is unlocked. The
    # Android tile is 80x24, so preserve it as three adjacent 32x32 OBJ parts
    # instead of scaling or trimming it.
    map_catalog_frames = [
        crop_rgba(tiles, 0, 200, 32, 24),
        crop_rgba(tiles, 32, 200, 32, 24),
        crop_rgba(tiles, 64, 200, 16, 24),
    ]
    map_catalog_path = _write_sprite_sheet(
        graphics_dir,
        "map_catalog_parts",
        map_catalog_frames,
        frame_width=32,
        frame_height=32,
        bpp_mode="bpp_4",
    )
    records.append(_record(
        source_member=TILES_MEMBER, source_bytes=tiles_bytes,
        source_width=tiles.width, source_height=tiles.height,
        output_path="graphics/map_catalog_parts.bmp", output_file=map_catalog_path,
        output_width=32 * len(map_catalog_frames), output_height=32, offset_x=0, offset_y=0,
    ))

    char_bytes = read_apk_member(apk_path, CHAR_SHEET_MEMBER)
    char = decode_rgba_png(char_bytes)
    if (char.width, char.height) != (256, 480):
        raise ValueError("M4 character extraction requires the canonical 256x480 sheet")
    for character in range(6):
        frames = []
        for frame in range(16):
            source_index = character * 16 + frame
            frames.append(crop_rgba(
                char, (source_index % 8) * 32, (source_index // 8) * 40, 32, 40
            ))
        stem = f"fishing_char_m4_{character}"
        path = _write_sprite_sheet(
            graphics_dir, stem, frames, frame_width=32, frame_height=64, bpp_mode="bpp_4"
        )
        records.append(_record(
            source_member=CHAR_SHEET_MEMBER, source_bytes=char_bytes,
            source_width=char.width, source_height=char.height,
            output_path=f"graphics/{stem}.bmp", output_file=path,
            output_width=32 * 16, output_height=64, offset_x=0, offset_y=0,
        ))

    return records



def stage_m7_assets(apk_path: Path, graphics_dir: Path) -> list[dict[str, object]]:
    """Stage M7 intro and native-only Options backgrounds."""
    graphics_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []

    credit_bytes = read_apk_member(apk_path, INTRO_CREDIT_MEMBER)
    credit = decode_rgba_png(credit_bytes)
    if (credit.width, credit.height) != (144, 64):
        raise ValueError("M7 intro credit requires the canonical 144x64 source")
    base = RgbaImage(240, 160, bytes((25, 5, 36, 255)) * (240 * 160))
    intro = composite_rgba(base, credit, 48, 48)
    intro_path = graphics_dir / "m7_intro_credit.bmp"
    offset_x, offset_y = write_centered_indexed_bmp(intro_path, intro)
    _write_json(graphics_dir / "m7_intro_credit.json", _REGULAR_BG_METADATA)
    dex_bytes = read_apk_member(apk_path, DEX_MEMBER)
    records.append(_record(
        source_member=f"{INTRO_CREDIT_MEMBER}+{DEX_MEMBER}:GameIntro.init",
        source_bytes=credit_bytes + dex_bytes,
        source_width=240, source_height=160,
        output_path="graphics/m7_intro_credit.bmp", output_file=intro_path,
        output_width=256, output_height=256, offset_x=offset_x, offset_y=offset_y,
    ))

    options_bytes = read_apk_member(apk_path, OPTIONS_MEMBER)
    options = decode_rgba_png(options_bytes)
    pixels = bytearray(options.pixels)
    sky = bytes((80, 156, 204, 255))
    # Remove only the Android image-mode row; the canonical sound row remains.
    for y in range(36, 52):
        for x in range(65, 238):
            pos = (y * options.width + x) * 4
            pixels[pos:pos + 4] = sky
    native_options = RgbaImage(options.width, options.height, bytes(pixels))

    sea_bytes = read_apk_member(apk_path, SEA_TILES_MEMBER)
    sea = decode_rgba_png(sea_bytes)
    maps = []
    for source_y in (0, 4, 8):
        strip = crop_rgba(sea, 0, source_y, 240, 4)
        composited = composite_rgba(native_options, strip, 0, 128)
        canvas, offset_x, offset_y = center_rgba(composited)
        maps.append(canvas)
    sheet = stack_rgba_vertical(maps)
    options_path = graphics_dir / "m7_options_anim.bmp"
    write_indexed_bmp(options_path, sheet)
    metadata = dict(_ANIMATED_REGULAR_BG_METADATA)
    _write_json(graphics_dir / "m7_options_anim.json", metadata)
    records.append(_record(
        source_member=f"{OPTIONS_MEMBER}+{SEA_TILES_MEMBER}:M7-native-only",
        source_bytes=options_bytes + sea_bytes,
        source_width=240, source_height=176,
        output_path="graphics/m7_options_anim.bmp", output_file=options_path,
        output_width=256, output_height=256 * 3, offset_x=offset_x, offset_y=offset_y,
    ))

    # DialogBox.loadAssets creates a 240x24 ARGB buffer filled with (25,5,36),
    # but setNewPage only fills x=[0,232). Render that with three full
    # 64x32 OBJ panels plus a 40px-wide tail panel; bottom 8px stay transparent.
    transparent = bytes((0, 0, 0, 0))
    purple = bytes((25, 5, 36, 255))
    panel_frames = []
    for fill_width in (64, 40):
        panel_pixels = bytearray()
        for y in range(32):
            for x in range(64):
                panel_pixels.extend(purple if y < 24 and x < fill_width else transparent)
        panel_frames.append(RgbaImage(64, 32, bytes(panel_pixels)))
    panel_path = _write_sprite_sheet(
        graphics_dir, "m7_dialog_panel", panel_frames,
        frame_width=64, frame_height=32, bpp_mode="bpp_4",
    )
    records.append(_record(
        source_member=f"{DEX_MEMBER}:DialogBox.loadAssets+DialogBox.setNewPage",
        source_bytes=dex_bytes, source_width=240, source_height=24,
        output_path="graphics/m7_dialog_panel.bmp", output_file=panel_path,
        output_width=128, output_height=32, offset_x=0, offset_y=0,
    ))

    tiles_bytes = read_apk_member(apk_path, TILES_MEMBER)
    tiles = decode_rgba_png(tiles_bytes)
    marker_frames = [_crop_tile(tiles, 96), _crop_tile(tiles, 98)]
    marker_path = _write_sprite_sheet(
        graphics_dir, "m7_dialog_markers", marker_frames,
        frame_width=16, frame_height=16, bpp_mode="bpp_4",
    )
    records.append(_record(
        source_member=f"{TILES_MEMBER}+{DEX_MEMBER}:DialogBox.setNewPage+DialogBox.drawDialog",
        source_bytes=tiles_bytes + dex_bytes, source_width=tiles.width, source_height=tiles.height,
        output_path="graphics/m7_dialog_markers.bmp", output_file=marker_path,
        output_width=32, output_height=16, offset_x=0, offset_y=0,
    ))

    dollar_path = _write_sprite_sheet(
        graphics_dir, "m7_dialog_dollar", [_crop_tile(tiles, 116)],
        frame_width=8, frame_height=8, bpp_mode="bpp_4",
    )
    records.append(_record(
        source_member=f"{TILES_MEMBER}+{DEX_MEMBER}:DialogBox.getChar($)",
        source_bytes=tiles_bytes + dex_bytes, source_width=tiles.width, source_height=tiles.height,
        output_path="graphics/m7_dialog_dollar.bmp", output_file=dollar_path,
        output_width=8, output_height=8, offset_x=0, offset_y=0,
    ))

    return records

def _write_manifest(path: Path, records: list[dict[str, object]]) -> None:
    columns = [
        "source_member",
        "source_sha256",
        "source_bytes",
        "source_width",
        "source_height",
        "output_path",
        "output_sha256",
        "output_bytes",
        "output_width",
        "output_height",
        "offset_x",
        "offset_y",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(columns)]
    lines.extend("\t".join(str(record[column]) for column in columns) for record in records)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage verified reference assets for Butano")
    parser.add_argument("apk", type=Path)
    parser.add_argument("--graphics", type=Path, default=ROOT / "graphics")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "reference" / "reference_asset_manifest.tsv",
    )
    args = parser.parse_args(argv)

    if not args.apk.is_file():
        print(f"reference APK not found: {args.apk}", file=sys.stderr)
        return 2

    errors = validate_reference(args.apk, ROOT / "reference" / "apk_inventory.tsv")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    title_record = stage_title(args.apk, args.graphics)
    m1_records = stage_m1_assets(args.apk, args.graphics)
    m2_records = stage_m2_assets(args.apk, args.graphics)
    m3_records = stage_m3_assets(args.apk, args.graphics)
    m4_records = stage_m4_assets(args.apk, args.graphics)
    m7_records = stage_m7_assets(args.apk, args.graphics)
    _write_manifest(args.manifest, [title_record, *m1_records, *m2_records, *m3_records, *m4_records, *m7_records])
    print("staged M0-M4 reference assets plus M7 intro/options/dialog assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
