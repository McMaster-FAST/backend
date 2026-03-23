from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile

from docx.shared import RGBColor

BLUE = RGBColor(0x00, 0x00, 0xFF)
LETTER_RE = re.compile(r"^\s*([A-D])\s*[\)\.\:]?\s*$", re.IGNORECASE)


def _find_image_command() -> str | None:
    for cmd in ("magick", "convert"):
        if shutil.which(cmd):
            return cmd
    return None


def _convert_emf_wmf_bytes_to_png(image_bytes: bytes, extension: str) -> tuple[bytes, str]:
    """
    Convert EMF/WMF bytes to PNG.

    Tries:
    1. LibreOffice headless
    2. ImageMagick (magick or convert)

    Returns (bytes, extension). Falls back to original if conversion fails.
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
                    return f.read(), ".png"

            print("LibreOffice conversion failed")
            print("command:", [office, "--headless", "--convert-to", "png", src_path, "--outdir", tmpdir])
            print("returncode:", res.returncode)
            print("stdout:", res.stdout)
            print("stderr:", res.stderr)

        # 2) ImageMagick
        img_cmd = shutil.which("magick") or shutil.which("convert")
        if img_cmd:
            dst_path = os.path.join(tmpdir, "image.png")
            res = subprocess.run(
                [img_cmd, src_path, dst_path],
                capture_output=True,
                text=True,
            )

            if res.returncode == 0 and os.path.exists(dst_path):
                with open(dst_path, "rb") as f:
                    return f.read(), ".png"

            print("ImageMagick conversion failed")
            print("command:", [img_cmd, src_path, dst_path])
            print("returncode:", res.returncode)
            print("stdout:", res.stdout)
            print("stderr:", res.stderr)

        return image_bytes, extension
