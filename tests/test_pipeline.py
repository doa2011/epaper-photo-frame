import unittest
from PIL import Image
from image_pipeline import convert, pack, PALETTES

class PipelineTests(unittest.TestCase):
    def test_palettes(self):
        for name, colors in PALETTES.items():
            for method in ("none","bayer","floyd","atkinson"):
                im, idx = convert(Image.new("RGB",(9,7),"white"),(5,3),name,method)
                self.assertEqual(im.size,(5,3))
                self.assertEqual(len(idx),15)
                self.assertTrue(set(idx) <= set(range(len(colors))))
    def test_exact_colors(self):
        for name, colors in PALETTES.items():
            for i,color in enumerate(colors):
                _, idx = convert(Image.new("RGB",(2,2),color),(2,2),name,"none")
                self.assertEqual(idx,bytes([i]*4))
    def test_packing(self):
        self.assertEqual(pack(bytes([0,1,2,3]),(4,1),[0,1,2,3],2),b"\x1b")
        self.assertEqual(pack(bytes([1,0,1,1,1,0]),(3,2),[0,1],1),b"\xa0\xc0")
    def test_frame_length(self):
        self.assertEqual(len(pack(bytes(800*480),(800,480),[0,1,2,3],2)),96000)
    def test_invalid(self):
        with self.assertRaises(ValueError):
            pack(b"", (2,2), [0,1], 1)
