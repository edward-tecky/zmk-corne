# ZMK Release Candidate Evidence

## Pre-flash gate

- Source commit: `72e4df5041a6ac7380385ddcd38cb858d7f4c340`
- Frozen manifest SHA-256:
  `ba267cda5f167ed251f9092c905597fb0ec6253bb64c9c53a24335754f6cc146`
- Exact-source boundary CI runs: `30579741764`, `30580040410`
- Both runs: success
- Boundary-run uploaded firmware artifacts: zero
- Distributable run `30579742076` uploaded only the ordinary right candidate;
  no Studio-left or settings-reset artifact was uploaded.
- Flash approval: **not granted**

## Deterministic validation hashes

| Target | SHA-256 in both runs | Flash status |
|---|---|---|
| Right | `20566c8128be9d50ca34c0e214966ba91af4d3f436245935fafad844b45e26dd` | Candidate; requires exact-hash approval |
| Ordinary left | `fec3be7ac31a6d9230e64f72737fe06ee07cd5d93d2ec27d5a428bc0812550e4` | Validation only |
| Locked BLE+USB Studio-left | `35f88000124255e2769071426821d464d7d3a890c45d85b0860fdb840d7e8ca3` | Candidate; requires exact-hash approval |
| Settings-reset | `001a0e3a33055c2a50dc132f3e1de09c1c448071a896649221c74f182f49be16` | Recovery candidate; requires exact-hash approval; undistributed |

## Residual controls

- ZMK-SEC-009: `open-disabled`; BLE Studio exists only in the locked,
  undistributed hardware-gate candidate.
- ZMK-SEC-021: `open-disabled`; settings-reset remains undistributed.
- Studio-left effective configuration includes `CONFIG_ZMK_STUDIO=y` and
  `CONFIG_ZMK_STUDIO_LOCKING=y`, BLE and UART transports, disconnect relock, and
  a 600-second idle relock.
- Ordinary halves contain no enabled Studio/custom-management interface.

## Finding map

| Finding | Release verdict |
|---|---|
| ZMK-SEC-001 | fixed-verified |
| ZMK-SEC-002 | fixed-verified |
| ZMK-SEC-003 | fixed-verified |
| ZMK-SEC-004 | removed-verified |
| ZMK-SEC-005 | fixed-verified |
| ZMK-SEC-006 | fixed-verified |
| ZMK-SEC-007 | fixed-verified |
| ZMK-SEC-008 | removed-verified |
| ZMK-SEC-009 | open-disabled |
| ZMK-SEC-010 | fixed-verified |
| ZMK-SEC-011 | fixed-verified |
| ZMK-SEC-012 | fixed-verified |
| ZMK-SEC-013 | fixed-verified |
| ZMK-SEC-014 | removed-verified |
| ZMK-SEC-015 | removed-verified |
| ZMK-SEC-016 | removed-verified |
| ZMK-SEC-017 | removed-verified |
| ZMK-SEC-018 | fixed-verified |
| ZMK-SEC-019 | fixed-verified |
| ZMK-SEC-020 | fixed-verified |
| ZMK-SEC-021 | open-disabled |

No `open-blocking` finding exists. Hardware checks remain unexecuted.
