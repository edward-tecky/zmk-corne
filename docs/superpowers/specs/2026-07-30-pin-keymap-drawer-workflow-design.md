# ZMK Security Remediation Portfolio Design

## Goal

Resolve all 21 findings in `security_best_practices_report.md` without flashing
unreviewed firmware, silently dropping required keyboard behavior, or mixing
unrelated fixes into one review.

This document replaces the original single-finding workflow-pin design. The
workflow pin remains first in the portfolio.

## Operating Rules

- Remediate one `ZMK-SEC-NNN` finding at a time.
- Require user approval before each implementation.
- Keep finding-specific tests, review, and commits separate.
- Do not flash until all applicable firmware findings are closed, both halves
  build from frozen inputs, and every manual hardware check passes.
- Prefer pinned official ZMK with no DYA modules or Cormoran core fork.
- Fix external code only in its owning repository or through a reviewed upstream
  change. Do not hide fork defects with local configuration claims.
- A removed or unreachable feature closes a finding only when build evidence
  proves affected code is absent.

## Disposition Options

Three portfolio approaches were considered:

1. **Patch current fork in place:** least feature disruption, largest long-term
   review burden.
2. **Migrate immediately, then harden:** smallest final trust base, but combines
   migration and behavior changes.
3. **Recommended — secure current supply/config boundaries, establish official
   baseline, then retain only proven needs:** preserves rollback evidence while
   preventing unnecessary fork/module fixes.

The portfolio uses approach 3.

## Finding Review

| ID | Review verdict | Owner / target | Planned disposition | Closure evidence |
|---|---|---|---|---|
| ZMK-SEC-001 | Confirmed High supply-chain risk | This repository | Pin keymap-drawer reusable workflow to audited SHA; retain scoped automatic commit flow | Workflow uses exact SHA; dispatch still commits only generated keymap output |
| ZMK-SEC-002 | Confirmed High supply-chain risk | This repository/build manifest | Replace every mutable direct/imported revision with reviewed SHAs through an owned frozen manifest/lock mechanism | Two clean `west update` runs resolve identical inventory SHAs and reproduce artifacts |
| ZMK-SEC-003 | Confirmed High physical-management gap | This repository | Enable Studio locking; keep physical `&studio_unlock`, disconnect relock, and idle relock | Locked USB/BLE requests fail before unlock and after relock; approved requests work after physical unlock |
| ZMK-SEC-004 | Confirmed High authorization defect | Module owners or removal path | Baseline removes DYA BLE/settings RPC modules; retain only after mutation methods become secured and bond deletion is narrowed | Effective build proves modules absent, or exhaustive pre/post-unlock mutation tests pass |
| ZMK-SEC-005 | Confirmed High client vulnerability | DYA Studio client owner | Central HTTPS-only navigation invariant; reject unsafe schemes before display/storage/navigation | Unit/browser fixtures reject malicious schemes and preserve valid HTTPS |
| ZMK-SEC-006 | Confirmed Medium CI supply-chain risk | This repository plus reusable workflow ownership | Pin called workflow; declare `contents: read`; require nested full-SHA action pins or vendor reviewed workflow | Effective token is read-only and every executed action identity is immutable |
| ZMK-SEC-007 | Confirmed Medium exposure gap | This repository | Move Studio/custom management symbols out of generic left config into explicit Studio-only target | Normal left/right configs contain no Studio/custom RPC; dedicated locked target contains only approved management paths |
| ZMK-SEC-008 | Confirmed Medium fork memory-safety defect | Cormoran/upstream fork owner, or fork removal | Prefer official baseline without affected fork delta; otherwise reject short/nonzero-offset relay writes before header copy | Affected code absent, or sanitizer/hardware boundary tests reject malformed writes |
| ZMK-SEC-009 | Confirmed Medium BLE denial of service; also present in inspected official ZMK | Official ZMK upstream | Wait for reviewed upstream fix; pin fixed commit; no local core exception currently approved | Ring-capacity boundary tests prove bounded callback return and no partial frame |
| ZMK-SEC-010 | Confirmed Medium hostile-device client DoS | `zmk-studio-ts-client` owner | Add measured maximum frame size and bounded transport queues | Oversized/no-EOF/repeated-SOF tests keep memory bounded and connection recoverable |
| ZMK-SEC-011 | Confirmed Medium RPC state-machine DoS | `zmk-studio-ts-client` and React wrapper owners | Abort timed-out read, release connection-scoped mutex, reject late response | Fake transport proves timeout recovery, late-response rejection, and independent connections |
| ZMK-SEC-012 | Confirmed Medium deployment hardening gap | DYA deployment owner | Remove/self-host analytics and fonts; deploy tested CSP and browser security headers | Built assets and every production route return approved headers; all device transports still work |
| ZMK-SEC-013 | Confirmed Medium wrong-device mutation risk | DYA/React client owners | Require explicit choice or confirmation for ambiguous same-VID/PID reconnect | Reordered identical-device fixtures never silently select a different device |
| ZMK-SEC-014 | Confirmed Low dormant wired-transport defect | Official/fork owner, only if wired split retained | Keep wired split disabled; fix callbacks before any enablement | Effective builds prove wired path absent, or fixture proves disabled receiver ignores commands |
| ZMK-SEC-015 | Confirmed Low HID-integrity defect | ZMK fork/upstream owner | Fix outer tap-dance ignore control flow or rely on pinned upstream fix | Behavior test proves ignored key emits no tap-dance HID event |
| ZMK-SEC-016 | Confirmed Low flash-wear hardening gap | Runtime-sensor/BLE module owners, only if retained | Remove modules by default; retained paths coalesce and suppress unchanged writes | Instrumented backend shows one debounced write and accurate failure result |
| ZMK-SEC-017 | Confirmed Low dormant runtime-input defect set | Runtime-input module owner, only if retained | Remove/uninstantiate module; do not retain until all range, fall-through, reset, result, notification, and authorization defects close | Effective build proves absence, or complete boundary/UB tests pass |
| ZMK-SEC-018 | Confirmed Low privacy gap | DYA client owner | Redact stable ID, sensitive URL parts, and excess UA detail by default; preview export | Snapshot excludes sensitive fields unless explicitly included |
| ZMK-SEC-019 | Confirmed Low accidental destructive-action gap | DYA client owner | Add accessible final-boundary confirmations for every enumerated disruptive action | Cancel causes zero mutation; Confirm causes exactly one intended mutation |
| ZMK-SEC-020 | Confirmed Low reachable encoder correctness defect | This repository | Choose one binding per physical encoder or explicitly model required sensor count; make excess binding fatal | Warning-free builds plus physical encoder tests on every layer |
| ZMK-SEC-021 | Confirmed Low conditional recovery memory-safety gap | Official/fork owner | Pin upstream guard/fix or prove zero-keymap handler compiled out before trusting reset artifact | Instrumented zero-keymap test passes; settings-reset build warning disappears |

## Execution Phases

### Phase 1 — Repository Supply Chain

1. ZMK-SEC-001: pin Draw Keymap workflow while preserving automatic commits.
2. ZMK-SEC-002: freeze complete west graph.
3. ZMK-SEC-006: pin build workflow/actions and enforce read-only token.

### Phase 2 — Local Firmware Boundaries

4. ZMK-SEC-003: enable Studio locking.
5. ZMK-SEC-007: separate ordinary and Studio artifacts.
6. ZMK-SEC-020: resolve encoder binding truncation.

Build both current halves after every manifest/configuration change. Do not
flash.

### Phase 3 — Official-ZMK Baseline

7. Establish pinned official ZMK with zero DYA modules.
8. Close ZMK-SEC-004, 008, 014, 016, and 017 through proven removal unless a
   concrete capability requirement justifies separate upstream/module work.
9. Require upstream closure for ZMK-SEC-009, 015, and 021 before affected
   behavior/artifacts are trusted.

### Phase 4 — DYA Client and Deployment

Address ZMK-SEC-005, 010, 011, 012, 013, 018, and 019 in their owning client or
deployment repositories. Each receives its own tests, review, and release gate.
The official Studio client remains baseline unless custom RPC UI is approved.

### Phase 5 — Integration and Hardware Gate

1. Rebuild normal right and dedicated locked central-left artifacts twice from
   identical frozen inputs.
2. Compare hashes and inspect effective Kconfig/Devicetree.
3. Run every check in `security/audit/manual-hardware-tests.md`.
4. Review residual findings and regression evidence.
5. Obtain explicit user approval before flashing any artifact.

## First Finding Design: ZMK-SEC-001

Change `.github/workflows/draw.yml` from
`caksoylar/keymap-drawer/.github/workflows/draw-zmk.yml@main` to audited commit
`3a4ca7e060a54ba700d3e7b6a43cb0b9cec347d2`.

Keep existing triggers, `contents: write`, `destination: "commit"`, commit
message, and failure behavior. Updated local keymap configuration still
regenerates and commits keymap output. Upstream workflow updates become explicit
reviewed SHA changes.

Verification:

1. Static check rejects `@main` and requires exact audited SHA.
2. Triggers, `contents: write`, and `destination: "commit"` remain unchanged.
3. `git diff --check` passes.
4. After push, `workflow_dispatch` commits only intended generated keymap files.

## Portfolio Completion

Portfolio completion requires all 21 findings to be either:

- fixed and verified;
- removed with effective-build proof;
- explicitly deferred because feature remains disabled and unreachable.

No finding closes from documentation alone. No current UF2 is approved for
flash.
