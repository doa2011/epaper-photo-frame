import unittest
from device_profiles import PANELS

class DeviceProfilesTests(unittest.TestCase):
    def test_registry(self):
        expected = {
            "gdem0397f81": ("SSD2677", 800, 480, 96000),
            "jd79665-800x480": ("JD79665", 800, 480, 96000),
            "gdey097f91": ("SSD2677", 960, 672, 161280),
            "waveshare-10.2-g": ("SSD2677", 960, 640, 153600),
            "gdey116f51": ("SSD2677", 960, 640, 153600),
            "gdey116f91": ("SSD2677", 960, 640, 153600),
            "gdey133f91": ("SSD2677", 960, 680, 163200),
        }
        self.assertEqual(set(PANELS), set(expected))
        for name, values in expected.items():
            with self.subTest(panel=name):
                p = PANELS[name]
                self.assertEqual((p.driver, p.width, p.height, p.frame_bytes), values)
                self.assertFalse(p.verified)

    def test_explicit_mapping_required(self):
        p = PANELS["gdey097f91"]
        with self.assertRaises(TypeError):
            p.encoder()
        with self.assertRaises(ValueError):
            p.encoder(codes=(0,0,2,3), msb_first=True,
                      flip_x=False, flip_y=False, pad_code=0)

    def test_full_frame(self):
        for name, p in PANELS.items():
            with self.subTest(panel=name):
                encoder = p.encoder(codes=(3,2,1,0), msb_first=True,
                                    flip_x=False, flip_y=False, pad_code=0)
                pixels = bytes((0,1,2,3)) * (p.width*p.height//4)
                self.assertEqual(encoder.encode(pixels), (bytes([0xe4])*p.frame_bytes,))

if __name__ == "__main__":
    unittest.main()
