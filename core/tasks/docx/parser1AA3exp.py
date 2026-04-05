from docx import Document
from docx.oxml.ns import qn
import hashlib
import html
import os
import re
from pathlib import Path
from lxml import etree
from docx.table import Table

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


MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_OMML_XSLT = None

def get_omml_xslt():
    global _OMML_XSLT
    if _OMML_XSLT is None:
        xsl_path = Path(__file__).with_name("omml2mml.xsl")
        xslt_doc = etree.parse(str(xsl_path))
        _OMML_XSLT = etree.XSLT(xslt_doc)
    return _OMML_XSLT


def omml_element_to_mathml(omml_el) -> str:
    try:
        transform = get_omml_xslt()

        # Wrap the OMML node in a tiny XML document so the XSLT has a stable root
        wrapper_xml = (
            b'<root xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">'
            + etree.tostring(omml_el)
            + b"</root>"
        )
        wrapper_doc = etree.fromstring(wrapper_xml)

        result = transform(wrapper_doc)
        mathml = str(result).strip()

        # remove xml declaration if present
        if mathml.startswith("<?xml"):
            mathml = mathml.split("?>", 1)[1].strip()

        return mathml
    except Exception as e:
        raw = etree.tostring(omml_el, encoding="unicode")
        return f'<span data-math-fallback="omml-error">{html.escape(str(e))}</span><span data-math-fallback="omml">{html.escape(raw)}</span>'


SYMBOL_MAP = {
    "": "ν",
    "": "0",
    "": "1",
    "": "2",
    "": "3",
    "": "4",
    "": "5",
    "": "6",
    "": "7",
    "": "8",
    "": "9",
}
WINGDINGS_MAP = {
    "à": "→",
    "á": "←",
    "â": "↑",
    "ã": "↓",
    "ä": "↔",
}

def convert_wingdings(text: str) -> str:
    return "".join(WINGDINGS_MAP.get(c, c) for c in text)

def normalize_symbol_text(text: str, font: str | None) -> str:
    if not text:
        return text
    #Wingdings font
    if font and "Wingdings" in font:
        text = convert_wingdings(text)
        
    text = "".join(SYMBOL_MAP.get(c, c) for c in text)

    return text

def run_element_to_html(run_element) -> str:
    parts = []

    rpr_list = run_element.xpath("./*[local-name()='rPr']")
    rpr = rpr_list[0] if rpr_list else None

    font = None
    if rpr is not None:
        rfonts = rpr.xpath("./*[local-name()='rFonts']")
        if rfonts:
            rfonts_el = rfonts[0]
            font = (
                rfonts_el.get(qn("w:ascii"))
                or rfonts_el.get(qn("w:hAnsi"))
                or rfonts_el.get(qn("w:cs"))
                or ""
            )

    is_subscript = False
    is_superscript = False
    is_underlined = False
    is_bold = False
    is_italic = False

    if rpr is not None:
        if rpr.xpath("./*[local-name()='vertAlign' and @*[local-name()='val']='subscript']"):
            is_subscript = True
        if rpr.xpath("./*[local-name()='vertAlign' and @*[local-name()='val']='superscript']"):
            is_superscript = True
        if rpr.xpath("./*[local-name()='u']"):
            is_underlined = True
        if rpr.xpath("./*[local-name()='b']"):
            is_bold = True
        if rpr.xpath("./*[local-name()='i']"):
            is_italic = True

    for t in run_element.xpath("./*[local-name()='t']"):
        txt = t.text or ""
        txt = normalize_symbol_text(txt, font)
        txt = html.escape(txt)

        if is_subscript:
            txt = f"<sub>{txt}</sub>"
        if is_superscript:
            txt = f"<sup>{txt}</sup>"
        if is_underlined:
            txt = f"<u>{txt}</u>"
        if is_bold:
            txt = f"<strong>{txt}</strong>"
        if is_italic:
            txt = f"<em>{txt}</em>"

        parts.append(txt)

    for _ in run_element.xpath("./*[local-name()='tab']"):
        parts.append("&emsp;")

    for _ in run_element.xpath("./*[local-name()='br']"):
        parts.append("<br>")

    return "".join(parts)


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
    nested_table_counter = 0

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

    tc = cell._tc

    for child in tc.iterchildren():
        local = etree.QName(child).localname
        ns = etree.QName(child).namespace

        # paragraph
        if ns == WORD_NS and local == "p":
            p_parts = []

            for p_child in child.iterchildren():
                p_local = etree.QName(p_child).localname
                p_ns = etree.QName(p_child).namespace

                if p_ns == WORD_NS and p_local == "r":
                    p_parts.append(run_element_to_html(p_child))

                    for blip in p_child.xpath(".//*[local-name()='blip']"):
                        rid = blip.get(qn("r:embed"))
                        ref = add_image_rid(rid)
                        if ref:
                            p_parts.append(ref)

                    for imagedata in p_child.xpath(".//*[local-name()='imagedata']"):
                        rid = imagedata.get(qn("r:id"))
                        ref = add_image_rid(rid)
                        if ref:
                            p_parts.append(ref)

                elif p_ns == MATH_NS and p_local in {"oMath", "oMathPara"}:
                    p_parts.append(omml_element_to_mathml(p_child))

            paragraph_html = "".join(p_parts).strip()
            if paragraph_html:
                parts.append(f"<p>{paragraph_html}</p>")

        # nested table in correct position
        elif ns == WORD_NS and local == "tbl":
            nested_table_counter += 1
            nested_tbl = Table(child, cell._parent)
            nested_html, nested_images = extract_table_html_and_images(
                doc,
                nested_tbl,
                f"{prefix}_tbl{nested_table_counter}",
            )
            parts.append(nested_html)
            images.extend(nested_images)

    return "".join(parts).strip(), images




def collapse_single_paragraph(cell_html: str) -> str:
    m = re.fullmatch(r"<p>(.*?)</p>", cell_html.strip(), flags=re.DOTALL)
    return m.group(1) if m else cell_html

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
            images.extend(cell_images)

            # remove <p> wrapper if simple (cleaner tables)
            cell_html = collapse_single_paragraph(cell_html)

            # first row = header
            tag = "th" if r == 1 else "td"

            cells_html.append(f'<{tag} class="mf-cell">{cell_html}</{tag}>')

        rows_html.append(f"<tr>{''.join(cells_html)}</tr>")

    html = (
        '<div class="mf-table-wrap">'
        '<table class="mf-table">'
        f"{''.join(rows_html)}"
        "</table>"
        "</div>"
    )

    return html, images


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
            #some solution files have 2 columns and some have 3 for question table.
        if not (len(qtbl.rows) == 5 and len(qtbl.columns) in (2, 3)):
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