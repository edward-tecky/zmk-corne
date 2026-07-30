from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
WEST = ROOT / "config" / "west.yml"
KEYMAP = ROOT / "config" / "eyelash_corne.keymap"
BUILD = ROOT / "build.yaml"
SECURITY_BUILD = ROOT / "security" / "build-firmware-boundaries.yaml"
SHIELD_ROOT = ROOT / "boards" / "shields" / "eyelash_corne"
REVIEWED_ZMK_SHA = "7c61a5496910a48d2db2d6abdb249950b791ca9a"


class OfficialBaselineTests(unittest.TestCase):
    def test_manifest_uses_only_full_sha_revisions_and_reviewed_zmk(self) -> None:
        manifest = WEST.read_text(encoding="utf-8")
        self.assertIn("url: https://github.com/edward-tecky/zmk", manifest)
        self.assertRegex(
            manifest,
            rf"(?ms)- name: zmk\b.*?revision: {REVIEWED_ZMK_SHA}\b",
        )
        self.assertNotIn("cormoran", manifest.lower())
        revisions = re.findall(r"(?m)^\s+revision:\s+(\S+)", manifest)
        self.assertGreater(len(revisions), 10)
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{40}", x) for x in revisions))

    def test_local_configuration_contains_no_dya_interfaces(self) -> None:
        files = [
            KEYMAP,
            SHIELD_ROOT / "eyelash_corne_left.overlay",
            SHIELD_ROOT / "eyelash_corne_right.overlay",
            SHIELD_ROOT / "eyelash_corne_left.conf",
            SHIELD_ROOT / "eyelash_corne_right.conf",
            SHIELD_ROOT / "eyelash_corne_studio.conf",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
        forbidden = (
            "runtime-sensor-rotate",
            "runtime-input-processor",
            "battery_history_request",
            "ZMK_BLE_MANAGEMENT",
            "ZMK_SETTINGS_RPC",
            "ZMK_SPLIT_RELAY_EVENT",
        )
        for token in forbidden:
            self.assertNotIn(token, combined)

    def test_official_encoder_and_usb_only_locked_studio(self) -> None:
        keymap = KEYMAP.read_text(encoding="utf-8")
        self.assertIn('compatible = "zmk,behavior-sensor-rotate";', keymap)
        self.assertIn("bindings = <&kp C_VOL_UP>, <&kp C_VOL_DN>;", keymap)
        studio = (
            SHIELD_ROOT / "eyelash_corne_studio.conf"
        ).read_text(encoding="utf-8")
        self.assertIn("CONFIG_ZMK_STUDIO=y", studio)
        self.assertIn("CONFIG_ZMK_STUDIO_TRANSPORT_BLE=n", studio)
        self.assertIn("CONFIG_ZMK_STUDIO_LOCKING=y", SECURITY_BUILD.read_text())
        self.assertNotIn("settings_reset", BUILD.read_text())

    def test_build_matrices_use_official_hwmv2_board_id(self) -> None:
        matrices = BUILD.read_text() + "\n" + SECURITY_BUILD.read_text()
        self.assertIn("board: nice_nano//zmk", BUILD.read_text())
        self.assertEqual(matrices.count("board: nice_nano//zmk"), 5)
        self.assertNotIn("board: nice_nano_v2", matrices)

    def test_removed_ws2812_kconfig_symbol_is_absent(self) -> None:
        config = (ROOT / "config" / "eyelash_corne.conf").read_text()
        self.assertNotIn("CONFIG_WS2812_STRIP", config)


if __name__ == "__main__":
    unittest.main()
