# ZMK Corne Security Audit Design

## Objective

Determine whether this repository and its complete firmware build supply chain
are safe enough to use. Produce an evidence-based security report and a
migration design based on official ZMK plus only the DYA capabilities this
keyboard needs.

No firmware will be flashed. Remediation will begin only after the report is
reviewed and individual fixes are approved.

## Scope

The audit covers:

- Repository configuration, shield definitions, keymap, and history
- GitHub Actions workflows and their effective permissions
- `west` manifest resolution, including imported manifests
- `a741725193/zmk-new_corne`
- `cormoran/zmk` and its differences from official ZMK
- All referenced Cormoran modules
- DYA Studio client and its custom RPC contract
- Direct and transitive build dependencies
- Generated firmware configuration and artifacts where reproducible

The audit focuses on firmware integrity, dependency provenance, mutable
references, CI compromise, Studio authorization, USB/BLE RPC parsing,
persistent settings, split transport, and unintended HID behavior.

The security-best-practices skill has no reference specific to C, Zephyr, or
ZMK. Applicable official ZMK and Zephyr documentation, GitHub Actions guidance,
language-independent secure coding practices, and direct source analysis will
therefore form the review baseline.

## Threat Model

Protected assets:

- Integrity of firmware flashed to both keyboard halves
- Host input integrity and confidentiality
- Bluetooth identities, bonds, and settings
- GitHub repository and Actions token
- Reproducibility and provenance of build artifacts

Relevant attackers and failures:

- Compromised or transferred dependency repository
- Mutable branch or tag changed after review
- Compromised reusable workflow or package dependency
- Malicious or malformed USB/BLE Studio request
- Nearby BLE client reaching an improperly unlocked management interface
- Memory-safety or validation defect in custom RPC or split-event code
- Accidental unsafe configuration or stale vendor fork

Physical compromise of the keyboard, Nordic bootloader security, malicious host
OS, and semiconductor attacks will be documented as residual risks rather than
fully assessed.

## Audit Method

### 1. Resolve Build Graph

Resolve every repository, revision, imported manifest, reusable workflow, and
package used by the firmware and drawing workflows. Record immutable commit
identities and flag unresolved or mutable inputs.

### 2. Review Local Configuration

Inspect shield wiring, enabled Kconfig options, Studio transport, locking,
keymap behaviors, bootloader/reset bindings, settings storage, build matrix,
workflow triggers, permissions, and artifact handling.

### 3. Isolate Vendor Changes

Find the Cormoran fork's official ZMK merge base. Review its firmware-relevant
delta, emphasizing custom Studio RPC, BLE advertising and authorization, event
relay, runtime settings, and wired transport.

### 4. Review External Modules and DYA Client

Trace RPC messages from DYA Studio through transport and dispatch to each
module. Check authentication state, authorization classification, bounds,
integer conversions, object lifetimes, persistent writes, error handling, and
unsafe logging. Review only client code that affects device trust, protocol
handling, deployment integrity, or dependency risk.

### 5. Verify Builds

Build left, right, Studio-left, and settings-reset artifacts from pinned source
where practical. Capture resolved revisions and effective configurations.
Compare artifacts or hashes across clean repeated builds where toolchain
behavior permits.

### 6. Produce Migration Matrix

For every currently enabled DYA capability, classify it as:

- Available in official ZMK
- Retainable as an isolated external module
- Requires a core ZMK fork
- Unused or unnecessary on this Corne

Recommend official ZMK plus the smallest necessary module set. A core fork is
acceptable only when a required capability cannot be implemented through a
stable module interface.

## Findings and Severity

Report findings in `security_best_practices_report.md`. Each finding will have:

- Numeric ID
- Severity: critical, high, medium, or low
- Affected component and exact file/line evidence
- Exploit or failure scenario
- Impact
- Recommended remediation
- Compatibility and regression considerations
- Verification method

Confirmed malicious behavior and exploitable vulnerabilities will be separated
from hardening gaps, mutable supply-chain risks, and maintainability concerns.
Absence of discovered malicious behavior will not be presented as proof of
safety.

## Target Security Properties

Recommended target should:

- Use official ZMK unless a documented required feature prevents it
- Pin firmware repositories and Actions to immutable commit SHAs
- Keep a human-readable upstream version comment beside each pin
- Enable ZMK Studio locking and require a physical `&studio_unlock` action
- Expose management transports only on intended builds and keyboard half
- Grant workflows minimum permissions
- Prevent untrusted workflow code from receiving write tokens
- Preserve a reviewed settings-reset and recovery route
- Generate an auditable dependency inventory with resolved commits
- Build both halves successfully before any flash recommendation

## Validation

Validation includes:

- Static source and configuration review
- Manifest and workflow resolution checks
- Secret and suspicious primitive scanning
- Fork-delta review
- Clean firmware builds where practical
- Effective Kconfig inspection
- Existing upstream/module tests where usable
- Focused malformed-input tests or fuzz harness recommendations for RPC parsers
- Migration feature and artifact comparison

Hardware-only behavior will be listed as a manual test checklist rather than
claimed verified.

## Deliverables and Gates

1. Committed audit design
2. Detailed implementation plan
3. `security_best_practices_report.md`
4. Dependency and feature-migration inventories
5. Proposed fixes ordered by severity

User reviews the report before remediation. Fixes proceed one finding at a
time, with build verification and explicit warning before any change that could
remove DYA functionality or alter persistent settings. Flashing hardware is
outside this audit unless separately requested.
