from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from typing import Dict, List

from bs4 import BeautifulSoup, Tag
from docx import Document
from docx.shared import RGBColor
from docx.oxml.ns import qn

BLUE = RGBColor(0x00, 0x00, 0xFF)
LETTER_RE = re.compile(r"^\s*([A-D])\s*[\)\.\:]?\s*$", re.IGNORECASE)


def _cell_has_blue_run(cell) -> bool:
    for p in cell.paragraphs:
        for r in p.runs:
            if r.font.color and r.font.color.rgb == BLUE:
                return True
    return False


def extract_correct_from_docx(docx_path: str) -> Dict[str, str]:
    doc = Document(docx_path)
    correct_map: Dict[str, str] = {}

    i = 0
    while i < len(doc.tables):
        t = doc.tables[i]

        if not (len(t.rows) == 5 and len(t.columns) == 3):
            i += 1
            continue

        qnum = (t.cell(0, 0).text or "").strip().rstrip(".")
        if not qnum:
            i += 1
            continue

        found = ""
        for r in range(1, 5):
            letter = (t.cell(r, 1).text or "").strip().replace(")", "").upper()
            if letter not in ("A", "B", "C", "D"):
                continue
            if _cell_has_blue_run(t.cell(r, 2)):
                found = letter
                break

        if found:
            correct_map[qnum] = found

        i += 2

    return correct_map


def run_pandoc(docx_path: str, html_path: str, extract_root: str) -> None:
    os.makedirs(extract_root, exist_ok=True)
    res = subprocess.run(
        [
            "pandoc",
            docx_path,
            "--from", "docx",
            "--to", "html5",
            "--no-highlight",
            "--mathjax",
            f"--extract-media={extract_root}",
            "-o", html_path,
        ],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"pandoc failed:\n{res.stderr}")


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


def _cell_inner_html(td: Tag) -> str:
    return (td.decode_contents() or "").strip()


def _table_shape(table: Tag) -> tuple[int, int]:
    trs = table.find_all("tr")
    max_cols = 0
    for tr in trs:
        max_cols = max(max_cols, len(tr.find_all(["td", "th"])))
    return len(trs), max_cols


def parse_questions_from_html(html: str) -> List[dict]:
    """
    Parse the Pandoc HTML into question text/options/explanations only.
    Images are handled separately from DOCX cells.
    """
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")

    out: List[dict] = []
    qnum_re = re.compile(r"^\s*(\d+)\s*\.\s*$")

    i = 0
    while i < len(tables):
        t = tables[i]
        rows, max_cols = _table_shape(t)

        if rows != 5 or max_cols < 3:
            i += 1
            continue

        trs = t.find_all("tr")
        first_cells = trs[0].find_all(["td", "th"])
        if len(first_cells) < 3:
            i += 1
            continue

        m = qnum_re.match(first_cells[0].get_text(" ", strip=True))
        if not m:
            i += 1
            continue
        qnum = m.group(1)

        stem_html = _cell_inner_html(first_cells[1]) or _cell_inner_html(first_cells[2])

        options = []
        for r in range(1, 5):
            cells = trs[r].find_all(["td", "th"])
            if len(cells) < 3:
                continue

            mm = LETTER_RE.match(cells[1].get_text(" ", strip=True))
            if not mm:
                continue

            letter = mm.group(1).upper()
            options.append({
                "letter": letter,
                "content": _cell_inner_html(cells[2]),
                "is_answer": False,
                "images": [],
            })

        explanation_html = ""
        if i + 1 < len(tables):
            t2 = tables[i + 1]
            cells2 = t2.find_all(["td", "th"])
            if len(cells2) == 1:
                explanation_html = _cell_inner_html(cells2[0])

        out.append({
            "number": qnum,
            "content": stem_html,
            "options": options,
            "answer_explanation": explanation_html,
            "images": [],
        })
        i += 2

    return out


def _extract_images_from_docx_cell(doc: Document, cell, prefix: str) -> list[dict]:
    """
    Extract embedded images directly from a python-docx table cell.
    This works even when Pandoc does not emit an <img> tag.
    Dedupes exact duplicate images within the same cell only.
    """
    images = []
    seen_rids = set()
    seen_hashes = set()

    def add_rid(rid: str):
        if not rid or rid in seen_rids:
            return
        seen_rids.add(rid)

        part = doc.part.related_parts.get(rid)
        if not part:
            return

        content_type = getattr(part, "content_type", "") or ""
        if not content_type.startswith("image/"):
            return

        partname = str(getattr(part, "partname", ""))
        ext = os.path.splitext(partname)[1].lower()

        if not ext:
            content_type_map = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/gif": ".gif",
                "image/bmp": ".bmp",
                "image/tiff": ".tif",
                "image/x-emf": ".emf",
                "image/emf": ".emf",
                "image/x-wmf": ".wmf",
                "image/wmf": ".wmf",
            }
            ext = content_type_map.get(content_type, "")

        if not ext:
            return

        data = part.blob
        data, ext = _convert_emf_wmf_bytes_to_png(data, ext)

        digest = hashlib.sha256(data).hexdigest()
        if digest in seen_hashes:
            return
        seen_hashes.add(digest)

        img_index = len(images) + 1
        name = f"{prefix}_{img_index}{ext}"
        images.append({
            "name": name,
            "bytes": data,
            "extension": ext,
            "ref": f"[[IMG:{prefix}_{img_index}]]",
        })

    tc = cell._tc

    for blip in tc.xpath(".//*[local-name()='blip']"):
        rid = blip.get(qn("r:embed"))
        if rid:
            add_rid(rid)

    for imagedata in tc.xpath(".//*[local-name()='imagedata']"):
        rid = imagedata.get(qn("r:id"))
        if rid:
            add_rid(rid)

    return images

def extract_docx_images_v3(docx_path: str) -> dict[str, dict]:
    """
    Returns:
    {
        "1": {
            "question_images": [...],
            "explanation_images": [...],
            "option_images": {
                "A": [...],
                "B": [...],
                "C": [...],
                "D": [...],
            }
        },
        ...
    }
    """
    doc = Document(docx_path)
    out: dict[str, dict] = {}

    i = 0
    while i < len(doc.tables):
        qtbl = doc.tables[i]

        if not (len(qtbl.rows) == 5 and len(qtbl.columns) == 3):
            i += 1
            continue

        qnum = (qtbl.cell(0, 0).text or "").strip().rstrip(".")
        if not qnum:
            i += 1
            continue

        question_images = []
        explanation_images = []
        option_images = {"A": [], "B": [], "C": [], "D": []}

        # Stem/header row images
        question_images.extend(
            _extract_images_from_docx_cell(doc, qtbl.cell(0, 1), f"q{qnum}_stem_1")
        )
        question_images.extend(
            _extract_images_from_docx_cell(doc, qtbl.cell(0, 2), f"q{qnum}_stem_2")
        )

        # Option images (rows 1..4, text column is 2)
        for r in range(1, 5):
            letter = (qtbl.cell(r, 1).text or "").strip().replace(")", "").upper()
            if letter in option_images:
                option_images[letter].extend(
                    _extract_images_from_docx_cell(doc, qtbl.cell(r, 2), f"q{qnum}_opt_{letter}")
                )

        # Explanation table follows
        if i + 1 < len(doc.tables):
            etbl = doc.tables[i + 1]
            if len(etbl.rows) == 1 and len(etbl.columns) == 1:
                explanation_images.extend(
                    _extract_images_from_docx_cell(doc, etbl.cell(0, 0), f"q{qnum}_expl")
                )

        out[qnum] = {
            "question_images": question_images,
            "explanation_images": explanation_images,
            "option_images": option_images,
        }

        i += 2

    return out

import hashlib

def dedupe_image_dicts(images: list[dict]) -> list[dict]:
    seen = set()
    out = []

    for img in images:
        data = img.get("bytes")
        name = img.get("name", "")
        if not data:
            continue

        key = (hashlib.sha256(data).hexdigest(), name.split(".")[-1].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(img)

    return out

def replace_img_tags_with_placeholders(html: str, images: list[dict]) -> str:
    """
    Replace existing <img> tags with image refs in order, preserving position.
    """
    soup = BeautifulSoup(html or "", "html.parser")
    img_tags = soup.find_all("img")

    for img_tag, image in zip(img_tags, images):
        img_tag.replace_with(image["ref"])

    return str(soup)

# def parse_v3(docx_path: str) -> List[dict]:
#     with tempfile.TemporaryDirectory() as tmpdir:
#         html_path = os.path.join(tmpdir, "temp.html")
#         extract_root = os.path.join(tmpdir, "public")

#         run_pandoc(docx_path, html_path, extract_root)

#         with open(html_path, "r", encoding="utf-8") as f:
#             html = f.read()

#         questions = parse_questions_from_html(html)
#         correct_map = extract_correct_from_docx(docx_path)
#         docx_image_map = extract_docx_images_v3(docx_path)

#         for q in questions:
#             qnum = str(q["number"])
#             correct = correct_map.get(qnum, "")
#             fallback = docx_image_map.get(qnum, {})

#             if qnum == "14":
#                 print("Q14 fallback explanation refs:")
#                 print([img["ref"] for img in fallback.get("explanation_images", [])])

#             q["content_images"] = dedupe_image_dicts(fallback.get("question_images", []))
#             q["explanation_images"] = dedupe_image_dicts(fallback.get("explanation_images", []))

#             q["content"] = replace_img_tags_with_placeholders(
#                 q.get("content", ""),
#                 q["content_images"],
#             )
#             q["answer_explanation"] = replace_img_tags_with_placeholders(
#                 q.get("answer_explanation", ""),
#                 q["explanation_images"],
#             )

#             for img in q["content_images"]:
#                 if img["ref"] not in q["content"]:
#                     q["content"] += img["ref"]

#             for img in q["explanation_images"]:
#                 if img["ref"] not in q["answer_explanation"]:
#                     q["answer_explanation"] += img["ref"]

#             for opt in q["options"]:
#                 opt["is_answer"] = (opt["letter"] == correct)
#                 opt["images"] = dedupe_image_dicts(fallback.get("option_images", {}).get(opt["letter"], []))

#                 opt["content"] = replace_img_tags_with_placeholders(
#                     opt.get("content", ""),
#                     opt["images"],
#                 )

#                 for img in opt["images"]:
#                     if img["ref"] not in opt["content"]:
#                         opt["content"] += img["ref"]

#         return questions