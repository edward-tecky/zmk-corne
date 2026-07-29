# Pin Keymap Drawer Workflow Design

## Goal

Remove ZMK-SEC-001 mutable-workflow risk without changing keymap publication behavior.

## Design

Change `.github/workflows/draw.yml` reusable workflow reference from
`caksoylar/keymap-drawer/.github/workflows/draw-zmk.yml@main` to audited commit
`3a4ca7e060a54ba700d3e7b6a43cb0b9cec347d2`.

Keep:

- existing `push` and `workflow_dispatch` triggers;
- `contents: write`;
- `destination: "commit"`;
- current commit-message and failure behavior.

Result: changes under configured trigger paths still regenerate and commit updated
keymap output. Upstream keymap-drawer changes no longer enter automatically; upgrades
require deliberate review and SHA replacement.

## Security Boundary

Pinning prevents `@main` retargeting from changing executed workflow code. Write
permission remains necessary for automatic commits and remains a trusted capability of
the pinned reusable workflow.

## Verification

1. Static check rejects `@main` and requires the exact audited SHA.
2. YAML inspection confirms triggers, `contents: write`, and `destination: "commit"`
   remain unchanged.
3. `git diff --check` passes.
4. GitHub `workflow_dispatch` remains the live end-to-end check after push; verify only
   intended generated keymap files are committed.

## Scope

Only workflow reference changes during implementation. No firmware, keymap, generated
SVG, permission, or trigger changes.
