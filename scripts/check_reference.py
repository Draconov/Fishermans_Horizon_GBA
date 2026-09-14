#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.reference_apk import CANONICAL_APK_SHA256, validate_reference


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the canonical Fisherman's Horizon APK")
    parser.add_argument("apk", type=Path)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=ROOT / "reference" / "apk_inventory.tsv",
    )
    args = parser.parse_args(argv)

    if not args.apk.is_file():
        print(f"reference APK not found: {args.apk}", file=sys.stderr)
        return 2

    errors = validate_reference(args.apk, args.inventory)
    if errors:
        print("reference APK verification FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"reference APK OK: {args.apk}")
    print(f"SHA-256: {CANONICAL_APK_SHA256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
