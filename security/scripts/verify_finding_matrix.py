#!/usr/bin/env python3
from pathlib import Path
import re
import sys


EXPECTED = {
    "ZMK-SEC-004": "Removed from baseline",
    "ZMK-SEC-008": "Removed from baseline",
    "ZMK-SEC-009": "Open; BLE Studio disabled",
    "ZMK-SEC-014": "Removed from baseline",
    "ZMK-SEC-015": "Removed from baseline",
    "ZMK-SEC-016": "Removed from baseline",
    "ZMK-SEC-017": "Removed from baseline",
    "ZMK-SEC-021": "Open; settings-reset undistributed",
}


def main() -> None:
    path = Path(sys.argv[1])
    rows = dict(
        re.findall(
            r"^\| (ZMK-SEC-\d{3}) \| ([^|]+?) \|",
            path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
    )
    if rows != EXPECTED:
        raise SystemExit(f"finding matrix mismatch: {rows!r}")


if __name__ == "__main__":
    main()
