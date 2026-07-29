# Manual hardware validation checklist

**Preconditions:** Current `studio-left-locked` and all other current-graph UF2 files are audit-only pre-remediation evidence, never production candidates or flash targets. Before any flash, obtain explicit user approval to remediate one finding at a time, close and verify every applicable report finding, build and inspect both halves, and prepare recovery copies. The later remediated USB Studio test artifact must have `CONFIG_ZMK_STUDIO_LOCKING=y`, USB CDC ACM virtual-UART transport, reachable physical `&studio_unlock`, lock-on-disconnect, and idle relock; test its BLE Studio transport separately. Never use the locking-disabled artifact. Use a known-good USB data cable, charged halves, and disposable host profile. No check below ran during static/build audit.

## Recovery and startup

- [ ] Enter UF2 bootloader/recovery on each half. Verify expected removable drive, copy correct half UF2, and confirm normal reboot.
- [ ] Flash and verify `settings_reset` recovery artifact only when both original artifacts are retained. Confirm reset clears intended settings and normal firmware can be restored.
- [ ] Boot each half independently, then together. Confirm central/peripheral reconnect and no boot loop.
- [ ] Power-cycle/reboot both halves. Confirm split reconnection and expected persisted state.

## BLE and Studio authorization

- [ ] Pair with host; reboot; verify bonded reconnect. Clear bond from keyboard and host; verify old connection cannot send HID or reconnect.
- [ ] On the user-approved remediated locking-enabled Studio artifact only, with Studio locked, attempt USB Studio connection and mutation. Confirm rejection before physical unlock; do not use either current audit artifact for this test.
- [ ] Trigger physical Studio unlock binding. Confirm USB Studio access opens only after action, required operations work, and automatic relock occurs after configured 600-second timeout and disconnect.
- [ ] With USB connected, identify USB CDC ACM Studio transport and confirm no hardware UART0/UART1 path is required.
- [ ] With USB disconnected, test encrypted BLE Studio independently: confirm same lock-before-unlock and relock behavior; record whether policy permits it for production.

## Input, lighting, power

- [ ] Exercise every key on every layer; verify no missing, duplicate, or wrong HID report.
- [ ] Exercise five-way switch: up, down, left, right, press.
- [ ] Exercise encoder clockwise, counter-clockwise, and press if fitted on every layer. Confirm no missing mapping; build warning currently shows each layer's second sensor binding is discarded.
- [ ] Exercise mouse movement, scroll, and mouse buttons. Verify no drift or unexpected reports.
- [ ] Verify RGB and backlight controls, brightness/effects, and persistence across reboot.
- [ ] Verify sleep, wake, and soft-off. Confirm expected wake source and no unintended host input.
- [ ] Leave keyboard idle while monitoring host HID events. Confirm no unexpected reports.

## Split and host state

- [ ] Switch each configured host/BLE profile. Verify intended host receives input and inactive hosts do not.
- [ ] Change split-relevant settings/keymap through supported flow; reboot/reconnect both halves; verify propagation and persisted agreement.
