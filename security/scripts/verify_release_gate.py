#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re


REQUIRED_TARGETS = {"right", "left", "studio-left", "settings-reset"}
EXPECTED_DEFERRED = {"ZMK-SEC-009", "ZMK-SEC-021"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ledger", default="security/audit/remediation-ledger.md"
    )
    parser.add_argument("--hardware")
    parser.add_argument(
        "--release", default="security/audit/release-gate.json"
    )
    args = parser.parse_args()

    release = json.loads(Path(args.release).read_text(encoding="utf-8"))
    if release["phase"] not in {"pre-flash", "hardware-complete"}:
        raise SystemExit("invalid release phase")
    if len(release["source_commit"]) != 40:
        raise SystemExit("source commit is not a full SHA")
    if set(release["artifacts"]) != REQUIRED_TARGETS:
        raise SystemExit("release target set mismatch")
    for target, evidence in release["artifacts"].items():
        if len(evidence["sha256"]) != 64:
            raise SystemExit(f"invalid {target} SHA-256")
        if evidence["run_a_sha256"] != evidence["run_b_sha256"]:
            raise SystemExit(f"nondeterministic {target}")
        if evidence["sha256"] != evidence["run_a_sha256"]:
            raise SystemExit(f"canonical hash mismatch for {target}")
    if release["uploaded_artifact_count"] != 0:
        raise SystemExit("unapproved firmware artifact was uploaded")

    ledger = Path(args.ledger).read_text(encoding="utf-8")
    rows = dict(
        re.findall(
            r"^\| (ZMK-SEC-\d{3}) \| "
            r"(fixed|removed|deferred-open) \|",
            ledger,
            re.MULTILINE,
        )
    )
    if len(rows) != 21:
        raise SystemExit("ledger is not software-gate complete")
    deferred = {finding for finding, status in rows.items()
                if status == "deferred-open"}
    if deferred != EXPECTED_DEFERRED:
        raise SystemExit(f"unexpected deferred findings: {sorted(deferred)}")

    if args.hardware and release["phase"] == "hardware-complete":
        hardware = Path(args.hardware).read_text(encoding="utf-8")
        if hardware.count("- [x]") != 18:
            raise SystemExit("hardware checklist is incomplete")

    print("release software gate passed")


if __name__ == "__main__":
    main()
