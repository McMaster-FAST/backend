class DocxDataIdentifier:
    def __init__(self, x, y, cells_range=0, regexp=None):
        """
            An identifier for data in a Word Doc Table

            :param x: The column index of the cell.
            :param y: The row index of the cell.
            :param cells_range: The number of cells to consider. From (x, y) to (x, y + cells_range - 1).
            :param regexp: Regular expression to extract specific data from cell text.
        """
        self.x = x
        self.y = y
        self.range = cells_range
        self.regexp = regexp

docx_table_format_a = {
    "question_number": DocxDataIdentifier(1, 0),
    "serial_number": DocxDataIdentifier(1, 1),
    "unit_number": DocxDataIdentifier(1, 2, regexp=r"^(.*?)\."),
    "unit": DocxDataIdentifier(1, 2, regexp=r" (.*) - "),
    "subtopic": DocxDataIdentifier(1, 2, regexp=r" - (.*)$"),
    "content": DocxDataIdentifier(1, 4),
    "options": DocxDataIdentifier(1, 5, cells_range=4),
    "option_selection_frequencies": DocxDataIdentifier(2, 5, cells_range=4),
    "answer": DocxDataIdentifier(1, 9),
    "explanation": DocxDataIdentifier(1, 10),
    "comments": DocxDataIdentifier(1, 11)
}
