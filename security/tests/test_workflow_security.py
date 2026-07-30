from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
DRAW_WORKFLOW = ROOT / ".github" / "workflows" / "draw.yml"
AUDITED_DRAW_SHA = "3a4ca7e060a54ba700d3e7b6a43cb0b9cec347d2"
DRAW_WORKFLOW_SOURCE = (
    "caksoylar/keymap-drawer/.github/workflows/draw-zmk.yml"
)
BUILD_CALLER = ROOT / ".github" / "workflows" / "build.yml"
BUILD_MATRIX = ROOT / "build.yaml"
FIRMWARE_SECURITY_WORKFLOW = (
    ROOT / ".github" / "workflows" / "security-firmware-boundaries.yml"
)
FIRMWARE_SECURITY_MATRIX = ROOT / "security" / "build-firmware-boundaries.yaml"
PINNED_BUILD_WORKFLOW = (
    ROOT / ".github" / "workflows" / "build-user-config-pinned.yml"
)
AUDITED_ACTION_USES = {
    "actions/checkout": "11d5960a326750d5838078e36cf38b85af677262",
    "actions/cache": "0057852bfaa89a56745cba8c7296529d2fc39830",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/upload-artifact/merge": (
        "ea165f8d65b6e75b540449e92b4886f43607fa02"
    ),
}
WEST_MANIFEST = ROOT / "config" / "west.yml"
DEPENDENCY_INVENTORY = ROOT / "security" / "audit" / "dependency-inventory.tsv"
AUDITED_NANOPB_SHA = "8c60555d6277a0360c876bd85d491fc4fb0cd74a"
AUDITED_WEST_REVISIONS = {
    "eyelash_corne": "ba1eeab627ba94ac46f7768b3ddc01f97873ca87",
    "zephyr": "dacab4875df72109b96cc8977547a0dc04875bcd",
    "zmk": "4493783ef88ce2e653bf8217c92ee17140df71e3",
    "zmk-behavior-runtime-sensor-rotate": (
        "8b1125ed676c1f5e14145d217984f33d0ebdcef4"
    ),
    "zmk-module-ble-management": (
        "851661cd21f2aded8ec649da86e01a207dc4b973"
    ),
    "zmk-module-battery-history": (
        "307755dd2ad4d320e14de162e8e5ef018f29d929"
    ),
    "zmk-module-settings-rpc": (
        "78f86df9e6c5edaf57bef3ccbd7f360cfdf49291"
    ),
    "zmk-module-runtime-input-processor": (
        "dbf92f764de8b6ffd60bf5850514302875fe2570"
    ),
}


class WorkflowSecurityTests(unittest.TestCase):
    def test_firmware_validation_is_repo_owned_and_publishes_nothing(self) -> None:
        workflow = FIRMWARE_SECURITY_WORKFLOW.read_text(encoding="utf-8")
        reusable = PINNED_BUILD_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn(
            "uses: ./.github/workflows/build-user-config-pinned.yml",
            workflow,
        )
        self.assertIn("build_matrix_path: security/build-firmware-boundaries.yaml", workflow)
        self.assertIn("upload_artifacts: false", workflow)
        self.assertRegex(workflow, re.compile(r"(?m)^\s+contents:\s+read\s*$"))
        self.assertNotRegex(workflow, re.compile(r"(?m)^\s+contents:\s+write\s*$"))
        self.assertIn("upload_artifacts:", reusable)
        self.assertIn("if: inputs.upload_artifacts", reusable)
        self.assertIn("Firmware SHA-256", reusable)
        self.assertIn("sha256sum", reusable)

    def test_firmware_validation_matrix_has_all_required_boundaries(self) -> None:
        matrix = FIRMWARE_SECURITY_MATRIX.read_text(encoding="utf-8")

        self.assertEqual(len(re.findall(r"(?m)^\s{2}- board:", matrix)), 4)
        for required in (
            "shield: eyelash_corne_right nice_view",
            "shield: eyelash_corne_left nice_view",
            "shield: eyelash_corne_left nice_view",
            "shield: settings_reset",
            "-DCONFIG_ZMK_STUDIO_LOCKING=y",
        ):
            self.assertIn(required, matrix)
        self.assertNotIn("-DCONFIG_ZMK_STUDIO_LOCKING=n", matrix)

    def test_distributable_build_matrix_only_contains_ordinary_right(self) -> None:
        matrix = BUILD_MATRIX.read_text(encoding="utf-8")

        self.assertEqual(len(re.findall(r"(?m)^\s{2}- board:", matrix)), 1)
        self.assertIn("shield: eyelash_corne_right nice_view", matrix)
        for withheld in (
            "settings_reset",
            "studio-rpc",
            "CONFIG_ZMK_STUDIO",
            "eyelash_corne_studio",
        ):
            self.assertNotIn(withheld, matrix)
        self.assertNotRegex(
            matrix,
            re.compile(r"(?m)^\s+(snippet|cmake-args|artifact-name):"),
        )

    def test_build_caller_is_local_and_read_only(self) -> None:
        caller = BUILD_CALLER.read_text(encoding="utf-8")
        self.assertIn(
            "uses: ./.github/workflows/build-user-config-pinned.yml",
            caller,
        )
        self.assertRegex(caller, re.compile(r"(?m)^\s+contents:\s+read\s*$"))
        self.assertNotIn("zmkfirmware/zmk/.github/workflows/", caller)

    def test_reusable_build_sanitizes_artifact_path_components(self) -> None:
        workflow = PINNED_BUILD_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("tr '/' '-'", workflow)
        self.assertIn("artifact_name=${safe_artifact_name}", workflow)

    def test_vendored_build_actions_are_pinned(self) -> None:
        workflow = PINNED_BUILD_WORKFLOW.read_text(encoding="utf-8")
        for source, sha in AUDITED_ACTION_USES.items():
            self.assertIn(f"uses: {source}@{sha}", workflow)
        self.assertNotRegex(
            workflow,
            re.compile(r"(?m)^\s*uses:\s+[^./][^@\s]*@(main|master|v\d+)"),
        )

    def test_west_manifest_is_frozen_reviewed_graph(self) -> None:
        manifest = WEST_MANIFEST.read_text(encoding="utf-8")
        revisions = re.findall(r"(?m)^\s+revision:\s+(\S+)", manifest)

        self.assertIn("url: https://github.com/edward-tecky/zmk", manifest)
        self.assertNotIn("cormoran", manifest.lower())
        self.assertGreater(len(revisions), 10)
        self.assertTrue(
            all(re.fullmatch(r"[0-9a-f]{40}", revision) for revision in revisions)
        )

    def test_frozen_manifest_has_single_nanopb_project(self) -> None:
        manifest = WEST_MANIFEST.read_text(encoding="utf-8")
        self.assertEqual(
            len(re.findall(r"(?m)^\s*-\s+name:\s+nanopb\s*$", manifest)),
            1,
        )
        self.assertIn(
            "url: https://github.com/zephyrproject-rtos/nanopb",
            manifest,
        )

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
