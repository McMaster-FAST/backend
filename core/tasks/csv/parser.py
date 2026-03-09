import csv
from typing import Generator, Dict, Any
from ..utils import str_to_float


def parse_questions_from_csv(file_path: str) -> Generator[Dict[str, Any], None, None]:
    # Parse MCQs from Brightspace Question Library import CSV file.
    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)

        current_question: Dict[str, Any] | None = None

        for row in reader:
            # Skip empty rows
            if not row or not any((cell or "").strip() for cell in row):
                continue

            # Skip comment lines starting with //
            first_cell = (row[0] or "").strip()
            if first_cell.startswith("//"):
                continue

            label = first_cell

            # Start of a new question block
            if label == "NewQuestion":
                # Flush previous question
                if current_question is not None:
                    parsed = finalize_question(current_question)
                    if parsed:
                        yield parsed

                q_type = (row[1] or "").strip() if len(row) > 1 else ""

                # Only handle Multiple Choice questions for now
                if q_type != "MC":
                    current_question = None
                    continue

                current_question = {
                    "id": "",
                    "title": "",
                    "content": "",
                    "points": None,
                    "difficulty": None,
                    "options": [],
                    "option_percents": [],
                    "explanation": "",
                    "image_path": "",
                }
                continue

            # If we don't have an active MC question, ignore subsequent rows
            if current_question is None:
                continue

            # Question metadata rows
            if label == "ID" and len(row) > 1:
                current_question["id"] = (row[1] or "").strip()
            elif label == "Title" and len(row) > 1:
                current_question["title"] = (row[1] or "").strip()
            elif label == "QuestionText" and len(row) > 1:
                current_question["content"] = (row[1] or "").strip()
            elif label == "Points" and len(row) > 1:
                current_question["points"] = str_to_float(row[1], default=1.0)
            elif label == "Difficulty" and len(row) > 1:
                current_question["difficulty"] = str_to_float(row[1], default=0.0)
            elif label == "Image" and len(row) > 1:
                current_question["image_path"] = (row[1] or "").strip()
            elif label == "Feedback" and len(row) > 1:
                current_question["explanation"] = (row[1] or "").strip()
            elif label == "Option":
                # Brightspace MC Option row format:
                # [ "Option", percent, text, HTML-flag, feedback, feedback-HTML-flag ]
                percent = str_to_float(row[1], default=0.0) if len(row) > 1 else 0.0
                option_text = (row[2] or "").strip() if len(row) > 2 else ""

                if not option_text:
                    continue

                current_question["options"].append(option_text)
                current_question["option_percents"].append(percent)

        # Flush last question
        if current_question is not None:
            parsed = finalize_question(current_question)
            if parsed:
                yield parsed


def finalize_question(block: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Convert an accumulated Brightspace MC question block into our internal dict format.
    """
    content = (block.get("content") or "").strip()
    if not content:
        return None

    options = block.get("options", [])
    if not options:
        return None

    percents = block.get("option_percents") or [0.0] * len(options)

     # Determine correct option: highest percentage gets treated as correct
    max_percent = max(percents) 
    correct_index = percents.index(max_percent)
    correct_answer_letter = chr(ord("A") + correct_index)

    serial_number = (
        (block.get("id") or "").strip()
        or (block.get("title") or "").strip()
        or f"MC_{content[:50]}"
    )

    # Build images list from image path if present
    images = []
    image_path = (block.get("image_path") or "").strip()
    if image_path:
        images.append({"src": image_path, "alt": "", "ref": "image_0"})

    return {
        "serial_number": serial_number,
        "content": content,
        "explanation": block.get("explanation", ""),
        "options": options,
        "answer": correct_answer_letter,
        "comments": block.get("hint", ""),
        "images": images,
        # TODO: map unit and subtopic dynamically instead of hardcoding
        "unit": "Week 1 - Cardiovascular System: Heart Structure and Function",
        "subtopic": "Heart Wall and Pericardium",
        "unit_number": 1,
    }
