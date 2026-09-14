from __future__ import annotations

import zipfile
from pathlib import Path

from tools.reference_apk import apk_inventory, sha256_file, validate_reference


def test_sha256_file_matches_known_bytes(tmp_path: Path):
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"fishermans-horizon")
    assert sha256_file(sample) == "ef5e5760b629ca064d6ec74b5ef5438365cde68153d41a52ebb7be8a63b42fb9"


def test_apk_inventory_reports_zip_entries(tmp_path: Path):
    apk = tmp_path / "sample.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("b.bin", b"12345")
        archive.writestr("a.txt", b"hi")

    entries = apk_inventory(apk)
    assert [(entry.path, entry.bytes) for entry in entries] == [
        ("a.txt", 2),
        ("b.bin", 5),
    ]


def test_validate_reference_reports_hash_and_inventory_mismatches(tmp_path: Path):
    apk = tmp_path / "sample.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("actual.bin", b"abc")

    inventory = tmp_path / "inventory.tsv"
    inventory.write_text("path\tbytes\nexpected.bin\t4\n", encoding="utf-8")

    errors = validate_reference(apk, inventory, expected_sha256="0" * 64)
    assert any("SHA-256 mismatch" in error for error in errors)
    assert "missing APK entry: expected.bin" in errors
    assert "unexpected APK entry: actual.bin" in errors


def test_reference_apk_matches_frozen_hash_and_inventory(reference_apk: Path):
    assert validate_reference(reference_apk, Path("reference/apk_inventory.tsv")) == []
