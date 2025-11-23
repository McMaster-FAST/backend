from docx import Document
from typing import Iterator
import re

def parse_questions_from_docx(document: Document, format: dict) -> Iterator[dict]:
    for table in document.tables:
        print([tuple(c.text for c in r.cells) for r in table.rows])
        yield parse_table(table, format)

def parse_table(table, format) -> dict:
    table_data = {}
    for key, identifier in format.items():
        if identifier.range == 0: # Single cell
            col_idx, row_idx = identifier.x, identifier.y
            cell = table.cell(row_idx, col_idx)
            value = cell.text.strip()

            if identifier.regexp is not None:
                match = re.search(identifier.regexp, cell.text.strip())
                value = match.group(1) if match else ""

            table_data[key] = value

        elif identifier.range > 0: # Range of cells
            start_col, start_row, num_items = identifier.x, identifier.y, identifier.range
            items = []
            for i in range(num_items):
                cell = table.cell(start_row + i, start_col)
                value = cell.text.strip()
                if identifier.regexp is not None:
                    match = re.search(identifier.regexp, cell.text.strip())
                    value = match.group(1) if match else ""

                items.append(value)
                
            table_data[key] = items
    return table_data