import hashlib
import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image
from photo_catalog import PhotoCatalog


class PhotoCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "photos"
        self.root.mkdir()
        (self.root / "nested").mkdir()
        self.photo = self.root / "nested" / "red.PNG"
        Image.new("RGB", (12, 8), (220, 0, 0)).save(self.photo)
        self.catalog = PhotoCatalog(self.root)

    def test_listing(self):
        Image.new("RGB", (2, 2)).save(self.root / "a.jpg")
        (self.root / "notes.txt").write_text("ignore")
        (self.root / "folder.png").mkdir()
        self.assertEqual(self.catalog.list(), ["a.jpg", "nested/red.PNG"])

    def test_path_boundaries(self):
        outside = Path(self.tmp.name) / "outside.png"
        Image.new("RGB", (2, 2)).save(outside)
        (self.root / "link.png").symlink_to(outside)
        for name in ("../outside.png", str(outside), "link.png"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.catalog.resolve(name)
        self.assertNotIn("link.png", self.catalog.list())

    def test_rgb_preview_read_only(self):
        before = hashlib.sha256(self.photo.read_bytes()).digest()
        png, indices = self.catalog.render("nested/red.PNG", (1280, 800), palette="rgb")
        self.assertIsNone(indices)
        with Image.open(BytesIO(png)) as im:
            self.assertEqual(im.size, (1280, 800))
            self.assertEqual(im.getpixel((0, 0)), (220, 0, 0))
        self.assertEqual(hashlib.sha256(self.photo.read_bytes()).digest(), before)

    def test_palette_preview(self):
        for palette in ("bwr", "bwry"):
            with self.subTest(palette=palette):
                png, indices = self.catalog.render("nested/red.PNG", (8, 4), palette=palette, method="none")
                self.assertEqual(indices, bytes([2]) * 32)
                with Image.open(BytesIO(png)) as im:
                    self.assertEqual(im.size, (8, 4))
                    self.assertEqual(im.getpixel((0, 0)), (220, 0, 0))

    def test_invalid_dimensions(self):
        for size in ((0, 1), (2049, 1), (1,), (1.5, 2)):
            with self.subTest(size=size), self.assertRaises(ValueError):
                self.catalog.render("nested/red.PNG", size)

    def test_exif_orientation(self):
        im = Image.new("RGB", (4, 2), (255, 0, 0))
        im.paste((0, 0, 255), (0, 1, 4, 2))
        exif = im.getexif()
        exif[274] = 6
        im.save(self.root / "rotated.png", exif=exif)
        png, _ = self.catalog.render("rotated.png", (2, 4), palette="rgb")
        with Image.open(BytesIO(png)) as preview:
            self.assertEqual(preview.getpixel((0, 0)), (0, 0, 255))
            self.assertEqual(preview.getpixel((1, 0)), (255, 0, 0))
