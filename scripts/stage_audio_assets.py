from __future__ import annotations

import argparse
from hashlib import sha256
import json
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


def _wav_bytes(pcm: bytes) -> bytes:
    byte_rate = SAMPLE_RATE * CHANNELS * (SAMPLE_WIDTH_BITS // 8)
    block_align = CHANNELS * (SAMPLE_WIDTH_BITS // 8)
    fmt = struct.pack("<HHIIHH", 1, CHANNELS, SAMPLE_RATE, byte_rate, block_align, SAMPLE_WIDTH_BITS)
    riff_size = 4 + (8 + len(fmt)) + (8 + len(pcm))
    return b"RIFF" + struct.pack("<I", riff_size) + b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(pcm)) + pcm


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
    for existing in output_dir.glob("*.wav"):
        existing.unlink()

    entries: list[dict[str, object]] = []
    with zipfile.ZipFile(apk_path, "r") as archive, tempfile.TemporaryDirectory() as temp:
        temp_dir = Path(temp)
        by_source = {item["apk_path"]: item for item in recovered["audio"]["assets"]}
        for source, output_name in sorted(AUDIO_OUTPUTS.items(), key=lambda item: item[1]):
            raw = archive.read(source)
            source_path = temp_dir / Path(source).name
            source_path.write_bytes(raw)
            pcm = _decode_mp3(source_path)
            wav = _wav_bytes(pcm)
            output_path = output_dir / output_name
            output_path.write_bytes(wav)
            entries.append({
                "source": source,
                "source_sha256": by_source[source]["sha256"],
                "output": output_name,
                "frames": len(pcm),
                "duration_ms": round(len(pcm) * 1000 / SAMPLE_RATE, 3),
                "bytes": len(wav),
                "sha256": sha256(wav).hexdigest(),
            })

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
