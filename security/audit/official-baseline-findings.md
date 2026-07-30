# Official ZMK Baseline Finding Gates

## Immutable baseline

- Product source: `7b602a3e0db38176a8cb5239ef8b8c14040e43b2`
- Official ZMK: `faaf39d9f59cd2a27eca3739cdd9eb197654299b`
- Frozen manifest SHA-256:
  `99746c675897454a044c335eb9741b0f0d30d808b1fe70944a0aa471b9f481d3`
- CI runs:
  `30539322688` (push) and `30539334928` (workflow dispatch)
- Both runs completed successfully from the same product source.
- Both runs uploaded zero firmware artifacts.

## Reproducible firmware hashes

| Validation target | SHA-256 in both runs |
|---|---|
| Ordinary right | `20566c8128be9d50ca34c0e214966ba91af4d3f436245935fafad844b45e26dd` |
| Ordinary left | `978b2659bbf443f856d96f2f6885d6fc988e8d029fe2568ed4ebc124037c2ab8` |
| Locked USB Studio-left | `004636e8cee9888f399fc64a1f19a722e06af21d011b737a8e54d656b9bc68de` |
| Settings-reset validation | `157e0cd816e5876f0e659010e754cc582e23281b94888e538e21297ada2755cc` |

## Effective configuration

- Ordinary left/right logs contain no enabled Studio, BLE-management,
  settings-RPC, runtime-input-RPC, or split-relay symbols.
- Studio-left contains `CONFIG_ZMK_STUDIO=y` and
  `CONFIG_ZMK_STUDIO_LOCKING=y`.
- Studio-left source explicitly sets `CONFIG_ZMK_STUDIO_TRANSPORT_BLE=n`;
  effective Kconfig output omits the disabled symbol.
- Frozen graph contains official ZMK/Zephyr projects and no Cormoran or DYA
  firmware module.
- Distributable `build.yaml` contains ordinary right only. Settings-reset and
  Studio builds remain CI validation targets and are never uploaded.

## Independent finding verdicts

| Finding | Verdict after baseline | Evidence rule |
|---|---|---|
| ZMK-SEC-004 | Removed from baseline | No BLE/settings custom module or symbol in frozen graph or effective config |
| ZMK-SEC-008 | Removed from baseline | Cormoran split-relay delta and symbol absent |
| ZMK-SEC-009 | Open; BLE Studio disabled | Inspected official SHA remains affected; Studio BLE transport explicitly disabled |
| ZMK-SEC-014 | Removed from baseline | Cormoran wired delta absent; no custom wired-split configuration |
| ZMK-SEC-015 | Removed from baseline | Cormoran ignore-position delta absent |
| ZMK-SEC-016 | Removed from baseline | Runtime-sensor and BLE-management modules absent |
| ZMK-SEC-017 | Removed from baseline | Runtime-input module and symbols absent |
| ZMK-SEC-021 | Open; settings-reset undistributed | Reviewed guard SHA not pinned; reset build is validation-only and uploaded nowhere |
