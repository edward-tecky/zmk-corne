from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
