# Security Best-Practices Report: ZMK Corne

## Executive Summary

Static audit at base `36de5b55a629a07666f5ada293df2c0f5c922b7b`. Five findings: mutable CI and firmware inputs, write-capable mutable workflow code, an unlocked USB Studio endpoint, and management features compiled into every left-half build. No critical finding. No high-confidence secret-pattern match in reachable Git history.

Protected assets: firmware integrity on both halves; host input integrity/confidentiality; Bluetooth identities, bonds, and settings; GitHub repository and Actions token; build-artifact provenance.

Threats reviewed: changed branch/tag after review, compromised dependency or reusable workflow, malicious USB/BLE Studio request, accidental management-interface exposure, and untrusted workflow code receiving a write token. Physical device compromise, Nordic bootloader security, host OS compromise, semiconductor attacks, and protocol memory safety require separate source/hardware review.

## Scope and Method

Scope: repository-local firmware configuration, build manifest, keymap, shield configuration/overlays, GitHub Actions, Task 1 dependency/workflow inventories, and reachable repository history. No firmware, configuration, workflow, dependency, hardware, or flash changes were made.

Method:

1. Read `build.yaml`, shield `.conf`/`.overlay` files, `config/eyelash_corne.conf`, and `config/eyelash_corne.keymap`; traced Studio, custom RPC, settings, reset, bootloader, and USB-UART configuration.
2. Traced workflow trigger to reusable workflow/action, effective declared permissions, repository write path, and immutable resolution using `security/audit/workflow-inventory.tsv`.
3. Used `security/audit/dependency-inventory.tsv` to identify mutable manifest inputs and their resolved commits.
4. Reviewed reachable history for sensitive additions and secret-pattern matches.

Command results:

- `rg -n '^(on:|[[:space:]]+(pull_request_target|pull_request|push|workflow_run|workflow_dispatch):|[[:space:]]+permissions:|[[:space:]]+contents:|[[:space:]]+uses:)' .github/workflows /tmp/zmk-corne-security-audit --glob '*.yml' --glob '*.yaml'` found only `push` and `workflow_dispatch`; no `pull_request`, `pull_request_target`, or `workflow_run`. It found unpinned `caksoylar/keymap-drawer@main`, `contents: write`, and `zmkfirmware/zmk@v0.3.0`.
- `git log --all --stat -- . ':!keymap-drawer/*.svg'` examined 260 commits (2,483 output lines).
- `git log -p --all -G '(token|secret|password|BEGIN .*PRIVATE KEY|curl|wget|uses:|url-base:|revision:)'` selected 13 commits. Review showed workflow/manifest history; it did not establish a credential disclosure.
- Required quoted form `git grep ... "$(git rev-list --all)"` exited 128 because Git treated newline-separated revisions as one path. Corrected equivalent `git grep ... $(git rev-list --all)` scanned all reachable revisions and returned zero matches. No secret values are reproduced here.

## Critical Findings

None in this local/CI scope.

## High Findings

### ZMK-SEC-001 — Mutable keymap drawer code receives repository write permission

**Severity:** High
**Class:** Supply-chain risk
**Evidence:** `.github/workflows/draw.yml:12-17`; Task 1 workflow inventory `security/audit/workflow-inventory.tsv:8` records requested `main` resolved to `3a4ca7e060a54ba700d3e7b6a43cb0b9cec347d2`.
**Impact:** Compromise or retargeting of `caksoylar/keymap-drawer` can execute attacker-controlled workflow code with permission to commit to this repository.
**Scenario:** Trusted `push` or manual dispatch starts Draw Keymap; caller resolves `@main`; called workflow receives `contents: write` and `destination: "commit"`; malicious replacement code pushes an arbitrary repository change.
**Recommendation:** Pin called workflow to reviewed commit `3a4ca7e060a54ba700d3e7b6a43cb0b9cec347d2`; preserve `contents: write` only in separate tightly scoped generation job if automatic commits remain required, otherwise generate artifact or pull request without write token.
**Regression risk:** Immutable pin stops automatic upstream changes; removing write permission changes generated-keymap publication flow.
**Verification:** Dispatch workflow from pinned commit; confirm only intended `keymap-drawer/**` change commits; inspect job token permissions and deny arbitrary repository write attempts.

### ZMK-SEC-002 — Firmware build graph resolves mutable source revisions

**Severity:** High
**Class:** Supply-chain risk
**Evidence:** `config/west.yml:8-29`; Task 1 dependency inventory `security/audit/dependency-inventory.tsv:2-9` records mutable inputs resolved to `eyelash_corne=ba1eeab627ba94ac46f7768b3ddc01f97873ca87`, `zmk=4493783ef88ce2e653bf8217c92ee17140df71e3`, `zmk-behavior-runtime-sensor-rotate=8b1125ed676c1f5e14145d217984f33d0ebdcef4`, `zmk-module-ble-management=851661cd21f2aded8ec649da86e01a207dc4b973`, `zmk-module-battery-history=307755dd2ad4d320e14de162e8e5ef018f29d929`, `zmk-module-settings-rpc=78f86df9e6c5edaf57bef3ccbd7f360cfdf49291`, `zmk-module-runtime-input-processor=dbf92f764de8b6ffd60bf5850514302875fe2570`, and imported `zephyr=dacab4875df72109b96cc8977547a0dc04875bcd`.
**Impact:** Same reviewed repository revision can build different firmware later, including malicious firmware, when branch or lightweight-tag targets move.
**Scenario:** Any mutable project revision changes after review; next local or CI `west update` resolves new source before build. Task 1 inventory records eight mutable direct/imported inputs, including `zmk`, all custom modules, and imported Zephyr.
**Recommendation:** Replace every Task 1 inventory row marked `mutable=yes` with its recorded full resolved SHA; current direct values include `eyelash_corne=ba1eeab627ba94ac46f7768b3ddc01f97873ca87`, `zmk=4493783ef88ce2e653bf8217c92ee17140df71e3`, and each listed module SHA. Retain human-readable upstream release/branch comment beside each pin.
**Regression risk:** Updates require explicit SHA review; fork/module compatibility can diverge from moving upstream branches.
**Verification:** Run `west update` twice from clean workspaces; compare `west list -f '{name} {revision}'` against inventory and reproduce firmware hashes where toolchain permits.

### ZMK-SEC-003 — Studio USB management endpoint starts unlocked

**Severity:** High
**Class:** Hardening gap
**Evidence:** `build.yaml:7-9`
**Impact:** Any host with physical USB access to Studio-left firmware can issue Studio management requests without first requiring local keyboard unlock.
**Scenario:** Studio-left build includes `studio-rpc-usb-uart` and explicitly sets `CONFIG_ZMK_STUDIO_LOCKING=n`; ZMK Studio core initializes unlocked when locking is disabled. Local physical attacker attaches USB and uses exposed management endpoint.
**Recommendation:** Set `CONFIG_ZMK_STUDIO_LOCKING=y` for Studio-left; retain `&studio_unlock` at `config/eyelash_corne.keymap:91` as deliberate physical authorization. Keep disconnect and idle re-lock enabled at upstream defaults unless a reviewed requirement overrides them.
**Regression risk:** Studio remapping requires physical unlock and may interrupt current installer workflow; validate supported DYA Studio compatibility before release.
**Verification:** Flash Studio-left test artifact; before unlock, verify Studio write/reset request is rejected; press `&studio_unlock`, verify intended operation; disconnect and wait idle timeout, then verify it is rejected again.

## Medium Findings

### ZMK-SEC-004 — Build workflow uses mutable reusable workflow/action tags

**Severity:** Medium
**Class:** Supply-chain risk
**Evidence:** `.github/workflows/build.yml:1-10`; Task 1 workflow inventory `security/audit/workflow-inventory.tsv:2-7` records requested `zmkfirmware/zmk@v0.3.0` resolved to `edf5c0814fd3ea202e43aad2d68fd32e882a518c`, `actions/checkout@v4` to `11d5960a326750d5838078e36cf38b85af677262`, `actions/cache@v4` to `0057852bfaa89a56745cba8c7296529d2fc39830`, and `actions/upload-artifact@v4`/`actions/upload-artifact/merge@v4` to `ea165f8d65b6e75b540449e92b4886f43607fa02`.
**Impact:** A moved workflow/action tag can alter CI build behavior or generated firmware artifact without a repository commit and, if repository Actions default grants write, can gain repository-write capability.
**Scenario:** `Build ZMK firmware` runs on trusted push/manual dispatch and resolves `zmkfirmware/zmk@v0.3.0`; nested `actions/*` references are lightweight tags, not immutable commits. Caller declares no `permissions`, so Task 1 inventory records that repository default governs effective `GITHUB_TOKEN` scope. Changed tag code runs during build with whatever scope that repository setting permits.
**Recommendation:** Pin reusable workflow to `edf5c0814fd3ea202e43aad2d68fd32e882a518c`; when upstream workflow update is reviewed, update SHA and release comment together. Add caller least-privilege `permissions`, normally `contents: read`, after confirming reusable workflow requirements; require called workflow to use full-SHA action pins or vendor a reviewed reusable workflow.
**Regression risk:** Pinning delays upstream CI fixes and can require manual update of nested action pins.
**Verification:** Manually check repository Settings → Actions → General → Workflow permissions and record read-only versus read/write default; inspect effective job token permissions. Then trigger build twice from clean runners; record called-workflow SHA and action SHAs from workflow inventory; verify expected firmware artifact names and hashes.

### ZMK-SEC-005 — Generic left-half configuration enables Studio and custom management RPCs

**Severity:** Medium
**Class:** Hardening gap
**Evidence:** `boards/shields/eyelash_corne/eyelash_corne_left.conf:14-32`
**Impact:** Every build selecting `eyelash_corne_left` contains Studio and enabled custom management/RPC components, even when `build.yaml` does not select USB Studio transport.
**Scenario:** Standard left and Studio-left build entries both select same left shield. Shield configuration enables Studio, BLE management Studio RPC, runtime-input Studio RPC, settings RPC, runtime-sensor Studio RPC, and persistent settings. Later transport or module change can expose management capability in artifact assumed non-Studio.
**Recommendation:** Move `CONFIG_ZMK_STUDIO` and all `*_STUDIO_RPC`/management Kconfig settings into explicit Studio-only configuration selected only by Studio-left build. Keep ordinary left build free of management interfaces; document any required peripheral settings RPC separately.
**Regression risk:** DYA Studio features, runtime settings, or encoder configuration can disappear from non-Studio left artifact; split central/peripheral behavior must be rebuilt and tested.
**Verification:** Build ordinary left, Studio-left, and right artifacts; inspect each effective `.config` and DTS for Studio, USB CDC ACM/UART, BLE management, settings RPC, runtime RPC, and split relay settings.

## Low Findings

None in this local/CI scope.

## Positive Security Observations

- Draw and build workflows use only trusted `push` and `workflow_dispatch`; no `pull_request`, `pull_request_target`, or `workflow_run` trigger appears in `.github/workflows/build.yml:2-10` or `.github/workflows/draw.yml:2-17`.
- USB Studio transport is requested only by named Studio-left build entry; right build has no transport snippet (`build.yaml:3-9`). This does not negate ZMK-SEC-005 because left-shield management Kconfig remains broad.
- `&studio_unlock` exists on Fn layer (`config/eyelash_corne.keymap:88-93`), ready for locking-enabled authorization.
- Dedicated `settings_reset` artifact preserves recovery path (`build.yaml:10-11`). Persistent settings are intentional on central left (`boards/shields/eyelash_corne/eyelash_corne_left.conf:31-32`).
- Bootloader and `sys_reset` bindings are reachable on Fn layer (`config/eyelash_corne.keymap:88-94`). No finding assigned: physical access and bootloader protection assumptions were not verified, and ordinary recovery bindings alone do not establish vulnerability.
- Required history secret-pattern scan returned zero matches. Pattern absence is not proof that history is credential-free.

## Migration Recommendation

Target state: official ZMK where feature requirements permit; smallest reviewed external module set; every west project and Action/reusable workflow pinned to immutable SHA with upstream version comment; Studio only in dedicated central-left artifact; Studio locking enabled with physical unlock; minimum CI permissions; reviewed settings-reset recovery image.

Do not treat custom RPC code, BLE authorization, DYA client behavior, or effective build output as reviewed by this report. Those need source, build, and hardware validation work.

## Limitations and Manual Validation

Static review only. No firmware build, hardware flash, serial probe, Studio client connection, BLE scan, reset, bootloader invocation, or settings-reset operation occurred.

Manual validation must confirm: intended central half, USB-only versus BLE Studio transport, lock-before-unlock behavior, re-lock on disconnect/idle, custom RPC authorization, persistence/reset semantics, and physical bootloader protection. Build inspection must establish effective Kconfig/DTS because shield and CMake configuration composition can alter results.

## Remediation Order

1. Eliminate write-token execution of mutable Draw Keymap code (ZMK-SEC-001).
2. Pin all west manifest sources and CI reusable workflows/actions (ZMK-SEC-002, ZMK-SEC-004).
3. Enable Studio locking and test physical unlock/re-lock behavior (ZMK-SEC-003).
4. Split Studio/custom RPC settings from normal left firmware; inspect all artifact effective configs (ZMK-SEC-005).

## Audit Record

**Files changed:** `security_best_practices_report.md` only. No firmware, configuration, workflow, dependency, or hardware state changed.

**Audit report commit:** `df60510124e2162b48f85d6945b190960513d651` (`docs: audit local ZMK security configuration`).

**Concerns:** Effective artifact configuration, custom RPC authorization/parser safety, BLE Studio reachability, physical bootloader protection, and hardware lock/re-lock behavior remain unverified. Required quoted history-secret command has shell argument-shape defect; corrected all-revision scan returned zero matches.
