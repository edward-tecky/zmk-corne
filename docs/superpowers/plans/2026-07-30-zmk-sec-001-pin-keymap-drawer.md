# ZMK-SEC-001 Keymap Drawer Pin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pin the Draw Keymap reusable workflow to its audited immutable commit while preserving automatic regeneration and commit of updated keymap output.

**Architecture:** Keep the existing trigger, permission, and reusable-workflow input contract unchanged. Add a repository-local standard-library test that treats the immutable workflow identity and automatic-commit settings as one security contract, then make the one-line workflow reference change.

**Tech Stack:** GitHub Actions YAML, Python 3 `unittest`, Git

## Global Constraints

- Remediate only `ZMK-SEC-001`; do not combine another finding.
- Require user approval before implementation.
- Do not change firmware, manifests, keymaps, generated SVG files, triggers, permissions, or publication mode.
- Preserve automatic commits of updated keymap output.
- Use audited workflow commit `3a4ca7e060a54ba700d3e7b6a43cb0b9cec347d2`.
- Do not flash firmware.
- Keep implementation, verification, review, and commit specific to this finding.
- Live GitHub dispatch is a post-push verification gate; do not claim it ran from local static checks.

---

## Planned File Structure

- Create `security/tests/test_workflow_security.py`: executable standard-library regression test for immutable Draw Keymap workflow identity and preserved automatic-commit contract.
- Modify `.github/workflows/draw.yml`: replace mutable `@main` reference with audited full SHA only.
- Preserve `docs/superpowers/specs/2026-07-30-pin-keymap-drawer-workflow-design.md`: portfolio design remains unchanged during implementation.

### Task 1: Pin Draw Keymap Without Changing Publication Behavior

**Files:**
- Create: `security/tests/test_workflow_security.py`
- Modify: `.github/workflows/draw.yml:12`
- Verify: `security/audit/workflow-inventory.tsv:8-11`

**Interfaces:**
- Consumes: audited workflow identity `3a4ca7e060a54ba700d3e7b6a43cb0b9cec347d2` and existing caller inputs in `.github/workflows/draw.yml`.
- Produces: `WorkflowSecurityTests.test_draw_workflow_is_pinned_and_keeps_commit_contract`, which fails if the workflow becomes mutable or automatic commit behavior changes.

- [ ] **Step 1: Create the failing workflow-security test**

Create `security/tests/test_workflow_security.py`:

```python
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
DRAW_WORKFLOW = ROOT / ".github" / "workflows" / "draw.yml"
AUDITED_DRAW_SHA = "3a4ca7e060a54ba700d3e7b6a43cb0b9cec347d2"
DRAW_WORKFLOW_SOURCE = (
    "caksoylar/keymap-drawer/.github/workflows/draw-zmk.yml"
)


class WorkflowSecurityTests(unittest.TestCase):
    def test_draw_workflow_is_pinned_and_keeps_commit_contract(self) -> None:
        workflow = DRAW_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn(
            f"uses: {DRAW_WORKFLOW_SOURCE}@{AUDITED_DRAW_SHA}",
            workflow,
        )
        self.assertNotRegex(
            workflow,
            re.compile(
                rf"uses:\s*{re.escape(DRAW_WORKFLOW_SOURCE)}"
                r"@(main|master|v[0-9][^\s]*)"
            ),
        )
        self.assertRegex(workflow, re.compile(r"(?m)^\s+contents:\s+write\s*$"))
        self.assertRegex(
            workflow,
            re.compile(r'(?m)^\s+destination:\s+"commit"\s*$'),
        )
        self.assertRegex(
            workflow,
            re.compile(r'(?m)^\s+-\s+"config/\*\*"\s*$'),
        )
        self.assertRegex(
            workflow,
            re.compile(r"(?m)^\s+workflow_dispatch:\s*$"),
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
python3 security/tests/test_workflow_security.py
```

Expected: one failure. Failure states the exact SHA-pinned `uses:` line is absent because `.github/workflows/draw.yml` still uses `@main`.

- [ ] **Step 3: Replace only the mutable workflow reference**

Change `.github/workflows/draw.yml:12` from:

```yaml
    uses: caksoylar/keymap-drawer/.github/workflows/draw-zmk.yml@main
```

to:

```yaml
    # keymap-drawer main resolved and audited on 2026-07-29.
    uses: caksoylar/keymap-drawer/.github/workflows/draw-zmk.yml@3a4ca7e060a54ba700d3e7b6a43cb0b9cec347d2
```

Do not change any other workflow line.

- [ ] **Step 4: Run the test and verify GREEN**

Run:

```bash
python3 security/tests/test_workflow_security.py
```

Expected:

```text
.
----------------------------------------------------------------------
Ran 1 test

OK
```

- [ ] **Step 5: Verify exact diff scope and workflow contract**

Run:

```bash
git diff --check
git diff -- .github/workflows/draw.yml security/tests/test_workflow_security.py
test "$(git diff --name-only | sort)" = "$(printf '%s\n' \
  .github/workflows/draw.yml \
  security/tests/test_workflow_security.py | sort)"
grep -F 'uses: caksoylar/keymap-drawer/.github/workflows/draw-zmk.yml@3a4ca7e060a54ba700d3e7b6a43cb0b9cec347d2' \
  .github/workflows/draw.yml
grep -F 'contents: write' .github/workflows/draw.yml
grep -F 'destination: "commit"' .github/workflows/draw.yml
```

Expected: all commands exit 0; diff contains one workflow-reference replacement plus the regression test.

- [ ] **Step 6: Commit the finding-specific change**

Run:

```bash
git add .github/workflows/draw.yml security/tests/test_workflow_security.py
git diff --cached --check
git commit -m "ci: pin keymap drawer workflow"
```

Expected: one commit containing exactly the two planned files.

- [ ] **Step 7: Perform post-push live verification**

After the implementation branch is pushed, run:

```bash
branch="$(git branch --show-current)"
gh workflow run draw.yml --ref "$branch"
sleep 5
run_id="$(gh run list \
  --workflow draw.yml \
  --branch "$branch" \
  --event workflow_dispatch \
  --limit 1 \
  --json databaseId \
  --jq '.[0].databaseId')"
test -n "$run_id"
gh run watch "$run_id" --exit-status
gh run view "$run_id" --json conclusion,headSha,url
```

Expected: workflow conclusion is `success`. If generated output was already current, no commit is required. If the run creates a commit, inspect it:

```bash
git fetch origin "$branch"
git diff-tree --no-commit-id --name-only -r "origin/$branch" \
  | awk 'NF && $0 !~ /^keymap-drawer\// { bad=1; print } END { exit bad }'
```

Expected: any changed path from the generated commit is under `keymap-drawer/`. Record the run URL. Until this live gate passes, report implementation as “pinned locally; live automatic-commit verification pending,” not fully closed.
