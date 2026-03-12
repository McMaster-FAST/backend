from pathlib import Path
import re
from MacFAST import settings
import pypandoc
from bs4 import BeautifulSoup
from .formats import DocxDataIdentifier

from typing import Iterator, Dict, Any
from logging import getLogger

logger = getLogger(__name__)

def parse_questions_from_docx(
    file_path: str, format_spec: Dict[str, DocxDataIdentifier]
) -> Iterator[Dict[str, Any]]:
    # Wrap none required or else newlines are inserted which messes with the frontend styling
    html = pypandoc.convert_file(source_file=file_path, to="html", format="docx", extra_args=["--wrap=none"])
    soup = BeautifulSoup(html, "html.parser")
    top_level_tables = [
        t for t in soup.find_all("table")
        if t.find_parent("table") is None
    ]
    logger.info(f"Found {len(top_level_tables)} top-level tables (Questions)")
    for table in top_level_tables:
        yield extract_table_data(table, format_spec)


def extract_cell_data(cell, identifier: DocxDataIdentifier, index: int) -> Any:
    """Extract data from a cell based on the identifier specifications."""
    images = []
    html_content = ""
    if identifier.regexp:
        text = cell.get_text(strip=True)
        match = re.search(identifier.regexp, text)
        html_content = match.group(1) if match else ""
    else:

        for tag in cell.find_all("img"):
            src = tag.get("src", "")
            file_extension = Path(src).suffix
            ref = f"image_{index}{file_extension}"
            tag["src"] = ref
            image = {
                "src": src,
                "alt": tag.get("alt", ""),
                "ref": ref,
            }
            images.append(image)
        html_content = cell.decode_contents()
    return html_content.strip(), images


def get_cell(table, x: int, y: int):
    """Get a cell from the table at position (x, y)."""
    rows = table.find_all("tr")

    if y >= len(rows):
        return None

    row = rows[y]
    cells = row.find_all(["td", "th"])

    if x >= len(cells):
        return None

    return cells[x]


def extract_table_data(
    table, format_spec: Dict[str, DocxDataIdentifier]
) -> Dict[str, Any]:
    """Extract data from a table based on the format specification."""
    result = {"images": []}
    for field_name, identifier in format_spec.items():
        image_count = 0
        if identifier.range > 0:
            # Handle multi-cell ranges
            data = []
            for i in range(identifier.range):
                cell = get_cell(table, identifier.x, identifier.y + i)
                if cell:
                    content, cell_images = extract_cell_data(cell, identifier, image_count)
                    image_count += len(cell_images)
                    result["images"].extend(cell_images)
                    data.append(content)
            result[field_name] = data
        else:
            # Handle single cell
            cell = get_cell(table, identifier.x, identifier.y)
            if cell:
                content, cell_images = extract_cell_data(cell, identifier, image_count)
                image_count += len(cell_images)
                result["images"].extend(cell_images)
                result[field_name] = content
            else:
                result[field_name] = None
    return result
