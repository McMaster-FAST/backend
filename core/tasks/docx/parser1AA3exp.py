from docx import Document
from docx.oxml.ns import qn
import hashlib
import html
import os
import re


def build_lookup_serial(file_name: str, qnum: int) -> str:
    """
    Example:
    1AA3_2020_T2_solutions.docx -> T2_2020_Q14
    """

    m = re.search(r"_(\d{4})_(T\d)", file_name)
    if not m:
        raise ValueError(f"Cannot parse year/term from filename: {file_name}")

    year = m.group(1)
    term = m.group(2)

    return f"{term}_{year}_Q{int(qnum):02d}"


def normalize_text(text: str) -> str:
    return (text or "").replace("\xa0", " ").strip()


def get_cell_text(cell) -> str:
    parts = []
    for p in cell.paragraphs:
        txt = normalize_text(p.text)
        if txt:
            parts.append(txt)
    return "\n".join(parts).strip()


def _convert_emf_wmf_bytes_to_png(data: bytes, ext: str) -> tuple[bytes, str]:
    from core.tasks.docx.parser1AA3 import _convert_emf_wmf_bytes_to_png as convert_fn
    return convert_fn(data, ext)


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

    # nested tables inside explanation cell
    for ti, tbl in enumerate(cell.tables, start=1):
        nested_html, nested_images = extract_table_html_and_images(doc, tbl, f"{prefix}_tbl{ti}")
        parts.append(nested_html)
        images.extend(nested_images)

    return "".join(parts).strip(), images


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


def parse_explanation_updates(docx_path: str, file_name: str) -> list[dict]:
    """
    format:
    table i   = question table
    table i+1 = explanation table

    Returns:
    [
        {
            "serial_number": "T2_2020_Q14",
            "answer_explanation": "<p>...</p>",
            "explanation_images": [...],
        },
        ...
    ]
    """
    doc = Document(docx_path)
    updates = []

    i = 0
    while i < len(doc.tables):
        qtbl = doc.tables[i]

        # old question tables are usually 5x3 in your earlier parser
        if not (len(qtbl.rows) == 5 and len(qtbl.columns) == 3):
            i += 1
            continue

        qnum_text = normalize_text(qtbl.cell(0, 0).text).rstrip(".")
        qnum_match = re.search(r"\d+", qnum_text)
        if not qnum_match:
            i += 1
            continue

        qnum = int(qnum_match.group())

        explanation_html = ""
        explanation_images = []

        if i + 1 < len(doc.tables):
            etbl = doc.tables[i + 1]

            # explanation table is the following 1x1 table
            if len(etbl.rows) == 1 and len(etbl.columns) == 1:
                explanation_html, explanation_images = extract_cell_html_and_images(
                    doc,
                    etbl.cell(0, 0),
                    f"q{qnum}_expl",
                )

        updates.append({
            "serial_number": build_lookup_serial(file_name, qnum),
            "answer_explanation": explanation_html,
            "explanation_images": explanation_images,
        })

        i += 2

    return updates