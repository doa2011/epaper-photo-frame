import unittest
from firmware_config import PRESETS, plan

class FirmwareConfigTests(unittest.TestCase):
    def test_presets_are_not_firmware(self):
        for name, config in PRESETS.items():
            with self.subTest(name=name):
                result = plan(config)
                self.assertFalse(result["buildable"])
                self.assertFalse(result["hardware_verified"])

    def test_frame_geometry(self):
        for panel, size in [("gdey097f91", 161280), ("gdey116f51", 153600),
                            ("gdey133f91", 163200), ("generic-420", 30000)]:
            with self.subTest(panel=panel):
                self.assertEqual(plan(dict(PRESETS["frame-usb"], panel=panel))["display"]["four_color_frame_bytes"], size)

    def test_wifi_on_ble_chip(self):
        with self.assertRaisesRegex(ValueError, "transport unsupported"):
            plan(dict(PRESETS["frame-usb"], chip="nrf52840"))

    def test_nfc_wake_without_ble(self):
        with self.assertRaisesRegex(ValueError, "requires BLE"):
            plan(dict(PRESETS["polaroid-hybrid"], transports=["nfc_wake"]))

    def test_passive_nfc_no_wifi(self):
        with self.assertRaisesRegex(ValueError, "dedicated passive"):
            plan(dict(PRESETS["frame-usb"], power="passive_nfc"))

    def test_passive_nfc_no_timer(self):
        with self.assertRaisesRegex(ValueError, "tap-to-write"):
            plan(dict(PRESETS["polaroid-passive"], features=["timer"]))

    def test_network_dependency(self):
        with self.assertRaisesRegex(ValueError, "requires Wi-Fi"):
            plan(dict(PRESETS["polaroid-ble"], features=["mqtt"]))

    def test_battery_status(self):
        with self.assertRaisesRegex(ValueError, "battery power"):
            plan(dict(PRESETS["frame-usb"], features=["battery_status"]))

    def test_timer_requires_slideshow(self):
        with self.assertRaisesRegex(ValueError, "timer requires"):
            plan(dict(PRESETS["polaroid-ble"], features=["timer"]))

    def test_duplicate_transport(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            plan(dict(PRESETS["polaroid-ble"], transports=["ble", "ble"]))

    def test_invalid_value_type(self):
        with self.assertRaises(ValueError):
            plan(dict(PRESETS["polaroid-ble"], chip=[]))

    def test_unknown_fields(self):
        with self.assertRaisesRegex(ValueError, "exactly"):
            plan(dict(PRESETS["frame-usb"], typo=True))
