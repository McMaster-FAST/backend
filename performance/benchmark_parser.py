import os
import sys
import django
import time
from statistics import mean
from pathlib import Path
import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MacFAST.settings")
django.setup()

from courses.models import Course, Unit
from core.models import Question
from core.tasks.parse_questions import parse_file


FILE_PATH = "tests/fixtures/1AA3_questions_archive_to2024_organic.docx"
RUNS = 10


def run_benchmark():
    with open(FILE_PATH, "rb") as f:
        file_bytes = f.read()

    course, _ = Course.objects.get_or_create(
        code="TESTCHEM1AA3",
        year=2024,
        semester="FALL",
        defaults={"name": "Test Course"},
    )

    runtimes = []

    for i in range(RUNS):
        print(f"\nRun {i+1}/{RUNS}")

        # clean DB before each run
        Question.objects.all().delete()
        Unit.objects.all().delete()

        start = time.perf_counter()

        parse_file(
            file_name="1AA3_questions_archive_to2024_organic.docx",
            file_data=file_bytes,
            course={
                "code": course.code,
                "year": course.year,
                "semester": course.semester,
            },
            create_required=True,
        )

        end = time.perf_counter()
        duration = end - start

        print(f"Runtime: {duration:.2f} seconds")
        runtimes.append(duration)

    avg = mean(runtimes)

    print("\n--- RESULTS ---")
    print("All runs:", [round(r, 2) for r in runtimes])
    print(f"Average runtime: {avg:.2f} seconds")

    return avg


if __name__ == "__main__":
    run_benchmark()