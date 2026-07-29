# Security Best-Practices Report: ZMK Corne

## Executive Summary

Static audit at base `36de5b55a629a07666f5ada293df2c0f5c922b7b`. Five findings: mutable CI and firmware inputs, write-capable mutable workflow code, an unlocked USB Studio endpoint, and management features compiled into every left-half build. No critical finding. No high-confidence secret-pattern match in reachable Git history.

Fork-source delta review at immutable Cormoran ZMK commit `4493783ef88ce2e653bf8217c92ee17140df71e3` adds three findings: an undersized encrypted relay write reaches an out-of-bounds header read, wired transport disable callbacks do not disable their receivers, and tap-dance ignored positions still resolve to HID behavior. The latter two are respectively a dormant hardening gap and a maintainability/HID-integrity defect, not remotely reachable vulnerabilities in the reviewed Corne configuration.

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

### ZMK-SEC-006 — One-byte relay writes reach a two-byte header read

**Severity:** Medium
**Class:** Vulnerability / memory safety
**Evidence:** Audited clone `/tmp/zmk-corne-security-audit/zmk/app/src/split/bluetooth/service.c:100-113` at `4493783ef88ce2e653bf8217c92ee17140df71e3`; the characteristic requires an encrypted write at `/tmp/zmk-corne-security-audit/zmk/app/src/split/bluetooth/service.c:278-282` at the same SHA.
**Impact:** A peer on an encrypted split link can make the peripheral read one byte beyond the supplied GATT attribute value. No disclosure path was established, but the C out-of-bounds read can consume unrelated buffer data and may fault or destabilize firmware depending on the Bluetooth buffer layout.
**Scenario:** Peer sends `WRITE WITHOUT RESPONSE` to the relay-event characteristic with `offset=0` and `len=1`; the initial check rejects only zero length or an oversized aggregate; `memcpy(header, buf, sizeof(struct relay_event_header))` then reads two bytes from the one-byte value before any minimum-header validation.
**Recommendation:** Reject `len < sizeof(struct relay_event_header)` and every nonzero offset before copying the header; retain the existing maximum-field and exact-total-length checks after that guard.
**Regression risk:** Strict rejection removes any accidental fragmented-write behavior. The characteristic already says offset support is absent and uses write-without-response, so a full-frame-only contract should be validated against the actual central.
**Verification:** Add a host-side GATT parser test for lengths 0, 1, exact header, exact valid frame, maximum valid frame, and oversized fields under ASan/UBSan where possible; on hardware, send the same encrypted writes and confirm rejection without reset or event delivery.

## Low Findings

None in this local/CI scope.

### ZMK-SEC-007 — Wired transport disable callbacks leave the receiver active

**Severity:** Low
**Class:** Hardening gap / dormant transport trust
**Evidence:** Audited clone `/tmp/zmk-corne-security-audit/zmk/app/src/split/wired/central.c:409-425`, `/tmp/zmk-corne-security-audit/zmk/app/src/split/wired/peripheral.c:380-399`, `/tmp/zmk-corne-security-audit/zmk/app/src/split/wired/peripheral.c:464-510`, and `/tmp/zmk-corne-security-audit/zmk/app/src/split/peripheral.c:27-59` at `4493783ef88ce2e653bf8217c92ee17140df71e3`.
**Impact:** A build that enables wired split cannot reliably deactivate its wired receiver during transport selection. This weakens the active-transport trust boundary and can leave a physical command-input path running after a switch. Reviewed Corne DTS does not enable wired split, so no current artifact reachability was established.
**Scenario:** Dual-transport firmware activates wired RX and later asks the registered transport API to disable it; central callback sets only its local argument and returns no defined status, peripheral callback returns success without acting, and peripheral internal disable overwrites `enabled=false` with `true`. Wired parser work therefore remains capable of queueing commands.
**Recommendation:** Make both public callbacks call their internal enable/disable implementation and return its result; remove the forced `enabled=true`; gate command processing on the registered transport being active.
**Regression risk:** Correct disable behavior changes failover timing and may expose latent health-check or UART power-management assumptions.
**Verification:** On a wired-enabled fixture, switch between wired and BLE while recording UART IRQ/async state; after disable, inject a valid CRC-framed behavior command and confirm it is ignored; re-enable and confirm normal operation.

### ZMK-SEC-008 — Tap-dance ignored positions still trigger HID behavior

**Severity:** Low
**Class:** Maintainability / HID integrity
**Evidence:** Audited clone `/tmp/zmk-corne-security-audit/zmk/app/src/behaviors/behavior_tap_dance.c:217-247` at `4493783ef88ce2e653bf8217c92ee17140df71e3`.
**Impact:** Configuration claims an ignored key will not interrupt an active tap dance, but that key can still stop the timer and press/release the selected tap-dance behavior, producing unintended host input. This is a functional HID-integrity defect, not an externally reachable vulnerability.
**Scenario:** Tap dance is undecided; a configured `ignore-key-positions` key is pressed; matching branch executes `continue` only for the inner ignore-list loop; control then reaches `stop_timer()` and `press_tap_dance_behavior()`.
**Recommendation:** Track a match and continue the outer active-tap-dance loop, or move ignore-list evaluation into a helper whose true result skips resolution.
**Regression risk:** Correct ignored-key behavior changes timing for users who may have unknowingly depended on current interruption.
**Verification:** Add behavior test with one active tap dance and one ignored key; assert no tap-dance press/release event on ignored press, then assert a non-ignored press still resolves it.

## Positive Security Observations

- Draw and build workflows use only trusted `push` and `workflow_dispatch`; no `pull_request`, `pull_request_target`, or `workflow_run` trigger appears in `.github/workflows/build.yml:2-10` or `.github/workflows/draw.yml:2-17`.
- USB Studio transport is requested only by named Studio-left build entry; right build has no transport snippet (`build.yaml:3-9`). This does not negate ZMK-SEC-005 because left-shield management Kconfig remains broad.
- `&studio_unlock` exists on Fn layer (`config/eyelash_corne.keymap:88-93`), ready for locking-enabled authorization.
- Dedicated `settings_reset` artifact preserves recovery path (`build.yaml:10-11`). Persistent settings are intentional on central left (`boards/shields/eyelash_corne/eyelash_corne_left.conf:31-32`).
- Bootloader and `sys_reset` bindings are reachable on Fn layer (`config/eyelash_corne.keymap:88-94`). No finding assigned: physical access and bootloader protection assumptions were not verified, and ordinary recovery bindings alone do not establish vulnerability.
- Required history secret-pattern scan returned zero matches. Pattern absence is not proof that history is credential-free.
- Custom Studio requests are bounded by pinned message option `zmk.custom.CallRequest.payload max_size:CONFIG_ZMK_STUDIO_RPC_CUSTOM_SUBSYSTEM_REQUEST_PAYLOAD_MAX_BYTES` (`/tmp/zmk-corne-security-audit/zmk-studio-messages/proto/zmk/custom.options.in:1-2` at `89b81d2e587fce807b668dff2a6967a40beef421`); fork Kconfig defaults that maximum to 25 bytes (`/tmp/zmk-corne-security-audit/zmk/app/src/studio/Kconfig:111-121` at `4493783ef88ce2e653bf8217c92ee17140df71e3`). Custom dispatch validates subsystem index and applies each registered subsystem's `SECURED` lock policy before invoking its handler (`/tmp/zmk-corne-security-audit/zmk/app/src/studio/custom_subsystem.c:90-113` at `4493783ef88ce2e653bf8217c92ee17140df71e3`). The top-level custom handler is intentionally unsecure because this inner check owns policy.
- BLE relay central-to-peripheral writes require both an L2-or-higher connection check and an encrypted-write GATT permission; peripheral-to-central frames validate header presence, configured name/data maxima, exact total length, and null-terminate the copied name before queueing (`/tmp/zmk-corne-security-audit/zmk/app/src/split/bluetooth/central.c:348-368` and `/tmp/zmk-corne-security-audit/zmk/app/src/split/bluetooth/central.c:380-438` at `4493783ef88ce2e653bf8217c92ee17140df71e3`). ZMK-SEC-006 is the asymmetric missing minimum-header check in the peripheral write callback.
- Relay macros enforce event payload and identifier capacity at build time, copy only `sizeof(struct event_type)`, and receivers require exact event-data size before reconstructing the typed event (`/tmp/zmk-corne-security-audit/zmk/app/include/zmk/event_manager.h:95-139` at `4493783ef88ce2e653bf8217c92ee17140df71e3`).
- Runtime activity settings accept only the exact persisted struct length and coalesce saves through delayed work (`/tmp/zmk-corne-security-audit/zmk/app/src/activity.c:67-83` and `/tmp/zmk-corne-security-audit/zmk/app/src/activity.c:106-122` at `4493783ef88ce2e653bf8217c92ee17140df71e3`). Save-result reporting, numeric policy, and hardware sleep behavior remain validation concerns rather than established vulnerabilities.

## Cormoran Fork Delta Provenance and Review

Audited source: `https://github.com/cormoran/zmk` at immutable commit `4493783ef88ce2e653bf8217c92ee17140df71e3` (`2026-05-04T16:25:41+09:00`, `Merge pull request #1 from cormoran/dev/v0.3-branch+dya/support-mouse-keymap`). This exactly matches Task 1's resolved `cormoran/zmk@v0.3-branch+dya` identity.

Official comparison: fetched `https://github.com/zmkfirmware/zmk.git` `main` at `faaf39d9f59cd2a27eca3739cdd9eb197654299b` on 2026-07-29. `git merge-base HEAD upstream/main` returned `edf5c0814fd3ea202e43aad2d68fd32e882a518c` (`2025-08-01T16:44:20-06:00`, `chore(main): release 0.3.0 (#2858)`), matching the expected official ZMK v0.3.0 base.

`git diff --stat edf5c0814fd3ea202e43aad2d68fd32e882a518c..4493783ef88ce2e653bf8217c92ee17140df71e3 -- app` reported 41 files, 1,322 insertions, and 69 deletions. Exact non-test app delta:

```text
M	app/CMakeLists.txt
M	app/dts/bindings/behaviors/zmk,behavior-hold-tap.yaml
M	app/dts/bindings/behaviors/zmk,behavior-tap-dance.yaml
M	app/dts/bindings/zmk,wired-split.yaml
M	app/include/drivers/behavior.h
A	app/include/linker/zmk-rpc-custom-subsystems.ld
M	app/include/zmk/activity.h
M	app/include/zmk/ble.h
M	app/include/zmk/endpoints.h
M	app/include/zmk/event_manager.h
M	app/include/zmk/split/bluetooth/uuid.h
M	app/include/zmk/split/central.h
M	app/include/zmk/split/transport/types.h
A	app/include/zmk/split/wired/peripheral.h
A	app/include/zmk/studio/custom.h
M	app/module/drivers/sensor/battery/battery_common.c
M	app/module/drivers/sensor/battery/battery_common.h
M	app/module/drivers/sensor/battery/battery_voltage_divider.c
M	app/module/dts/bindings/sensor/zmk,battery-voltage-divider.yaml
M	app/src/activity.c
M	app/src/behaviors/behavior_bt.c
M	app/src/behaviors/behavior_hold_tap.c
M	app/src/behaviors/behavior_input_two_axis.c
M	app/src/behaviors/behavior_tap_dance.c
M	app/src/ble.c
M	app/src/endpoints.c
M	app/src/event_manager.c
M	app/src/split/Kconfig
M	app/src/split/bluetooth/central.c
M	app/src/split/bluetooth/service.c
M	app/src/split/central.c
M	app/src/split/peripheral.c
M	app/src/split/wired/central.c
M	app/src/split/wired/peripheral.c
M	app/src/studio/CMakeLists.txt
M	app/src/studio/Kconfig
M	app/src/studio/core.c
A	app/src/studio/custom_subsystem.c
M	app/src/studio/gatt_rpc_transport.c
M	app/src/studio/rpc.c
M	app/west.yml
```

Required split primitive search returned 103 matching diff lines. Required added-dangerous-primitive search returned 28 lines: four `allocate` documentation/name false positives, five relay macro copies protected by compile-time size assertions, and outbound/inbound relay pack/unpack operations. Review found one actionable unmatched bound, ZMK-SEC-006; other inbound copies follow maximum and exact-total-length checks, while current outbound callers derive lengths from compile-time-sized event types.

Runtime/HID dispositions: activity persistence checks stored length and debounces writes but does not report `settings_save_one()` failure; activity setters update idle before sleep with no rollback if the latter fails; battery interpolation assumes a nonempty ordered devicetree threshold list, but reviewed Corne uses `zmk,battery-nrf-vddh`, not the changed voltage-divider driver; hold-tap list lengths bound their loops; tap-dance ignore control flow produces ZMK-SEC-008. Wired health/enable code produces ZMK-SEC-007 but is dormant without a `zmk,wired-split` devicetree node.

Fork `git diff --check` is not clean: `app/dts/bindings/zmk,wired-split.yaml:41` has a new blank line at EOF. This is maintainability evidence, not a security finding, and source was not changed.

## Migration Recommendation

Target state: official ZMK where feature requirements permit; smallest reviewed external module set; every west project and Action/reusable workflow pinned to immutable SHA with upstream version comment; Studio only in dedicated central-left artifact; Studio locking enabled with physical unlock; minimum CI permissions; reviewed settings-reset recovery image.

Do not treat custom RPC code, BLE authorization, DYA client behavior, or effective build output as reviewed by this report. Those need source, build, and hardware validation work.

Task 3 narrows that earlier limitation: Cormoran fork dispatcher, framing deltas, BLE/split relay paths, wired transport changes, runtime activity storage, changed behaviors, and battery-driver delta were statically reviewed at the immutable SHA above. External custom subsystem implementations, complete BLE pairing policy, DYA client, effective build output, and hardware behavior remain outside verified scope.

## Limitations and Manual Validation

Static review only. No firmware build, hardware flash, serial probe, Studio client connection, BLE scan, reset, bootloader invocation, or settings-reset operation occurred.

Manual validation must confirm: intended central half, USB-only versus BLE Studio transport, lock-before-unlock behavior, re-lock on disconnect/idle, custom RPC authorization, persistence/reset semantics, and physical bootloader protection. Build inspection must establish effective Kconfig/DTS because shield and CMake configuration composition can alter results.

Fork delta review was also static. No Zephyr/ZMK build, sanitizer execution against the embedded GATT callback, BLE packet injection, split pairing, wired fixture, HID capture, or battery/sleep measurement occurred. Hardware behavior and actual compiler/linker configuration remain unverified. External custom subsystem implementations were consulted only to understand dispatcher policy and activity reachability; they were not exhaustively audited here.

## Remediation Order

1. Eliminate write-token execution of mutable Draw Keymap code (ZMK-SEC-001).
2. Pin all west manifest sources and CI reusable workflows/actions (ZMK-SEC-002, ZMK-SEC-004).
3. Enable Studio locking and test physical unlock/re-lock behavior (ZMK-SEC-003).
4. Split Studio/custom RPC settings from normal left firmware; inspect all artifact effective configs (ZMK-SEC-005).
5. Reject undersized/nonzero-offset relay writes before header access (ZMK-SEC-006).
6. Correct wired transport disable semantics before enabling wired split in an artifact (ZMK-SEC-007).
7. Make tap-dance ignored positions skip outer resolution and add HID-event regression coverage (ZMK-SEC-008).

## Audit Record

**Files changed:** `security_best_practices_report.md` only. No firmware, configuration, workflow, dependency, or hardware state changed.

**Audit report commit:** `df60510124e2162b48f85d6945b190960513d651` (`docs: audit local ZMK security configuration`).

**Concerns:** Effective artifact configuration, custom RPC authorization/parser safety, BLE Studio reachability, physical bootloader protection, and hardware lock/re-lock behavior remain unverified. Required quoted history-secret command has shell argument-shape defect; corrected all-revision scan returned zero matches.

**Fork audit scope:** Cormoran ZMK `4493783ef88ce2e653bf8217c92ee17140df71e3` against official merge base `edf5c0814fd3ea202e43aad2d68fd32e882a518c`; report-only update, no source remediation or flash.

**Fork audit concerns:** ZMK-SEC-006 needs sanitizer and encrypted-link packet tests; ZMK-SEC-007 needs a wired fixture but is dormant in reviewed Corne DTS; ZMK-SEC-008 needs behavior/HID event coverage. Hardware behavior remains unverified.
