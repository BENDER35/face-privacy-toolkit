#!/usr/bin/env python3
"""Face Privacy Toolkit - privacy-focused image utilities.

Legitimate uses: protect your own photos, audit metadata, find local duplicates,
and generate manual reverse-image search links for images you own.

This tool does NOT identify people, scrape social networks, or perform
biometric matching against online profiles.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus

try:
    from PIL import Image, ImageFilter, ImageOps
    from PIL.ExifTags import TAGS
except Exception as exc:  # pragma: no cover
    print("Missing dependency: Pillow. Install with: pip install -r requirements.txt", file=sys.stderr)
    raise

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None


SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


@dataclass
class Region:
    x: int
    y: int
    w: int
    h: int

    @classmethod
    def parse(cls, value: str) -> "Region":
        parts = [p.strip() for p in value.split(",")]
        if len(parts) != 4:
            raise argparse.ArgumentTypeError("Region must be x,y,w,h")
        try:
            x, y, w, h = [int(p) for p in parts]
        except ValueError as exc:
            raise argparse.ArgumentTypeError("Region values must be integers") from exc
        if w <= 0 or h <= 0:
            raise argparse.ArgumentTypeError("Region width/height must be > 0")
        return cls(x=x, y=y, w=w, h=h)


def iter_images(path: Path) -> Iterable[Path]:
    if path.is_file():
        if path.suffix.lower() in SUPPORTED:
            yield path
        return
    for p in sorted(path.rglob("*")):
        if p.is_file() and p.suffix.lower() in SUPPORTED:
            yield p


def cmd_exif(args: argparse.Namespace) -> int:
    path = Path(args.image)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    with Image.open(path) as img:
        exif = img.getexif()
        data = {}
        if exif:
            for k, v in exif.items():
                name = TAGS.get(k, str(k))
                try:
                    data[name] = v if isinstance(v, (int, float, str)) else str(v)
                except Exception:
                    data[name] = "<unreadable>"

    if args.clean:
        out = Path(args.output) if args.output else path.with_name(path.stem + ".clean" + path.suffix)
        with Image.open(path) as img:
            clean = ImageOps.exif_transpose(img)
            clean.save(out)
        print(f"Clean image written: {out}")
        return 0

    if args.json:
        print(json.dumps({"file": str(path), "exif": data}, ensure_ascii=False, indent=2))
    else:
        print(f"File: {path}")
        if not data:
            print("No EXIF metadata found.")
        for k in sorted(data):
            print(f"- {k}: {data[k]}")
    return 0


def ahash(image: Image.Image, size: int = 8) -> int:
    if np is None:
        # Fallback without numpy: compare grayscale pixels to mean.
        pixels = list(image.convert("L").resize((size, size)).getdata())
        mean = sum(pixels) / len(pixels)
        bits = 0
        for i, px in enumerate(pixels):
            if px >= mean:
                bits |= 1 << i
        return bits
    arr = np.asarray(image.convert("L").resize((size, size)), dtype=np.float32)
    mean = arr.mean()
    bits = (arr >= mean).flatten()
    value = 0
    for i, b in enumerate(bits):
        if b:
            value |= 1 << i
    return int(value)


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def cmd_hash(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"Path not found: {target}", file=sys.stderr)
        return 2
    images = list(iter_images(target))
    if not images:
        print("No supported images found.")
        return 1
    records = []
    for p in images:
        try:
            with Image.open(p) as img:
                records.append((p, ahash(img)))
        except Exception as exc:
            print(f"Skipping {p}: {exc}", file=sys.stderr)

    if args.compare:
        other = Path(args.compare)
        if not other.exists():
            print(f"Compare file not found: {other}", file=sys.stderr)
            return 2
        with Image.open(other) as img:
            target_hash = ahash(img)
        rows = []
        for p, h in records:
            dist = hamming(target_hash, h)
            rows.append((dist, p))
        rows.sort(key=lambda x: x[0])
        print(f"Comparing against: {other}")
        for dist, p in rows[: args.limit]:
            verdict = "likely-similar" if dist <= args.threshold else "different"
            print(f"{dist:>3}  {verdict:>14}  {p}")
        return 0

    for p, h in records:
        print(f"{h:016x}  {p}")
    return 0


def cmd_search_links(args: argparse.Namespace) -> int:
    # No scraping, no API calls: generate URLs for manual review by the owner.
    image = Path(args.image)
    if not image.exists():
        print(f"File not found: {image}", file=sys.stderr)
        return 2
    public_url = args.public_url
    engines = {
        "google_lens": "https://lens.google.com/uploadbyurl?url={url}",
        "bing_visual": "https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIIRP&sbisrc=UrlPaste&q=imgurl:{url}",
        "yandex_images": "https://yandex.com/images/search?rpt=imageview&url={url}",
        "tineye": "https://tineye.com/search?url={url}",
    }
    print("Manual reverse-image search links (no scraping, no automatic identification):")
    print(f"Local image: {image.resolve()}")
    if public_url:
        enc = quote_plus(public_url)
        for name, tpl in engines.items():
            print(f"- {name}: {tpl.format(url=enc)}")
        print("\nNote: public_url must point to an image you own and are allowed to publish.")
    else:
        print("Provide --public-url with an image URL you control to get direct engine links.")
        print("You can also open these engines and upload the local file manually:")
        print("- Google Lens: https://lens.google.com/")
        print("- Bing Visual Search: https://www.bing.com/visualsearch")
        print("- Yandex Images: https://yandex.com/images/")
        print("- TinEye: https://tineye.com/")
    return 0


def detect_faces_opencv(img: Image.Image) -> list[Region]:
    try:
        import cv2  # type: ignore
    except Exception:
        return []
    arr = np.asarray(img.convert("RGB")) if np is not None else None
    if arr is None:
        # Minimal fallback via Pillow->bytes; cv2 can decode from file, but here we have image.
        import io

        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG")
        data = np.frombuffer(buf.getvalue(), dtype=np.uint8)
        arr = cv2.imdecode(data, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
    else:
        bgr = arr[:, :, ::-1].copy()
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(str(cascade_path))
    if detector.empty():
        return []
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return [Region(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]


def cmd_redact(args: argparse.Namespace) -> int:
    src = Path(args.image)
    if not src.exists():
        print(f"File not found: {src}", file=sys.stderr)
        return 2
    out = Path(args.output) if args.output else src.with_name(src.stem + ".redacted" + src.suffix)
    regions = list(args.region or [])
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        if args.auto:
            detected = detect_faces_opencv(img)
            if not detected:
                print("Automatic face detection unavailable or no faces found.")
                print("Install optional dependency: pip install opencv-python-headless")
                if not regions:
                    print("No regions provided; nothing changed.")
                    return 1
            else:
                print(f"Detected {len(detected)} face region(s).")
                regions.extend(detected)
        if not regions:
            print("No regions to redact. Use --auto or --region x,y,w,h", file=sys.stderr)
            return 2
        for r in regions:
            box = (max(0, r.x), max(0, r.y), min(img.width, r.x + r.w), min(img.height, r.y + r.h))
            if box[2] <= box[0] or box[3] <= box[1]:
                continue
            crop = img.crop(box)
            crop = crop.filter(ImageFilter.GaussianBlur(radius=args.blur))
            # Pixelate for stronger anonymization
            small = crop.resize((max(1, crop.width // args.pixelate), max(1, crop.height // args.pixelate)), Image.NEAREST)
            crop = small.resize(crop.size, Image.NEAREST)
            img.paste(crop, box)
        img.save(out)
    print(f"Redacted image written: {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="face-privacy", description="Privacy-focused image toolkit. No social scraping, no biometric identification.")
    sub = p.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("exif", help="Show or remove EXIF metadata")
    ex.add_argument("image")
    ex.add_argument("--json", action="store_true", help="Output JSON")
    ex.add_argument("--clean", action="store_true", help="Write image without EXIF metadata")
    ex.add_argument("--output", help="Output path for --clean")
    ex.set_defaults(func=cmd_exif)

    h = sub.add_parser("hash", help="Compute perceptual hashes or compare local images")
    h.add_argument("path", help="Image file or directory")
    h.add_argument("--compare", help="Compare all images in path against this image")
    h.add_argument("--threshold", type=int, default=10, help="Hamming distance threshold for likely-similar")
    h.add_argument("--limit", type=int, default=20, help="Max results for --compare")
    h.set_defaults(func=cmd_hash)

    s = sub.add_parser("search-links", help="Generate manual reverse-image search links for an image you own")
    s.add_argument("image")
    s.add_argument("--public-url", help="Public URL of the image you own/control")
    s.set_defaults(func=cmd_search_links)

    r = sub.add_parser("redact", help="Blur/pixelate faces or regions for privacy")
    r.add_argument("image")
    r.add_argument("--output", help="Output path")
    r.add_argument("--auto", action="store_true", help="Auto-detect faces (requires opencv-python-headless)")
    r.add_argument("--region", action="append", type=Region.parse, help="Region x,y,w,h. Can be repeated")
    r.add_argument("--blur", type=float, default=12.0, help="Gaussian blur radius")
    r.add_argument("--pixelate", type=int, default=12, help="Pixelation factor")
    r.set_defaults(func=cmd_redact)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
