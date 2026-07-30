# ZMK Release Candidate Evidence

## Pre-flash gate

- Source commit: `7297a06969009ec7824826d44dde9df4becaeb88`
- Frozen manifest SHA-256:
  `99746c675897454a044c335eb9741b0f0d30d808b1fe70944a0aa471b9f481d3`
- Exact-source CI runs: `30561289211`, `30561292657`
- Both runs: success
- Uploaded firmware artifacts: zero
- Flash approval: **not granted**

## Deterministic validation hashes

| Target | SHA-256 in both runs | Flash status |
|---|---|---|
| Right | `20566c8128be9d50ca34c0e214966ba91af4d3f436245935fafad844b45e26dd` | Candidate; requires exact-hash approval |
| Ordinary left | `978b2659bbf443f856d96f2f6885d6fc988e8d029fe2568ed4ebc124037c2ab8` | Validation only |
| Locked USB Studio-left | `004636e8cee9888f399fc64a1f19a722e06af21d011b737a8e54d656b9bc68de` | Candidate; requires exact-hash approval |
| Settings-reset | `157e0cd816e5876f0e659010e754cc582e23281b94888e538e21297ada2755cc` | Validation only; undistributed |

## Residual controls

- ZMK-SEC-009: `open-disabled`; BLE Studio remains disabled.
- ZMK-SEC-021: `open-disabled`; settings-reset remains undistributed.
- Studio-left effective configuration includes `CONFIG_ZMK_STUDIO=y` and
  `CONFIG_ZMK_STUDIO_LOCKING=y`; source forces BLE transport off.
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
