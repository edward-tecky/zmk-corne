# Official-ZMK Migration Feature Matrix

## Decision basis

This matrix recommends a **safer target architecture**, not firmware already
verified safe. Final audit resolves to authorized repository base
`8bbdaf1ae0cd2118cae0ecb4172e6286f13892a1`. Task 6 built both halves only with
the pinned Cormoran/DYA graph. It did **not** build, flash, or exercise an
official-ZMK migration target.

Official support was rechecked on 2026-07-29 against
[`zmkfirmware/zmk@faaf39d9f59cd2a27eca3739cdd9eb197654299b`](https://github.com/zmkfirmware/zmk/commit/faaf39d9f59cd2a27eca3739cdd9eb197654299b),
authored 2026-07-28. Decision evidence uses documentation and source pinned to
that commit, not mutable rendered documentation:

- [ZMK Studio capabilities and build configuration](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/features/studio.md),
  [locking configuration](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/config/studio.md), and
  [physical unlock behavior](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/behaviors/studio-unlock.md)
- [Keymaps and layers](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/index.mdx),
  [macros](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/behaviors/macros.md), and
  [combos](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/combos.md)
- [Sensor rotation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/behaviors/sensor-rotate.md),
  [pointing](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/features/pointing.md), and
  [input processors](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/input-processors/index.md)
- [Bluetooth profile behavior](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/behaviors/bluetooth.md),
  [output selection](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/behaviors/outputs.md), and
  [power configuration](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/config/power.md)
- [Split keyboard event model](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/features/split-keyboards.md),
  [battery configuration](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/config/battery.md), and
  [Studio RPC protocol](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/development/studio-rpc-protocol.md)
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
| Keymap editing | Left and both Studio-left builds have Studio; DYA calls official keymap RPCs. | Four named layers and 42-key bindings exist in `config/eyelash_corne.keymap`; no hardware Studio session ran. | [Pinned Studio documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/features/studio.md) supports runtime key assignment over USB/BLE. | Not needed. | No. | official | Build official central with locking; before unlock reject mutation, after physical unlock edit/save/discard/restore one key, then verify HID and persistence. |
| Layer management | DYA calls official get/add/move/remove/property RPCs. | Four layers use `&mo`/`&lt`; no runtime layer mutation was hardware-tested. | [Pinned keymap/Studio documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/features/studio.md) supports layer naming/reordering and enabling reserved layers; devicetree still bounds maximum layers. | Not needed. | No. | official | Add reserved capacity explicitly; exercise rename/add/move/remove/save/restore without removing default layer; verify layer order and bindings after reboot. |
| Macros and combos | Static combo `softoff` is enabled; no local macro node or current-firmware runtime macro/combo subsystem was established. | Three-position soft-off combo exists at `config/eyelash_corne.keymap:40-47`; Task 5 client only probes optional DYA runtime macro/combo subsystems. | Pinned official [macro](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/behaviors/macros.md) and [combo](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/combos.md) documentation supports static configuration; pinned Studio documentation lists runtime combo and advanced macro property editing as planned. | Possible, but no current requirement justifies one. | No for static behavior. | official | Compile official static combo/macro fixtures; verify combo timing, cancel/hold behavior, and soft-off on both halves. Do not claim Studio runtime macro/combo editing. |
| Encoder rotation | Runtime-sensor module is enabled on left and instantiates `rsr_vol`/`rsr_trans`. | One encoder exists; current successful build warns that two sensor bindings target one sensor and drops `rsr_trans`. No encoder hardware test ran. | [Pinned sensor-rotation documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/behaviors/sensor-rotate.md) supports `zmk,behavior-sensor-rotate` and `zmk,behavior-sensor-rotate-var`. | Not needed for fixed volume behavior. | No. | official | Replace runtime behavior with one official sensor binding per layer; compile warning-free; verify both directions on every layer and split source behavior. |
| Runtime encoder binding editing | Current runtime-sensor Studio RPC is compiled and DYA has get/set calls. | Configuration proves exposure, but no recorded user session or requirement proves runtime rebinding is necessary. | [Pinned Studio capability documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/features/studio.md) marks encoder assignment low priority; no current official UI contract preserves DYA runtime edits. | Possible only after a module/message/client port and focused review. | Current DYA path uses the Cormoran custom dispatcher; no target fork is approved. | defer | First record concrete runtime-rebinding workflow. Then prototype against pinned official RPC interfaces; require secured mutations, coalesced persistence, lock/relock tests, encoder regression, and client review before changing decision. |
| Pointing and smooth scrolling | Pointing is enabled on right/left; smooth scrolling resolves enabled on left and disabled on right. | Keymap uses `&mmv` and `&mkp`; no physical pointing sensor is referenced and no HID capture ran. | [Pinned pointing documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/features/pointing.md) covers mouse emulation, pointing, input listeners, split input, and smooth scrolling. | External hardware drivers/processors remain possible if later hardware needs them. | No. | official | Build both official halves; verify descriptor changes after re-pair, buttons/movement on every layer, scroll resolution, and no right-half Kconfig mismatch that affects intended HID. |
| Runtime input processors | Custom runtime-input module/RPC compiles on left; effective DTS has zero processor instances. | Task 4 and Task 6 confirm no referenced instance; warning inventory classifies its symbols as dead compiled code. | [Pinned input-processor documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/input-processors/index.md) provides static scaler, transform, mapper, behavior, and temporary-layer processors; runtime RPC mutation is not official. | Yes, through the documented input-processor driver API if a future device needs one. | No. | remove | Remove current module/RPC and confirm no DTS reference or symbol. If later needed, add an official static processor fixture first and validate movement boundaries under native tests and hardware. |
| Physical BLE profile operations | Custom BLE-management RPC compiles on left; keymap uses `BT_SEL`, `BT_CLR`, and `BT_CLR_ALL`. | Physical profile keys are present; no bond mutation was run. | [Pinned Bluetooth behavior documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/behaviors/bluetooth.md) supports select, next/previous, disconnect, selected-profile clear, and clear-all. | Not needed. | No. | official | Remove custom BLE RPC; with disposable hosts test all profile keys, selection persistence, per-profile clear, clear-all procedure, and split re-pair recovery. |
| Runtime BLE profile naming | BLE-management Studio RPC is compiled on left; DYA calls `setProfileName`. | Static call-path evidence exists, but no recorded naming session or concrete user requirement. | Pinned [Bluetooth behavior](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/behaviors/bluetooth.md) and [Studio](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/features/studio.md) documentation exposes no runtime profile-name operation. | Possible after a secured module/message/client port; current module is blocked by ZMK-SEC-004 and ZMK-SEC-016. | Current DYA path uses custom dispatcher; no target fork is approved. | defer | First record a concrete naming workflow. If approved, require locked mutation, unchanged-write suppression, debounced persistence, failure semantics, client tests, and disposable-host hardware validation. |
| Endpoint priority | Custom BLE-management RPC exposes output priority; keymap uses `&out OUT_USB` and `&out OUT_BLE`. | Physical endpoint bindings exist; no runtime RPC or host-routing test ran. | [Pinned output-selection documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/keymaps/behaviors/outputs.md) supports persisted preferred USB/BLE output. | Not needed. | No. | official | Test USB-only, BLE-only, both-connected, USB-power-only, reboot persistence, and Studio transport matching selected endpoint. |
| Fixed idle/deep-sleep policy | Both normal halves enable sleep with 3,600,000 ms deep-sleep timeout. | Static config exists; no sleep-current or wake hardware measurement ran. | [Pinned power documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/config/power.md) provides `CONFIG_ZMK_IDLE_TIMEOUT`, `CONFIG_ZMK_SLEEP`, and `CONFIG_ZMK_IDLE_SLEEP_TIMEOUT`. | Not needed. | No. | official | Build both halves with explicit identical policy; measure idle/deep-sleep transition, wake sources, reconnect, and persistence expectations. |
| Runtime idle/deep-sleep editing | Settings Studio RPC is compiled on left and DYA calls `setActivitySettings`; split relay applies changes to peripheral. | Static call-path evidence exists, but no recorded runtime-setting session or concrete user requirement. | [Pinned power documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/config/power.md) exposes build-time policy, not a Studio runtime mutation contract. | Possible after a secured module/message/client port; current path is blocked by ZMK-SEC-004 and ZMK-SEC-008 relay limitations. | Current DYA path uses custom dispatcher/core relay; no target fork is approved. | defer | First record a concrete runtime-policy workflow. If approved, require bounded values, locked mutation, atomic two-half result semantics, debounced persistence, disconnect/reboot behavior, and measured hardware validation. |
| Split event relay | Custom generic relay is enabled on both normal halves and carries DYA activity-setting events. | Official key/sensor traffic is required; no concrete requirement remains for arbitrary activity relay while runtime power editing is deferred. | [Pinned split documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/features/split-keyboards.md) covers key-position, sensor, input, battery, and behavior-locality traffic but no arbitrary named-event API. | Feature-specific module/transport work is possible, but unnecessary for selected target. | Current generic relay requires Cormoran core changes; target does not. | remove | Remove generic relay/settings receiver; build both official halves; test every key, encoder direction, pointing input, battery proxy if enabled, soft-off, reset locality, disconnect, and re-pair. |
| Battery history | Module is fetched, but feature and Studio RPC are disabled in every reviewed artifact. | No runtime history, storage, or UI use evidence. Ordinary current battery reporting is separate. | [Pinned battery documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/config/battery.md) covers reporting and split proxy, not persistent history/clear RPC. | Current disabled module exists. | No. | remove | Drop module from manifest; confirm effective configs/source graph contain no history symbols; verify ordinary live battery reporting on both halves. |
| Studio USB transport | Enabled only in Studio-left builds through `studio-rpc-usb-uart`; current declared build disables locking, while Task 6 also built a locked candidate. | USB CDC ACM virtual UART compiled; UART0/UART1 nodes remain disabled. No USB request was sent. | [Pinned Studio documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/features/studio.md) supports USB serial using the same snippet. | Not needed. | No. | official | Dedicated central-only artifact; require locking, physical `&studio_unlock`, rejection before unlock, save after unlock, disconnect/idle relock, hostile framing bounds, and manual checklist before flash. |
| Studio BLE transport | Enabled by default on normal left and both Studio-left builds. | Effective config proves BLE transport; no encrypted BLE Studio session ran. | Pinned [Studio documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/features/studio.md) supports BLE, but inspected pinned [GATT source](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/app/src/studio/gatt_rpc_transport.c) retains ZMK-SEC-009 zero-progress loop. | Not needed after an upstream fix. | No; local core patch is not approved. | official | Block deployment until a later official revision containing an upstream fix is inspected and pinned, then test RX capacity at free, free+1, and oversized writes plus encrypted lock/relock and valid-RPC recovery. |
| DYA custom RPC client/UI | Cormoran custom dispatcher and four local custom module namespaces compile on left; DYA client supports many more optional namespaces not established in effective firmware. | Static client/module evidence only; no browser/device exchange passed. Client findings ZMK-SEC-005, ZMK-SEC-010 through ZMK-SEC-013, ZMK-SEC-018, and ZMK-SEC-019 remain open. | [Pinned RPC documentation](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/docs/docs/development/studio-rpc-protocol.md) and [handler source](https://github.com/zmkfirmware/zmk/blob/faaf39d9f59cd2a27eca3739cdd9eb197654299b/app/include/zmk/studio/rpc.h) provide fixed protobuf subsystems, not DYA arbitrary discovery/payload. | A port may combine narrowly scoped modules with reviewed message/client changes; feasibility and compatibility are not validated. | Current implementation does; no concrete requirement approves retaining it. | defer | Use official Studio client for baseline. Consider a client fork only for an approved retained custom RPC; close client findings, pin dependencies/deployment, and run adversarial browser/transport plus hardware authorization tests. |

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
official revision `faaf39d9...` retains ZMK-SEC-009. BLE Studio deployment
requires a later official revision containing an upstream fix, inspection of
that fix, an immutable pin, and boundary tests. A local core patch is not part
of this plan. Tasks 2–6 findings remain applicable until their specific
remediation and validation gates pass.

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
   until a later upstream-fixed official revision is inspected, pinned, and
   regression-tested.
4. **Add one required external module at a time.** Start from the passing
   official baseline. Require a concrete capability gap, immutable pin, narrow
   source audit, secured mutations, build/test evidence, and hardware
   regression before adding the next module.
5. **Consider client fork only for retained custom RPC UI.** Default to official
   Studio. Fork client/messages only after a custom RPC capability is approved,
   and close client findings ZMK-SEC-005, ZMK-SEC-010 through ZMK-SEC-013,
   ZMK-SEC-018, and ZMK-SEC-019 before deployment.
6. **Keep Cormoran core fork only for approved `core-fork-exception` rows.**
   There are none. A future exception needs both a cited missing official/module
   interface and a concrete user requirement, plus a bounded delta and its own
   review/validation record.

Advancing a stage requires its validation evidence; successful compilation is
not runtime authorization, memory-safety, radio, split, or hardware proof.
