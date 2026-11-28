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

WEB_UI = "<!doctype html>\n<html lang=\"zh-CN\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n<title>电子相册</title><style>body{font:16px system-ui;max-width:900px;margin:2rem auto;padding:0 1rem}label{display:block;margin:.7rem 0}select,input,button{font:inherit;max-width:100%;padding:.4rem}img{max-width:100%;height:auto}#status{white-space:pre-wrap}</style>\n<h1>电子相册 · 本地预览</h1><label>API Token <input id=\"token\" type=\"password\" autocomplete=\"off\"></label><button id=\"load\">读取照片和设备</button>\n<label>照片 <select id=\"photo\"></select></label><button id=\"prev\">上一页</button> <button id=\"next\">下一页</button>\n<label>设备 <select id=\"device\"></select></label><label>颜色 <select id=\"palette\"><option value=\"\">设备默认</option><option>rgb</option><option>bw</option><option>bwr</option><option>bwy</option><option>bwry</option></select></label>\n<label>抖动 <select id=\"method\"><option>floyd</option><option>bayer</option><option>atkinson</option><option>none</option></select></label><button id=\"render\">生成预览</button><p id=\"status\" role=\"status\"></p><img id=\"preview\" alt=\"照片预览\">\n<script>\nconst el=id=>document.getElementById(id); let offset=0,total=0,oldUrl=null,busy=false;\nasync function api(path,params={}){const r=await fetch(path+'?'+new URLSearchParams(params),{headers:{Authorization:'Bearer '+el('token').value},cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);return r}\nfunction options(id,values){el(id).replaceChildren(...values.map(([v,t])=>new Option(t,v)))}\nasync function page(){const data=await (await api('/api/photos',{offset,limit:100})).json();total=data.total;options('photo',data.photos.map(x=>[x,x]));el('status').textContent='照片 '+total+' 张；当前偏移 '+offset}\nasync function run(fn){if(busy)return;busy=true;try{await fn()}catch(e){el('status').textContent=e.message}finally{busy=false}}\nel('load').onclick=()=>run(async()=>{offset=0;const d=await (await api('/api/devices')).json();options('device',Object.entries(d).map(([k,v])=>[k,k+' '+v.width+'×'+v.height]));await page()});\nel('prev').onclick=()=>run(async()=>{offset=Math.max(0,offset-100);await page()});\nel('next').onclick=()=>run(async()=>{if(offset+100<total){offset+=100;await page()}});\nel('render').onclick=()=>run(async()=>{el('status').textContent='正在转换…';const p={photo:el('photo').value,device:el('device').value,method:el('method').value};if(el('palette').value)p.palette=el('palette').value;const b=await (await api('/api/preview',p)).blob();const u=URL.createObjectURL(b);const image=new Image();image.src=u;try{await image.decode()}catch(e){URL.revokeObjectURL(u);throw e}el('preview').src=u;if(oldUrl)URL.revokeObjectURL(oldUrl);oldUrl=u;el('status').textContent='预览完成（非实机显示）'});\n</script></html>"

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
            if self.path == "/":
                return self.send_data(200, WEB_UI.encode("utf-8"), "text/html; charset=utf-8")
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
