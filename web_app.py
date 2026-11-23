#!/usr/bin/env python3
"""Local web UI for Face Privacy Toolkit.

Runs on localhost and processes files locally. No social scraping, no biometric identification.
"""
from __future__ import annotations

import html
import io
import os
import secrets
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from PIL import Image, ImageOps

import face_privacy as fp

MAX_UPLOAD = 15 * 1024 * 1024
TMP = Path(os.environ.get("FACE_PRIVACY_TMP", "/tmp/opencode/face-privacy-web"))
TMP.mkdir(parents=True, exist_ok=True)


def page(title: str, body: str, msg: str = "") -> bytes:
    notice = f'<div class="msg">{html.escape(msg)}</div>' if msg else ""
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:980px;margin:2rem auto;padding:0 1rem;background:#f6f7f9;color:#1b1f24}}
.card{{background:#fff;border:1px solid #d7dde5;border-radius:10px;padding:1rem;margin:1rem 0}}
label{{display:block;margin:.5rem 0 .2rem;font-weight:600}} input,button{{font:inherit;padding:.45rem .6rem}}
input[type=text],input[type=number],input[type=file]{{width:100%;max-width:520px}}
button{{background:#1f6feb;color:#fff;border:0;border-radius:6px;cursor:pointer}} button:hover{{background:#1858bd}}
.msg{{background:#eef6ff;border:1px solid #b9d7ff;padding:.7rem;border-radius:8px;margin:1rem 0}}
pre{{background:#111827;color:#e5e7eb;padding:1rem;border-radius:8px;overflow:auto}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem}}
small{{color:#57606a}} .warn{{color:#8a1f11}}
nav a{{margin-right:1rem}}
</style></head><body>
<h1>Face Privacy Toolkit</h1>
<p><small>Local, privacy-focused image utilities. No social scraping, no biometric identification, no online profile matching.</small></p>
<nav><a href="/">Home</a><a href="/exif">EXIF</a><a href="/redact">Redact</a><a href="/hash">Local Hash</a><a href="/search-links">Manual Search Links</a></nav>
{notice}
{body}
</body></html>"""
    return doc.encode("utf-8")


def parse_multipart(handler: BaseHTTPRequestHandler):
    ctype = handler.headers.get("Content-Type", "")
    if "multipart/form-data" not in ctype:
        return {}, {}
    # Extract boundary
    boundary = None
    for part in ctype.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary = part.split("=", 1)[1].strip('"')
    if not boundary:
        return {}, {}
    length = int(handler.headers.get("Content-Length", "0"))
    if length > MAX_UPLOAD:
        raise ValueError("Upload too large (max 15MB)")
    body = handler.rfile.read(length)
    sep = ("--" + boundary).encode()
    fields, files = {}, {}
    for chunk in body.split(sep):
        if not chunk or chunk in (b"--\r\n", b"--"):
            continue
        if chunk.startswith(b"\r\n"):
            chunk = chunk[2:]
        if chunk.endswith(b"\r\n"):
            chunk = chunk[:-2]
        if b"\r\n\r\n" not in chunk:
            continue
        head, data = chunk.split(b"\r\n\r\n", 1)
        headers = head.decode("utf-8", "ignore")
        name = filename = None
        for line in headers.split("\r\n"):
            if line.lower().startswith("content-disposition:"):
                for p in line.split(";"):
                    p = p.strip()
                    if p.startswith("name="):
                        name = p.split("=", 1)[1].strip('"')
                    if p.startswith("filename="):
                        filename = p.split("=", 1)[1].strip('"')
        if filename and name:
            files[name] = (filename, data)
        elif name:
            fields[name] = data.decode("utf-8", "ignore")
    return fields, files


def save_upload(files, key="image"):
    if key not in files:
        return None
    filename, data = files[key]
    if not data:
        return None
    ext = Path(filename).suffix.lower() or ".bin"
    if ext not in fp.SUPPORTED:
        raise ValueError("Unsupported image type")
    path = TMP / f"up-{secrets.token_hex(8)}{ext}"
    path.write_bytes(data)
    return path


class Handler(BaseHTTPRequestHandler):
    def _send(self, status=200, content=b"", ctype="text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path == "/":
            body = """
<div class="grid">
  <div class="card"><h2>EXIF</h2><p>Inspect or remove metadata from an image.</p><a href="/exif">Open</a></div>
  <div class="card"><h2>Redact</h2><p>Blur/pixelate a manual region. Optional auto-detect requires OpenCV.</p><a href="/redact">Open</a></div>
  <div class="card"><h2>Local Hash</h2><p>Compute a perceptual hash for a local image. No online lookup.</p><a href="/hash">Open</a></div>
  <div class="card"><h2>Manual Search Links</h2><p>Generate reverse-image links for images you own/control.</p><a href="/search-links">Open</a></div>
</div>
<div class="card warn"><strong>Ethics/legal:</strong> Use only with images you own or have permission to process. Do not use for identifying or tracking people without consent.</div>
"""
            return self._send(200, page("Face Privacy Toolkit", body))
        if self.path == "/exif":
            return self._send(200, page("EXIF", self._form_exif()))
        if self.path == "/redact":
            return self._send(200, page("Redact", self._form_redact()))
        if self.path == "/hash":
            return self._send(200, page("Local Hash", self._form_hash()))
        if self.path == "/search-links":
            return self._send(200, page("Manual Search Links", self._form_links()))
        if self.path.startswith("/file/"):
            name = Path(self.path.rsplit("/", 1)[-1]).name
            p = TMP / name
            if not p.exists():
                return self._send(404, page("Not found", "<div class='card'>File not found.</div>"))
            data = p.read_bytes()
            ctype = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
            return self._send(200, data, ctype)
        return self._send(404, page("Not found", "<div class='card'>Not found.</div>"))

    def do_POST(self):
        try:
            fields, files = parse_multipart(self)
        except Exception as e:
            return self._send(400, page("Error", "<div class='card'>Bad request.</div>", str(e)))
        try:
            if self.path == "/exif":
                return self._handle_exif(fields, files)
            if self.path == "/redact":
                return self._handle_redact(fields, files)
            if self.path == "/hash":
                return self._handle_hash(fields, files)
            if self.path == "/search-links":
                return self._handle_links(fields, files)
        except Exception as e:
            return self._send(400, page("Error", f"<div class='card'>Error: {html.escape(str(e))}</div>"))
        return self._send(404, page("Not found", "<div class='card'>Not found.</div>"))

    def _form_exif(self):
        return """<div class="card"><form method="post" enctype="multipart/form-data">
<label>Image</label><input type="file" name="image" accept="image/*" required>
<label><input type="checkbox" name="clean" value="1"> Remove EXIF and return clean image</label>
<button type="submit">Process</button></form></div>"""

    def _form_redact(self):
        return """<div class="card"><form method="post" enctype="multipart/form-data">
<label>Image</label><input type="file" name="image" accept="image/*" required>
<label><input type="checkbox" name="auto" value="1"> Try auto face detection (needs opencv-python-headless)</label>
<label>Region x,y,w,h (optional)</label><input type="text" name="region" placeholder="120,80,140,140">
<label>Blur radius</label><input type="number" name="blur" value="12" min="1" max="60">
<label>Pixelate factor</label><input type="number" name="pixelate" value="12" min="1" max="60">
<button type="submit">Redact</button></form></div>"""

    def _form_hash(self):
        return """<div class="card"><form method="post" enctype="multipart/form-data">
<label>Image</label><input type="file" name="image" accept="image/*" required>
<button type="submit">Compute hash</button></form></div>"""

    def _form_links(self):
        return """<div class="card"><form method="post" enctype="multipart/form-data">
<label>Image (local reference only; not uploaded to search engines by this app)</label><input type="file" name="image" accept="image/*" required>
<label>Public URL you own/control (optional)</label><input type="text" name="public_url" placeholder="https://example.com/photo.jpg">
<button type="submit">Generate links</button></form></div>"""

    def _handle_exif(self, fields, files):
        p = save_upload(files)
        if not p:
            raise ValueError("No image uploaded")
        with Image.open(p) as img:
            exif = img.getexif()
            data = {}
            if exif:
                for k, v in exif.items():
                    name = fp.TAGS.get(k, str(k))
                    data[name] = v if isinstance(v, (int, float, str)) else str(v)
        if fields.get("clean") == "1":
            out = TMP / f"clean-{secrets.token_hex(8)}.jpg"
            with Image.open(p) as img:
                ImageOps.exif_transpose(img).convert("RGB").save(out, format="JPEG", quality=92)
            return self._send(200, page("EXIF", f"<div class='card'><p>Clean image created.</p><p><a href='/file/{out.name}'>Download/view clean image</a></p></div>"))
        rows = "".join(f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>" for k, v in sorted(data.items()))
        table = f"<table border='1' cellpadding='6' cellspacing='0'><tr><th>Tag</th><th>Value</th></tr>{rows}</table>" if rows else "<p>No EXIF metadata found.</p>"
        return self._send(200, page("EXIF", f"<div class='card'><h2>EXIF</h2>{table}</div>"))

    def _handle_redact(self, fields, files):
        p = save_upload(files)
        if not p:
            raise ValueError("No image uploaded")
        regions = []
        reg = fields.get("region", "").strip()
        if reg:
            regions.append(fp.Region.parse(reg))
        with Image.open(p) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            if fields.get("auto") == "1":
                regions.extend(fp.detect_faces_opencv(img))
            if not regions:
                raise ValueError("No regions found/provided. Add a region or enable auto with OpenCV installed.")
            blur = float(fields.get("blur", "12") or 12)
            pix = int(fields.get("pixelate", "12") or 12)
            for r in regions:
                box = (max(0,r.x), max(0,r.y), min(img.width,r.x+r.w), min(img.height,r.y+r.h))
                if box[2]<=box[0] or box[3]<=box[1]: continue
                crop = img.crop(box).filter(fp.ImageFilter.GaussianBlur(radius=blur))
                small = crop.resize((max(1,crop.width//pix), max(1,crop.height//pix)), Image.NEAREST)
                img.paste(small.resize(crop.size, Image.NEAREST), box)
            out = TMP / f"redacted-{secrets.token_hex(8)}.jpg"
            img.save(out, format="JPEG", quality=92)
        return self._send(200, page("Redact", f"<div class='card'><p>Redacted image created.</p><img src='/file/{out.name}' style='max-width:100%;height:auto'><p><a href='/file/{out.name}'>Open image</a></p></div>"))

    def _handle_hash(self, fields, files):
        p = save_upload(files)
        if not p:
            raise ValueError("No image uploaded")
        with Image.open(p) as img:
            h = fp.ahash(img)
        return self._send(200, page("Local Hash", f"<div class='card'><p>Perceptual hash (aHash): <code>{h:016x}</code></p><p><small>Local-only hash. Not an identity, not an online lookup.</small></p></div>"))

    def _handle_links(self, fields, files):
        p = save_upload(files)
        if not p:
            raise ValueError("No image uploaded")
        public_url = fields.get("public_url", "").strip()
        engines = {
            "Google Lens": "https://lens.google.com/uploadbyurl?url={url}",
            "Bing Visual": "https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIIRP&sbisrc=UrlPaste&q=imgurl:{url}",
            "Yandex Images": "https://yandex.com/images/search?rpt=imageview&url={url}",
            "TinEye": "https://tineye.com/search?url={url}",
        }
        items = []
        if public_url:
            from urllib.parse import quote_plus
            enc = quote_plus(public_url)
            for n, tpl in engines.items():
                url = tpl.format(url=enc)
                items.append(f"<li><a href='{html.escape(url)}' target='_blank' rel='noopener'>{html.escape(n)}</a></li>")
            extra = "<p><small>Only use URLs for images you own/control.</small></p>"
        else:
            for n, url in [("Google Lens","https://lens.google.com/"),("Bing Visual Search","https://www.bing.com/visualsearch"),("Yandex Images","https://yandex.com/images/"),("TinEye","https://tineye.com/")]:
                items.append(f"<li><a href='{url}' target='_blank' rel='noopener'>{n}</a> (manual upload)</li>")
            extra = "<p><small>Provide a public URL you control for direct links, or upload manually on these sites.</small></p>"
        return self._send(200, page("Manual Search Links", f"<div class='card'><p>Local file: <code>{html.escape(str(p.name))}</code></p><ul>{''.join(items)}</ul>{extra}</div>"))

    def log_message(self, fmt, *args):
        pass


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Face Privacy Toolkit web UI: http://{host}:{port}")
    print("Local processing only. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
