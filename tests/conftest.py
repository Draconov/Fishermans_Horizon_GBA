from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def reference_apk() -> Path:
    value = os.environ.get("FH_REFERENCE_APK")
    if not value:
        pytest.skip("FH_REFERENCE_APK is not set")
    path = Path(value)
    if not path.is_file():
        pytest.fail(f"FH_REFERENCE_APK does not exist: {path}")
    return path


@pytest.fixture(scope="session")
def reference_dex(reference_apk: Path) -> bytes:
    import zipfile

    with zipfile.ZipFile(reference_apk, "r") as archive:
        return archive.read("classes.dex")


@pytest.fixture(scope="session")
def reference_dex_file(reference_dex: bytes):
    from tools.dex import DexFile

    return DexFile(reference_dex)
