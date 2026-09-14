from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.recover_m5 import AUDIO_OUTPUTS, recover_from_apk

SAMPLE_RATE = 16000
SAMPLE_WIDTH_BITS = 8
CHANNELS = 1
S3M_CHUNK_FRAMES = 64000
S3M_SPEED = 6
S3M_TEMPO = 150


def _align16(data: bytearray) -> None:
    data.extend(b"\0" * ((-len(data)) & 15))


def _s3m_pattern(events: dict[int, tuple[int | None, int | None]]) -> bytes:
    """Build one packed 64-row S3M pattern for channel 0.

    events maps row -> (instrument_number, order_jump). A note event uses C-4,
    whose C2SPD is the original PCM sample rate. order_jump emits Bxx.
    """
    packed = bytearray()
    for row in range(64):
        instrument, jump = events.get(row, (None, None))
        if instrument is not None:
            packed.extend((0x20, 0x40, instrument))
        if jump is not None:
            packed.extend((0x80, 0x02, jump))
        packed.append(0)
    return struct.pack("<H", len(packed) + 2) + packed


def _s3m_bytes(pcm: bytes) -> tuple[bytes, int]:
    """Wrap long unsigned 8-bit PCM in a one-channel looping S3M module.

    S3M sample instruments are kept at <= 64,000 bytes. At speed 6 / tempo
    150, each pattern row is 0.1 seconds (1,600 source frames), so a 64,000
    byte chunk lands exactly every 40 rows. The final B00 jump loops within
    one row of the source duration (less than 5 ms for the canonical title).
    """
    if not pcm:
        raise ValueError("title PCM is empty")
    chunks = [pcm[i:i + S3M_CHUNK_FRAMES] for i in range(0, len(pcm), S3M_CHUNK_FRAMES)]
    if len(chunks) > 99:
        raise ValueError("too many title S3M chunks")

    row_frames = int(SAMPLE_RATE * 2.5 * S3M_SPEED / S3M_TEMPO)
    if row_frames != 1600 or S3M_CHUNK_FRAMES % row_frames:
        raise AssertionError("S3M timing constants no longer align to PCM chunks")
    rows_per_chunk = S3M_CHUNK_FRAMES // row_frames

    last_start_row = (len(chunks) - 1) * rows_per_chunk
    total_rows = (len(pcm) + row_frames - 1) // row_frames
    loop_row = max(last_start_row, total_rows - 1)
    pattern_count = loop_row // 64 + 1
    order_count = pattern_count + 1  # include 0xFF terminator
    if order_count & 1:
        order_count += 1             # S3M order count should be even

    header = bytearray(96)
    title = b"FISH HORIZON TITLE"
    header[0:len(title)] = title
    header[28] = 0x1A
    header[29] = 0x10
    struct.pack_into("<H", header, 32, order_count)
    struct.pack_into("<H", header, 34, len(chunks))
    struct.pack_into("<H", header, 36, pattern_count)
    struct.pack_into("<H", header, 38, 0)
    struct.pack_into("<H", header, 40, 0x1320)
    struct.pack_into("<H", header, 42, 2)  # unsigned samples
    header[44:48] = b"SCRM"
    header[48] = 64
    header[49] = S3M_SPEED
    header[50] = S3M_TEMPO
    header[51] = 64                 # mono master volume
    header[52] = 0
    header[53] = 0
    struct.pack_into("<H", header, 62, 0)
    header[64] = 0                  # PCM channel 0 enabled
    header[65:96] = bytes([255]) * 31

    orders = list(range(pattern_count)) + [255]
    while len(orders) < order_count:
        orders.append(255)

    data = bytearray(header)
    data.extend(bytes(orders))
    instrument_ptr_pos = len(data)
    data.extend(b"\0" * (2 * len(chunks)))
    pattern_ptr_pos = len(data)
    data.extend(b"\0" * (2 * pattern_count))
    _align16(data)

    instrument_offsets = []
    for index, chunk in enumerate(chunks, start=1):
        instrument_offsets.append(len(data))
        inst = bytearray(80)
        inst[0] = 1
        filename = f"TTL{index:02d}.RAW".encode("ascii")
        inst[1:1 + len(filename)] = filename
        # sample pointer is filled after sample offsets are known
        struct.pack_into("<I", inst, 16, len(chunk))
        struct.pack_into("<I", inst, 20, 0)
        struct.pack_into("<I", inst, 24, 0)
        inst[28] = 64
        inst[29] = 0
        inst[30] = 0
        inst[31] = 0
        struct.pack_into("<I", inst, 32, SAMPLE_RATE)
        sample_name = f"Title chunk {index:02d}".encode("ascii")
        inst[48:48 + len(sample_name)] = sample_name
        inst[76:80] = b"SCRS"
        data.extend(inst)

    pattern_offsets = []
    events_by_pattern: list[dict[int, tuple[int | None, int | None]]] = [dict() for _ in range(pattern_count)]
    for index in range(len(chunks)):
        global_row = index * rows_per_chunk
        events_by_pattern[global_row // 64][global_row % 64] = (index + 1, None)
    lp = events_by_pattern[loop_row // 64]
    existing = lp.get(loop_row % 64, (None, None))
    lp[loop_row % 64] = (existing[0], 0)

    for events in events_by_pattern:
        _align16(data)
        pattern_offsets.append(len(data))
        data.extend(_s3m_pattern(events))

    sample_offsets = []
    for chunk in chunks:
        _align16(data)
        sample_offsets.append(len(data))
        data.extend(chunk)

    for index, offset in enumerate(instrument_offsets):
        struct.pack_into("<H", data, instrument_ptr_pos + index * 2, offset // 16)
        sample_para = sample_offsets[index] // 16
        data[offset + 13] = (sample_para >> 16) & 0xFF
        struct.pack_into("<H", data, offset + 14, sample_para & 0xFFFF)
    for index, offset in enumerate(pattern_offsets):
        struct.pack_into("<H", data, pattern_ptr_pos + index * 2, offset // 16)

    return bytes(data), len(chunks)


def _wav_bytes(pcm: bytes) -> bytes:
    byte_rate = SAMPLE_RATE * CHANNELS * (SAMPLE_WIDTH_BITS // 8)
    block_align = CHANNELS * (SAMPLE_WIDTH_BITS // 8)
    fmt = struct.pack("<HHIIHH", 1, CHANNELS, SAMPLE_RATE, byte_rate, block_align, SAMPLE_WIDTH_BITS)
    riff_size = 4 + (8 + len(fmt)) + (8 + len(pcm))
    return b"RIFF" + struct.pack("<I", riff_size) + b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(pcm)) + pcm


def _apply_gain_u8(pcm: bytes, gain_db: float) -> bytes:
    if gain_db == 0:
        return pcm
    scale = math.pow(10.0, gain_db / 20.0)
    result = bytearray(len(pcm))
    for index, sample in enumerate(pcm):
        centered = sample - 128
        amplified = int(round(centered * scale))
        if amplified < -128:
            amplified = -128
        elif amplified > 127:
            amplified = 127
        result[index] = amplified + 128
    return bytes(result)


def _decode_mp3(mp3_path: Path) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to stage M5 audio")
    result = subprocess.run(
        [
            ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(mp3_path), "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE),
            "-f", "u8", "-acodec", "pcm_u8", "pipe:1",
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {mp3_path.name}: {result.stderr.decode(errors='replace')}")
    if not result.stdout:
        raise RuntimeError(f"ffmpeg produced no PCM for {mp3_path.name}")
    return result.stdout


def stage_audio_assets(apk_path: Path, output_dir: Path, manifest_path: Path) -> dict[str, object]:
    recovered = recover_from_apk(apk_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.wav", "*.s3m"):
        for existing in output_dir.glob(pattern):
            existing.unlink()

    entries: list[dict[str, object]] = []
    with zipfile.ZipFile(apk_path, "r") as archive, tempfile.TemporaryDirectory() as temp:
        temp_dir = Path(temp)
        by_source = {item["apk_path"]: item for item in recovered["audio"]["assets"]}
        for source, recovered_output_name in sorted(AUDIO_OUTPUTS.items(), key=lambda item: item[1]):
            raw = archive.read(source)
            source_path = temp_dir / Path(source).name
            source_path.write_bytes(raw)
            pcm = _decode_mp3(source_path)
            is_title = source == "assets/audio/music/title.mp3"
            gain_db = 6.0 if is_title else 0.0
            pcm = _apply_gain_u8(pcm, gain_db)

            if is_title:
                output_name = "title.s3m"
                payload, chunk_count = _s3m_bytes(pcm)
                extra = {"format": "s3m", "chunk_count": chunk_count, "sample_rate": SAMPLE_RATE}
            else:
                output_name = recovered_output_name
                payload = _wav_bytes(pcm)
                extra = {"format": "wav"}

            output_path = output_dir / output_name
            output_path.write_bytes(payload)
            entry = {
                "source": source,
                "source_sha256": by_source[source]["sha256"],
                "output": output_name,
                "gain_db": gain_db,
                "frames": len(pcm),
                "duration_ms": round(len(pcm) * 1000 / SAMPLE_RATE, 3),
                "bytes": len(payload),
                "sha256": sha256(payload).hexdigest(),
            }
            entry.update(extra)
            entries.append(entry)

    manifest = {
        "sample_rate": SAMPLE_RATE,
        "channels": CHANNELS,
        "sample_width_bits": SAMPLE_WIDTH_BITS,
        "assets": entries,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "audio")
    parser.add_argument("--manifest", type=Path, default=ROOT / "reference/m5_audio_assets.json")
    args = parser.parse_args(argv)
    stage_audio_assets(args.apk, args.output_dir, args.manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
