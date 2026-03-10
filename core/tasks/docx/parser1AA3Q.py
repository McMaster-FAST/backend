# from docx import Document
# import re

# def normalize_label(text: str) -> str:
#     return " ".join(text.strip().split())

# def get_cell_text(cell) -> str:
#     parts = []
#     for p in cell.paragraphs:
#         txt = p.text.strip()
#         if txt:
#             parts.append(txt)
#     return "\n".join(parts).strip()

# def table_to_html(tbl) -> str:
#     rows_html = []
#     for row in tbl.rows:
#         cells_html = []
#         seen = set()
#         for cell in row.cells:
#             tc_id = id(cell._tc)
#             if tc_id in seen:
#                 continue
#             seen.add(tc_id)

#             text = get_cell_text(cell)
#             nested = "".join(table_to_html(t) for t in cell.tables)
#             content = (text + nested).strip()
#             cells_html.append(f"<td>{content}</td>")
#         rows_html.append(f"<tr>{''.join(cells_html)}</tr>")
#     return f"<table>{''.join(rows_html)}</table>"

# def cell_to_html(cell) -> str:
#     parts = []
#     for p in cell.paragraphs:
#         txt = p.text.strip()
#         if txt:
#             parts.append(f"<p>{txt}</p>")
#     for tbl in cell.tables:
#         parts.append(table_to_html(tbl))
#     return "".join(parts).strip()

# def parse_selection_frequency(text: str) -> float:
#     text = (text or "").strip().lstrip("*").strip()
#     try:
#         return float(text) if text else 0.0
#     except ValueError:
#         return 0.0

# def extract_serial_base(serial_text: str, qnum: int) -> str:
#     m = re.match(r"^(T\d+_\d{4}_Q\d+)", serial_text.strip())
#     if m:
#         return m.group(1)
#     return f"Q{qnum}"

# def extract_difficulty(serial_text: str) -> float:
#     m = re.search(r"_D(\d+)", serial_text or "")
#     if not m:
#         return 0.0

#     raw = m.group(1)
#     return float(raw) / 100.0

# def parse(docx_path: str) -> list[dict]:
#     doc = Document(docx_path)
#     questions = []

#     for tbl in doc.tables:
#         if not tbl.rows or len(tbl.rows[0].cells) < 2:
#             continue

#         first_label = normalize_label(tbl.cell(0, 0).text)
#         if first_label != "Q#:":
#             continue

#         qnum_text = get_cell_text(tbl.cell(0, 1))
#         qnum_match = re.search(r"\d+", qnum_text)
#         if not qnum_match:
#             continue
#         qnum = int(qnum_match.group())

#         row_map = {}
#         option_rows = {}

#         for row in tbl.rows:
#             if len(row.cells) < 2:
#                 continue

#             label = normalize_label(row.cells[0].text)
#             if label in {"Q#:", "Serial #:", "Unit", "Used", "Stem", "Ans:", "Variants", "Comments"}:
#                 row_map[label] = row
#             elif re.fullmatch(r"[A-D]\)", label):
#                 option_rows[label[0]] = row

#         serial_text = get_cell_text(row_map["Serial #:"].cells[1]) if "Serial #:" in row_map else ""
#         unit_text = get_cell_text(row_map["Unit"].cells[1]) if "Unit" in row_map else ""
#         stem_html = cell_to_html(row_map["Stem"].cells[1]) if "Stem" in row_map else ""
#         ans_text = get_cell_text(row_map["Ans:"].cells[1]) if "Ans:" in row_map else ""

#         options = []
#         for letter in ["A", "B", "C", "D"]:
#             row = option_rows.get(letter)
#             if not row:
#                 continue

#             option_text = get_cell_text(row.cells[1]) if len(row.cells) > 1 else ""
#             freq_text = get_cell_text(row.cells[2]) if len(row.cells) > 2 else ""

#             options.append({
#                 "letter": letter,
#                 "content": option_text,
#                 "images": [],
#                 "is_answer": ans_text.strip().upper() == letter,
#                 "selection_frequency": parse_selection_frequency(freq_text),
#             })

#         questions.append({
#             "number": qnum,
#             "serial_number": serial_text.strip(),   # exact value from file
#             "content": stem_html,
#             "content_images": [],
#             "options": options,
#             "answer_explanation": "",
#             "explanation_images": [],
#             "subtopic_name": unit_text.strip(),
#             "difficulty": extract_difficulty(serial_text),
#         })

#     return questions

from docx import Document
from docx.oxml.ns import qn
import hashlib
import html
import os
import re


def normalize_label(text: str) -> str:
    return " ".join(text.strip().split())


def get_cell_text(cell) -> str:
    parts = []
    for p in cell.paragraphs:
        txt = p.text.strip()
        if txt:
            parts.append(txt)
    return "\n".join(parts).strip()


def parse_selection_frequency(text: str) -> float:
    text = (text or "").strip().lstrip("*").strip()
    try:
        return float(text) if text else 0.0
    except ValueError:
        return 0.0

def parse_unit_and_subtopic(unit_text: str):
    if not unit_text:
        return None, None, None

    m = re.match(r"(\d+)\.(\d+)\s+(.+?)\s*-\s*(.+)", unit_text.strip())

    if not m:
        return None, None, None

    unit_number = int(m.group(1))
    unit_name = m.group(3).strip()
    subtopic_name = m.group(4).strip()

    return unit_number, unit_name, subtopic_name

def extract_difficulty(serial_text: str) -> float:
    m = re.search(r"_D(\d+)", serial_text or "")
    if not m:
        return 0.0
    return float(m.group(1)) / 100.0


def _convert_emf_wmf_bytes_to_png(data: bytes, ext: str) -> tuple[bytes, str]:
    from core.tasks.docx.parser1AA3 import _convert_emf_wmf_bytes_to_png as convert_fn
    return convert_fn(data, ext)


def extract_table_html_and_images(doc: Document, tbl, prefix: str) -> tuple[str, list[dict]]:
    rows_html = []
    images = []

    for r, row in enumerate(tbl.rows, start=1):
        cells_html = []
        seen_tcs = set()

        for c, cell in enumerate(row.cells, start=1):
            tc_id = id(cell._tc)
            if tc_id in seen_tcs:
                continue
            seen_tcs.add(tc_id)

            cell_html, cell_images = extract_cell_html_and_images(
                doc,
                cell,
                f"{prefix}_r{r}_c{c}",
            )
            cells_html.append(f"<td>{cell_html}</td>")
            images.extend(cell_images)

        rows_html.append(f"<tr>{''.join(cells_html)}</tr>")

    return f"<table>{''.join(rows_html)}</table>", images


def extract_cell_html_and_images(doc: Document, cell, prefix: str) -> tuple[str, list[dict]]:
    parts = []
    images = []
    seen_keys = set()
    img_counter = 0

    def add_image_rid(rid: str) -> str:
        nonlocal img_counter

        if not rid:
            return ""

        part = doc.part.related_parts.get(rid)
        if not part:
            return ""

        content_type = getattr(part, "content_type", "") or ""
        if not content_type.startswith("image/"):
            return ""

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
            return ""

        data = part.blob
        data, ext = _convert_emf_wmf_bytes_to_png(data, ext)

        digest = hashlib.sha256(data).hexdigest()
        key = (rid, digest)
        if key in seen_keys:
            return ""
        seen_keys.add(key)

        img_counter += 1
        ref = f"[[IMG:{prefix}_{img_counter}]]"
        name = f"{prefix}_{img_counter}{ext}"

        images.append({
            "name": name,
            "bytes": data,
            "extension": ext,
            "ref": ref,
        })
        return ref

    for p in cell.paragraphs:
        p_parts = []

        for run in p.runs:
            if run.text:
                p_parts.append(html.escape(run.text))

            run_element = run._r

            for blip in run_element.xpath(".//*[local-name()='blip']"):
                rid = blip.get(qn("r:embed"))
                ref = add_image_rid(rid)
                if ref:
                    p_parts.append(ref)

            for imagedata in run_element.xpath(".//*[local-name()='imagedata']"):
                rid = imagedata.get(qn("r:id"))
                ref = add_image_rid(rid)
                if ref:
                    p_parts.append(ref)

            for _ in run_element.xpath("./*[local-name()='br']"):
                p_parts.append("<br>")

        paragraph_html = "".join(p_parts).strip()
        if paragraph_html:
            parts.append(f"<p>{paragraph_html}</p>")

    for ti, tbl in enumerate(cell.tables, start=1):
        nested_html, nested_images = extract_table_html_and_images(
            doc,
            tbl,
            f"{prefix}_tbl{ti}",
        )
        parts.append(nested_html)
        images.extend(nested_images)

    return "".join(parts).strip(), images


def parse(docx_path: str) -> list[dict]:
    doc = Document(docx_path)
    questions = []

    for tbl in doc.tables:
        if not tbl.rows or len(tbl.rows[0].cells) < 2:
            continue

        first_label = normalize_label(tbl.cell(0, 0).text)
        if first_label != "Q#:":
            continue

        qnum_text = get_cell_text(tbl.cell(0, 1))
        qnum_match = re.search(r"\d+", qnum_text)
        if not qnum_match:
            continue
        qnum = int(qnum_match.group())

        row_map = {}
        option_rows = {}

        for row in tbl.rows:
            if len(row.cells) < 2:
                continue

            label = normalize_label(row.cells[0].text)
            if label in {"Q#:", "Serial #:", "Unit", "Used", "Stem", "Ans:", "Variants", "Comments"}:
                row_map[label] = row
            elif re.fullmatch(r"[A-D]\)", label):
                option_rows[label[0]] = row

        serial_text = get_cell_text(row_map["Serial #:"].cells[1]) if "Serial #:" in row_map else ""
        unit_text = get_cell_text(row_map["Unit"].cells[1]) if "Unit" in row_map else ""
        unit_number, unit_name, subtopic_name = parse_unit_and_subtopic(unit_text)
        ans_text = get_cell_text(row_map["Ans:"].cells[1]) if "Ans:" in row_map else ""

        stem_html = ""
        stem_images = []
        if "Stem" in row_map:
            stem_html, stem_images = extract_cell_html_and_images(
                doc,
                row_map["Stem"].cells[1],
                f"q{qnum}_stem",
            )

        options = []
        for letter in ["A", "B", "C", "D"]:
            row = option_rows.get(letter)
            if not row:
                continue

            option_html = ""
            option_images = []
            if len(row.cells) > 1:
                option_html, option_images = extract_cell_html_and_images(
                    doc,
                    row.cells[1],
                    f"q{qnum}_opt_{letter}",
                )

            freq_text = get_cell_text(row.cells[2]) if len(row.cells) > 2 else ""

            options.append({
                "letter": letter,
                "content": option_html,
                "images": option_images,
                "is_answer": ans_text.strip().upper() == letter,
                "selection_frequency": parse_selection_frequency(freq_text),
            })

        questions.append({
            "number": qnum,
            "serial_number": serial_text.strip(),
            "content": stem_html,
            "content_images": stem_images,
            "options": options,
            "answer_explanation": "",
            "explanation_images": [],
            "unit_number": unit_number,
            "unit_name": unit_name,
            "subtopic_name": subtopic_name,
            "difficulty": extract_difficulty(serial_text),
        })

    return questions