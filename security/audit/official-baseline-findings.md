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

## Reviewed patch integration

- Product source: `0ebe524c795dcfaeb30ed7d7c1570732dcd8abf4`
- Reviewed ZMK fork: `df896a2f4ffafa145bbae043debe523561b28493`
- Push CI: distributable run `30576318651`; boundary run `30576318713`
- Exact-source repeat CI: distributable run `30576777245`; boundary run
  `30576779722`
- All runs passed. Boundary runs uploaded no artifacts.

| Validation target | SHA-256 in both boundary runs |
|---|---|
| Ordinary right | `20566c8128be9d50ca34c0e214966ba91af4d3f436245935fafad844b45e26dd` |
| Ordinary left | `fec3be7ac31a6d9230e64f72737fe06ee07cd5d93d2ec27d5a428bc0812550e4` |
| Locked USB Studio-left | `24618d7d2d90db6186aa353806b73b29e5a9144485a19643373b55a85e40ee08` |
| Settings-reset validation | `001a0e3a33055c2a50dc132f3e1de09c1c448071a896649221c74f182f49be16` |

ZMK-SEC-009 and ZMK-SEC-021 move from accepted deferral to `in-review`.
Software and deterministic-build gates pass. BLE Studio remains disabled until
its encrypted hardware boundary test; settings-reset remains undistributed
until its manual recovery test.
