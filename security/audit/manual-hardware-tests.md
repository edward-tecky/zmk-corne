# Manual hardware validation checklist

**Preconditions:** Build and inspect both halves before any flash recommendation. Use known-good USB data cable, charged halves, disposable host profile, and recovery copies. No check below ran during static/build audit.

## Recovery and startup

- [ ] Enter UF2 bootloader/recovery on each half. Verify expected removable drive, copy correct half UF2, and confirm normal reboot.
- [ ] Flash and verify `settings_reset` recovery artifact only when both original artifacts are retained. Confirm reset clears intended settings and normal firmware can be restored.
- [ ] Boot each half independently, then together. Confirm central/peripheral reconnect and no boot loop.
- [ ] Power-cycle/reboot both halves. Confirm split reconnection and expected persisted state.

## BLE and Studio authorization

- [ ] Pair with host; reboot; verify bonded reconnect. Clear bond from keyboard and host; verify old connection cannot send HID or reconnect.
- [ ] With Studio locked, attempt connection and mutation. Confirm rejection before physical unlock.
- [ ] Trigger physical Studio unlock binding. Confirm access opens only after action, required operations work, and automatic relock occurs after configured timeout/disconnect.
- [ ] Test USB-only Studio with BLE disabled/disconnected. Confirm expected access and no BLE fallback.
- [ ] Test BLE-only Studio with USB disconnected. Confirm expected access and no USB fallback.

## Input, lighting, power

- [ ] Exercise every key on every layer; verify no missing, duplicate, or wrong HID report.
- [ ] Exercise five-way switch: up, down, left, right, press.
- [ ] Exercise encoder clockwise, counter-clockwise, and press if fitted.
- [ ] Exercise mouse movement, scroll, and mouse buttons. Verify no drift or unexpected reports.
- [ ] Verify RGB and backlight controls, brightness/effects, and persistence across reboot.
- [ ] Verify sleep, wake, and soft-off. Confirm expected wake source and no unintended host input.
- [ ] Leave keyboard idle while monitoring host HID events. Confirm no unexpected reports.

## Split and host state

- [ ] Switch each configured host/BLE profile. Verify intended host receives input and inactive hosts do not.
- [ ] Change split-relevant settings/keymap through supported flow; reboot/reconnect both halves; verify propagation and persisted agreement.
