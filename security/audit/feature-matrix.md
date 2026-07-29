# Official-ZMK Migration Feature Matrix

## Decision basis

This matrix recommends a **safer target architecture**, not firmware already
verified safe. Current `main` resolves to repository base
`61837a020e6882f4ca4ff37445cdcbbbe0b223ca`. Task 6 built both halves only with
the pinned Cormoran/DYA graph. It did **not** build, flash, or exercise an
official-ZMK migration target.

Official support was rechecked on 2026-07-29 against
[`zmkfirmware/zmk@faaf39d9f59cd2a27eca3739cdd9eb197654299b`](https://github.com/zmkfirmware/zmk/commit/faaf39d9f59cd2a27eca3739cdd9eb197654299b),
authored 2026-07-28. Documentation and source links below were inspected at
that revision or on the live official documentation site on 2026-07-29:

- [ZMK Studio capabilities and build configuration](https://zmk.dev/docs/features/studio),
  [locking configuration](https://zmk.dev/docs/config/studio), and
  [physical unlock behavior](https://zmk.dev/docs/keymaps/behaviors/studio-unlock)
- [Keymaps and layers](https://zmk.dev/docs/keymaps),
  [macros](https://zmk.dev/docs/keymaps/behaviors/macros), and
  [combos](https://zmk.dev/docs/keymaps/combos)
- [Sensor rotation](https://zmk.dev/docs/keymaps/behaviors/sensor-rotate),
  [pointing](https://zmk.dev/docs/features/pointing), and
  [input processors](https://zmk.dev/docs/keymaps/input-processors)
- [Bluetooth profile behavior](https://zmk.dev/docs/keymaps/behaviors/bluetooth),
  [output selection](https://zmk.dev/docs/keymaps/behaviors/outputs), and
  [power configuration](https://zmk.dev/docs/config/power)
- [Split keyboard event model](https://zmk.dev/docs/features/split-keyboards),
  [battery configuration](https://zmk.dev/docs/config/battery), and
  [Studio RPC protocol](https://zmk.dev/docs/development/studio-rpc-protocol)
- Pinned official source:
  [`studio/Kconfig`](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/app/src/studio/Kconfig),
  [`studio/rpc.h`](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/app/include/zmk/studio/rpc.h),
  and
  [`studio/gatt_rpc_transport.c`](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/app/src/studio/gatt_rpc_transport.c)

`Decision` has exactly one of `official`, `retain-module`, `defer`, `remove`,
or `core-fork-exception`. “Official” means preserve the required behavior using
official ZMK, not preserve every current DYA runtime-management UI. “Remove”
means omit the current custom implementation from the migration target.
“Defer” means no deployment dependency until a concrete requirement and
security contract are approved.

## Capability decisions

| Capability | Enabled now | Hardware/use evidence | Official ZMK | External module possible | Core fork required | Decision | Validation |
|---|---|---|---|---|---|---|---|
| Keymap editing | Left and both Studio-left builds have Studio; DYA calls official keymap RPCs. | Four named layers and 42-key bindings exist in `config/eyelash_corne.keymap`; no hardware Studio session ran. | Runtime key assignment over USB/BLE is supported by official Studio. | Not needed. | No. | official | Build official central with locking; before unlock reject mutation, after physical unlock edit/save/discard/restore one key, then verify HID and persistence. |
| Layer management | DYA calls official get/add/move/remove/property RPCs. | Four layers use `&mo`/`&lt`; no runtime layer mutation was hardware-tested. | Official Studio supports layer naming/reordering and enabling reserved layers; devicetree still bounds maximum layers. | Not needed. | No. | official | Add reserved capacity explicitly; exercise rename/add/move/remove/save/restore without removing default layer; verify layer order and bindings after reboot. |
| Macros and combos | Static combo `softoff` is enabled; no local macro node or current-firmware runtime macro/combo subsystem was established. | Three-position soft-off combo exists at `config/eyelash_corne.keymap:40-47`; Task 5 client only probes optional DYA runtime macro/combo subsystems. | Static macros and combos are official. Official Studio lists runtime combo and advanced macro property editing as planned, not current support. | Possible, but no current requirement justifies one. | No for static behavior. | official | Compile official static combo/macro fixtures; verify combo timing, cancel/hold behavior, and soft-off on both halves. Do not claim Studio runtime macro/combo editing. |
| Encoder rotation | Runtime-sensor module is enabled on left and instantiates `rsr_vol`/`rsr_trans`. | One encoder exists; current successful build warns that two sensor bindings target one sensor and drops `rsr_trans`. No encoder hardware test ran. | Official `zmk,behavior-sensor-rotate` and `zmk,behavior-sensor-rotate-var` preserve clockwise/counter-clockwise behavior. | Not needed for fixed volume behavior. | No. | official | Replace runtime behavior with one official sensor binding per layer; compile warning-free; verify both directions on every layer and split source behavior. |
| Runtime encoder binding editing | Current runtime-sensor Studio RPC is compiled and DYA has get/set calls. | Configuration proves exposure, but no recorded user session or requirement proves runtime rebinding is necessary. | Official Studio marks assigning behaviors to encoders low priority; no current official UI contract preserves DYA runtime edits. | Possible only after a module/message/client port and focused review. | Current DYA path uses the Cormoran custom dispatcher; no target fork is approved. | defer | First record concrete runtime-rebinding workflow. Then prototype against pinned official RPC interfaces; require secured mutations, coalesced persistence, lock/relock tests, encoder regression, and client review before changing decision. |
| Pointing and smooth scrolling | Pointing is enabled on right/left; smooth scrolling resolves enabled on left and disabled on right. | Keymap uses `&mmv` and `&mkp`; no physical pointing sensor is referenced and no HID capture ran. | Official mouse emulation, pointing, input listeners, split input, and smooth-scrolling Kconfig cover current behavior. | External hardware drivers/processors remain possible if later hardware needs them. | No. | official | Build both official halves; verify descriptor changes after re-pair, buttons/movement on every layer, scroll resolution, and no right-half Kconfig mismatch that affects intended HID. |
| Runtime input processors | Custom runtime-input module/RPC compiles on left; effective DTS has zero processor instances. | Task 4 and Task 6 confirm no referenced instance; warning inventory classifies its symbols as dead compiled code. | Official static scaler, transform, mapper, behavior, and temporary-layer processors exist. Runtime RPC mutation is not an official capability. | Yes, through the documented input-processor driver API if a future device needs one. | No. | remove | Remove current module/RPC and confirm no DTS reference or symbol. If later needed, add an official static processor fixture first and validate movement boundaries under native tests and hardware. |
| BLE profile management | Custom BLE-management RPC compiles on left; keymap also uses `BT_SEL`, `BT_CLR`, and `BT_CLR_ALL`. | Physical profile keys are present; DYA calls profile switch/unpair/name methods. No bond mutation was run. | Official `&bt` supports select, next/previous, disconnect, selected-profile clear, and clear-all. Profile naming via Studio is not official. | Current module exists, but ZMK-SEC-010/011 block retention as-is. | No for required profile operations. | official | Remove custom BLE RPC; with disposable hosts test all profile keys, selection persistence, per-profile clear, clear-all confirmation procedure, and split re-pair recovery. |
| Endpoint priority | Custom BLE-management RPC exposes output priority; keymap uses `&out OUT_USB` and `&out OUT_BLE`. | Physical endpoint bindings exist; no runtime RPC or host-routing test ran. | Official `&out` selects and persists preferred USB/BLE output. | Not needed. | No. | official | Test USB-only, BLE-only, both-connected, USB-power-only, reboot persistence, and Studio transport matching selected endpoint. |
| Idle/deep-sleep settings | Both normal halves enable sleep with 3,600,000 ms deep-sleep timeout; custom settings RPC mutates activity policy. | Static config exists; no sleep-current, wake, or runtime-setting hardware measurement ran. | Official `CONFIG_ZMK_IDLE_TIMEOUT`, `CONFIG_ZMK_SLEEP`, and `CONFIG_ZMK_IDLE_SLEEP_TIMEOUT` cover fixed policy. | Current settings RPC exists, but ZMK-SEC-010 blocks it as-is. | No for fixed policy. | official | Remove runtime settings RPC; build both halves with explicit identical policy; measure idle/deep-sleep transition, wake sources, reconnect, and persistence expectations. |
| Split event relay | Custom generic relay is enabled on both normal halves and carries DYA activity-setting events. | Official key/sensor traffic is required; no concrete requirement remains for arbitrary activity relay once runtime settings RPC is removed. | Official split transport already carries key-position, sensor, input, battery, and behavior-locality traffic; it has no equivalent arbitrary named-event API. | Feature-specific module/transport work is possible, but unnecessary for selected target. | Current generic relay requires Cormoran core changes; target does not. | remove | Remove generic relay/settings receiver; build both official halves; test every key, encoder direction, pointing input, battery proxy if enabled, soft-off, reset locality, disconnect, and re-pair. |
| Battery history | Module is fetched, but feature and Studio RPC are disabled in every reviewed artifact. | No runtime history, storage, or UI use evidence. Ordinary current battery reporting is separate. | Official battery reporting and split battery proxy exist; persistent history/clear RPC does not. | Current disabled module exists. | No. | remove | Drop module from manifest; confirm effective configs/source graph contain no history symbols; verify ordinary live battery reporting on both halves. |
| Studio USB transport | Enabled only in Studio-left builds through `studio-rpc-usb-uart`; current declared build disables locking, while Task 6 also built a locked candidate. | USB CDC ACM virtual UART compiled; UART0/UART1 nodes remain disabled. No USB request was sent. | Official Studio supports USB serial using the same snippet. | Not needed. | No. | official | Dedicated central-only artifact; require locking, physical `&studio_unlock`, rejection before unlock, save after unlock, disconnect/idle relock, hostile framing bounds, and manual checklist before flash. |
| Studio BLE transport | Enabled by default on normal left and both Studio-left builds. | Effective config proves BLE transport; no encrypted BLE Studio session ran. | Official Studio supports BLE on documented clients. Inspected official revision still contains the zero-progress RX-ring loop pattern described by ZMK-SEC-007, so migration alone does not close it. | Not needed for transport, but an upstream fix or narrowly reviewed patch is required before deployment. | No approved target fork; prefer a pinned upstream fix. | official | Block deployment until RX capacity handling is fixed and tested at free, free+1, and oversized writes; then test encrypted access, lock/unlock, disconnect/idle relock, malformed framing, and later valid RPC recovery. |
| DYA custom RPC client/UI | Cormoran custom dispatcher and four local custom module namespaces compile on left; DYA client supports many more optional namespaces not established in effective firmware. | Static client/module evidence only; no browser/device exchange passed. Client findings ZMK-SEC-013 through ZMK-SEC-019 remain open. | Official protocol provides fixed protobuf subsystems and handler registration, not the current arbitrary DYA subsystem discovery/payload contract. | A port may combine narrowly scoped modules with reviewed message/client changes; feasibility and compatibility are not validated. | Current implementation does; no concrete requirement approves retaining it. | defer | Use official Studio client for baseline. Consider a client fork only for an approved retained custom RPC; close client findings, pin dependencies/deployment, and run adversarial browser/transport plus hardware authorization tests. |

No row has decision `core-fork-exception`. Current evidence supplies no concrete user
requirement that both lacks an official/module interface and justifies retaining
the Cormoran core fork. Any future exception must name that requirement, cite the
missing interface at a newly inspected official revision, bound the fork delta,
and pass source, build, transport, and hardware review.

## Minimum trusted architecture

Target: official ZMK at a reviewed immutable commit, no Cormoran core fork, and
no DYA external firmware module in the baseline. Use official Studio client,
official static sensor rotation/input processing, official `&bt`/`&out`, fixed
power policy, and official split traffic. Build a normal right artifact and a
dedicated central-left Studio artifact with
`CONFIG_ZMK_STUDIO_LOCKING=y`, lock-on-disconnect, idle relock, and physical
`&studio_unlock`. Keep management features out of the right and any separate
non-Studio artifact.

This is smaller and easier to review, but not yet verified safe. In particular,
official revision `faaf39d9...` still needs the ZMK-SEC-007 RX-ring remediation
or a later pinned upstream fix. Tasks 2–6 findings remain applicable until their
specific remediation and validation gates pass.

## Migration stages

1. **Pin and lock current build without feature change.** Pin every west project,
   workflow, action, toolchain, and generated input; retain current artifact
   hashes as rollback evidence. Do not flash.
2. **Establish official-ZMK baseline for both halves.** Select and pin a reviewed
   official commit, remove Cormoran core/custom modules, port official
   keymap/sensor/input behavior, and build right plus central-left from clean
   workspaces. These builds do not yet exist.
3. **Test official Studio keymap functionality with locking.** Use a dedicated
   central-left Studio artifact with locking, physical unlock, disconnect/idle
   relock, and separate USB/encrypted-BLE validation. Do not deploy BLE Studio
   until ZMK-SEC-007 is fixed and regression-tested.
4. **Add one required external module at a time.** Start from the passing
   official baseline. Require a concrete capability gap, immutable pin, narrow
   source audit, secured mutations, build/test evidence, and hardware
   regression before adding the next module.
5. **Consider client fork only for retained custom RPC UI.** Default to official
   Studio. Fork client/messages only after a custom RPC capability is approved,
   and close ZMK-SEC-013 through ZMK-SEC-019 before deployment.
6. **Keep Cormoran core fork only for approved `core-fork-exception` rows.**
   There are none. A future exception needs both a cited missing official/module
   interface and a concrete user requirement, plus a bounded delta and its own
   review/validation record.

Advancing a stage requires its validation evidence; successful compilation is
not runtime authorization, memory-safety, radio, split, or hardware proof.
