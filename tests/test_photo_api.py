"""Exercise the NAS API over real loopback HTTP, not mocked handlers."""
import json
import threading
import unittest
from http.server import HTTPServer
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

from PIL import Image
from photo_api import make_handler
from photo_catalog import PhotoCatalog


class PhotoAPITests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        Image.new("RGB", (16, 10), "red").save(root / "a.png")
        Image.new("RGB", (16, 10), "blue").save(root / "b.png")
        (root / "broken.png").write_bytes(b"not an image")
        self.server = HTTPServer(("127.0.0.1", 0), make_handler(PhotoCatalog(root), "test-token"))
        self.addCleanup(self.server.server_close)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.base = "http://127.0.0.1:%d" % self.server.server_port

    def stop_server(self):
        self.server.shutdown()
        self.thread.join(timeout=5)

    def get(self, path, token="test-token", **params):
        if params:
            path += "?" + urlencode(params)
        headers = {} if token is None else {"Authorization": "Bearer " + token}
        try:
            response = urlopen(Request(self.base + path, headers=headers), timeout=15)
        except HTTPError as exc:
            response = exc
        with response:
            return response.code, response.headers, response.read()

    def test_authentication(self):
        for token in (None, "wrong"):
            for path in ("/api/health", "/api/photos", "/api/devices", "/api/image"):
                with self.subTest(token=token, path=path):
                    self.assertEqual(self.get(path, token)[0], 401)
        status, headers, body = self.get("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"status": "ok"})
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_pagination(self):
        status, _, body = self.get("/api/photos", offset=1, limit=1)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"photos": ["b.png"], "total": 3})
        for params in ({"offset": -1}, {"limit": 0}, {"limit": 201}, {"offset": "bad"}):
            self.assertEqual(self.get("/api/photos", **params)[0], 400)
        self.assertEqual(self.get("/api/photos?limit=1&limit=2")[0], 400)

    def test_devices(self):
        status, _, body = self.get("/api/devices")
        self.assertEqual(status, 200)
        devices = json.loads(body)
        self.assertEqual((devices["blozi-1280x800"]["width"], devices["blozi-1280x800"]["height"]), (1280, 800))
        self.assertTrue(all(not d["verified"] for d in devices.values()))

    def test_rgb_image(self):
        status, headers, body = self.get("/api/image", photo="a.png", device="blozi-1280x800")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "image/png")
        self.assertEqual(int(headers["Content-Length"]), len(body))
        with Image.open(BytesIO(body)) as image:
            self.assertEqual(image.size, (1280, 800))
            self.assertEqual(image.getpixel((0, 0)), (255, 0, 0))

    def test_invalid_requests(self):
        for photo in ("../outside.png", "/etc/passwd", "broken.png"):
            self.assertEqual(self.get("/api/image", photo=photo, device="blozi-1280x800")[0], 400)
        self.assertEqual(self.get("/api/image", photo="missing.png", device="blozi-1280x800")[0], 404)
        self.assertEqual(self.get("/api/image", photo="a.png", device="unknown")[0], 400)
        self.assertEqual(self.get("/api/image", photo="a.png", device="blozi-1280x800", palette="bwr")[0], 400)
        self.assertEqual(self.get("/api/preview", photo="a.png", device="blozi-1280x800", method="invalid")[0], 400)
        self.assertEqual(self.get("/unknown")[0], 404)

    def test_web_ui_entrypoint(self):
        status, headers, body = self.get("/", token=None)
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertEqual(headers["Cache-Control"], "no-store")
        html = body.decode("utf-8")
        for control in ("token", "load", "photo", "prev", "next", "device", "palette", "method", "render", "preview"):
            self.assertIn('id="' + control + '"', html)
        for endpoint in ("/api/photos", "/api/devices", "/api/preview"):
            self.assertIn(endpoint, html)
        self.assertNotIn("test-token", html)
        self.assertEqual(self.get("/api/preview", token=None)[0], 401)

    def test_web_ui_preview_contract(self):
        status, _, body = self.get("/api/devices")
        self.assertEqual(status, 200)
        devices = json.loads(body)
        device = next(k for k in devices if k != "blozi-1280x800")
        status, headers, body = self.get("/api/preview", photo="a.png", device=device, palette="bwry", method="none")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "image/png")
        with Image.open(BytesIO(body)) as image:
            self.assertEqual(image.size, (devices[device]["width"], devices[device]["height"]))
            self.assertEqual(image.convert("RGB").getpixel((0, 0)), (255, 0, 0))
