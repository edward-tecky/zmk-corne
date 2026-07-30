from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
BUILD_MATRIX = ROOT / "security" / "build-firmware-boundaries.yaml"
LEFT_CONF = (
    ROOT / "boards" / "shields" / "eyelash_corne"
    / "eyelash_corne_left.conf"
)
STUDIO_CONF = (
    ROOT / "boards" / "shields" / "eyelash_corne"
    / "eyelash_corne_studio.conf"
)
KEYMAP = ROOT / "config" / "eyelash_corne.keymap"


class FirmwareSecurityTests(unittest.TestCase):
    def test_studio_artifact_enables_locking(self) -> None:
        matrix = BUILD_MATRIX.read_text(encoding="utf-8")
        self.assertIn("-DCONFIG_ZMK_STUDIO_LOCKING=y", matrix)
        self.assertNotIn("-DCONFIG_ZMK_STUDIO_LOCKING=n", matrix)
        self.assertIn("&studio_unlock", KEYMAP.read_text(encoding="utf-8"))

    def test_generic_left_excludes_management_interfaces(self) -> None:
        left = LEFT_CONF.read_text(encoding="utf-8")
        forbidden = (
            "CONFIG_ZMK_STUDIO=",
            "CONFIG_ZMK_BLE_MANAGEMENT=",
            "CONFIG_ZMK_BLE_MANAGEMENT_STUDIO_RPC=",
            "CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR=",
            "CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR_STUDIO_RPC=",
            "CONFIG_ZMK_SETTINGS_RPC=",
            "CONFIG_ZMK_SETTINGS_RPC_STUDIO=",
            "CONFIG_ZMK_RUNTIME_SENSOR_ROTATE_STUDIO_RPC=",
        )
        for symbol in forbidden:
            self.assertNotIn(symbol, left)

    def test_studio_add_on_owns_management_interfaces(self) -> None:
        studio = STUDIO_CONF.read_text(encoding="utf-8")
        required = (
            "CONFIG_ZMK_STUDIO=y",
            "CONFIG_ZMK_BLE_MANAGEMENT=y",
            "CONFIG_ZMK_BLE_MANAGEMENT_STUDIO_RPC=y",
            "CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR=y",
            "CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR_STUDIO_RPC=y",
            "CONFIG_ZMK_SETTINGS_RPC=y",
            "CONFIG_ZMK_SETTINGS_RPC_STUDIO=y",
            "CONFIG_ZMK_RUNTIME_SENSOR_ROTATE_STUDIO_RPC=y",
        )
        for symbol in required:
            self.assertIn(symbol, studio)

        matrix = BUILD_MATRIX.read_text(encoding="utf-8")
        self.assertIn(
            "shield: eyelash_corne_left eyelash_corne_studio nice_view",
            matrix,
        )

    def test_each_layer_has_one_physical_encoder_binding(self) -> None:
        keymap = KEYMAP.read_text(encoding="utf-8")
        bindings = re.findall(r"sensor-bindings\s*=\s*<([^>]+)>;", keymap)
        self.assertEqual(4, len(bindings))
        self.assertEqual(["&rsr_vol"] * 4, [" ".join(x.split()) for x in bindings])
        self.assertNotIn("rsr_trans:", keymap)


if __name__ == "__main__":
    unittest.main()
