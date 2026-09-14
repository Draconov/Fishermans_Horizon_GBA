from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import csv
import zipfile

CANONICAL_APK_SHA256 = "581aeb20073592905b5a82ddc38a54f522f2f369330ae92f025ae7d52ca0d137"


@dataclass(frozen=True, order=True)
class InventoryEntry:
    path: str
    bytes: int


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_inventory(path: Path) -> list[InventoryEntry]:
    with path.open("r", encoding="utf-8", newline="") as source:
        rows = csv.DictReader(source, delimiter="\t")
        return sorted(InventoryEntry(row["path"], int(row["bytes"])) for row in rows)


def apk_inventory(path: Path) -> list[InventoryEntry]:
    with zipfile.ZipFile(path, "r") as archive:
        return sorted(
            InventoryEntry(info.filename, info.file_size)
            for info in archive.infolist()
            if not info.is_dir()
        )


def validate_reference(
    apk_path: Path,
    inventory_path: Path,
    *,
    expected_sha256: str = CANONICAL_APK_SHA256,
) -> list[str]:
    errors: list[str] = []

    actual_sha256 = sha256_file(apk_path)
    if actual_sha256 != expected_sha256:
        errors.append(
            f"SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}"
        )

    expected = {entry.path: entry.bytes for entry in read_inventory(inventory_path)}
    actual = {entry.path: entry.bytes for entry in apk_inventory(apk_path)}

    for path in sorted(expected.keys() - actual.keys()):
        errors.append(f"missing APK entry: {path}")

    for path in sorted(actual.keys() - expected.keys()):
        errors.append(f"unexpected APK entry: {path}")

    for path in sorted(expected.keys() & actual.keys()):
        expected_size = expected[path]
        actual_size = actual[path]
        if expected_size != actual_size:
            errors.append(
                f"APK entry size mismatch: {path}: expected {expected_size}, got {actual_size}"
            )

    return errors
