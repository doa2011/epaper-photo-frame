"""Local, authenticated NAS photo HTTP API (prototype)."""
import argparse
import hmac
import json
import os
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs
from PIL import Image
from photo_catalog import PhotoCatalog
from device_profiles import PANELS
from image_pipeline import PALETTES

def make_handler(catalog, token):
    if not token:
        raise ValueError("API token required")
    class Handler(BaseHTTPRequestHandler):
        def send_data(self, status, data, mime="application/json"):
            if mime == "application/json":
                data = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format, *args):
            # Do not log private photo names or query strings.
            pass

        def do_GET(self):
            supplied = self.headers.get("Authorization", "")
            if not hmac.compare_digest(supplied.encode(), ("Bearer " + token).encode()):
                return self.send_data(401, {"error": "unauthorized"})
            try:
                url = urlsplit(self.path)
                q = parse_qs(url.query, max_num_fields=16)
                if any(len(v) != 1 for v in q.values()):
                    raise ValueError("duplicate parameter")
                def param(key, default=None):
                    return q.get(key, [default])[0]
                if url.path == "/api/health":
                    return self.send_data(200, {"status": "ok"})
                if url.path == "/api/devices":
                    devices = {k: asdict(v) for k,v in PANELS.items()}
                    devices["blozi-1280x800"] = {"width":1280,"height":800,"verified":False,"driver":"LCD"}
                    return self.send_data(200, devices)
                if url.path == "/api/photos":
                    offset, limit = int(param("offset", "0")), int(param("limit", "100"))
                    if offset < 0 or not 1 <= limit <= 200:
                        raise ValueError("invalid pagination")
                    names = catalog.list()
                    return self.send_data(200, {"photos":names[offset:offset+limit],"total":len(names)})
                if url.path in ("/api/preview", "/api/image"):
                    name = param("photo")
                    if not name:
                        raise ValueError("photo required")
                    device = param("device")
                    if device == "blozi-1280x800":
                        size, default_palette = (1280,800), "rgb"
                    elif device in PANELS:
                        p = PANELS[device]
                        size, default_palette = (p.width,p.height), "bwry"
                    else:
                        raise ValueError("unknown device")
                    palette = param("palette", default_palette)
                    method = param("method", "floyd")
                    if palette not in (*PALETTES, "rgb") or method not in ("none","floyd","bayer","atkinson"):
                        raise ValueError("invalid rendering option")
                    if url.path == "/api/image" and palette != "rgb":
                        raise ValueError("image endpoint requires rgb")
                    png, _ = catalog.render(name, size, palette=palette, method=method)
                    return self.send_data(200, png, "image/png")
                return self.send_data(404, {"error":"not found"})
            except (ValueError, KeyError, RuntimeError, Image.DecompressionBombError):
                return self.send_data(400, {"error":"invalid request or image"})
            except FileNotFoundError:
                return self.send_data(404, {"error":"photo not found"})
            except OSError:
                return self.send_data(400, {"error":"unreadable image"})
    return Handler

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--photos", required=True)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080)
    a = p.parse_args()
    handler = make_handler(PhotoCatalog(a.photos), os.environ.get("PHOTO_API_TOKEN"))
    with HTTPServer((a.host,a.port), handler) as server:
        server.serve_forever()

if __name__ == "__main__":
    main()
