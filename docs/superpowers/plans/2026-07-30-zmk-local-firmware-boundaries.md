# ZMK Local Firmware Boundary Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close ZMK-SEC-003, ZMK-SEC-007, and ZMK-SEC-020 while preserving ordinary keyboard behavior and creating one explicit locked Studio artifact.

**Architecture:** First enable Studio locking in the existing Studio build. Then move management Kconfig symbols from the generic left shield into an additive `eyelash_corne_studio` shield selected only by the Studio build. Finally align the single physical encoder with one `rsr_vol` binding per layer and remove the dropped `rsr_trans` declaration.

**Tech Stack:** ZMK/Zephyr Kconfig, Devicetree, build matrix YAML, Python 3
`unittest`, repository-owned GitHub Actions

## Global Constraints

- Execute each finding as a separate task, commit, and review.
- Require user approval before each task.
- Build right, ordinary left, locked Studio-left, and settings-reset after
  configuration changes using repository-owned GitHub Actions.
- Validation workflow must upload no firmware artifacts.
- Push only to `edward-tecky/zmk-corne`; open no pull requests.
- Never flash during this plan.
- Preserve physical `&studio_unlock` at `config/eyelash_corne.keymap:91`.
- Ordinary left and right artifacts must contain no Studio/custom management RPC.
- Studio-left must use `CONFIG_ZMK_STUDIO_LOCKING=y`, disconnect relock, and idle relock.
- Keep one physical encoder and one sensor binding per layer.

---

## Planned File Structure

- Create `security/tests/test_firmware_security.py`: static artifact-boundary and sensor-capacity contracts.
- Create `security/build-firmware-boundaries.yaml`: non-published four-artifact
  validation matrix.
- Create `.github/workflows/security-firmware-boundaries.yml`: CI caller.
- Modify `.github/workflows/build-user-config-pinned.yml`: allow callers to
  suppress artifact upload while retaining build/Kconfig/devicetree logs.
- Modify `boards/shields/eyelash_corne/eyelash_corne_left.conf`: ordinary central hardware only.
- Modify `boards/shields/eyelash_corne/Kconfig.shield`: declare additive Studio shield.
- Create `boards/shields/eyelash_corne/eyelash_corne_studio.conf`: Studio/custom-management symbols.
- Create `boards/shields/eyelash_corne/eyelash_corne_studio.overlay`: empty additive overlay.
- Modify `config/eyelash_corne.keymap`: one encoder binding per layer.

### Task 1: ZMK-SEC-003 — Enable Studio Locking

**Files:**
- Create: `security/tests/test_firmware_security.py`
- Modify: `security/build-firmware-boundaries.yaml`

**Interfaces:**
- Consumes: existing Studio artifact and physical `&studio_unlock`.
- Produces: build declaration requiring Studio locking.

- [x] **Step 1: Write locking contract test**

Create:

```python
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
BUILD_MATRIX = ROOT / "build.yaml"
LEFT_CONF = (
    ROOT / "boards" / "shields" / "eyelash_corne"
    / "eyelash_corne_left.conf"
)
STUDIO_CONF = (
    ROOT / "boards" / "shields" / "eyelash_corne"
    / "eyelash_corne_studio.conf"
)
KEYMAP = ROOT / "config" / "eyelash_corne.keymap"


class FirmwareSecurityTests(unittest.TestCase):
    def test_studio_artifact_enables_locking(self) -> None:
        matrix = BUILD_MATRIX.read_text(encoding="utf-8")
        self.assertIn("-DCONFIG_ZMK_STUDIO_LOCKING=y", matrix)
        self.assertNotIn("-DCONFIG_ZMK_STUDIO_LOCKING=n", matrix)
        self.assertIn("&studio_unlock", KEYMAP.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Verify existing CI harness already satisfies locking contract**

```bash
python3 security/tests/test_firmware_security.py
```

Expected: locking test fails because build matrix contains `LOCKING=n`.

- [x] **Step 3: Enable locking**

Set the Studio validation entry to:

```yaml
    cmake-args: -DCONFIG_ZMK_STUDIO=y -DCONFIG_ZMK_STUDIO_LOCKING=y
```

- [x] **Step 4: Verify GREEN and build Studio-left**

```bash
python3 security/tests/test_firmware_security.py
python3 security/tests/test_workflow_security.py
git diff --check
git push origin main
gh run watch "$(gh run list --workflow security-firmware-boundaries.yml \
  --branch main --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
gh run view "$(gh run list --workflow security-firmware-boundaries.yml \
  --branch main --limit 1 --json databaseId --jq '.[0].databaseId')" --log |
  grep -E 'CONFIG_ZMK_STUDIO_LOCKING=y|CONFIG_ZMK_BEHAVIOR_STUDIO_UNLOCK=y'
```

Expected: test/build pass and both effective symbols print.

- [x] **Step 5: Commit ZMK-SEC-003**

```bash
git add build.yaml security/tests/test_firmware_security.py
git diff --cached --check
git commit -m "build: require Studio physical unlock"
```

### Task 2: ZMK-SEC-007 — Isolate Studio Management Configuration

**Files:**
- Modify: `boards/shields/eyelash_corne/eyelash_corne_left.conf:14-29`
- Modify: `boards/shields/eyelash_corne/Kconfig.shield`
- Create: `boards/shields/eyelash_corne/eyelash_corne_studio.conf`
- Create: `boards/shields/eyelash_corne/eyelash_corne_studio.overlay`
- Modify: `security/build-firmware-boundaries.yaml`
- Modify: `security/tests/test_firmware_security.py`

**Interfaces:**
- Consumes: base `eyelash_corne_left` shield.
- Produces: additive `eyelash_corne_studio` shield selected only by Studio build.

- [x] **Step 1: Add failing artifact-boundary tests**

Add:

```python
    def test_generic_left_excludes_management_interfaces(self) -> None:
        left = LEFT_CONF.read_text(encoding="utf-8")
        forbidden = (
            "CONFIG_ZMK_STUDIO=",
            "CONFIG_ZMK_BLE_MANAGEMENT=",
            "CONFIG_ZMK_BLE_MANAGEMENT_STUDIO_RPC=",
            "CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR=",
            "CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR_STUDIO_RPC=",
            "CONFIG_ZMK_SETTINGS_RPC=",
            "CONFIG_ZMK_SETTINGS_RPC_STUDIO=",
            "CONFIG_ZMK_RUNTIME_SENSOR_ROTATE_STUDIO_RPC=",
        )
        for symbol in forbidden:
            self.assertNotIn(symbol, left)

    def test_studio_add_on_owns_management_interfaces(self) -> None:
        studio = STUDIO_CONF.read_text(encoding="utf-8")
        required = (
            "CONFIG_ZMK_STUDIO=y",
            "CONFIG_ZMK_BLE_MANAGEMENT=y",
            "CONFIG_ZMK_BLE_MANAGEMENT_STUDIO_RPC=y",
            "CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR=y",
            "CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR_STUDIO_RPC=y",
            "CONFIG_ZMK_SETTINGS_RPC=y",
            "CONFIG_ZMK_SETTINGS_RPC_STUDIO=y",
            "CONFIG_ZMK_RUNTIME_SENSOR_ROTATE_STUDIO_RPC=y",
        )
        for symbol in required:
            self.assertIn(symbol, studio)

        matrix = BUILD_MATRIX.read_text(encoding="utf-8")
        self.assertIn(
            "shield: eyelash_corne_left eyelash_corne_studio nice_view",
            matrix,
        )
```

- [x] **Step 2: Verify RED**

```bash
python3 security/tests/test_firmware_security.py
```

Expected: add-on file missing and generic left still enables management.

- [x] **Step 3: Declare additive Studio shield**

Append to `Kconfig.shield`:

```kconfig
config SHIELD_EYELASH_CORNE_STUDIO
    def_bool $(shields_list_contains,eyelash_corne_studio)
```

Create `eyelash_corne_studio.overlay`:

```dts
/*
 * Additive Studio configuration shield.
 * Hardware remains owned by eyelash_corne_left.
 */

/ {
};
```

- [x] **Step 4: Move management symbols into add-on conf**

Create `eyelash_corne_studio.conf`:

```conf
# Studio transport and custom management RPCs.
CONFIG_ZMK_STUDIO=y
CONFIG_ZMK_BLE_MANAGEMENT=y
CONFIG_ZMK_BLE_MANAGEMENT_STUDIO_RPC=y
CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR=y
CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR_STUDIO_RPC=y
CONFIG_ZMK_SETTINGS_RPC=y
CONFIG_ZMK_SETTINGS_RPC_STUDIO=y
CONFIG_ZMK_RUNTIME_SENSOR_ROTATE_STUDIO_RPC=y
```

Delete the corresponding symbols from `eyelash_corne_left.conf`. Keep
`CONFIG_ZMK_RUNTIME_SENSOR_ROTATE=y`, `CONFIG_SETTINGS=y`, split settings, encoder,
power, and battery-disabled symbols in generic left.

- [x] **Step 5: Select add-on shield only for Studio build**

Change Studio entry:

```yaml
  - board: nice_nano_v2
    shield: eyelash_corne_left eyelash_corne_studio nice_view
    snippet: studio-rpc-usb-uart
    cmake-args: -DCONFIG_ZMK_STUDIO=y -DCONFIG_ZMK_STUDIO_LOCKING=y
    artifact-name: eyelash_corne_studio_left
```

- [ ] **Step 6: Verify tests and all effective artifacts**

```bash
python3 security/tests/test_firmware_security.py
python3 security/tests/test_workflow_security.py
git diff --check
git push origin main
gh run watch "$(gh run list --workflow security-firmware-boundaries.yml \
  --branch main --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
gh run view "$(gh run list --workflow security-firmware-boundaries.yml \
  --branch main --limit 1 --json databaseId --jq '.[0].databaseId')" --log |
  grep -E 'CONFIG_ZMK_(STUDIO|STUDIO_LOCKING|BLE_MANAGEMENT|SETTINGS_RPC)=y'
```

Expected: ordinary left has no management symbols; Studio artifact has Studio and locking.

- [ ] **Step 7: Commit ZMK-SEC-007**

```bash
git add build.yaml boards/shields/eyelash_corne \
  security/tests/test_firmware_security.py
git diff --cached --check
git commit -m "build: isolate Studio management artifact"
```

### Task 3: ZMK-SEC-020 — Match Encoder Binding Capacity

**Files:**
- Modify: `config/eyelash_corne.keymap:25-37,61,73,85,97`
- Modify: `security/tests/test_firmware_security.py`

**Interfaces:**
- Consumes: one physical `left_encoder`.
- Produces: one `&rsr_vol` sensor binding per layer; removes unused `rsr_trans`.

- [ ] **Step 1: Add failing sensor-capacity test**

```python
    def test_each_layer_has_one_physical_encoder_binding(self) -> None:
        keymap = KEYMAP.read_text(encoding="utf-8")
        bindings = re.findall(r"sensor-bindings\s*=\s*<([^>]+)>;", keymap)
        self.assertEqual(4, len(bindings))
        self.assertEqual(["&rsr_vol"] * 4, [" ".join(x.split()) for x in bindings])
        self.assertNotIn("rsr_trans:", keymap)
```

- [ ] **Step 2: Verify RED**

```bash
python3 security/tests/test_firmware_security.py
```

Expected: four layers contain two bindings and `rsr_trans` exists.

- [ ] **Step 3: Keep one volume binding per layer**

Delete the entire `rsr_trans` behavior node at lines 33-37. Replace each:

```dts
sensor-bindings = <&rsr_vol &rsr_trans>;
```

with:

```dts
sensor-bindings = <&rsr_vol>;
```

- [ ] **Step 4: Verify GREEN and warning-free builds**

```bash
python3 security/tests/test_firmware_security.py
python3 security/tests/test_workflow_security.py
git diff --check
git push origin main
gh run watch "$(gh run list --workflow security-firmware-boundaries.yml \
  --branch main --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
! gh run view "$(gh run list --workflow security-firmware-boundaries.yml \
  --branch main --limit 1 --json databaseId --jq '.[0].databaseId')" --log |
  grep -F 'excess elements in array initializer'
```

Expected: tests/builds pass; excess-initializer warning absent. Hardware encoder behavior remains a later manual gate.

- [ ] **Step 5: Commit ZMK-SEC-020**

```bash
git add config/eyelash_corne.keymap \
  security/tests/test_firmware_security.py
git diff --cached --check
git commit -m "fix: align encoder sensor bindings"
```
