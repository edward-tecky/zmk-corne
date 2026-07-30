# ZMK Security Remediation Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Orchestrate every ZMK security remediation plan from repository preflight through finding closure, deterministic builds, explicit flash approval, and hardware verification.

**Architecture:** Treat seven detailed plans as independently reviewable work packages joined by explicit dependency gates. Run repository, upstream-ZMK, and DYA-client lanes concurrently where their workspaces do not overlap; serialize local firmware changes, official-baseline migration, and final integration because they modify or consume the same product state.

**Tech Stack:** Git, GitHub Actions, west, ZMK/Zephyr, Python contract tests, Vitest, Cloudflare Workers, subagent-driven-development

## Execution Status

Updated 2026-07-31:

- Task 1 complete (`c4c4cb4`).
- Task 2 complete.
  - Product supply-chain work complete through ZMK-SEC-006 containment
    (`d825e4d`, `0a6143e`, `7c78ffd`, `c2a3f51`).
  - Upstream fixes retained only in `edward-tecky/zmk`; product features remain
    disabled pending official-baseline gates.
  - DYA client Tasks 1–8 complete through ZMK-SEC-019 (`314bab6`); dependency
    pins and cross-repository integration fixtures verified.
- Task 3 complete (`4af6ad7`, `18a0aa7`, `7713bc9`, `28cab0c`).
  Repository-owned GitHub Actions runs 30534460476, 30534737625, and
  30534942755 passed required four-target gates and uploaded no firmware
  artifacts.
- Task 4 complete through official-baseline adjudication (`e280d2f`,
  `2a94633`, `0bba543`, `7b602a3`). Exact-source CI runs 30539322688 and
  30539334928 produced identical four-target hashes and uploaded no artifacts.
  Six Cormoran/DYA findings are removed; ZMK-SEC-009 and ZMK-SEC-021 remain
  in-review with affected artifacts disabled/undistributed.
- Task 5 complete. Client lane evidence remains verified; user explicitly
  accepted ZMK-SEC-009 and ZMK-SEC-021 as `deferred-open` on 2026-07-31 with
  BLE Studio disabled and settings-reset undistributed.
- Task 6 pre-flash software gate complete for source `7297a06`; exact-source
  CI runs 30561289211 and 30561292657 are deterministic and uploaded no
  artifacts. Exact-hash approval and all hardware checks remain pending.
- Reviewed ZMK fixes are now combined at
  `df896a2f4ffafa145bbae043debe523561b28493` and pinned by product source
  `0ebe524c795dcfaeb30ed7d7c1570732dcd8abf4`. Independent review found no
  Critical or Important issues. Push and exact-source repeat runs
  30576318651/30576777245 and 30576318713/30576779722 passed with deterministic
  hashes. ZMK-SEC-009 and ZMK-SEC-021 retain accepted `deferred-open` status;
  their remaining gates require hardware, so BLE Studio stays disabled and
  settings-reset stays undistributed.
- No hardware artifact has been flashed.
- First-wave checkpoint used consolidated
  `python3 security/tests/test_workflow_security.py` (6 tests) because three
  originally planned per-topic scripts were replaced by this unified suite.

## Global Constraints

- Execute product work on `main` in `/home/ed/Coding/zmk-corne`; do not create a product worktree.
- External repositories use the immutable bases and dedicated paths specified by their child plans.
- One finding per commit and review except the documented shared official-ZMK migration commit; shared evidence never merges finding verdicts.
- Run relevant automated tests and `git diff --check` before every commit.
- Build both keyboard halves after every manifest or firmware-configuration
  change. Repository-owned CI may provide this gate when no local ZMK workspace
  exists.
- Do not flash any artifact until the user approves its exact SHA-256.
- Never treat documentation, an accepted deferral, or a disabled feature as a closed finding.
- Stop a lane on failed verification, unexpected repository state, mutable dependency resolution, or scope drift.
- Child plans contain implementation detail and remain authoritative for file paths, tests, code, and commit boundaries.

---

## Work-Package Graph

```text
Preflight
   |
   +--> ZMK-SEC-001 drawer pin -------------------+
   |                                              |
   +--> supply-chain plan ------------------------+--> local firmware plan
   |                                                   |
   +--> upstream ZMK fixes ----------------------------+--> official baseline
   |                                                   |         |
   +--> DYA client remediation ------------------------+---------+
                                                               |
                                                     integration gate
                                                               |
                                               exact-hash approval + hardware
```

Hard dependencies:

1. Preflight precedes every lane.
2. ZMK-SEC-002 frozen graph precedes product firmware changes.
3. Supply-chain and local-firmware plans precede official-ZMK baseline.
4. Upstream fixes may run concurrently, but affected features remain disabled
   until reviewed merge SHAs are pinned and their product gates pass.
5. DYA remediation may run concurrently; custom client deployment remains
   outside trusted baseline until all seven client findings pass.
6. Integration starts only after all child plans have recorded a verdict for
   every finding and any deferral has explicit user acceptance.

### Task 1: Establish Master Ledger and Clean-Tree Baseline

**Files:**
- Create: `security/audit/remediation-ledger.md`
- Reference: `security_best_practices_report.md`
- Reference: `docs/superpowers/specs/2026-07-30-pin-keymap-drawer-workflow-design.md`

**Interfaces:**
- Produces: one row per `ZMK-SEC-001` through `ZMK-SEC-021` with fields `Status`, `Owner`, `Plan`, `Commit`, `Evidence`, `Reviewer`, and `Residual gate`.

- [x] **Step 1: Verify starting repository**

```bash
cd /home/ed/Coding/zmk-corne
test "$(git branch --show-current)" = main
test -z "$(git status --porcelain)"
git rev-parse HEAD
git log -1 --oneline
```

Expected: `main`, clean worktree, exact starting SHA recorded in execution log.

- [x] **Step 2: Create complete ledger**

```markdown
# Security Remediation Ledger

| Finding | Status | Owner | Plan | Commit | Evidence | Reviewer | Residual gate |
|---|---|---|---|---|---|---|---|
| ZMK-SEC-001 | open | product | `docs/superpowers/plans/2026-07-30-zmk-sec-001-pin-keymap-drawer.md` | — | — | — | drawer workflow immutable |
| ZMK-SEC-002 | open | product | `docs/superpowers/plans/2026-07-30-zmk-supply-chain-remediation.md` | — | — | — | complete west graph immutable |
| ZMK-SEC-003 | open | product | `docs/superpowers/plans/2026-07-30-zmk-local-firmware-boundaries.md` | — | — | — | physical unlock and relock pass |
| ZMK-SEC-004 | open | firmware baseline | `docs/superpowers/plans/2026-07-30-official-zmk-baseline-and-gates.md` | — | — | — | DYA mutation RPCs absent |
| ZMK-SEC-005 | open | dya-studio | `docs/superpowers/plans/2026-07-30-dya-client-security-remediation.md` | — | — | — | navigation accepts HTTPS only |
| ZMK-SEC-006 | open | product | `docs/superpowers/plans/2026-07-30-zmk-supply-chain-remediation.md` | — | — | — | workflow and actions immutable |
| ZMK-SEC-007 | open | product | `docs/superpowers/plans/2026-07-30-zmk-local-firmware-boundaries.md` | — | — | — | normal artifact excludes management |
| ZMK-SEC-008 | open | firmware baseline | `docs/superpowers/plans/2026-07-30-official-zmk-baseline-and-gates.md` | — | — | — | vulnerable relay absent |
| ZMK-SEC-009 | open | upstream ZMK | `docs/superpowers/plans/2026-07-30-upstream-zmk-security-fixes.md` | — | — | — | BLE Studio disabled until fixed |
| ZMK-SEC-010 | open | zmk-studio-ts-client | `docs/superpowers/plans/2026-07-30-dya-client-security-remediation.md` | — | — | — | frame size bounded |
| ZMK-SEC-011 | open | zmk-studio-ts-client | `docs/superpowers/plans/2026-07-30-dya-client-security-remediation.md` | — | — | — | timeout releases mutex |
| ZMK-SEC-012 | open | dya-studio deployment | `docs/superpowers/plans/2026-07-30-dya-client-security-remediation.md` | — | — | — | isolated origin headers pass |
| ZMK-SEC-013 | open | react-zmk-studio | `docs/superpowers/plans/2026-07-30-dya-client-security-remediation.md` | — | — | — | ambiguous reconnect prompts |
| ZMK-SEC-014 | open | firmware baseline | `docs/superpowers/plans/2026-07-30-official-zmk-baseline-and-gates.md` | — | — | — | vulnerable wired callback absent |
| ZMK-SEC-015 | open | firmware baseline | `docs/superpowers/plans/2026-07-30-official-zmk-baseline-and-gates.md` | — | — | — | ignored positions cannot emit HID |
| ZMK-SEC-016 | open | firmware baseline | `docs/superpowers/plans/2026-07-30-official-zmk-baseline-and-gates.md` | — | — | — | write-amplifying RPCs absent |
| ZMK-SEC-017 | open | firmware baseline | `docs/superpowers/plans/2026-07-30-official-zmk-baseline-and-gates.md` | — | — | — | faulty runtime-input RPCs absent |
| ZMK-SEC-018 | open | dya-studio | `docs/superpowers/plans/2026-07-30-dya-client-security-remediation.md` | — | — | — | support export sanitized |
| ZMK-SEC-019 | open | dya-studio | `docs/superpowers/plans/2026-07-30-dya-client-security-remediation.md` | — | — | — | disruptive actions confirmed |
| ZMK-SEC-020 | open | product | `docs/superpowers/plans/2026-07-30-zmk-local-firmware-boundaries.md` | — | — | — | sensor binding capacity exact |
| ZMK-SEC-021 | open | upstream ZMK | `docs/superpowers/plans/2026-07-30-upstream-zmk-security-fixes.md` | — | — | — | settings-reset absent until fixed |
```

Allowed statuses are `open`, `in-review`, `fixed`, `removed`, and
`deferred-open`; only `fixed` and `removed` count as closed.

- [x] **Step 3: Validate ledger inventory**

```bash
python3 - <<'PY'
import pathlib, re

report = pathlib.Path("security_best_practices_report.md").read_text()
ledger = pathlib.Path("security/audit/remediation-ledger.md").read_text()
expected = {f"ZMK-SEC-{n:03d}" for n in range(1, 22)}
assert set(re.findall(r"ZMK-SEC-\d{3}", report)) == expected
assert set(re.findall(r"^\| (ZMK-SEC-\d{3}) ", ledger, re.M)) == expected
assert ledger.count("| open |") == 21
PY
git diff --check
```

- [x] **Step 4: Commit ledger**

```bash
git add security/audit/remediation-ledger.md
git commit -m "docs: add security remediation ledger"
```

### Task 2: Launch Independent First-Wave Work Packages

**Files:**
- Execute: `docs/superpowers/plans/2026-07-30-zmk-sec-001-pin-keymap-drawer.md`
- Execute: `docs/superpowers/plans/2026-07-30-zmk-supply-chain-remediation.md`
- Execute: `docs/superpowers/plans/2026-07-30-upstream-zmk-security-fixes.md`
- Execute: `docs/superpowers/plans/2026-07-30-dya-client-security-remediation.md`
- Modify: `security/audit/remediation-ledger.md`

**Interfaces:**
- Consumes: clean baseline and complete ledger from Task 1.
- Produces: reviewed commits/evidence for ZMK-SEC-001/002/005/006/009/010/011/012/013/018/019/021, with product features for 009 and 021 still disabled.

- [x] **Step 1: Dispatch three non-overlapping lanes**

Use one worker per lane:

```text
Product supply-chain lane:
  1. Execute 2026-07-30-zmk-sec-001-pin-keymap-drawer.md.
  2. Review its commit and verification evidence.
  3. Execute 2026-07-30-zmk-supply-chain-remediation.md task-by-task.
  4. Review each finding commit before next product task.

Upstream ZMK lane:
  Execute 2026-07-30-upstream-zmk-security-fixes.md task-by-task in
  /home/ed/Coding/zmk-security-remediation/zmk.

DYA client lane:
  Execute 2026-07-30-dya-client-security-remediation.md task-by-task in its
  three immutable external-repository workspaces.
```

Do not let two workers edit `/home/ed/Coding/zmk-corne` simultaneously.
If a child-plan commit already exists on `main`, verify its exact diff and test
evidence, update ledger, and skip reapplying that change.

- [x] **Step 2: Gate every child task**

For each child task:

```bash
git diff --check
git status --short
git log -1 --format='%H %s'
```

Require test output named by the child plan, a focused diff review, and exact
commit SHA before marking its ledger row `fixed`, `removed`, or `in-review`.

- [x] **Step 3: Record upstream boundary**

For ZMK-SEC-009 and ZMK-SEC-021, record upstream PR URL and reviewed commit SHA.
Keep status `in-review` until the product manifest pins reviewed code and the
affected product verification passes. Keep BLE Studio and settings-reset
disabled.

- [x] **Step 4: Review first-wave checkpoint**

```bash
cd /home/ed/Coding/zmk-corne
git status --short
git log --oneline --decorate -12
python3 security/tests/test_draw_workflow_pin.py
python3 security/tests/test_west_manifest_lock.py
python3 security/tests/test_build_workflow_pin.py
git diff --check
```

Expected: clean product tree; supply-chain tests pass; external-lane evidence is
linked from ledger.

- [x] **Step 5: Commit ledger checkpoint**

```bash
git add security/audit/remediation-ledger.md
git commit -m "docs: record first security remediation wave"
```

### Task 3: Execute Local Firmware Boundaries Serially

**Files:**
- Execute: `docs/superpowers/plans/2026-07-30-zmk-local-firmware-boundaries.md`
- Modify: `security/audit/remediation-ledger.md`

**Interfaces:**
- Consumes: frozen supply chain from Task 2.
- Produces: reviewed product commits for ZMK-SEC-003, ZMK-SEC-007, and ZMK-SEC-020 plus both-half build evidence.

- [x] **Step 1: Run child plan in declared order**

Execute Tasks 1–3 from
`docs/superpowers/plans/2026-07-30-zmk-local-firmware-boundaries.md`.
After each task, stop for its test/build gate and focused review before starting
the next task.

Use the repository-owned firmware-boundary validation workflow. It must build
ordinary right, ordinary left, locked Studio-left, and settings-reset without
uploading firmware artifacts. Push only to `edward-tecky/zmk-corne`; do not open
pull requests or write to upstream repositories.

- [x] **Step 2: Confirm artifact separation**

```bash
python3 security/tests/test_firmware_security.py
python3 security/tests/test_workflow_security.py
git diff --check
```

Expected: normal halves exclude Studio/custom management configuration; dedicated
central artifact is locked; encoder declarations match generated capacity.

- [x] **Step 3: Update and commit ledger**

Record commit SHA and build evidence separately for ZMK-SEC-003, ZMK-SEC-007,
and ZMK-SEC-020.

```bash
git add security/audit/remediation-ledger.md
git commit -m "docs: record local firmware boundary results"
```

### Task 4: Migrate to Official ZMK and Adjudicate Firmware Findings

**Files:**
- Execute: `docs/superpowers/plans/2026-07-30-official-zmk-baseline-and-gates.md`
- Modify: `security/audit/remediation-ledger.md`

**Interfaces:**
- Consumes: immutable workflow/manifest, isolated Studio artifact, upstream review state.
- Produces: official-ZMK product baseline and individual verdicts for ZMK-SEC-004/008/009/014/015/016/017/021.

- [x] **Step 1: Execute official-baseline child plan**

Run all three tasks in
`docs/superpowers/plans/2026-07-30-official-zmk-baseline-and-gates.md`.
Do not collapse its eight finding rows into one migration verdict.

- [x] **Step 2: Apply upstream gate**

If ZMK-SEC-009 or ZMK-SEC-021 lacks reviewed upstream merge SHA, leave affected
feature disabled and mark `deferred-open` only after explicit user acceptance.
If reviewed SHAs exist, pin them, rerun child-plan tests and both-half builds,
then request focused finding review before closure.

- [x] **Step 3: Verify effective removal and residual gates**

```bash
python3 security/tests/test_official_baseline.py
python3 security/scripts/verify_finding_matrix.py \
  security/audit/official-baseline-findings.md
git diff --check
```

Expected: zero DYA firmware modules in effective build; one independent verdict
for each of eight findings; no disabled feature silently marked closed.

- [x] **Step 4: Update and commit ledger**

```bash
git add security/audit/remediation-ledger.md \
  security/audit/official-baseline-findings.md
git commit -m "docs: record official ZMK finding verdicts"
```

### Task 5: Close Client Lane and Portfolio Software Gate

**Files:**
- Reference: `docs/superpowers/plans/2026-07-30-dya-client-security-remediation.md`
- Modify: `security/audit/remediation-ledger.md`

**Interfaces:**
- Consumes: DYA child-plan commits, test logs, deployment evidence, official firmware verdicts.
- Produces: complete 21-row software disposition ready for integration.

- [x] **Step 1: Verify DYA lane completion**

Require exact base and result SHAs for `zmk-studio-ts-client`,
`react-zmk-studio`, and `dya-studio`; require passing commands from all eight DYA
tasks. Record production isolation/header evidence for ZMK-SEC-012.

- [x] **Step 2: Validate portfolio status**

```bash
python3 - <<'PY'
import pathlib, re

text = pathlib.Path("security/audit/remediation-ledger.md").read_text()
rows = re.findall(
    r"^\| (ZMK-SEC-\d{3}) \| (open|in-review|fixed|removed|deferred-open) \|",
    text,
    re.M,
)
assert len(rows) == 21
assert len({finding for finding, _ in rows}) == 21
assert all(status in {"fixed", "removed", "deferred-open"} for _, status in rows)
PY
git diff --check
```

Any `deferred-open` row requires explicit user acceptance text in `Evidence` and
must name its disabled feature in `Residual gate`.

- [x] **Step 3: Obtain software-gate review**

Review every ledger row against report evidence, child-plan test output, exact
commit, and reviewer decision. Reopen any row whose evidence proves only
documentation or configuration intent.

- [x] **Step 4: Commit software-gate ledger**

```bash
git add security/audit/remediation-ledger.md
git commit -m "docs: complete security software gate"
```

### Task 6: Execute Deterministic Integration and Hardware Gate

**Files:**
- Execute: `docs/superpowers/plans/2026-07-30-zmk-security-integration-gate.md`
- Modify: `security/audit/remediation-ledger.md`
- Modify: `security/audit/manual-hardware-tests.md`

**Interfaces:**
- Consumes: complete software disposition and exact release candidate source SHA.
- Produces: reproducible UF2 hashes, explicit user approval, hardware results, final portfolio verdict.

- [x] **Step 1: Run integration child plan Task 1**

Execute deterministic clean resolution, two-pass builds, artifact comparison,
effective Kconfig/Devicetree inspection, and residual review exactly as specified
by `2026-07-30-zmk-security-integration-gate.md`.

- [ ] **Step 2: Present exact approval packet**

Provide:

```text
Source commit: output of `git rev-parse HEAD`
Right UF2 SHA-256: output of `sha256sum release/right/zmk.uf2`
Studio-left UF2 SHA-256: output of `sha256sum release/studio-left/zmk.uf2`
Open/deferred findings: rows selected from ledger with status `open` or `deferred-open`
Automated gate: PASS
```

Do not flash without user approval naming these exact hashes.

- [ ] **Step 3: Run child plan Tasks 2–3 after approval**

Execute all 18 hardware checks. Record device, side, transport, expected result,
actual result, artifact hash, tester, and timestamp for every check.

- [ ] **Step 4: Apply final stop rule**

Any failed hardware check:

1. stop further flashing;
2. mark affected findings `open`;
3. preserve logs and exact artifact hashes;
4. diagnose under `superpowers:systematic-debugging`;
5. rebuild and request new exact-hash approval before retry.

- [ ] **Step 5: Commit final evidence**

```bash
git add security/audit/remediation-ledger.md \
  security/audit/manual-hardware-tests.md \
  security/audit/release-gate.json
git diff --cached --check
git commit -m "docs: record ZMK security release gate"
```

- [ ] **Step 6: Final verification**

```bash
test -z "$(git status --porcelain)"
python3 security/scripts/verify_release_gate.py \
  --ledger security/audit/remediation-ledger.md \
  --hardware security/audit/manual-hardware-tests.md \
  --release security/audit/release-gate.json
git log --oneline --decorate -20
```

Completion requires 21 `fixed` or `removed` findings, deterministic artifacts,
all hardware checks passing, and no unapproved UF2 flash.
