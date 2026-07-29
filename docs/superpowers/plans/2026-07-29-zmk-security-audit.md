# ZMK Corne Security Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an evidence-based security report for this repository and its complete build supply chain, plus a migration matrix toward official ZMK with only necessary DYA capabilities.

**Architecture:** Treat the audit as a reproducible evidence pipeline: first freeze dependency identities, then review local configuration, vendor fork, external modules, DYA client, and resolved builds. Store compact inventories beside one prioritized report; do not change firmware configuration or flash hardware during this plan.

**Tech Stack:** ZMK, Zephyr/west manifests, Devicetree/Kconfig, C, GitHub Actions YAML, React 19/TypeScript/Vite, Git, shell tools, GitHub source, official ZMK/Zephyr documentation.

## Global Constraints

- Audit repository configuration, history, workflows, complete `west` graph, DYA Studio, Cormoran ZMK fork/modules, and direct/transitive dependencies.
- Do not flash firmware.
- Do not remediate findings during this plan.
- Use immutable commit identities in evidence even when source manifests use branches or tags.
- Distinguish confirmed vulnerabilities from hardening gaps, mutable supply-chain risks, and maintainability concerns.
- Every reported code finding must include exact file and line references.
- Recommend official ZMK plus smallest required module set; retain a core fork only when a required feature cannot use a module interface.
- Enable Studio locking and require physical `&studio_unlock` in recommended target.
- Build both halves before any later flash recommendation.
- Record hardware-only behavior as manual tests, never as verified.
- User reviews final report before fixes proceed one finding at a time.

---

## Planned File Structure

- Create `security/audit/dependency-inventory.tsv`: machine-readable repository, requested revision, resolved SHA, provenance, mutability, import, and audit-scope inventory.
- Create `security/audit/workflow-inventory.tsv`: reusable actions, requested references, resolved SHAs, permissions, triggers, and token exposure.
- Create `security/audit/feature-matrix.md`: current DYA capability, actual Corne use, official-ZMK support, migration decision, and validation.
- Create `security/audit/manual-hardware-tests.md`: physical checks required after remediation and before flashing is recommended.
- Create `security_best_practices_report.md`: executive summary, methodology, prioritized numbered findings, limitations, and remediation order.
- Modify no firmware, workflow, manifest, keymap, or shield file.

### Task 1: Freeze Complete Dependency and Workflow Graph

**Files:**
- Create: `security/audit/dependency-inventory.tsv`
- Create: `security/audit/workflow-inventory.tsv`
- Inspect: `config/west.yml:1-31`
- Inspect: `.github/workflows/build.yml:1-10`
- Inspect: `.github/workflows/draw.yml:1-18`

**Interfaces:**
- Consumes: repository `HEAD`, all west manifests imported from it, and both reusable workflows.
- Produces: tab-separated inventories consumed by Tasks 2–8. Dependency columns are `component`, `source_url`, `requested_revision`, `resolved_sha`, `mutable`, `import_path`, `scope`, `notes`. Workflow columns are `workflow`, `source`, `requested_ref`, `resolved_sha`, `trigger`, `permissions`, `writes_repository`, `notes`.

- [ ] **Step 1: Create audit workspace and capture repository identity**

Run:

```bash
mkdir -p security/audit /tmp/zmk-corne-security-audit
git rev-parse HEAD
git status --short
```

Expected: one commit SHA; clean status except this plan if it has not yet been committed.

- [ ] **Step 2: Resolve direct west projects**

For every project in `config/west.yml`, run:

```bash
git ls-remote https://github.com/a741725193/zmk-new_corne main
git ls-remote https://github.com/cormoran/zmk v0.3-branch+dya
git ls-remote https://github.com/cormoran/zmk-behavior-runtime-sensor-rotate main
git ls-remote https://github.com/cormoran/zmk-module-ble-management zmk-v0.3.0.0
git ls-remote https://github.com/cormoran/zmk-module-battery-history main
git ls-remote https://github.com/cormoran/zmk-module-settings-rpc main
git ls-remote https://github.com/cormoran/zmk-module-runtime-input-processor zmk-v0.3.0.0
```

Expected: one matching SHA per requested revision. Record every SHA and mark `main` mutable. Treat tags as mutable unless tag-object verification proves otherwise.

- [ ] **Step 3: Resolve imported west manifests recursively**

Clone each direct project at its resolved SHA under `/tmp/zmk-corne-security-audit`, then run:

```bash
find /tmp/zmk-corne-security-audit \
  -path '*/.git' -prune -o \
  \( -name west.yml -o -path '*/west/*.yml' \) -type f -print
rg -n '(^|[[:space:]])(url|url-base|remote|revision|import):' \
  /tmp/zmk-corne-security-audit --glob '*.yml' --glob '!**/.git/**'
```

Expected: all imported manifest paths and their additional projects become inventory rows. Continue until no new imported manifest introduces an unrecorded project.

- [ ] **Step 4: Resolve reusable workflows and nested actions**

Download or clone exact sources for:

```text
zmkfirmware/zmk/.github/workflows/build-user-config.yml@v0.3.0
caksoylar/keymap-drawer/.github/workflows/draw-zmk.yml@main
```

Inspect nested `uses:` entries recursively:

```bash
rg -n '^[[:space:]]*uses:' /tmp/zmk-corne-security-audit --glob '*.yml' --glob '*.yaml'
```

Expected: every action or reusable workflow has an inventory row with resolved SHA, trigger context, effective permissions, and whether repository content can be written.

- [ ] **Step 5: Validate inventory shape and completeness**

Run:

```bash
awk -F '\t' 'NF != 8 { print FNR ":" NF ":" $0; bad=1 } END { exit bad }' \
  security/audit/dependency-inventory.tsv
awk -F '\t' 'NF != 8 { print FNR ":" NF ":" $0; bad=1 } END { exit bad }' \
  security/audit/workflow-inventory.tsv
grep -F $'caksoylar/keymap-drawer\t' security/audit/workflow-inventory.tsv
grep -F $'cormoran/zmk\t' security/audit/dependency-inventory.tsv
```

Expected: both `awk` commands exit 0; required rows print once.

- [ ] **Step 6: Commit inventories**

```bash
git add security/audit/dependency-inventory.tsv security/audit/workflow-inventory.tsv
git commit -m "docs: inventory ZMK build dependencies"
```

### Task 2: Audit Local Firmware and CI Configuration

**Files:**
- Modify: `security_best_practices_report.md`
- Inspect: `.github/workflows/build.yml:1-10`
- Inspect: `.github/workflows/draw.yml:1-18`
- Inspect: `build.yaml:1-11`
- Inspect: `config/eyelash_corne.conf:1-49`
- Inspect: `config/eyelash_corne.keymap:1-100`
- Inspect: `boards/shields/eyelash_corne/eyelash_corne_left.conf:1-41`
- Inspect: `boards/shields/eyelash_corne/eyelash_corne_right.conf:1-21`
- Inspect: `boards/shields/eyelash_corne/*.overlay`

**Interfaces:**
- Consumes: Task 1 inventories.
- Produces: report introduction, threat model, methodology, and numbered findings limited to local configuration and CI.

- [ ] **Step 1: Create report skeleton with fixed sections**

Create `security_best_practices_report.md` containing:

```markdown
# Security Best-Practices Report: ZMK Corne

## Executive Summary
## Scope and Method
## Critical Findings
## High Findings
## Medium Findings
## Low Findings
## Positive Security Observations
## Migration Recommendation
## Limitations and Manual Validation
## Remediation Order
```

Finding format:

```markdown
### ZMK-SEC-NNN — Title

**Severity:** High
**Class:** Vulnerability | Supply-chain risk | Hardening gap | Maintainability risk
**Evidence:** `path/file:line-line`
**Impact:** One concrete outcome.
**Scenario:** Preconditions and failure/exploit path.
**Recommendation:** Exact safe target.
**Regression risk:** Features or state that may change.
**Verification:** Command or physical test proving remediation.
```

- [ ] **Step 2: Review workflow trust boundaries**

Trace trigger → called workflow/action → effective token permissions → repository write or artifact output. Explicitly evaluate `.github/workflows/draw.yml:12-17`, where mutable `@main` code receives `contents: write`.

Run:

```bash
rg -n '^(on:|[[:space:]]+(pull_request_target|pull_request|push|workflow_run|workflow_dispatch):|[[:space:]]+permissions:|[[:space:]]+contents:|[[:space:]]+uses:)' \
  .github/workflows /tmp/zmk-corne-security-audit --glob '*.yml' --glob '*.yaml'
```

Expected: report records mutable executable references, excessive permissions, unsafe event contexts, or confirms absence with evidence.

- [ ] **Step 3: Review firmware-exposed management features**

Trace `build.yaml:7-9`, left/right `.conf` files, and `&studio_unlock` bindings. Confirm separately:

- Studio enabled only on intended artifact/half
- `CONFIG_ZMK_STUDIO_LOCKING=n` effect
- USB UART snippet exposure
- custom RPC module enablement
- persistent settings and reset path
- bootloader/reset bindings reachable through normal keymap layers

Expected: each unsafe default becomes one numbered finding; ordinary recovery bindings are not mislabeled without a credible attack path.

- [ ] **Step 4: Scan repository history and content**

Run:

```bash
git log --all --stat -- . ':!keymap-drawer/*.svg'
git log -p --all -G '(token|secret|password|BEGIN .*PRIVATE KEY|curl|wget|uses:|url-base:|revision:)'
git grep -n -I -E '(BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|AKIA[0-9A-Z]{16})' \
  "$(git rev-list --all)"
```

Expected: no secret match, or immediate critical/high finding with affected commits and rotation recommendation. Do not print secret values into report.

- [ ] **Step 5: Validate report references**

Run:

```bash
grep -n '^### ZMK-SEC-' security_best_practices_report.md
rg -n '\*\*Evidence:\*\* `[^`]+:[0-9]+(-[0-9]+)?`' security_best_practices_report.md
git diff --check
```

Expected: every current finding has ID and line evidence; diff check passes.

- [ ] **Step 6: Commit local audit**

```bash
git add security_best_practices_report.md
git commit -m "docs: audit local ZMK security configuration"
```

### Task 3: Audit Cormoran ZMK Fork Delta

**Files:**
- Modify: `security_best_practices_report.md`
- Inspect: `/tmp/zmk-corne-security-audit/zmk/app/src/studio/`
- Inspect: `/tmp/zmk-corne-security-audit/zmk/app/include/zmk/studio/`
- Inspect: `/tmp/zmk-corne-security-audit/zmk/app/src/split/`
- Inspect: `/tmp/zmk-corne-security-audit/zmk/app/src/activity.c`
- Inspect: `/tmp/zmk-corne-security-audit/zmk/app/src/event_manager.c`

**Interfaces:**
- Consumes: resolved Cormoran ZMK SHA from Task 1 and report format from Task 2.
- Produces: fork provenance and vulnerability findings; exact official-ZMK merge base and changed firmware file list.

- [ ] **Step 1: Establish official merge base and immutable comparison**

Run inside cloned `cormoran/zmk`:

```bash
git remote add upstream https://github.com/zmkfirmware/zmk.git || true
git fetch upstream main
merge_base="$(git merge-base HEAD upstream/main)"
git show -s --format='%H %aI %s' "$merge_base"
git diff --stat "$merge_base"..HEAD -- app
git diff --name-status "$merge_base"..HEAD -- app ':!app/tests'
```

Expected: record merge base `edf5c0814fd3ea202e43aad2d68fd32e882a518c` if source has not moved from audited SHA; otherwise record and explain new value.

- [ ] **Step 2: Review custom Studio RPC dispatch and framing**

Inspect all additions touching:

```text
app/include/zmk/studio/custom.h
app/src/studio/custom_subsystem.c
app/src/studio/core.c
app/src/studio/rpc.c
app/src/studio/gatt_rpc_transport.c
```

Check security classification, lock-state checks, subsystem indices, protobuf lengths, ring-buffer claims, framing bytes, callback lifetimes, concurrency, and error cleanup. For each suspected defect, write exact input → state transition → impact before assigning severity.

- [ ] **Step 3: Review BLE and split-event changes**

Inspect changed central/service/wired files. Check encrypted-link enforcement on every read/write/notify path, packet header arithmetic before copying, event name/data bounds, termination, queue behavior, remote event-type selection, and role/source trust.

Run:

```bash
git diff "$merge_base"..HEAD -- app/src/split app/include/zmk/split \
  | rg -n '(memcpy|memmove|strcpy|strncpy|strlen|size|length|offset|encrypted|security|queue|STRUCT_SECTION)'
```

Expected: every memory operation is paired with reviewed bounds evidence or a finding.

- [ ] **Step 4: Review runtime settings and HID-affecting changes**

Inspect `activity.c`, behavior files, endpoints, event manager, and battery driver changes. Check numeric ranges, flash-write frequency, rollback on partial failure, settings-load length checks, host-controlled behavior changes, and unintended HID emission.

- [ ] **Step 5: Search for generic dangerous primitives in changed firmware**

Run:

```bash
git diff --unified=0 "$merge_base"..HEAD -- app \
  | rg -n '^\+.*(memcpy|memmove|strcpy|strcat|sprintf|vsprintf|alloca|system\(|popen|shell_execute|LOG_(DBG|INF).*(key|payload|data))'
```

Expected: each match reviewed and disposition recorded in working notes; report contains only actionable findings and positive controls.

- [ ] **Step 6: Commit fork audit**

```bash
git add security_best_practices_report.md
git commit -m "docs: audit Cormoran ZMK fork"
```

### Task 4: Audit External Firmware Modules

**Files:**
- Modify: `security_best_practices_report.md`
- Inspect: `/tmp/zmk-corne-security-audit/{zmk-behavior-runtime-sensor-rotate,zmk-module-ble-management,zmk-module-battery-history,zmk-module-settings-rpc,zmk-module-runtime-input-processor}/src/**/*.c`
- Inspect: same module roots under `proto/`, `Kconfig`, `CMakeLists.txt`, `west.yml`, and `zephyr/module.yml`

**Interfaces:**
- Consumes: module SHAs and imported dependencies from Task 1; custom RPC contract reviewed in Task 3.
- Produces: module-specific findings and a map from enabled Kconfig symbol to compiled C source and RPC methods.

- [ ] **Step 1: Prove which module source is compiled**

For each module, trace `Kconfig` symbol → `CMakeLists.txt` condition → compiled source → local shield `.conf` enablement. Record disabled battery-history code separately; do not treat fetched-but-disabled code as equal runtime exposure.

Run:

```bash
rg -n 'CONFIG_ZMK_(BLE_MANAGEMENT|BATTERY_HISTORY|SETTINGS_RPC|RUNTIME_INPUT_PROCESSOR|RUNTIME_SENSOR_ROTATE)' \
  boards config build.yaml /tmp/zmk-corne-security-audit \
  --glob 'Kconfig*' --glob 'CMakeLists.txt' --glob '*.conf'
```

- [ ] **Step 2: Review every enabled RPC handler**

For each handler, enumerate request fields and verify:

- lock/security class
- enum and index validation
- signed/unsigned conversion
- range validation before device-state mutation
- bounded copies and protobuf callback lifetime
- result accuracy after partial failure
- persistent-write frequency and flash-wear guard

Expected: report gives exact handler file/lines for every issue.

- [ ] **Step 3: Review event relay and split propagation**

Trace central request through custom RPC, ZMK event, split serialization, peripheral mutation, response/notification. Confirm source identifiers cannot select arbitrary event types or copy attacker-sized data.

- [ ] **Step 4: Run focused static checks**

Run:

```bash
rg -n '(memcpy|memmove|strcpy|strncpy|strcat|sprintf|sscanf|atoi|strtol|pb_decode|pb_encode|settings_save|settings_save_one|settings_delete)' \
  /tmp/zmk-corne-security-audit/{zmk-behavior-runtime-sensor-rotate,zmk-module-ble-management,zmk-module-battery-history,zmk-module-settings-rpc,zmk-module-runtime-input-processor} \
  --glob '*.{c,h}'
```

Expected: manually inspect every match; absence of a scanner warning is not a pass.

- [ ] **Step 5: Run available module tests without changing source**

For each enabled module, follow its checked-in test command. Capture command, SHA, and pass/fail summary in report limitations. If toolchain setup blocks execution, record exact missing prerequisite and do not claim test coverage.

- [ ] **Step 6: Commit module audit**

```bash
git add security_best_practices_report.md
git commit -m "docs: audit DYA firmware modules"
```

### Task 5: Audit DYA Studio Client and Deployment

**Files:**
- Modify: `security_best_practices_report.md`
- Inspect: `/tmp/zmk-corne-security-audit/dya-studio/package.json`
- Inspect: `/tmp/zmk-corne-security-audit/dya-studio/src/`
- Inspect: `/tmp/zmk-corne-security-audit/dya-studio/vite.config.ts`
- Inspect: `/tmp/zmk-corne-security-audit/dya-studio/wrangler.toml`
- Inspect: `/tmp/zmk-corne-security-audit/dya-studio/.github/workflows/`

**Interfaces:**
- Consumes: RPC and locking behavior from Tasks 3–4.
- Produces: client/deployment findings and confirmation of which official-ZMK versus custom methods DYA invokes.

- [ ] **Step 1: Clone exact DYA Studio source and load applicable guidance**

Resolve `cormoran/dya-studio@main` to SHA, add it to dependency inventory, and clone that SHA. Read both applicable skill references in full:

```text
/home/ed/.codex/skills/security-best-practices/references/javascript-general-web-frontend-security.md
/home/ed/.codex/skills/security-best-practices/references/javascript-typescript-react-web-frontend-security.md
```

Expected: report scope states React/TypeScript guidance applies to client only, not firmware.

- [ ] **Step 2: Map browser trust and data flows**

Trace origin-loaded JavaScript → Web Serial/Web Bluetooth permission → device discovery → RPC encoding → firmware mutation. Identify network calls, analytics, remote assets, dynamic code, stored device data, demo data, and support-report export.

Run:

```bash
rg -n '(fetch\(|WebSocket|EventSource|sendBeacon|XMLHttpRequest|navigator\.(serial|bluetooth)|localStorage|sessionStorage|indexedDB|innerHTML|dangerouslySetInnerHTML|eval\(|new Function|postMessage|window\.open)' \
  /tmp/zmk-corne-security-audit/dya-studio/src
```

- [ ] **Step 3: Review RPC client validation**

Check response correlation, length limits, disconnect/reconnect state, device identity, method authorization assumptions, hostile device responses, support-report redaction, and UI confirmation for destructive operations such as unpairing or settings reset.

- [ ] **Step 4: Review dependencies and deployment workflow**

Run from exact source:

```bash
npm ci
npm audit --omit=dev
npm run lint
npm test -- --runInBand
npm run build
```

Expected: capture exact results. Audit advisories require reachability analysis before becoming report findings.

Inspect GitHub Actions references, Cloudflare configuration, security headers, source maps, and AGPL source-availability implications. Treat license notes as migration constraints, not vulnerabilities.

- [ ] **Step 5: Commit client audit**

```bash
git add security/audit/dependency-inventory.tsv security_best_practices_report.md
git commit -m "docs: audit DYA Studio client"
```

### Task 6: Resolve and Build Firmware Configurations

**Files:**
- Modify: `security_best_practices_report.md`
- Create: `security/audit/manual-hardware-tests.md`
- Inspect: generated build outputs under `/tmp/zmk-corne-security-audit/build/`

**Interfaces:**
- Consumes: frozen dependency graph and reviewed current source.
- Produces: build/test evidence for right, left, Studio-left, and settings-reset artifacts; effective security configuration; manual hardware validation checklist.

- [ ] **Step 1: Initialize a clean west workspace at frozen revisions**

Use a copy of the manifest under `/tmp` whose project revisions are replaced only with Task 1 SHAs. Do not edit repository `config/west.yml`.

Run:

```bash
west init -l /tmp/zmk-corne-security-audit/frozen-config/config \
  /tmp/zmk-corne-security-audit/west-workspace
cd /tmp/zmk-corne-security-audit/west-workspace
west update
west zephyr-export
```

Expected: every checked-out `git rev-parse HEAD` equals inventory SHA.

- [ ] **Step 2: Build each declared configuration**

Run equivalent west builds for:

```text
nice_nano_v2 + eyelash_corne_right + nice_view
nice_nano_v2 + eyelash_corne_left + nice_view
nice_nano_v2 + eyelash_corne_left + nice_view + studio-rpc-usb-uart + current Studio CMake arguments
nice_nano_v2 + settings_reset
```

Expected: record exact commands and pass/fail. Preserve logs under `/tmp`; do not commit generated firmware.

- [ ] **Step 3: Inspect effective Kconfig and Devicetree**

For each successful build, inspect `.config` and `zephyr.dts`. Confirm Studio, locking, UART, BLE management, settings RPC, runtime input, split relay, bootloader, logging, shell, and debug settings.

Run:

```bash
rg -n '^CONFIG_(ZMK_STUDIO|ZMK_STUDIO_LOCKING|ZMK_BLE_MANAGEMENT|ZMK_SETTINGS_RPC|ZMK_RUNTIME_INPUT_PROCESSOR|ZMK_SPLIT_RELAY_EVENT|SHELL|LOG|DEBUG)=' \
  /tmp/zmk-corne-security-audit/build/**/zephyr/.config
```

- [ ] **Step 4: Check repeatability**

Rebuild one left and one right artifact from clean build directories using identical frozen inputs. Compare:

```bash
sha256sum /tmp/zmk-corne-security-audit/build-first/**/zephyr/zmk.uf2
sha256sum /tmp/zmk-corne-security-audit/build-second/**/zephyr/zmk.uf2
```

Expected: matching hashes, or documented nondeterministic sections and tooling needed to normalize them.

- [ ] **Step 5: Write manual hardware checklist**

Create checklist covering:

- UF2 recovery and settings-reset recovery
- both halves boot and reconnect
- BLE pairing/bond clearing
- physical Studio unlock and automatic relock
- rejected Studio connection while locked
- USB-only and BLE-only Studio access
- all keys, five-way switch, encoder, mouse movement/buttons, RGB, backlight
- sleep/wake and soft-off
- no unexpected HID reports while idle
- host switch and split-half settings propagation

- [ ] **Step 6: Commit build evidence**

```bash
git add security_best_practices_report.md security/audit/manual-hardware-tests.md
git commit -m "docs: verify ZMK firmware build configurations"
```

### Task 7: Produce Official-ZMK Migration Matrix

**Files:**
- Create: `security/audit/feature-matrix.md`
- Modify: `security_best_practices_report.md`

**Interfaces:**
- Consumes: Tasks 2–6 findings and current official ZMK documentation.
- Produces: one decision per enabled DYA capability and recommended minimum trusted architecture.

- [ ] **Step 1: Enumerate current capabilities from effective builds**

Include at minimum:

```text
keymap editing
layer management
macros and combos
encoder/runtime sensor rotation
pointing and smooth scrolling
runtime input processors
BLE profile management
endpoint priority
idle/deep-sleep settings
split event relay
battery history
Studio USB transport
Studio BLE transport
```

- [ ] **Step 2: Classify each capability**

Use table columns:

```markdown
| Capability | Enabled now | Hardware/use evidence | Official ZMK | External module possible | Core fork required | Decision | Validation |
```

Allowed `Decision` values:

```text
official
retain-module
defer
remove
core-fork-exception
```

Any `core-fork-exception` must cite missing official/module interface and a concrete user requirement.

- [ ] **Step 3: Define migration stages**

Document:

1. Pin and lock current build without feature change.
2. Establish official-ZMK baseline for both halves.
3. Test official Studio keymap functionality with locking.
4. Add one required external module at a time.
5. Consider client fork only for retained custom RPC UI.
6. Keep Cormoran core fork only for approved `core-fork-exception` rows.

- [ ] **Step 4: Reconcile report recommendation**

Ensure executive summary, migration section, remediation order, and feature matrix give identical decisions. Explicitly separate “safer target” from “verified safe firmware.”

- [ ] **Step 5: Commit migration matrix**

```bash
git add security/audit/feature-matrix.md security_best_practices_report.md
git commit -m "docs: define official ZMK migration path"
```

### Task 8: Finalize and Quality-Gate Security Report

**Files:**
- Modify: `security_best_practices_report.md`
- Verify: `security/audit/dependency-inventory.tsv`
- Verify: `security/audit/workflow-inventory.tsv`
- Verify: `security/audit/feature-matrix.md`
- Verify: `security/audit/manual-hardware-tests.md`

**Interfaces:**
- Consumes: all prior audit deliverables.
- Produces: final report ready for user review; no fixes.

- [ ] **Step 1: Normalize finding severity and IDs**

Use contiguous IDs `ZMK-SEC-001`, `ZMK-SEC-002`, and so on. Critical findings must contain a one-sentence impact statement. Severity must reflect demonstrated preconditions and impact, not distrust of maintainer identity.

- [ ] **Step 2: Verify every citation**

For every local or cloned-source `path:line` citation:

```bash
nl -ba path/to/file | sed -n 'START,ENDp'
```

Expected: cited range directly supports claim. For mutable remote sources, include audited commit SHA next to citation.

- [ ] **Step 3: Check report completeness**

Confirm report contains:

- executive safety recommendation
- full audit scope and resolved commit date
- critical/high/medium/low sections, including explicit “none found” where empty
- positive controls
- dependency/workflow findings
- local configuration findings
- fork/module/client findings
- build evidence
- migration recommendation
- limitations and manual tests
- ordered fixes, one finding at a time

- [ ] **Step 4: Run automated consistency checks**

Run:

```bash
pattern='T''BD|T''ODO|FIX''ME|X''XX|implement lat''er|add appropri''ate|write tests f''or|similar to Ta''sk'
rg -n "$pattern" \
  security_best_practices_report.md security/audit || true
git diff --check
awk -F '\t' 'NF != 8 { print FNR ":" NF ":" $0; bad=1 } END { exit bad }' \
  security/audit/dependency-inventory.tsv
awk -F '\t' 'NF != 8 { print FNR ":" NF ":" $0; bad=1 } END { exit bad }' \
  security/audit/workflow-inventory.tsv
```

Expected: placeholder search prints nothing; remaining commands pass.

- [ ] **Step 5: Perform clean-reader review**

Read report without source open. Verify every finding answers: what is wrong, where, credible scenario, impact, exact remediation, regression risk, and proof of fix. Remove speculative claims that cannot answer all seven.

- [ ] **Step 6: Commit final report**

```bash
git add security_best_practices_report.md security/audit
git commit -m "docs: finalize ZMK security audit"
```

- [ ] **Step 7: Stop at report-review gate**

Present report location, finding counts by severity, build results, highest-priority risks, and migration recommendation. Ask user to review before implementing any remediation.
