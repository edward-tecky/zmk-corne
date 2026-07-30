# ZMK Security Integration and Hardware Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove deterministic official-ZMK artifacts satisfy every resolved software gate, then execute the manual hardware checklist before any flash approval.

**Architecture:** Re-resolve the committed frozen manifest in two clean workspaces, build right and locked USB-Studio left twice, compare artifacts/effective configuration, and map every finding to fixed/removed/open evidence. Hardware flashing occurs only after explicit user approval of exact hashes; manual results are recorded without converting failures into silent acceptance.

**Tech Stack:** repository-owned GitHub Actions, SHA-256,
Kconfig/Devicetree, GitHub CLI, physical Corne hardware

## Global Constraints

- Run only after all preceding repository, local-boundary, official-baseline, and selected DYA plans complete.
- No current artifact is implicitly approved.
- User must approve exact SHA-256 values before first flash.
- Build all four validation targets twice from the same exact source using
  repository-owned CI. Upload no firmware artifacts before approval.
- Any hash mismatch, open applicable firmware finding, build warning classified as correctness/memory safety, or failed manual test stops approval.
- Record hardware-only behavior as manual evidence.
- Never mark ZMK-SEC-009 closed while official BLE Studio remains disabled rather than fixed.
- Never distribute settings-reset while ZMK-SEC-021 remains open.

---

## Planned File Structure

- Create `security/scripts/verify_release_gate.py`: deterministic artifact/config/finding gate.
- Create `security/audit/release-candidate-evidence.md`: commands, hashes, configs, finding map, and user approval.
- Modify `security/audit/manual-hardware-tests.md`: append dated result/evidence columns without deleting original checks.

### Task 1: Build and Verify Deterministic Release Candidates

**Files:**
- Create: `security/scripts/verify_release_gate.py`
- Create: `security/audit/release-candidate-evidence.md`

**Interfaces:**
- Consumes: committed frozen manifest and official baseline.
- Produces: exact right/Studio-left hashes and machine-checked gate result.

- [x] **Step 1: Create failing release-gate test script**

```python
#!/usr/bin/env python3
from pathlib import Path
import hashlib
import sys


ROOTS = (Path("/tmp/zmk-release-a"), Path("/tmp/zmk-release-b"))
ARTIFACTS = ("right", "studio")
REQUIRED_STUDIO = {
    "CONFIG_ZMK_STUDIO=y",
    "CONFIG_ZMK_STUDIO_LOCKING=y",
    "CONFIG_ZMK_STUDIO_TRANSPORT_BLE=n",
}
FORBIDDEN_RIGHT_PREFIXES = (
    "CONFIG_ZMK_STUDIO=y",
    "CONFIG_ZMK_BLE_MANAGEMENT=y",
    "CONFIG_ZMK_SETTINGS_RPC=y",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    for artifact in ARTIFACTS:
        first = ROOTS[0] / "build" / artifact / "zephyr" / "zmk.uf2"
        second = ROOTS[1] / "build" / artifact / "zephyr" / "zmk.uf2"
        if not first.exists() or not second.exists():
            raise SystemExit(f"missing {artifact} build")
        if digest(first) != digest(second):
            raise SystemExit(f"nondeterministic {artifact}")

    right = (ROOTS[0] / "build/right/zephyr/.config").read_text().splitlines()
    studio = (ROOTS[0] / "build/studio/zephyr/.config").read_text().splitlines()
    for symbol in FORBIDDEN_RIGHT_PREFIXES:
        if symbol in right:
            raise SystemExit(f"right exposes {symbol}")
    missing = REQUIRED_STUDIO.difference(studio)
    if missing:
        raise SystemExit(f"studio missing {sorted(missing)}")
    print("release software gate passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [x] **Step 2: Run RED before evidence**

```bash
python3 security/scripts/verify_release_gate.py
```

Expected: fails with `missing right build`.

- [x] **Step 3: Dispatch two exact-source clean CI runs**

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
for root in /tmp/zmk-release-a /tmp/zmk-release-b; do
  rm -rf "$root"
  mkdir "$root"
  cp -a "$REPO_ROOT/config" "$root/config"
  (
    cd "$root"
    west init -l config
    west update
    west zephyr-export
    west manifest --freeze > frozen.yml
  )
done
diff -u /tmp/zmk-release-a/frozen.yml /tmp/zmk-release-b/frozen.yml
```

- [x] **Step 4: Build four validation targets twice**

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
for root in /tmp/zmk-release-a /tmp/zmk-release-b; do
  (
    cd "$root"
    west build -p always -s zmk/app -d build/right \
      -b nice_nano_v2 -- -DZMK_CONFIG="$REPO_ROOT/config" \
      -DZMK_EXTRA_MODULES="$REPO_ROOT" \
      '-DSHIELD=eyelash_corne_right nice_view'
    west build -p always -s zmk/app -d build/studio \
      -b nice_nano_v2 -S studio-rpc-usb-uart -- \
      -DZMK_CONFIG="$REPO_ROOT/config" -DZMK_EXTRA_MODULES="$REPO_ROOT" \
      '-DSHIELD=eyelash_corne_left eyelash_corne_studio nice_view' \
      -DCONFIG_ZMK_STUDIO=y -DCONFIG_ZMK_STUDIO_LOCKING=y \
      -DCONFIG_ZMK_STUDIO_TRANSPORT_BLE=n
  )
done
```

- [x] **Step 5: Run GREEN and record evidence**

```bash
python3 security/scripts/verify_release_gate.py
sha256sum /tmp/zmk-release-{a,b}/build/{right,studio}/zephyr/zmk.uf2
git diff --check
```

Write exact commands/output, manifest digest, tool versions, artifact hashes,
effective security symbols, and warning inventory to
`security/audit/release-candidate-evidence.md`.

- [x] **Step 6: Add finding map**

Add one row for every ZMK-SEC-001 through ZMK-SEC-021 with status restricted to:

```text
fixed-verified
removed-verified
open-disabled
open-blocking
```

Any `open-blocking` stops this plan. `open-disabled` must name the disabled feature
and effective-build evidence.

- [x] **Step 7: Commit software gate**

```bash
git add security/scripts/verify_release_gate.py \
  security/audit/release-candidate-evidence.md
git diff --cached --check
git commit -m "test: verify ZMK release candidate gate"
```

### Task 2: Obtain Exact-Artifact Flash Approval

**Files:**
- Modify: `security/audit/release-candidate-evidence.md`

- [ ] Present right, locked BLE+USB Studio-left, and settings-reset SHA-256
  values plus all open-disabled findings to user.
- [ ] Wait for explicit approval naming all three hashes. A generic “go ahead”
  without matching hashes does not authorize flashing.
- [ ] Record approval text/date in evidence file and commit:

```bash
git add security/audit/release-candidate-evidence.md
git commit -m "docs: record ZMK artifact approval"
```

### Task 3: Execute Manual Hardware Checklist

**Files:**
- Modify: `security/audit/manual-hardware-tests.md`
- Modify: `security/audit/release-candidate-evidence.md`

- [ ] Flash only approved right, Studio-left, and settings-reset hashes.
- [ ] Execute all 18 existing checklist items in order, recording date, host,
  observed result, PASS/FAIL, and recovery notes.
- [ ] Stop immediately on failed recovery, unexpected HID, unlocked Studio access,
  missing relock, split propagation error, or sleep/wake failure.
- [ ] Verify Studio USB is rejected while locked, accepted after physical
  `&studio_unlock`, and rejected after disconnect/600-second idle relock.
- [ ] Confirm encrypted BLE Studio enforces the same lock-before-unlock and
  relock policy as USB Studio.
- [ ] Run all keys, five-way switch, encoder directions on every layer, mouse,
  RGB/backlight, host switching, split propagation, sleep/wake, soft-off, and idle
  HID observation.
- [ ] Commit factual results without changing FAIL to accepted:

```bash
git add security/audit/manual-hardware-tests.md \
  security/audit/release-candidate-evidence.md
git diff --cached --check
git commit -m "test: record ZMK hardware security gate"
```

Expected: flash recommendation exists only if all 18 checks pass and no finding is
`open-blocking`.
