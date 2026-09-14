from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class RgbaImage:
    width: int
    height: int
    pixels: bytes

    def rgba_at(self, x: int, y: int) -> tuple[int, int, int, int]:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError((x, y))
        offset = (y * self.width + x) * 4
        return tuple(self.pixels[offset : offset + 4])  # type: ignore[return-value]


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def decode_rgba_png(data: bytes) -> RgbaImage:
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("invalid PNG signature")

    cursor = len(PNG_SIGNATURE)
    width = height = None
    idat = bytearray()
    saw_iend = False

    while cursor + 12 <= len(data):
        length = struct.unpack_from(">I", data, cursor)[0]
        chunk_type = data[cursor + 4 : cursor + 8]
        chunk_data_start = cursor + 8
        chunk_data_end = chunk_data_start + length
        crc_end = chunk_data_end + 4
        if crc_end > len(data):
            raise ValueError("truncated PNG chunk")
        chunk_data = data[chunk_data_start:chunk_data_end]

        if chunk_type == b"IHDR":
            if length != 13:
                raise ValueError("invalid PNG IHDR")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if bit_depth != 8 or color_type != 6:
                raise ValueError("PNG decoder requires 8-bit RGBA PNG")
            if compression != 0 or filtering != 0 or interlace != 0:
                raise ValueError("unsupported PNG compression/filter/interlace mode")
        elif chunk_type == b"IDAT":
            idat.extend(chunk_data)
        elif chunk_type == b"IEND":
            saw_iend = True
            break

        cursor = crc_end

    if width is None or height is None or not idat or not saw_iend:
        raise ValueError("incomplete PNG")

    bytes_per_pixel = 4
    row_bytes = width * bytes_per_pixel
    raw = zlib.decompress(bytes(idat))
    expected_size = height * (row_bytes + 1)
    if len(raw) != expected_size:
        raise ValueError(f"unexpected PNG data size: expected {expected_size}, got {len(raw)}")

    pixels = bytearray(width * height * bytes_per_pixel)
    previous = bytearray(row_bytes)
    source = 0

    for y in range(height):
        filter_type = raw[source]
        source += 1
        encoded = raw[source : source + row_bytes]
        source += row_bytes
        current = bytearray(row_bytes)

        for x in range(row_bytes):
            left = current[x - bytes_per_pixel] if x >= bytes_per_pixel else 0
            up = previous[x]
            up_left = previous[x - bytes_per_pixel] if x >= bytes_per_pixel else 0
            value = encoded[x]
            if filter_type == 0:
                decoded = value
            elif filter_type == 1:
                decoded = value + left
            elif filter_type == 2:
                decoded = value + up
            elif filter_type == 3:
                decoded = value + ((left + up) // 2)
            elif filter_type == 4:
                decoded = value + _paeth(left, up, up_left)
            else:
                raise ValueError(f"unsupported PNG filter type: {filter_type}")
            current[x] = decoded & 0xFF

        target = y * row_bytes
        pixels[target : target + row_bytes] = current
        previous = current

    return RgbaImage(width, height, bytes(pixels))


def crop_rgba(image: RgbaImage, x: int, y: int, width: int, height: int) -> RgbaImage:
    if width <= 0 or height <= 0:
        raise ValueError("crop dimensions must be positive")
    if x < 0 or y < 0 or x + width > image.width or y + height > image.height:
        raise ValueError("crop is outside source image")

    row_bytes = width * 4
    source_row_bytes = image.width * 4
    pixels = bytearray(row_bytes * height)
    for row in range(height):
        source_start = ((y + row) * source_row_bytes) + x * 4
        target_start = row * row_bytes
        pixels[target_start : target_start + row_bytes] = image.pixels[
            source_start : source_start + row_bytes
        ]
    return RgbaImage(width, height, bytes(pixels))


def composite_rgba(base: RgbaImage, overlay: RgbaImage, x: int, y: int) -> RgbaImage:
    if x < 0 or y < 0 or x + overlay.width > base.width or y + overlay.height > base.height:
        raise ValueError("overlay is outside base image")

    pixels = bytearray(base.pixels)
    for overlay_y in range(overlay.height):
        for overlay_x in range(overlay.width):
            color = overlay.rgba_at(overlay_x, overlay_y)
            if color[3] == 0:
                continue
            if color[3] != 255:
                raise ValueError("semi-transparent pixels are not supported")
            target_offset = ((y + overlay_y) * base.width + (x + overlay_x)) * 4
            pixels[target_offset : target_offset + 4] = bytes(color)
    return RgbaImage(base.width, base.height, bytes(pixels))


def place_rgba(
    image: RgbaImage,
    *,
    canvas_width: int,
    canvas_height: int,
    x: int,
    y: int,
) -> RgbaImage:
    if x < 0 or y < 0 or x + image.width > canvas_width or y + image.height > canvas_height:
        raise ValueError("source image does not fit RGBA canvas")
    canvas = RgbaImage(canvas_width, canvas_height, bytes(canvas_width * canvas_height * 4))
    return composite_rgba(canvas, image, x, y)


def center_rgba(
    image: RgbaImage,
    *,
    canvas_width: int = 256,
    canvas_height: int = 256,
) -> tuple[RgbaImage, int, int]:
    if image.width > canvas_width or image.height > canvas_height:
        raise ValueError("source image does not fit RGBA canvas")
    offset_x = (canvas_width - image.width) // 2
    offset_y = (canvas_height - image.height) // 2
    return (
        place_rgba(
            image,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            x=offset_x,
            y=offset_y,
        ),
        offset_x,
        offset_y,
    )


def stack_rgba_vertical(images: tuple[RgbaImage, ...] | list[RgbaImage]) -> RgbaImage:
    if not images:
        raise ValueError("at least one image is required")
    width = images[0].width
    if any(image.width != width for image in images):
        raise ValueError("all stacked images must have the same width")
    pixels = b"".join(image.pixels for image in images)
    return RgbaImage(width, sum(image.height for image in images), pixels)


def stack_rgba_horizontal(images: tuple[RgbaImage, ...] | list[RgbaImage]) -> RgbaImage:
    if not images:
        raise ValueError("at least one image is required")
    height = images[0].height
    if any(image.height != height for image in images):
        raise ValueError("all stacked images must have the same height")
    width = sum(image.width for image in images)
    pixels = bytearray(width * height * 4)
    for y in range(height):
        target_x = 0
        for image in images:
            source_start = y * image.width * 4
            source_end = source_start + image.width * 4
            target_start = (y * width + target_x) * 4
            pixels[target_start : target_start + image.width * 4] = image.pixels[
                source_start:source_end
            ]
            target_x += image.width
    return RgbaImage(width, height, bytes(pixels))


def write_indexed_bmp(path: Path, image: RgbaImage) -> None:
    opaque_colors: list[tuple[int, int, int, int]] = []
    color_to_index: dict[tuple[int, int, int, int], int] = {}

    for pos in range(0, len(image.pixels), 4):
        color = tuple(image.pixels[pos : pos + 4])  # type: ignore[assignment]
        alpha = color[3]
        if alpha == 0:
            continue
        if alpha != 255:
            raise ValueError("semi-transparent pixels are not supported")
        if color not in color_to_index:
            opaque_colors.append(color)
            color_to_index[color] = len(opaque_colors)  # index 0 is transparent

    if len(opaque_colors) > 255:
        raise ValueError("image needs more than 255 opaque palette colors")

    indexed = bytearray(image.width * image.height)
    for y in range(image.height):
        for x in range(image.width):
            color = image.rgba_at(x, y)
            indexed[y * image.width + x] = 0 if color[3] == 0 else color_to_index[color]

    palette = [(0, 0, 0, 0)] + opaque_colors
    palette.extend([(0, 0, 0, 0)] * (256 - len(palette)))

    row_stride = (image.width + 3) & ~3
    image_size = row_stride * image.height
    pixel_offset = 14 + 40 + 256 * 4
    file_size = pixel_offset + image_size

    output = bytearray()
    output.extend(struct.pack("<2sIHHI", b"BM", file_size, 0, 0, pixel_offset))
    output.extend(
        struct.pack(
            "<IiiHHIIiiII",
            40,
            image.width,
            image.height,
            1,
            8,
            0,
            image_size,
            2835,
            2835,
            256,
            0,
        )
    )
    for red, green, blue, _alpha in palette:
        output.extend(struct.pack("<BBBB", blue, green, red, 0))

    padding = b"\x00" * (row_stride - image.width)
    for y in range(image.height - 1, -1, -1):
        start = y * image.width
        output.extend(indexed[start : start + image.width])
        output.extend(padding)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(output)


def write_centered_indexed_bmp(
    path: Path,
    image: RgbaImage,
    *,
    canvas_width: int = 256,
    canvas_height: int = 256,
) -> tuple[int, int]:
    canvas, offset_x, offset_y = center_rgba(
        image, canvas_width=canvas_width, canvas_height=canvas_height
    )
    write_indexed_bmp(path, canvas)
    return offset_x, offset_y
