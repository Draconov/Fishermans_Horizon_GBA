from __future__ import annotations

import json
from pathlib import Path
import struct
import zipfile

from tools.png_asset import RgbaImage, composite_rgba, crop_rgba, decode_rgba_png

_GBA_SPRITE_SIZES = {
    (8, 8), (16, 16), (32, 32), (64, 64),
    (16, 8), (32, 8), (32, 16), (64, 32),
    (8, 16), (8, 32), (16, 32), (32, 64),
}


def _read_bmp(path: Path) -> tuple[int, int, int, list[tuple[int, int, int, int]], bytes]:
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError(f"invalid BMP: {path}")
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    if dib_size < 40:
        raise ValueError(f"unsupported BMP DIB: {path}")
    width, raw_height, planes, bpp = struct.unpack_from("<iiHH", data, 18)
    if width <= 0 or raw_height == 0 or planes != 1 or bpp != 8:
        raise ValueError(f"expected indexed 8bpp BMP: {path}")
    height = abs(raw_height)
    palette_start = 14 + dib_size
    palette_count = (pixel_offset - palette_start) // 4
    palette: list[tuple[int, int, int, int]] = []
    for index in range(palette_count):
        blue, green, red, _ = struct.unpack_from("<BBBB", data, palette_start + index * 4)
        palette.append((red, green, blue, 0 if index == 0 else 255))
    row_stride = (width + 3) & ~3
    indexes = bytearray(width * height)
    bottom_up = raw_height > 0
    for y in range(height):
        source_y = height - 1 - y if bottom_up else y
        start = pixel_offset + source_y * row_stride
        indexes[y * width:(y + 1) * width] = data[start:start + width]
    return width, height, bpp, palette, bytes(indexes)


def _bmp_rgba(path: Path) -> RgbaImage:
    width, height, _bpp, palette, indexes = _read_bmp(path)
    pixels = bytearray(width * height * 4)
    for pos, index in enumerate(indexes):
        if index >= len(palette):
            raise ValueError(f"palette index {index} outside palette in {path}")
        pixels[pos * 4:(pos + 1) * 4] = bytes(palette[index])
    return RgbaImage(width, height, bytes(pixels))


def validate_graphics_resources(graphics_dir: Path) -> list[str]:
    errors: list[str] = []
    for metadata_path in sorted(graphics_dir.glob("*.json")):
        bmp_path = metadata_path.with_suffix(".bmp")
        if not bmp_path.is_file():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            width, height, _bpp, _palette, indexes = _read_bmp(bmp_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{metadata_path.name}: {exc}")
            continue

        kind = metadata.get("type")
        mode = metadata.get("bpp_mode")
        if mode == "bpp_4" and indexes and max(indexes) > 15:
            errors.append(f"{metadata_path.name}: 4bpp asset uses palette index {max(indexes)}")
        elif mode not in ("bpp_4", "bpp_8", "bpp_4_manual", "bpp_4_auto"):
            errors.append(f"{metadata_path.name}: unsupported bpp mode {mode!r}")

        if kind == "sprite":
            frame_width = int(metadata.get("width", width))
            frame_height = int(metadata.get("height", height))
            if (frame_width, frame_height) not in _GBA_SPRITE_SIZES:
                errors.append(
                    f"{metadata_path.name}: illegal GBA sprite frame {frame_width}x{frame_height}"
                )
            if width % frame_width or height % frame_height:
                errors.append(
                    f"{metadata_path.name}: sheet {width}x{height} is not divisible by frame "
                    f"{frame_width}x{frame_height}"
                )
        elif kind == "regular_bg":
            map_height = int(metadata.get("height", height))
            if width not in (256, 512) or map_height not in (256, 512):
                errors.append(f"{metadata_path.name}: illegal regular BG map {width}x{map_height}")
            if height % map_height:
                errors.append(f"{metadata_path.name}: stacked BG height {height} not divisible by {map_height}")
        else:
            errors.append(f"{metadata_path.name}: unsupported graphics type {kind!r}")
    return errors


def scene_oam_budgets() -> dict[str, int]:
    # Counts are upper bounds from the scene-owned sprite_ptr/vector capacities.
    return {
        "title": 0,
        "map": 6,
        "fishing": 125,  # 13 fixed + 32 line dots + 6 dialog chrome + 64 dialog glyphs + up to 10 bait-name glyphs.
        "shop": 82,      # keeper + cursor + 16 sold-out + 64 text.
        "catalog": 109,  # cursor + 44 fish + 64 text.
        "options": 33,   # cursor + 32 text.
        "event": 71,     # Cecil + 6 dialog chrome + up to 64 dialog glyphs.
    }


def _read_apk_rgba(archive: zipfile.ZipFile, member: str) -> RgbaImage:
    return decode_rgba_png(archive.read(member))


def _visible(image: RgbaImage, map_index: int = 0) -> RgbaImage:
    return crop_rgba(image, 8, map_index * 256 + 48, 240, 160)


def _compare(stem: str, expected: list[RgbaImage], graphics_dir: Path, errors: list[str]) -> None:
    path = graphics_dir / f"{stem}.bmp"
    if not path.is_file():
        errors.append(f"{stem}: missing BMP")
        return
    try:
        actual = _bmp_rgba(path)
    except (OSError, ValueError) as exc:
        errors.append(f"{stem}: {exc}")
        return
    for index, expected_frame in enumerate(expected):
        try:
            actual_frame = _visible(actual, index)
        except ValueError as exc:
            errors.append(f"{stem}[{index}]: {exc}")
            continue
        if actual_frame.pixels != expected_frame.pixels:
            errors.append(f"{stem}[{index}]: visible 240x160 pixels differ")


def _fill_runtime_text_fields(image: RgbaImage, rects: tuple[tuple[int, int, int, int], ...]) -> RgbaImage:
    pixels = bytearray(image.pixels)
    color = bytes((25, 5, 36, 255))
    for x, y, width, height in rects:
        for row in range(y, y + height):
            start = (row * image.width + x) * 4
            for column in range(width):
                pos = start + column * 4
                pixels[pos:pos + 4] = color
    return RgbaImage(image.width, image.height, bytes(pixels))


def validate_visual_parity(apk_path: Path, graphics_dir: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(apk_path, "r") as archive:
        sea = _read_apk_rgba(archive, "assets/graphic/tile/seaTiles.png")
        sea_frames = [crop_rgba(sea, 0, y, 240, 4) for y in (0, 4, 8)]

        title = _read_apk_rgba(archive, "assets/graphic/background/title.png")
        _compare("title_anim", [composite_rgba(title, frame, 0, 128) for frame in sea_frames], graphics_dir, errors)

        map_bg = _read_apk_rgba(archive, "assets/graphic/background/map.png")
        _compare("map", [map_bg], graphics_dir, errors)

        for stem, member in (
            ("fishing_area_crystal", "assets/graphic/background/crystalLake.png"),
            ("fishing_area_pier", "assets/graphic/background/pier.png"),
            ("fishing_area_river", "assets/graphic/background/river.png"),
            ("fishing_area_ocean", "assets/graphic/background/ocean.png"),
            ("fishing_area_cave", "assets/graphic/background/cave.png"),
            ("m4_catalog_anim", "assets/graphic/background/catalog.png"),
            ("m4_options_anim", "assets/graphic/background/options.png"),
            ("m4_event_anim", "assets/graphic/background/crystalLakeNoHud.png"),
        ):
            background = _read_apk_rgba(archive, member)
            if stem.startswith("fishing_area_"):
                background = _fill_runtime_text_fields(
                    background, ((126, 8, 92, 8), (193, 144, 22, 8))
                )
            _compare(stem, [composite_rgba(background, frame, 0, 128) for frame in sea_frames], graphics_dir, errors)

        shop = _read_apk_rgba(archive, "assets/graphic/background/shop.png")
        shop = _fill_runtime_text_fields(
            shop, ((126, 8, 92, 8), (24, 144, 32, 8), (193, 144, 22, 8))
        )
        _compare("m4_shop", [shop], graphics_dir, errors)
    return errors
