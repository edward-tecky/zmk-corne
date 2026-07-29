# Official ZMK Baseline and Firmware Finding Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a frozen official-ZMK baseline with zero DYA modules, then review ZMK-SEC-004/008/009/014/015/016/017/021 separately against effective build evidence.

**Architecture:** Generate a frozen west manifest from official ZMK commit `faaf39d9f59cd2a27eca3739cdd9eb197654299b`, convert the encoder to official sensor rotation, and remove every DYA include/Kconfig/module. Disable BLE Studio because that official revision retains ZMK-SEC-009; remove settings-reset from distributable artifacts while ZMK-SEC-021 remains unresolved. One migration commit creates shared evidence; each finding receives an individual verdict in a committed evidence matrix.

**Tech Stack:** Official ZMK, west 1.5.0, Zephyr SDK 0.16.3, Devicetree/Kconfig, Python 3 `unittest`

## Global Constraints

- Require completed ZMK-SEC-001/002/003/006/007/020 plans first.
- Require user approval before migration.
- Use official ZMK commit `faaf39d9f59cd2a27eca3739cdd9eb197654299b`.
- Baseline contains no Cormoran core fork and no DYA firmware module.
- Disable BLE Studio until a later reviewed official commit fixes ZMK-SEC-009.
- Do not distribute or flash settings-reset while ZMK-SEC-021 remains open.
- Build normal right and locked USB-Studio left twice from clean frozen inputs.
- No flash during this plan.
- Shared build evidence may support several findings, but record each verdict separately.

---

## Planned File Structure

- Create `security/tests/test_official_baseline.py`: source/config absence and official-baseline contracts.
- Modify `config/west.yml`: generated full-SHA official graph.
- Modify `config/eyelash_corne.keymap`: official sensor-rotate behavior.
- Modify left/right overlays and conf files: remove DYA includes/symbols.
- Modify `boards/shields/eyelash_corne/eyelash_corne_studio.conf`: official Studio only, BLE transport disabled.
- Modify `build.yaml`: normal right plus locked USB Studio-left; remove settings-reset distribution.
- Create `security/audit/official-baseline-evidence.md`: immutable manifest digest, build hashes, effective configs, and separate finding verdicts.

### Task 1: Generate Frozen Official Manifest

**Files:**
- Create: `security/tests/test_official_baseline.py`
- Modify: `config/west.yml`

**Interfaces:**
- Consumes: official ZMK SHA.
- Produces: frozen root manifest whose every project revision is a 40-character SHA.

- [ ] **Step 1: Write failing manifest test**

```python
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
WEST = ROOT / "config" / "west.yml"
KEYMAP = ROOT / "config" / "eyelash_corne.keymap"
BUILD = ROOT / "build.yaml"
SHIELD_ROOT = ROOT / "boards" / "shields" / "eyelash_corne"
OFFICIAL_ZMK_SHA = "faaf39d9f59cd2a27eca3739cdd9eb197654299b"


class OfficialBaselineTests(unittest.TestCase):
    def test_manifest_uses_only_full_sha_revisions_and_official_zmk(self) -> None:
        manifest = WEST.read_text(encoding="utf-8")
        self.assertIn("url: https://github.com/zmkfirmware/zmk", manifest)
        self.assertRegex(
            manifest,
            rf"(?ms)- name: zmk\b.*?revision: {OFFICIAL_ZMK_SHA}\b",
        )
        self.assertNotIn("cormoran", manifest.lower())
        revisions = re.findall(r"(?m)^\s+revision:\s+(\S+)", manifest)
        self.assertGreater(len(revisions), 10)
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{40}", x) for x in revisions))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify RED**

```bash
python3 security/tests/test_official_baseline.py
```

Expected: current manifest contains Cormoran and fewer than the frozen official graph projects.

- [ ] **Step 3: Generate candidate and freeze it**

```bash
rm -rf /tmp/zmk-official-freeze
mkdir -p /tmp/zmk-official-freeze/config
cat > /tmp/zmk-official-freeze/config/west.yml <<'YAML'
manifest:
  projects:
    - name: zmk
      url: https://github.com/zmkfirmware/zmk
      revision: faaf39d9f59cd2a27eca3739cdd9eb197654299b
      import: app/west.yml
  self:
    path: config
YAML
python3 -m venv /tmp/zmk-official-venv
/tmp/zmk-official-venv/bin/pip install west==1.5.0
(
  cd /tmp/zmk-official-freeze
  /tmp/zmk-official-venv/bin/west init -l config
  /tmp/zmk-official-venv/bin/west update
  /tmp/zmk-official-venv/bin/west manifest --freeze > frozen.yml
)
cp /tmp/zmk-official-freeze/frozen.yml config/west.yml
```

Open generated file and ensure `self.path` remains `config`; change only that field if west emitted a different manifest path.

- [ ] **Step 4: Verify GREEN and deterministic graph**

```bash
python3 security/tests/test_official_baseline.py
cp /tmp/zmk-official-freeze/frozen.yml /tmp/official-frozen-first.yml
rm -rf /tmp/zmk-official-freeze-2
mkdir /tmp/zmk-official-freeze-2
cp -a config /tmp/zmk-official-freeze-2/config
(
  cd /tmp/zmk-official-freeze-2
  /tmp/zmk-official-venv/bin/west init -l config
  /tmp/zmk-official-venv/bin/west update
  /tmp/zmk-official-venv/bin/west manifest --freeze > frozen.yml
)
diff -u /tmp/official-frozen-first.yml \
  /tmp/zmk-official-freeze-2/frozen.yml
```

Expected: tests pass and frozen graphs match.

### Task 2: Convert Local Configuration to Official Features

**Files:**
- Modify: `config/eyelash_corne.keymap`
- Modify: `boards/shields/eyelash_corne/eyelash_corne_left.overlay`
- Modify: `boards/shields/eyelash_corne/eyelash_corne_right.overlay`
- Modify: left/right/Studio `.conf`
- Modify: `build.yaml`
- Modify: `security/tests/test_official_baseline.py`

**Interfaces:**
- Consumes: official behaviors and locked additive Studio shield.
- Produces: zero-DYA local configuration with USB-only Studio.

- [ ] **Step 1: Add failing absence/official-feature tests**

```python
    def test_local_configuration_contains_no_dya_interfaces(self) -> None:
        files = [
            KEYMAP,
            SHIELD_ROOT / "eyelash_corne_left.overlay",
            SHIELD_ROOT / "eyelash_corne_right.overlay",
            SHIELD_ROOT / "eyelash_corne_left.conf",
            SHIELD_ROOT / "eyelash_corne_right.conf",
            SHIELD_ROOT / "eyelash_corne_studio.conf",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
        forbidden = (
            "runtime-sensor-rotate",
            "runtime-input-processor",
            "battery_history_request",
            "ZMK_BLE_MANAGEMENT",
            "ZMK_SETTINGS_RPC",
            "ZMK_SPLIT_RELAY_EVENT",
        )
        for token in forbidden:
            self.assertNotIn(token, combined)

    def test_official_encoder_and_usb_only_locked_studio(self) -> None:
        keymap = KEYMAP.read_text(encoding="utf-8")
        self.assertIn('compatible = "zmk,behavior-sensor-rotate";', keymap)
        self.assertIn("bindings = <&kp C_VOL_UP>, <&kp C_VOL_DN>;", keymap)
        studio = (
            SHIELD_ROOT / "eyelash_corne_studio.conf"
        ).read_text(encoding="utf-8")
        self.assertIn("CONFIG_ZMK_STUDIO=y", studio)
        self.assertIn("CONFIG_ZMK_STUDIO_TRANSPORT_BLE=n", studio)
        self.assertIn("CONFIG_ZMK_STUDIO_LOCKING=y", BUILD.read_text())
        self.assertNotIn("settings_reset", BUILD.read_text())
```

- [ ] **Step 2: Verify RED**

```bash
python3 security/tests/test_official_baseline.py
```

Expected: custom includes/symbols remain; keymap uses runtime behavior; settings-reset remains distributed.

- [ ] **Step 3: Convert encoder behavior**

Replace runtime behavior include with:

```dts
#include <behaviors.dtsi>
```

Replace `rsr_vol` node with:

```dts
        encoder_volume: encoder_volume {
            compatible = "zmk,behavior-sensor-rotate";
            #sensor-binding-cells = <0>;
            bindings = <&kp C_VOL_UP>, <&kp C_VOL_DN>;
        };
```

Replace every `sensor-bindings = <&rsr_vol>;` with:

```dts
sensor-bindings = <&encoder_volume>;
```

- [ ] **Step 4: Remove DYA overlay includes and symbols**

Delete `battery_history_request.dtsi`, `runtime-input-processor.dtsi`, and custom
processor includes from left/right overlays. Delete all `ZMK_BLE_MANAGEMENT`,
`ZMK_SETTINGS_RPC`, `ZMK_SPLIT_RELAY_EVENT`, `ZMK_RUNTIME_INPUT_PROCESSOR`,
`ZMK_RUNTIME_SENSOR_ROTATE`, and battery-history symbols from left/right/Studio
conf files.

Set Studio add-on conf to:

```conf
CONFIG_ZMK_STUDIO=y
CONFIG_ZMK_STUDIO_TRANSPORT_BLE=n
```

- [ ] **Step 5: Remove settings-reset artifact**

Keep only normal right and locked Studio-left entries in `build.yaml`. Preserve:

```yaml
    snippet: studio-rpc-usb-uart
    cmake-args: -DCONFIG_ZMK_STUDIO=y -DCONFIG_ZMK_STUDIO_LOCKING=y -DCONFIG_ZMK_STUDIO_TRANSPORT_BLE=n
```

- [ ] **Step 6: Run tests and build twice**

```bash
python3 security/tests/test_official_baseline.py
git diff --check
REPO_ROOT="$(git rev-parse --show-toplevel)"
for pass in first second; do
  (
    cd /tmp/zmk-official-freeze
    /tmp/zmk-official-venv/bin/west build -p always -s zmk/app \
      -d "/tmp/official-$pass-right" -b nice_nano_v2 -- \
      -DZMK_CONFIG="$REPO_ROOT/config" -DZMK_EXTRA_MODULES="$REPO_ROOT" \
      '-DSHIELD=eyelash_corne_right nice_view'
    /tmp/zmk-official-venv/bin/west build -p always -s zmk/app \
      -d "/tmp/official-$pass-studio" -b nice_nano_v2 \
      -S studio-rpc-usb-uart -- \
      -DZMK_CONFIG="$REPO_ROOT/config" -DZMK_EXTRA_MODULES="$REPO_ROOT" \
      '-DSHIELD=eyelash_corne_left eyelash_corne_studio nice_view' \
      -DCONFIG_ZMK_STUDIO=y -DCONFIG_ZMK_STUDIO_LOCKING=y \
      -DCONFIG_ZMK_STUDIO_TRANSPORT_BLE=n
  )
done
sha256sum /tmp/official-{first,second}-{right,studio}/zephyr/zmk.uf2
cmp /tmp/official-first-right/zephyr/zmk.uf2 \
  /tmp/official-second-right/zephyr/zmk.uf2
cmp /tmp/official-first-studio/zephyr/zmk.uf2 \
  /tmp/official-second-studio/zephyr/zmk.uf2
```

Expected: all builds pass and each pair is identical.

- [ ] **Step 7: Commit migration implementation**

```bash
git add config/west.yml config/eyelash_corne.keymap build.yaml \
  boards/shields/eyelash_corne security/tests/test_official_baseline.py
git diff --cached --check
git commit -m "build: establish official ZMK baseline"
```

### Task 3: Record Finding-by-Finding Gates

**Files:**
- Create: `security/audit/official-baseline-evidence.md`

**Interfaces:**
- Consumes: exact effective configs, frozen graph, and repeat hashes from Tasks 1-2.
- Produces: separate verdicts without merging finding decisions.

- [ ] **Step 1: Capture immutable evidence**

```bash
sha256sum config/west.yml \
  /tmp/official-first-right/zephyr/zmk.uf2 \
  /tmp/official-first-studio/zephyr/zmk.uf2 \
  > /tmp/official-baseline-hashes.txt
rg -n '^CONFIG_(ZMK_STUDIO|ZMK_STUDIO_LOCKING|ZMK_STUDIO_TRANSPORT_BLE|ZMK_BLE_MANAGEMENT|ZMK_SETTINGS_RPC|ZMK_RUNTIME_INPUT_PROCESSOR|ZMK_SPLIT_RELAY_EVENT)=' \
  /tmp/official-first-{right,studio}/zephyr/.config \
  > /tmp/official-baseline-config.txt
```

- [ ] **Step 2: Create exact verdict matrix**

Write `security/audit/official-baseline-evidence.md` with these rows and attach command output:

```markdown
| Finding | Verdict after baseline | Evidence rule |
|---|---|---|
| ZMK-SEC-004 | Removed from baseline | No BLE/settings custom module or symbol in graph/effective config |
| ZMK-SEC-008 | Removed from baseline | Cormoran split relay delta absent |
| ZMK-SEC-009 | Open; BLE Studio disabled | Official inspected SHA remains affected |
| ZMK-SEC-014 | Removed from baseline | Cormoran wired delta absent; wired split disabled |
| ZMK-SEC-015 | Removed from baseline | Cormoran ignore-position delta absent |
| ZMK-SEC-016 | Removed from baseline | Runtime-sensor/BLE modules absent |
| ZMK-SEC-017 | Removed from baseline | Runtime-input module absent |
| ZMK-SEC-021 | Open; settings-reset undistributed | Upstream guard/instrumented test absent |
```

Do not label ZMK-SEC-009 or ZMK-SEC-021 closed.

- [ ] **Step 3: Commit evidence**

```bash
git add security/audit/official-baseline-evidence.md
git diff --cached --check
git commit -m "docs: record official baseline security gates"
```
