from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from io import BytesIO

from docx.shared import RGBColor
from PIL import Image, ImageChops

BLUE = RGBColor(0x00, 0x00, 0xFF)
LETTER_RE = re.compile(r"^\s*([A-D])\s*[\)\.\:]?\s*$", re.IGNORECASE)


def _trim_png_canvas(png_bytes: bytes) -> bytes:
    """
    Drop excess margin LibreOffice/ImageMagick often leave around EMF/WMF exports.

    Uses alpha bbox when margins are transparent; otherwise trims against the most
    common corner colour (typical uniform white / light page background).
    """
    try:
        im = Image.open(BytesIO(png_bytes))
    except OSError:
        return png_bytes

    rgba = im.convert("RGBA")
    alpha = rgba.split()[3]
    bbox = alpha.getbbox()
    if bbox and bbox != (0, 0, rgba.width, rgba.height):
        cropped = rgba.crop(bbox)
    else:
        rgb = rgba.convert("RGB")
        corners = [
            rgb.getpixel((0, 0)),
            rgb.getpixel((rgb.width - 1, 0)),
            rgb.getpixel((0, rgb.height - 1)),
            rgb.getpixel((rgb.width - 1, rgb.height - 1)),
        ]
        bg = max(set(corners), key=corners.count)
        diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, bg))
        bbox = diff.getbbox()
        if not bbox or bbox == (0, 0, rgb.width, rgb.height):
            return png_bytes
        cropped = rgba.crop(bbox)

    out = BytesIO()
    cropped.save(out, format="PNG", optimize=True)
    return out.getvalue()

def normalize_embedded_docx_image_bytes(image_bytes: bytes, extension: str) -> tuple[bytes, str]:
    """Normalize DOCX embeddings that browsers mishandle (.tif, .emf, .wmf) → PNG."""
    ext = extension.lower()
    if ext in {".tif", ".tiff"}:
        return _convert_tiff_bytes_to_png(image_bytes, extension)
    return _convert_emf_wmf_bytes_to_png(image_bytes, extension)

def _convert_tiff_bytes_to_png(image_bytes: bytes, extension: str) -> tuple[bytes, str]:
    """
    Convert TIFF bytes to PNG.
    """
    ext = extension.lower()
    if ext not in {".tif", ".tiff"}:
        return image_bytes, extension

    try:
        with Image.open(BytesIO(image_bytes)) as im:
            if getattr(im, "n_frames", 1) > 1:
                im.seek(0)
            if im.mode not in {"RGB", "RGBA"}:
                im = im.convert("RGBA")

            out = BytesIO()
            im.save(out, format="PNG", optimize=True)
            return out.getvalue(), ".png"
    except OSError:
        return image_bytes, extension

def _convert_emf_wmf_bytes_to_png(image_bytes: bytes, extension: str) -> tuple[bytes, str]:
    """
    Convert EMF/WMF bytes to PNG.
    Tries:
    1. LibreOffice headless
    2. ImageMagick (magick or convert)

    Returns (bytes, extension). Falls back to original if conversion fails.
    Successful PNG output is cropped to remove large empty margins from export.
    """
    ext = extension.lower()
    if ext not in (".emf", ".wmf"):
        return image_bytes, extension

    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, f"image{ext}")
        with open(src_path, "wb") as f:
            f.write(image_bytes)

        # 1) LibreOffice / soffice
        office = shutil.which("libreoffice") or shutil.which("soffice")
        if office:
            res = subprocess.run(
                [
                    office,
                    "--headless",
                    "--convert-to", "png",
                    src_path,
                    "--outdir", tmpdir,
                ],
                capture_output=True,
                text=True,
            )

            dst_path = os.path.join(tmpdir, "image.png")
            if res.returncode == 0 and os.path.exists(dst_path):
                with open(dst_path, "rb") as f:
                    raw_png = f.read()
                return _trim_png_canvas(raw_png), ".png"

            print("LibreOffice conversion failed")
            print("command:", [office, "--headless", "--convert-to", "png", src_path, "--outdir", tmpdir])
            print("returncode:", res.returncode)
            print("stdout:", res.stdout)
            print("stderr:", res.stderr)

        # # 2) ImageMagick
        # img_cmd = shutil.which("magick") or shutil.which("convert")
        # if img_cmd:
        #     dst_path = os.path.join(tmpdir, "image.png")
        #     res = subprocess.run(
        #         [img_cmd, src_path, dst_path],
        #         capture_output=True,
        #         text=True,
        #     )

        #     if res.returncode == 0 and os.path.exists(dst_path):
        #         with open(dst_path, "rb") as f:
        #             raw_png = f.read()
        #         return _trim_png_canvas(raw_png), ".png"

        #     print("ImageMagick conversion failed")
        #     print("command:", [img_cmd, src_path, dst_path])
        #     print("returncode:", res.returncode)
        #     print("stdout:", res.stdout)
        #     print("stderr:", res.stderr)

        return image_bytes, extension
