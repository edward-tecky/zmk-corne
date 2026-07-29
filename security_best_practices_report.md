# Security Best-Practices Report: ZMK Corne

## Executive Summary

Static audit at base `36de5b55a629a07666f5ada293df2c0f5c922b7b`. Five findings: mutable CI and firmware inputs, write-capable mutable workflow code, an unlocked USB Studio endpoint, and management features compiled into every left-half build. No critical finding. No high-confidence secret-pattern match in reachable Git history.

Fork-source delta review at immutable Cormoran ZMK commit `4493783ef88ce2e653bf8217c92ee17140df71e3` adds four findings: an undersized encrypted relay write reaches an out-of-bounds header read, BLE Studio RX can spin forever when its ring buffer fills, wired transport disable callbacks do not disable their receivers, and tap-dance ignored positions still resolve to HID behavior. Wired and tap-dance findings are respectively a dormant hardening gap and a maintainability/HID-integrity defect, not remotely reachable vulnerabilities in the reviewed Corne configuration.

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

### ZMK-SEC-007 — Full Studio RX ring buffer traps BLE callback in an infinite loop

**Severity:** Medium
**Class:** Vulnerability / denial of service
**Evidence:** Audited clone `/tmp/zmk-corne-security-audit/zmk/app/src/studio/gatt_rpc_transport.c:63-85` and default 30-byte RX capacity at `/tmp/zmk-corne-security-audit/zmk/app/src/studio/Kconfig:97-103` at `4493783ef88ce2e653bf8217c92ee17140df71e3`; BLE Studio transport is enabled by default at `/tmp/zmk-corne-security-audit/zmk/app/src/studio/Kconfig:74-80` at the same SHA.
**Impact:** An encrypted BLE Studio client can trap Bluetooth callback processing indefinitely, preventing RPC notification and denying Bluetooth processing until watchdog/reset intervention.
**Scenario:** With `handling_rx=true`, encrypted client sends a Studio GATT write whose length exceeds current free RX-ring capacity; callback copies until the 30-byte default ring fills; `ring_buf_put_claim()` then returns zero, `copied` does not advance, loop never exits, and `zmk_rpc_rx_notify()` is never reached.
**Recommendation:** Before copying, atomically reject a write that exceeds current ring-buffer free space, or implement bounded backpressure that exits callback and resumes only after consumer progress; never wait or spin inside Bluetooth write callback. Define one full-write acceptance contract so rejected data cannot leave a partial RPC frame.
**Regression risk:** Whole-write rejection can require client retry/framing changes and can expose existing assumptions about ATT write size versus RPC ring capacity; asynchronous backpressure adds synchronization and disconnect cleanup complexity.
**Verification:** Host test should prefill RX ring to controlled free capacities, submit writes at `free`, `free+1`, and larger-than-empty-capacity sizes, and assert bounded callback return, no partial enqueue on rejection, and notification only for accepted bytes. Hardware test should negotiate a sufficiently large BLE MTU, send an encrypted oversized or rapid write sequence, and confirm BLE remains responsive, callback returns, malformed RPC is rejected, and later valid RPC succeeds.

## Low Findings

None in this local/CI scope.

### ZMK-SEC-008 — Wired transport disable callbacks leave the receiver active

**Severity:** Low
**Class:** Hardening gap / dormant transport trust
**Evidence:** Audited clone `/tmp/zmk-corne-security-audit/zmk/app/src/split/wired/central.c:409-425`, `/tmp/zmk-corne-security-audit/zmk/app/src/split/wired/peripheral.c:380-399`, `/tmp/zmk-corne-security-audit/zmk/app/src/split/wired/peripheral.c:464-510`, and `/tmp/zmk-corne-security-audit/zmk/app/src/split/peripheral.c:27-59` at `4493783ef88ce2e653bf8217c92ee17140df71e3`.
**Impact:** A build that enables wired split cannot reliably deactivate its wired receiver during transport selection. This weakens the active-transport trust boundary and can leave a physical command-input path running after a switch. Reviewed Corne DTS does not enable wired split, so no current artifact reachability was established.
**Scenario:** Dual-transport firmware activates wired RX and later asks the registered transport API to disable it; central callback sets only its local argument and returns no defined status, peripheral callback returns success without acting, and peripheral internal disable overwrites `enabled=false` with `true`. Wired parser work therefore remains capable of queueing commands.
**Recommendation:** Make both public callbacks call their internal enable/disable implementation and return its result; remove the forced `enabled=true`; gate command processing on the registered transport being active.
**Regression risk:** Correct disable behavior changes failover timing and may expose latent health-check or UART power-management assumptions.
**Verification:** On a wired-enabled fixture, switch between wired and BLE while recording UART IRQ/async state; after disable, inject a valid CRC-framed behavior command and confirm it is ignored; re-enable and confirm normal operation.

### ZMK-SEC-009 — Tap-dance ignored positions still trigger HID behavior

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

Separate Studio GATT control-flow review found ZMK-SEC-007; the required dangerous-primitive regex does not select `ring_buf_put_claim()` or the zero-progress loop. RX-ring capacity, callback progress, and notify reachability are now explicitly dispositioned by that finding.

Runtime/HID dispositions: activity persistence checks stored length and debounces writes but does not report `settings_save_one()` failure; activity setters update idle before sleep with no rollback if the latter fails; battery interpolation assumes a nonempty ordered devicetree threshold list, but reviewed Corne uses `zmk,battery-nrf-vddh`, not the changed voltage-divider driver; hold-tap list lengths bound their loops; tap-dance ignore control flow produces ZMK-SEC-009. Wired health/enable code produces ZMK-SEC-008 but is dormant without a `zmk,wired-split` devicetree node.

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
6. Bound Studio BLE RX writes so a full ring never traps callback processing (ZMK-SEC-007).
7. Correct wired transport disable semantics before enabling wired split in an artifact (ZMK-SEC-008).
8. Make tap-dance ignored positions skip outer resolution and add HID-event regression coverage (ZMK-SEC-009).

## Audit Record

**Files changed:** `security_best_practices_report.md` only. No firmware, configuration, workflow, dependency, or hardware state changed.

**Audit report commit:** `df60510124e2162b48f85d6945b190960513d651` (`docs: audit local ZMK security configuration`).

**Concerns:** Effective artifact configuration, custom RPC authorization/parser safety, BLE Studio reachability, physical bootloader protection, and hardware lock/re-lock behavior remain unverified. Required quoted history-secret command has shell argument-shape defect; corrected all-revision scan returned zero matches.

**Fork audit scope:** Cormoran ZMK `4493783ef88ce2e653bf8217c92ee17140df71e3` against official merge base `edf5c0814fd3ea202e43aad2d68fd32e882a518c`; report-only update, no source remediation or flash.

**Fork audit concerns:** ZMK-SEC-006 needs sanitizer and encrypted-link packet tests; ZMK-SEC-007 needs bounded host-ring and encrypted BLE stress tests; ZMK-SEC-008 needs a wired fixture but is dormant in reviewed Corne DTS; ZMK-SEC-009 needs behavior/HID event coverage. Hardware behavior remains unverified.

## External DYA Firmware Module Audit

Static module review at authorized repository base `e7c5b978cf075e411e03665fefe13ed2cdec5e74` adds three findings: lock-bypassing BLE/settings mutation RPCs, immediate per-request flash writes, and dormant runtime-input numeric/control-flow faults. Exact clones were clean and matched Task 1: `zmk-behavior-runtime-sensor-rotate=8b1125ed676c1f5e14145d217984f33d0ebdcef4`, `zmk-module-ble-management=851661cd21f2aded8ec649da86e01a207dc4b973`, `zmk-module-battery-history=307755dd2ad4d320e14de162e8e5ef018f29d929`, `zmk-module-settings-rpc=78f86df9e6c5edaf57bef3ccbd7f360cfdf49291`, and `zmk-module-runtime-input-processor=dbf92f764de8b6ffd60bf5850514302875fe2570`. Clone directories below are Task 1 aliases under `/tmp/zmk-corne-security-audit`; each cited file was inspected at its module SHA.

### ZMK-SEC-010 — Unsecured module RPCs bypass Studio lock for bond and activity mutations

**Severity:** High
**Class:** Authorization / management integrity
**Evidence:** BLE management registers `cormoran_ble` as `ZMK_STUDIO_RPC_HANDLER_UNSECURED` at audited clone `/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c:50-66` and exposes profile switching/unpairing, all-bond deletion, and output selection at `/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c:379-447` and `/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c:491-550`, all at `851661cd21f2aded8ec649da86e01a207dc4b973`. Settings RPC registers `zmk__settings` unsecured at `/tmp/zmk-corne-security-audit/settings-rpc/src/studio/settings_rpc_handler.c:20-40` and mutates idle/sleep settings at `/tmp/zmk-corne-security-audit/settings-rpc/src/studio/settings_rpc_handler.c:207-253`, all at `78f86df9e6c5edaf57bef3ccbd7f360cfdf49291`. Fork dispatch checks the Studio lock only for subsystems marked `SECURED` at `/tmp/zmk-corne-security-audit/zmk/app/src/studio/custom_subsystem.c:90-113` at `4493783ef88ce2e653bf8217c92ee17140df71e3`. Both handlers are enabled in `boards/shields/eyelash_corne/eyelash_corne_left.conf:14-25`; settings changes relay to the enabled right-half event receiver.
**Impact:** A host allowed to reach Studio custom RPC can mutate keyboard connectivity and persistent central activity policy without physical `&studio_unlock`: it can switch or remove host profiles, call `zmk_ble_clear_all_bonds()` through the nominal split-bond method, select output transport, or request activity-timeout relay to the peripheral. BLE Studio still requires its transport's encrypted GATT permissions (`/tmp/zmk-corne-security-audit/zmk/app/src/studio/gatt_rpc_transport.c:88-94` at `4493783ef88ce2e653bf8217c92ee17140df71e3`); USB requires physical host access. This finding does not claim unauthenticated radio reachability.
**Scenario:** Encrypted BLE Studio client or attached USB host lists custom subsystems, calls unsecured `cormoran_ble.forget_split_bond`, and reaches `zmk_ble_clear_all_bonds()`; alternatively it calls unsecured `zmk__settings.set_activity_settings`, whose central setters schedule persistence and attempt a fixed `as` relay event. Central success does not prove delivery or peripheral application: the handler ignores the event-raise result and returns from central setter status alone (`/tmp/zmk-corne-security-audit/settings-rpc/src/studio/settings_rpc_handler.c:211-252`), while the peripheral listener ignores both setter results (`/tmp/zmk-corne-security-audit/settings-rpc/src/events/activity_settings_changed.c:19-37`), all at `78f86df9e6c5edaf57bef3ccbd7f360cfdf49291`. Enabling Studio locking later would not block either subsystem because their metadata remains `UNSECURED`.
**Recommendation:** Mark every state-mutating BLE/settings method `SECURED`; if read-only profile/status methods must remain available while locked, split read and mutation operations into separately classified subsystems or add explicit per-method authorization before mutation. Rename or narrow `forget_split_bond` so its implementation cannot erase unrelated host bonds. Validate activity timeout policy before central mutation and split propagation.
**Regression risk:** Clients that currently manage bonds or activity while locked will require physical unlock; separating read/write methods changes subsystem identifiers or client routing. Narrowing bond deletion can change reset/re-pair recovery flow.
**Verification:** With locking enabled, test every method over USB and encrypted BLE before and after physical unlock. Before unlock, assert all mutation methods return `UNLOCK_REQUIRED` and cause no bond, transport, timeout, settings, or split event change; decide and test read-only policy separately. After unlock, verify intended per-profile and split-only bond deletion using disposable identities, then confirm idle/sleep values on both halves. Hardware tests are required; none were run in this audit.

### ZMK-SEC-011 — Two management paths commit flash on every accepted request

**Severity:** Low
**Class:** Availability / flash-wear hardening
**Evidence:** Runtime-sensor set handlers accept each request and call the persistent setter at `/tmp/zmk-corne-security-audit/runtime-sensor/src/studio/custom_handler.c:101-170`; the setter mutates RAM then immediately calls `settings_save_one()` at `/tmp/zmk-corne-security-audit/runtime-sensor/src/behaviors/behavior_runtime_sensor_rotate.c:120-146`, all at `8b1125ed676c1f5e14145d217984f33d0ebdcef4`. BLE profile naming updates its cache and immediately calls `settings_save_one()` at `/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c:115-151` at `851661cd21f2aded8ec649da86e01a207dc4b973`. Runtime-sensor RPC is compiled for the left and marked secured, but the reviewed build explicitly disables Studio locking at `build.yaml:5-9`; BLE profile naming is part of unsecured `cormoran_ble` from ZMK-SEC-010. By contrast, runtime-input and fork activity persistence coalesce writes through delayed work.
**Impact:** A reachable client can generate one persistent settings write per accepted binding or profile-name request, bypassing the repository's 10-second save-debounce policy for other settings. Actual flash lifetime reduction depends on Zephyr backend wear leveling, hardware endurance, request rate, and whether unchanged writes are elided; no endurance claim was measured.
**Scenario:** Client repeatedly alternates a valid encoder binding or paired-profile name. Each request reaches `settings_save_one()` synchronously instead of rescheduling a single delayed save; repeated traffic therefore amplifies flash operations compared with coalesced settings paths.
**Recommendation:** Validate values first, update a bounded in-memory pending state, and coalesce persistence with `CONFIG_ZMK_SETTINGS_SAVE_DEBOUNCE`; suppress unchanged writes. Preserve a way to flush safely before shutdown if required. Return persistence failure accurately and define whether RAM mutation rolls back or is reported as applied-but-not-persisted.
**Regression risk:** Delayed persistence can lose the newest change on sudden power removal and changes when clients may assume a write is durable. Shared work must be per setting/device or correctly synchronize combined updates.
**Verification:** Host test should issue unchanged, alternating, and burst updates while instrumenting settings-backend calls; assert one write after the debounce window and accurate failure results. Hardware endurance and power-loss behavior require separate testing; static inspection cannot establish them.

### ZMK-SEC-012 — Dormant runtime-input RPC paths contain narrowing and fall-through faults

**Severity:** Low
**Class:** Vulnerability / dormant input-processing availability and integrity
**Evidence:** `cormoran_rip` is compiled and registered unsecured at audited clone `/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c:19-36` at `dbf92f764de8b6ffd60bf5850514302875fe2570`. Its `set_xy_swap_enabled` switch case lacks a `break`, so it falls through to `set_x_invert` at `/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c:149-159`; both setters persist mutations at `/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c:771-793` and `/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c:631-653`. RPC `uint32` IDs, layers, delays, thresholds, and timeouts are passed to `uint8_t`/`uint16_t` APIs without pre-conversion range checks (`/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c:228-268`, `/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c:428-513`, and `/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c:547-625`); divisor `65536` remains nonzero in stored `uint32_t` state but becomes zero at the signed 16-bit division in `/tmp/zmk-corne-security-audit/runtime-input/src/pointing/input_processor_runtime.c:238-259`, and an axis-snap timeout from 1 through 49 reaches division by `(timeout_ms / 50)==0` at `/tmp/zmk-corne-security-audit/runtime-input/src/pointing/input_processor_runtime.c:368-407`. Additional result/state defects occur at the same module SHA: scale handlers report success for zero while the setter retains old components (`/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c:274-338` and `/tmp/zmk-corne-security-audit/runtime-input/src/pointing/input_processor_runtime.c:698-731`); reset omits axis-snap and XY-mapping fields initialized at `/tmp/zmk-corne-security-audit/runtime-input/src/pointing/input_processor_runtime.c:644-660` from its reset block at `/tmp/zmk-corne-security-audit/runtime-input/src/pointing/input_processor_runtime.c:761-816`; setter notifications omit `.id` at `/tmp/zmk-corne-security-audit/runtime-input/src/pointing/input_processor_runtime.c:683-695`, and the listener publishes that zero-initialized ID at `/tmp/zmk-corne-security-audit/runtime-input/src/studio/input_processor_listener.c:53-92`.
**Impact:** If a runtime processor instance is added, crafted RPC values can select an ID modulo 256, silently truncate layer/delay/threshold/timeout values, make one XY-swap request also change X inversion, and set divisors/timeouts that can fault during later pointer movement. Even non-faulting requests can return success without applying zero scale values, leave axis-snap/XY mapping unchanged after reset, and misattribute every setter notification to processor ID 0. Current repository exposure is dormant: module source and RPC handler compile on left, but module DTS defines both processor nodes `/omit-if-no-ref/` at `/tmp/zmk-corne-security-audit/runtime-input/dts/input/processors/runtime-input-processor.dtsi:11-50`, and no local DTS/keymap references either node, so static review found no instantiated mutation target.
**Scenario:** Future keymap references `mouse_runtime_input_processor`; client calls `set_scale_divisor(id=0,value=65536)` and later movement reaches division by zero after the setter stores the unvalidated value. Independently, `set_xy_swap_enabled(id=0,enabled=true)` executes both swap and X-invert handlers and returns the X-invert response tag. A zero scale request returns a success response while retaining the prior value; reset returns success while preserving prior axis-snap/XY settings; a setter on processor 1 emits a notification carrying ID 0.
**Recommendation:** Reject IDs above `UINT8_MAX` before lookup and validate against instantiated count; validate layer against effective keymap layers; validate all 32-bit values against destination widths before casting; require nonzero scaling components representable by the actual arithmetic; reject axis-snap timeouts below the algorithm's 50 ms quantum or change the calculation to avoid a zero divisor; add the missing `break`. Reject zero scale components or return an explicit unchanged result; reset every runtime/persistent field and axis-snap state to its devicetree default; populate notification ID from `zmk_input_processor_runtime_get_id(dev)` and propagate/report failures. Mark mutation RPCs secured before any processor instance is enabled.
**Regression risk:** Strict ranges can reject values accepted by current UI and require defining intended maximum scaling/delay semantics. Fixing fall-through changes response and removes accidental dual mutation.
**Verification:** Add handler tests for `255/256/257`, `65535/65536`, enum out-of-range values, layer bounds, timeout `0/1/49/50`, zero scale components, reset of every mutable field, notification IDs for at least two processors, and each oneof response tag. Instantiate native test processors, drive input after each accepted configuration under divide-by-zero/undefined-behavior instrumentation, and assert XY-swap never changes X inversion. No current-instance or hardware behavior is claimed.

### Static Kconfig-to-Source Exposure Map

| Module and immutable SHA | Local enablement | Kconfig to CMake to source | Reviewed artifact exposure |
|---|---|---|---|
| `zmk-behavior-runtime-sensor-rotate` `8b1125ed676c1f5e14145d217984f33d0ebdcef4` | Left `CONFIG_ZMK_RUNTIME_SENSOR_ROTATE=y` and `CONFIG_ZMK_RUNTIME_SENSOR_ROTATE_STUDIO_RPC=y` (`boards/shields/eyelash_corne/eyelash_corne_left.conf:27-29`) | `/tmp/zmk-corne-security-audit/runtime-sensor/Kconfig:1-9` → `/tmp/zmk-corne-security-audit/runtime-sensor/CMakeLists.txt:5-29` → `/tmp/zmk-corne-security-audit/runtime-sensor/src/behaviors/behavior_runtime_sensor_rotate.c` plus `/tmp/zmk-corne-security-audit/runtime-sensor/src/studio/custom_handler.c` | Left only; keymap instantiates `rsr_vol` and `rsr_trans` (`config/eyelash_corne.keymap:25-37`). `cormoran_rsr` is `SECURED`, but Studio locking is disabled in reviewed Studio-left build. |
| `zmk-module-ble-management` `851661cd21f2aded8ec649da86e01a207dc4b973` | Left base and Studio RPC enabled (`boards/shields/eyelash_corne/eyelash_corne_left.conf:14-17`) | `/tmp/zmk-corne-security-audit/ble-management/Kconfig:1-9` → `/tmp/zmk-corne-security-audit/ble-management/CMakeLists.txt:5-28` → `/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c` | Left only; all eight `cormoran_ble` methods compile and subsystem is `UNSECURED`. |
| `zmk-module-settings-rpc` `78f86df9e6c5edaf57bef3ccbd7f360cfdf49291` | Left base+Studio (`boards/shields/eyelash_corne/eyelash_corne_left.conf:23-25`); right base only (`boards/shields/eyelash_corne/eyelash_corne_right.conf:19-20`) | `/tmp/zmk-corne-security-audit/settings-rpc/Kconfig:1-26` → `/tmp/zmk-corne-security-audit/settings-rpc/CMakeLists.txt:5-30` → `/tmp/zmk-corne-security-audit/settings-rpc/src/events/activity_settings_changed.c` and `/tmp/zmk-corne-security-audit/settings-rpc/src/events/activity_settings_report.c`; left additionally `/tmp/zmk-corne-security-audit/settings-rpc/src/studio/settings_rpc_handler.c` | Left hosts three unsecured Studio methods and central relay send/report listener. Right compiles typed event receivers/report sender without Studio handler. Fixed relay identifiers are `as`, `srq`, and `srp`. |
| `zmk-module-runtime-input-processor` `dbf92f764de8b6ffd60bf5850514302875fe2570` | Left base and Studio RPC enabled (`boards/shields/eyelash_corne/eyelash_corne_left.conf:19-21`) | `/tmp/zmk-corne-security-audit/runtime-input/Kconfig:1-12` → `/tmp/zmk-corne-security-audit/runtime-input/CMakeLists.txt:5-33` → four behavior/input files, `/tmp/zmk-corne-security-audit/runtime-input/src/events/input_processor_state_changed.c`, and `/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c` and `/tmp/zmk-corne-security-audit/runtime-input/src/studio/input_processor_listener.c` | Left source and 19-method unsecured RPC compile. Included DTS processor nodes are omitted because local configuration does not reference them; no current mutation target was established. |
| `zmk-module-battery-history` `307755dd2ad4d320e14de162e8e5ef018f29d929` | Explicitly disabled on both halves (`boards/shields/eyelash_corne/eyelash_corne_left.conf:34-36`; `boards/shields/eyelash_corne/eyelash_corne_right.conf:16-18`) | `/tmp/zmk-corne-security-audit/battery-history/Kconfig:2-102`; entire source addition is guarded by `if(CONFIG_ZMK_BATTERY_HISTORY)` in `/tmp/zmk-corne-security-audit/battery-history/CMakeLists.txt:10-34` | Fetched but disabled. No `battery_history.c`, request behavior, Studio handler, periodic work, settings writes, or battery-history relay is treated as current runtime exposure. |

This map is a static composition proof from local `.conf` through module Kconfig/CMake and source/DTS. Effective generated `.config`, preprocessed DTS, object list, linker map, and firmware image were not produced because the checked-in test prerequisite `west` is absent. Accordingly, “compile” above means selected by the reviewed configuration/CMake path, not a claim that a fresh toolchain build completed.

### Enabled RPC Handler Inventory

| Subsystem / security | Methods and request fields | Validation, mutation, persistence, and result notes |
|---|---|---|
| `cormoran_rsr` / `SECURED` | `set_layer_cw_binding(sensor_index:uint32, layer:uint32, binding{behavior_id:uint32,param1:uint32,param2:uint32,tap_ms:uint32})`; `set_layer_ccw_binding(sensor_index:uint32, layer:uint32, binding{behavior_id:uint32,param1:uint32,param2:uint32,tap_ms:uint32})`; `get_all_layer_bindings(sensor_index:uint32)`; `get_sensors()` | Layer is checked before mutation, but `sensor_index` and 32-bit `behavior_id` narrow to 8/16 bits, so out-of-range values alias rather than reject (`/tmp/zmk-corne-security-audit/runtime-sensor/src/studio/custom_handler.c:101-170`, `/tmp/zmk-corne-security-audit/runtime-sensor/src/behaviors/behavior_runtime_sensor_rotate.c:173-179`, and `/tmp/zmk-corne-security-audit/zmk/app/include/zmk/behavior.h:14-18`). Setter rechecks narrowed sensor/layer, writes RAM, then immediately persists; persistence failure returns error after RAM changed (`/tmp/zmk-corne-security-audit/runtime-sensor/src/behaviors/behavior_runtime_sensor_rotate.c:120-146`). Bounded nanopb arrays are 16 layers/10 sensors and sensor names copy into zero-initialized 16-byte fields (`/tmp/zmk-corne-security-audit/runtime-sensor/proto/cormoran/rsr/custom.options:4-7` and `/tmp/zmk-corne-security-audit/runtime-sensor/src/studio/custom_handler.c:223-242`). Module evidence is at `8b1125ed676c1f5e14145d217984f33d0ebdcef4`; fork typedef evidence is at `4493783ef88ce2e653bf8217c92ee17140df71e3`. |
| `cormoran_ble` / `UNSECURED` | `get_profiles()`; `set_profile_name(index:uint32,name:string)`; `switch_profile(index:uint32)`; `unpair_profile(index:uint32)`; `get_split_info()`; `forget_split_bond()`; `set_output_priority(priority:enum)`; `get_output_priority()` | Profile indexes are checked against count; name is nanopb-bounded to 32 bytes and copies are terminated; output enum uses an exhaustive switch (`/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c:344-401` and `/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c:517-550`). Name cache changes before immediate persistence, so a save failure leaves RAM changed (`/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c:139-151`). Unpair clears cache before profile operations, does not roll back on later failure, and never deletes the persisted name (`/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c:407-447`). On central builds `get_split_info()` hard-codes `peripheral_connected=false` and `central_bonded=false`, so it can return false state rather than measured state (`/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c:453-485`). Forget reports success after void all-bond clear (`/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c:491-511`); unknown internal transport is reported as BLE (`/tmp/zmk-corne-security-audit/ble-management/src/studio/ble_management_handler.c:555-586`). Mutations bypass lock: ZMK-SEC-010. All module evidence is at `851661cd21f2aded8ec649da86e01a207dc4b973`. |
| `zmk__settings` / `UNSECURED` | `get_activity_settings()`; `set_activity_settings(settings{idle_ms:uint32,sleep_ms:uint32,source:uint32})`; `get_all_activity_settings()` | Source supplied by setter is ignored; relay source is fixed to self and overwritten from transport on receive. Idle applies before sleep and no rollback occurs if sleep fails; central response is based only on central setter booleans and ignores relay-event result (`/tmp/zmk-corne-security-audit/settings-rpc/src/studio/settings_rpc_handler.c:211-252`). Peripheral listener calls both setters but ignores their results, so central success does not prove peripheral application (`/tmp/zmk-corne-security-audit/settings-rpc/src/events/activity_settings_changed.c:19-37`). Notification helper is declared `void`, attempts `return -ENOENT`, ignores notification raise result, and callers cannot observe notification failure (`/tmp/zmk-corne-security-audit/settings-rpc/src/studio/settings_rpc_handler.c:152-181`). Get-all still reports `request_sent=true` without checking local notification or request-event delivery (`/tmp/zmk-corne-security-audit/settings-rpc/src/studio/settings_rpc_handler.c:260-289`). Persistence is debounced by fork activity code. Mutations bypass lock: ZMK-SEC-010. Module evidence is at `78f86df9e6c5edaf57bef3ccbd7f360cfdf49291`. |
| `cormoran_rip` / `UNSECURED`, no current instances | `list_input_processors()`; `get_input_processor(id)`; `set_scale_multiplier(id,value)`; `set_scale_divisor(id,value)`; `set_rotation(id,value)`; `reset_input_processor(id)`; `set_temp_layer_enabled(id,enabled)`; `set_temp_layer_layer(id,layer)`; `set_temp_layer_activation_delay(id,activation_delay_ms)`; `set_temp_layer_deactivation_delay(id,deactivation_delay_ms)`; `set_active_layers(id,layers)`; `set_axis_snap_mode(id,mode)`; `set_axis_snap_threshold(id,threshold)`; `set_axis_snap_timeout(id,timeout_ms)`; `set_xy_to_scroll_enabled(id,enabled)`; `set_xy_swap_enabled(id,enabled)`; `set_x_invert(id,invert)`; `set_y_invert(id,invert)`; `get_layer_info()` | Every target lookup accepts `uint32` but calls a `uint8_t` ID API; layer/delay/threshold/timeout values also narrow before validation, and axis mode validates only after narrowing (`/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c:228-268`, `/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c:428-625`, and `/tmp/zmk-corne-security-audit/runtime-input/include/zmk/pointing/input_processor_runtime.h:104-110` and `/tmp/zmk-corne-security-audit/runtime-input/include/zmk/pointing/input_processor_runtime.h:157-241`). Scale handlers report success for zero values while the setter retains old components (`/tmp/zmk-corne-security-audit/runtime-input/src/studio/custom_handler.c:274-338` and `/tmp/zmk-corne-security-audit/runtime-input/src/pointing/input_processor_runtime.c:698-731`). Reset omits axis-snap and XY mapping despite initializing them (`/tmp/zmk-corne-security-audit/runtime-input/src/pointing/input_processor_runtime.c:644-660` and `/tmp/zmk-corne-security-audit/runtime-input/src/pointing/input_processor_runtime.c:761-816`). Setter notifications omit processor ID and the listener publishes zero (`/tmp/zmk-corne-security-audit/runtime-input/src/pointing/input_processor_runtime.c:683-695` and `/tmp/zmk-corne-security-audit/runtime-input/src/studio/input_processor_listener.c:53-92`). Writes use 10-second delayed persistence. Missing switch `break`, division hazards, and current non-instantiation are captured by ZMK-SEC-012. Layer-name encoder points to static keymap strings; notification payload encodes synchronously before stack data expires. All module evidence is at `dbf92f764de8b6ffd60bf5850514302875fe2570`. |

Battery-history has two fetched RPC methods, `get_history()` and `clear_history()`, registered `UNSECURED` in `/tmp/zmk-corne-security-audit/battery-history/src/battery_history/battery_history_handler.c:28-54` at `307755dd2ad4d320e14de162e8e5ef018f29d929`, but both the base feature and Studio RPC are explicitly disabled. Disabled-source review found that persisted `head`/`count` are loaded without checking them against `MAX_ENTRIES` (`/tmp/zmk-corne-security-audit/battery-history/src/battery_history/battery_history.c:340-369`) and configurations allow up to 500 entries while notification indexes/counts are `uint8_t` (`/tmp/zmk-corne-security-audit/battery-history/Kconfig:18-25` and `/tmp/zmk-corne-security-audit/battery-history/src/battery_history/battery_history.c:479-505`). These are fetched-disabled hardening concerns, not current-artifact findings.

### Relay, Copy, and Callback Review

- Settings central mutation uses compile-time identifier `as`; request/report use `srq`/`srp`. Fork macros build-assert name/payload capacity, copy `sizeof(struct event_type)`, require exact data size before reconstructing a typed event, compare only registered fixed identifiers, and overwrite typed `source` from transport (`/tmp/zmk-corne-security-audit/zmk/app/include/zmk/event_manager.h:94-144` and `/tmp/zmk-corne-security-audit/zmk/app/include/zmk/event_manager.h:146-214` at `4493783ef88ce2e653bf8217c92ee17140df71e3`). RPC `settings.source` cannot choose an event type, data length, or peripheral source ID.
- Settings path attempts: custom call → central setters → `zmk_activity_settings_changed` with self source → fixed typed split payload → encrypted split transport → exact-size peripheral event reconstruction with transport-derived source → peripheral activity setter calls. Central success reflects only central setter results and ignores relay-event result (`/tmp/zmk-corne-security-audit/settings-rpc/src/studio/settings_rpc_handler.c:211-252`); peripheral setter results are ignored (`/tmp/zmk-corne-security-audit/settings-rpc/src/events/activity_settings_changed.c:19-37`). Get-all reverses through typed report event and central custom notification, but the helper ignores notification-event result (`/tmp/zmk-corne-security-audit/settings-rpc/src/studio/settings_rpc_handler.c:152-181`), so request/response status does not prove cross-half delivery or application. The relay transport memory-safety exception remains ZMK-SEC-006. All settings evidence is at `78f86df9e6c5edaf57bef3ccbd7f360cfdf49291`.
- Runtime-input state notifications contain static devicetree names and by-value configuration. Module copies names into terminated fixed arrays. Custom notification callbacks point to stack protobuf objects, but fork contract explicitly encodes synchronously before `raise_zmk_studio_custom_notification()` returns (`/tmp/zmk-corne-security-audit/zmk/app/include/zmk/studio/custom.h:14-20` at the fork SHA). Response objects use the fork's per-subsystem static response-buffer macro and serialize requests, as already recorded in the fork audit.
- Required dangerous-primitive scan matched 45 lines across the five modules. Every match was manually dispositioned: nanopb decode/encode uses generated bounded messages; profile/sensor/processor strings use fixed bounds and zero termination or zero initialization; relay copies use compile-time/event-size contracts; runtime-input and activity writes debounce; immediate runtime-sensor/profile-name writes produce ZMK-SEC-011; disabled battery `atoi`/settings paths are recorded separately. Scanner absence was not treated as proof of safety.

### Module Test Evidence and Limitations

Checked-in firmware-test command for each enabled module is `python -m unittest` (`/tmp/zmk-corne-security-audit/runtime-sensor/README.md:265-285`, `/tmp/zmk-corne-security-audit/ble-management/README.md:71-85`, `/tmp/zmk-corne-security-audit/settings-rpc/README.md:169-189`, and `/tmp/zmk-corne-security-audit/runtime-input/README.md:464-486`). It was run without source changes in each exact clone:

| Clone / SHA | Command | Result |
|---|---|---|
| `runtime-sensor` / `8b1125ed676c1f5e14145d217984f33d0ebdcef4` | `python -m unittest -v` | Exit 5; `setUpClass` raised `FileNotFoundError: [Errno 2] No such file or directory: 'west'`; 0 tests ran. |
| `ble-management` / `851661cd21f2aded8ec649da86e01a207dc4b973` | `python -m unittest -v` | Same missing `west`; exit 5; 0 tests ran. |
| `settings-rpc` / `78f86df9e6c5edaf57bef3ccbd7f360cfdf49291` | `python -m unittest -v` | Same missing `west`; exit 5; 0 tests ran. |
| `runtime-input` / `dbf92f764de8b6ffd60bf5850514302875fe2570` | `python -m unittest -v` | Same missing `west`; exit 5; 0 tests ran. |

Battery-history tests were not run because feature is explicitly disabled in both reviewed halves and Step 5 requires enabled modules. No module test, build, generated configuration, static analyzer, sanitizer, flash, BLE/USB connection, split packet exchange, bond mutation, persistence endurance measurement, or hardware behavior passed in this task. Findings derive from immutable static source/configuration review. Test files mainly assert build/config presence and a generic Studio test; no checked-in focused cases cover unauthorized mutation, numeric boundaries, fall-through, zero-scale result accuracy, complete reset state, notification processor IDs, split-info state accuracy, partial failure, settings-write frequency, relay delivery/application results, or relay source integrity.

### Module Positive Security Observations

- All five clone HEADs exactly matched Task 1 SHAs and were clean before and after inspection/testing.
- Runtime-sensor alone classifies its custom subsystem `SECURED`; local layer checks and underlying narrowed sensor checks prevent direct array out-of-bounds through its RPC handlers.
- BLE profile indexes and output enum are validated before calling ZMK APIs; nanopb options bound request/profile/error strings, and copies preserve termination.
- Settings RPC does not trust client-supplied source. Typed relay identifiers and data sizes are compile-time fixed, receive sizes are exact, and transport derives peripheral source.
- Runtime-input settings require exact persisted struct size and coalesce writes with `CONFIG_ZMK_SETTINGS_SAVE_DEBOUNCE`; axis-snap setter rejects modes above Y after conversion. Current configuration instantiates no runtime-input processor, materially reducing current reachability of ZMK-SEC-012.
- Battery history is explicitly disabled on both halves despite being fetched and included in overlays. Its periodic work, flash history, global request behavior, unsecured RPC, and split events therefore are not reported as compiled exposure.
- Nanopb request payload remains bounded by the fork contract, response buffers are static rather than stack-backed, and custom notification callback lifetime matches the fork's synchronous encoding contract.

### Module Audit Record

**Scope:** Five DYA module clones at the immutable SHAs above; local Kconfig/CMake/DTS composition; every module C/header/protobuf handler; dangerous primitives; enabled module test entrypoints; custom RPC dispatcher and typed split relay contract from Task 3. No DYA web UI/client code was audited.

**Files changed:** `security_best_practices_report.md` only. No firmware, module source, configuration, workflow, dependency, clone, build output, or hardware state was changed.

**Remaining concerns:** Effective object/link reachability awaits a working west/ZMK toolchain. ZMK-SEC-010 needs per-transport lock tests and disposable bond/split fixtures. ZMK-SEC-011 needs settings-backend instrumentation and endurance/power-loss analysis. ZMK-SEC-012 needs native instantiated processors with numeric-boundary, sanitizer, full-reset, and notification-ID coverage before any local reference is added. Static review cannot establish pairing authorization, flash endurance, event concurrency, radio behavior, reset behavior, or hardware impact.
