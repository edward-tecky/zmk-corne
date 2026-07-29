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
