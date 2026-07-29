# ZMK Supply-Chain Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close ZMK-SEC-002 and ZMK-SEC-006 through immutable west resolution and an immutable, least-privilege local build workflow.

**Architecture:** Downstream west project definitions override imported definitions by project name, so the root manifest pins all seven direct projects plus imported Zephyr while preserving Zephyr imports. CI vendors the audited reusable workflow, replaces every nested action tag with its audited SHA, and gives the build caller only `contents: read`.

**Tech Stack:** west 1.5.0 manifest YAML, GitHub Actions YAML, Python 3 `unittest`, Git

## Global Constraints

- Execute ZMK-SEC-002 and ZMK-SEC-006 as separate tasks, commits, and review gates.
- Require user approval before each task.
- Preserve current firmware sources exactly by pinning the audit-resolved SHAs.
- Preserve build matrix, artifact names, and build behavior.
- Do not flash firmware.
- Build both halves after manifest changes.
- Do not claim a finding closed until its task-specific verification passes.
- ZMK-SEC-001 plan must land first so `security/tests/test_workflow_security.py` exists.

---

## Planned File Structure

- Modify `config/west.yml`: immutable direct pins plus downstream Zephyr override.
- Modify `security/tests/test_workflow_security.py`: add west and build-workflow security contracts.
- Create `.github/workflows/build-user-config-pinned.yml`: vendored audited reusable build workflow with nested actions pinned.
- Modify `.github/workflows/build.yml`: local reusable workflow call plus `contents: read`.

### Task 1: ZMK-SEC-002 — Freeze Complete West Graph

**Files:**
- Modify: `config/west.yml:7-29`
- Modify: `security/tests/test_workflow_security.py`
- Verify: `security/audit/dependency-inventory.tsv:2-82`

**Interfaces:**
- Consumes: eight audited mutable rows and resolved SHAs from `security/audit/dependency-inventory.tsv`.
- Produces: root west manifest whose downstream `zephyr` definition overrides imported Zephyr while `import: true` preserves Zephyr dependencies.

- [ ] **Step 1: Add failing west-pin contract test**

Add below existing constants in `security/tests/test_workflow_security.py`:

```python
WEST_MANIFEST = ROOT / "config" / "west.yml"
AUDITED_WEST_REVISIONS = {
    "eyelash_corne": "ba1eeab627ba94ac46f7768b3ddc01f97873ca87",
    "zephyr": "dacab4875df72109b96cc8977547a0dc04875bcd",
    "zmk": "4493783ef88ce2e653bf8217c92ee17140df71e3",
    "zmk-behavior-runtime-sensor-rotate": (
        "8b1125ed676c1f5e14145d217984f33d0ebdcef4"
    ),
    "zmk-module-ble-management": (
        "851661cd21f2aded8ec649da86e01a207dc4b973"
    ),
    "zmk-module-battery-history": (
        "307755dd2ad4d320e14de162e8e5ef018f29d929"
    ),
    "zmk-module-settings-rpc": (
        "78f86df9e6c5edaf57bef3ccbd7f360cfdf49291"
    ),
    "zmk-module-runtime-input-processor": (
        "dbf92f764de8b6ffd60bf5850514302875fe2570"
    ),
}
```

Add to `WorkflowSecurityTests`:

```python
    def test_west_projects_use_audited_revisions(self) -> None:
        manifest = WEST_MANIFEST.read_text(encoding="utf-8")

        for name, revision in AUDITED_WEST_REVISIONS.items():
            block_match = re.search(
                rf"(?ms)^\s{{4}}- name: {re.escape(name)}\s*$"
                rf"(?P<body>.*?)(?=^\s{{4}}- name:|^\s{{2}}self:)",
                manifest,
            )
            self.assertIsNotNone(block_match, name)
            self.assertRegex(
                block_match.group("body"),
                rf"(?m)^\s{{6}}revision:\s+{revision}\s*$",
                name,
            )

        zephyr = re.search(
            r"(?ms)^\s{4}- name: zephyr\s*$"
            r"(?P<body>.*?)(?=^\s{4}- name:|^\s{2}self:)",
            manifest,
        )
        self.assertIsNotNone(zephyr)
        self.assertRegex(zephyr.group("body"), r"(?m)^\s{6}import:\s+true\s*$")
```

- [ ] **Step 2: Run RED test**

Run:

```bash
python3 security/tests/test_workflow_security.py
```

Expected: west test fails because current revisions use branches/lightweight tags and no root `zephyr` override exists.

- [ ] **Step 3: Replace root manifest with exact immutable project definitions**

Use this complete `config/west.yml`:

```yaml
manifest:
  remotes:
    - name: zmkfirmware
      url-base: https://github.com/zmkfirmware
    - name: cormoran
      url-base: https://github.com/cormoran
  projects:
    - name: eyelash_corne
      url: https://github.com/a741725193/zmk-new_corne
      revision: ba1eeab627ba94ac46f7768b3ddc01f97873ca87 # audited main
    - name: zephyr
      remote: zmkfirmware
      revision: dacab4875df72109b96cc8977547a0dc04875bcd # audited v3.5.0+zmk-fixes
      import: true
    - name: zmk
      remote: cormoran
      revision: 4493783ef88ce2e653bf8217c92ee17140df71e3 # audited v0.3-branch+dya
      import: app/west.yml
    - name: zmk-behavior-runtime-sensor-rotate
      remote: cormoran
      revision: 8b1125ed676c1f5e14145d217984f33d0ebdcef4 # audited main
    - name: zmk-module-ble-management
      remote: cormoran
      revision: 851661cd21f2aded8ec649da86e01a207dc4b973 # audited zmk-v0.3.0.0
    - name: zmk-module-battery-history
      remote: cormoran
      revision: 307755dd2ad4d320e14de162e8e5ef018f29d929 # audited main
    - name: zmk-module-settings-rpc
      remote: cormoran
      revision: 78f86df9e6c5edaf57bef3ccbd7f360cfdf49291 # audited main
    - name: zmk-module-runtime-input-processor
      remote: cormoran
      revision: dbf92f764de8b6ffd60bf5850514302875fe2570 # audited zmk-v0.3.0.0
  self:
    path: config
```

- [ ] **Step 4: Run GREEN static test**

Run:

```bash
python3 security/tests/test_workflow_security.py
git diff --check
```

Expected: all tests and diff check pass.

- [ ] **Step 5: Resolve twice and compare frozen manifests**

Run:

```bash
rm -rf /tmp/zmk-sec-002-a /tmp/zmk-sec-002-b
python3 -m venv /tmp/zmk-sec-002-venv
/tmp/zmk-sec-002-venv/bin/pip install west==1.5.0
REPO_ROOT="$(git rev-parse --show-toplevel)"
for suffix in a b; do
  mkdir -p "/tmp/zmk-sec-002-$suffix"
  cp -a "$REPO_ROOT/config" "/tmp/zmk-sec-002-$suffix/config"
  (
    cd "/tmp/zmk-sec-002-$suffix"
    /tmp/zmk-sec-002-venv/bin/west init -l config
    /tmp/zmk-sec-002-venv/bin/west update
    /tmp/zmk-sec-002-venv/bin/west manifest --freeze \
      > frozen-west.yml
  )
done
diff -u /tmp/zmk-sec-002-a/frozen-west.yml \
  /tmp/zmk-sec-002-b/frozen-west.yml
```

Expected: both updates pass and frozen manifests are byte-identical.

- [ ] **Step 6: Compare resolved mutable rows with audit inventory**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
import re

expected = {}
for line in Path("security/audit/dependency-inventory.tsv").read_text().splitlines()[1:]:
    component, _, _, sha, mutable, _, scope, _ = line.split("\t")
    if mutable == "yes" and not any(
        word in scope for word in ("disabled", "excluded", "blocklisted")
    ):
        expected[component] = sha

frozen = Path("/tmp/zmk-sec-002-a/frozen-west.yml").read_text()
for component, sha in expected.items():
    pattern = rf"(?ms)- name: {re.escape(component)}\b.*?revision: {sha}\b"
    if not re.search(pattern, frozen):
        raise SystemExit(f"{component} did not resolve to {sha}")
print(f"verified {len(expected)} formerly mutable projects")
PY
```

Expected: `verified 8 formerly mutable projects`.

- [ ] **Step 7: Build both halves from one clean frozen workspace**

Run with Zephyr SDK 0.16.3:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
(
  cd /tmp/zmk-sec-002-a
  /tmp/zmk-sec-002-venv/bin/west zephyr-export
  /tmp/zmk-sec-002-venv/bin/west build -p always -s zmk/app \
    -d build/right -b nice_nano_v2 -- \
    -DZMK_CONFIG="$REPO_ROOT/config" \
    -DZMK_EXTRA_MODULES="$REPO_ROOT" \
    '-DSHIELD=eyelash_corne_right nice_view'
  /tmp/zmk-sec-002-venv/bin/west build -p always -s zmk/app \
    -d build/left -b nice_nano_v2 -- \
    -DZMK_CONFIG="$REPO_ROOT/config" \
    -DZMK_EXTRA_MODULES="$REPO_ROOT" \
    '-DSHIELD=eyelash_corne_left nice_view'
  sha256sum build/right/zephyr/zmk.uf2 build/left/zephyr/zmk.uf2
)
```

Expected: both builds pass. If SDK 0.16.3 is unavailable, stop Task 1 as blocked; manifest-only verification does not satisfy the spec's both-half build gate.

- [ ] **Step 8: Commit ZMK-SEC-002**

```bash
git add config/west.yml security/tests/test_workflow_security.py
git diff --cached --check
git commit -m "build: freeze west dependency graph"
```

### Task 2: ZMK-SEC-006 — Vendor and Pin Build Workflow

**Files:**
- Create: `.github/workflows/build-user-config-pinned.yml`
- Modify: `.github/workflows/build.yml:8-10`
- Modify: `security/tests/test_workflow_security.py`

**Interfaces:**
- Consumes: audited reusable workflow commit `edf5c0814fd3ea202e43aad2d68fd32e882a518c` and action SHAs in `security/audit/workflow-inventory.tsv:2-7`.
- Produces: local reusable workflow with immutable nested actions and caller `contents: read`.

- [ ] **Step 1: Add failing build-workflow contract test**

Add constants:

```python
BUILD_CALLER = ROOT / ".github" / "workflows" / "build.yml"
PINNED_BUILD_WORKFLOW = (
    ROOT / ".github" / "workflows" / "build-user-config-pinned.yml"
)
AUDITED_ACTION_USES = {
    "actions/checkout": "11d5960a326750d5838078e36cf38b85af677262",
    "actions/cache": "0057852bfaa89a56745cba8c7296529d2fc39830",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/upload-artifact/merge": (
        "ea165f8d65b6e75b540449e92b4886f43607fa02"
    ),
}
```

Add tests:

```python
    def test_build_caller_is_local_and_read_only(self) -> None:
        caller = BUILD_CALLER.read_text(encoding="utf-8")
        self.assertIn(
            "uses: ./.github/workflows/build-user-config-pinned.yml",
            caller,
        )
        self.assertRegex(caller, re.compile(r"(?m)^\s+contents:\s+read\s*$"))
        self.assertNotIn("zmkfirmware/zmk/.github/workflows/", caller)

    def test_vendored_build_actions_are_pinned(self) -> None:
        workflow = PINNED_BUILD_WORKFLOW.read_text(encoding="utf-8")
        for source, sha in AUDITED_ACTION_USES.items():
            self.assertIn(f"uses: {source}@{sha}", workflow)
        self.assertNotRegex(
            workflow,
            re.compile(r"(?m)^\s*uses:\s+[^./][^@\s]*@(main|master|v\d+)"),
        )
```

- [ ] **Step 2: Run RED test**

```bash
python3 security/tests/test_workflow_security.py
```

Expected: local pinned workflow file is missing and caller still uses remote tag.

- [ ] **Step 3: Vendor audited workflow and replace exact action refs**

```bash
curl -fsSL \
  https://raw.githubusercontent.com/zmkfirmware/zmk/edf5c0814fd3ea202e43aad2d68fd32e882a518c/.github/workflows/build-user-config.yml \
  -o .github/workflows/build-user-config-pinned.yml
python3 - <<'PY'
from pathlib import Path

path = Path(".github/workflows/build-user-config-pinned.yml")
text = path.read_text()
replacements = {
    "actions/checkout@v4":
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    "actions/cache@v4":
        "actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830",
    "actions/upload-artifact@v4":
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/upload-artifact/merge@v4":
        "actions/upload-artifact/merge@ea165f8d65b6e75b540449e92b4886f43607fa02",
}
for old, new in replacements.items():
    count = text.count(old)
    if count == 0:
        raise SystemExit(f"missing audited source reference: {old}")
    text = text.replace(old, new)
path.write_text(text)
PY
```

- [ ] **Step 4: Replace caller with local least-privilege call**

Use:

```yaml
jobs:
  build:
    permissions:
      contents: read
    uses: ./.github/workflows/build-user-config-pinned.yml
```

- [ ] **Step 5: Run GREEN and exact-scope checks**

```bash
python3 security/tests/test_workflow_security.py
git diff --check
git diff -- .github/workflows/build.yml \
  .github/workflows/build-user-config-pinned.yml \
  security/tests/test_workflow_security.py
```

Expected: all tests pass; caller behavior is unchanged except local identity and token scope; nested action refs use full SHAs.

- [ ] **Step 6: Commit ZMK-SEC-006**

```bash
git add .github/workflows/build.yml \
  .github/workflows/build-user-config-pinned.yml \
  security/tests/test_workflow_security.py
git diff --cached --check
git commit -m "ci: pin ZMK build workflow actions"
```

- [ ] **Step 7: Post-push build verification**

```bash
branch="$(git branch --show-current)"
gh workflow run build.yml --ref "$branch"
sleep 5
run_id="$(gh run list --workflow build.yml --branch "$branch" \
  --event workflow_dispatch --limit 1 --json databaseId \
  --jq '.[0].databaseId')"
gh run watch "$run_id" --exit-status
gh run view "$run_id" --json conclusion,url,headSha
```

Expected: workflow succeeds and produces expected firmware artifact archive. Record run URL; until this passes, report ZMK-SEC-006 as implemented with live CI verification pending.
