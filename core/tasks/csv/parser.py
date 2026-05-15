import csv
from typing import Generator, Dict, Any
from ..utils import str_to_float


# -----------------------------------------------------------------------------
# CSV Parser
# -----------------------------------------------------------------------------

def parse_questions_from_csv(file_path: str) -> Generator[Dict[str, Any], None, None]:

    def get(row, i: int, default: str = "") -> str:
        return row[i].strip() if len(row) > i and row[i] else default

    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)

        q = None  # current question block

        for row in reader:
            if not row:
                continue

            label = get(row, 0)

            if label.startswith("//"):
                continue

            # -----------------------------------------------------------------
            # Start new question
            # -----------------------------------------------------------------
            if label == "NewQuestion":
                if q:
                    out = finalize_question(q)
                    if out:
                        yield out

                if get(row, 1) != "MC":
                    q = None
                    continue

                q = {
                    "id": "",
                    "title": "",
                    "content": "",
                    "points": 1.0,
                    "difficulty": 0.0,
                    "options": [],
                    "option_percents": [],
                    "option_explanations": [],
                    "explanation": "",
                    "image_path": "",
                }
                continue

            if q is None:
                continue

            # -----------------------------------------------------------------
            # Option row
            # -----------------------------------------------------------------
            if label == "Option":
                if len(row) >= 3:
                    q["options"].append(get(row, 2))
                    q["option_percents"].append(str_to_float(row[1], 0.0))
                    q["option_explanations"].append(get(row, 4))
                continue

            # -----------------------------------------------------------------
            # Metadata rows 
            # -----------------------------------------------------------------
            if label == "ID":
                q["id"] = get(row, 1)

            elif label == "Title":
                q["title"] = get(row, 1)

            elif label == "QuestionText":
                q["content"] = get(row, 1)

            elif label == "Image":
                q["image_path"] = get(row, 1)

            elif label == "Feedback":
                q["explanation"] = get(row, 1)

            elif label == "Points":
                q["points"] = str_to_float(row[1], 1.0) if len(row) > 1 else 1.0

            elif label == "Difficulty":
                q["difficulty"] = str_to_float(row[1], 0.0) if len(row) > 1 else 0.0

        # ---------------------------------------------------------------------
        # Flush last question
        # ---------------------------------------------------------------------
        if q:
            out = finalize_question(q)
            if out:
                yield out


# -----------------------------------------------------------------------------
# Question ID parsing
# -----------------------------------------------------------------------------

def parse_question_id(question_id: str) -> Dict[str, Any]:
    parts = question_id.split("-")

    def safe_float(x: str) -> float:
        try:
            return float(x)
        except Exception:
            return 0.0

    return {
        "source": parts[0] if len(parts) > 0 else "",
        "unit_tag": parts[1] if len(parts) > 1 else "",
        "subtopic_tag": parts[2] if len(parts) > 2 else "",
        "descriptor": parts[3] if len(parts) > 3 else "",
        "q_num": safe_float(parts[4][1:]) if len(parts) > 4 and parts[4].startswith("Q") else 0.0,
        "blooms": parts[5] if len(parts) > 5 else "",
        "difficulty": safe_float(parts[6]) if len(parts) > 6 else 0.0,
    }


# -----------------------------------------------------------------------------
# Finalizer
# -----------------------------------------------------------------------------

def finalize_question(block: Dict[str, Any]) -> Dict[str, Any] | None:
    get = block.get

    content = (get("content") or "").strip()
    if not content:
        return None

    options = get("options") or []
    if not options:
        return None

    percents = get("option_percents") or [0.0] * len(options)

    explanations = get("option_explanations") or []
    if len(explanations) < len(options):
        explanations += [""] * (len(options) - len(explanations))
    explanations = explanations[:len(options)]

    max_percent = max(percents)
    correct_index = percents.index(max_percent)
    answer = chr(ord("A") + correct_index)

    raw_id = (get("id") or "").strip()
    title = (get("title") or "").strip()

    serial_number = raw_id or title or f"MC_{content[:50]}"

    parsed = parse_question_id(raw_id) if raw_id else {}

    image_path = (get("image_path") or "").strip()
    images = [{"src": image_path, "alt": "", "ref": "image_0"}] if image_path else []

    return {
        "serial_number": serial_number,
        "content": content,
        "explanation": get("explanation", ""),
        "option_explanations": explanations,
        "options": options,
        "answer": answer,
        "comments": get("hint", ""),
        "images": images,
        "unit_tag": parsed.get("unit_tag", ""),
        "subtopic_tag": parsed.get("subtopic_tag", ""),
        "source_tag": parsed.get("source", ""),
        "descriptor_tag": parsed.get("descriptor", ""),
        "q_num_tag": parsed.get("q_num", 0.0),
        "blooms_tag": parsed.get("blooms", ""),
        "difficulty": parsed.get("difficulty", 0.0),
    }