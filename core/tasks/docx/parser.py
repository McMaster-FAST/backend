import unicodedata
from docx import Document
from docx.table import Table
from typing import Iterator
import re
import os

from docx.opc.constants import RELATIONSHIP_TYPE as RT

def parse_questions_from_docx(document: Document, format: dict, tmpdirname: str) -> Iterator[dict]:
    image_parts = {rel.rId: rel.target_part for rel in document.part.rels.values() if rel.reltype == RT.IMAGE}
    for idx, table in enumerate(document.tables):
        question_data = parse_table(table, format, idx, image_parts, tmpdirname)
        yield question_data
    
def parse_table(table: Table, format: dict, table_idx: int, image_parts: dict, tmpdirname: str) -> dict:
    """
    Parses question data from a docx table using the given format.
    """
    table_data = {}
    for key, identifier in format.items():
        if identifier.range == 0: # Single cell
            col_idx, row_idx = identifier.x, identifier.y
            cell = table.cell(row_idx, col_idx)
            if identifier.images:
                value = parse_cell_with_images(cell, table_idx, key, image_parts, tmpdirname)
            else:
                value = extract_text_from_cell(cell, identifier.regexp)
            table_data[key] = value

        elif identifier.range > 0: # Range of cells
            start_col, start_row, num_items = identifier.x, identifier.y, identifier.range
            items = []
            for i in range(num_items):
                cell = table.cell(start_row + i, start_col)
                if identifier.images:
                    value = parse_cell_with_images(cell, table_idx, key, image_parts, tmpdirname)
                else:
                    value = extract_text_from_cell(cell, identifier.regexp)
                items.append(value)
                
            table_data[key] = items
    return table_data

def extract_text_from_cell(cell, regexp: str) -> str:
    value = cell.text.strip()
    if regexp is None:
        return value
    # There might be odd characters like em dahses instead of hyphens; normalize them
    value = unicodedata.normalize("NFKC", value)
    print(f"Extracting with regexp '{regexp}' from value: {value}")
    match = re.search(regexp, value)
    return match.group(1) if match else ""

def parse_cell_with_images(cell, table_idx, key, image_parts, tmpdirname) -> str:
    """
    Extract text from a cell, inserting placeholders for images.
    """
    content = ""
    img_count = 0
    os.makedirs(f"{tmpdirname}/{table_idx}", exist_ok=True)
    for para in cell.paragraphs:
        for run in para.runs:
            # Check for inline images in this run

            blips = run._element.findall(
                ".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
            )
            for blip in blips:
                rId = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                if rId in image_parts:
                    img_count += 1
                    content += f"[{key}_image_{img_count}]"
                    ext = image_parts[rId].content_type.split('/')[-1]
                    filename = f"{key}_image{img_count}.{ext}"
                    with open(f"{tmpdirname}/{table_idx}/{filename}", "wb") as f:
                        f.write(image_parts[rId].blob)
            
            # Append the text from the run
            content += run.text
        content += "\n"  # End of paragraph

    return content
