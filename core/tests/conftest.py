import pytest
from courses.models import Course, Unit
from core.models import Question
from core.tasks.parse_questions import parse_file


@pytest.fixture(scope="module")
def sample_docx_file_bytes():
    with open("core/tests/fixtures/1AA3_questions_archive_to2024_organic.docx", "rb") as f:
        return f.read()


@pytest.fixture(scope="module")
def parsed_docx(django_db_setup, django_db_blocker, sample_docx_file_bytes):
    with django_db_blocker.unblock():
        course, _ = Course.objects.get_or_create(
            code="TESTCHEM1AA3",
            year=2024,
            semester="FALL",
            defaults={"name": "Test Course"},
        )

        Question.objects.all().delete()
        Unit.objects.all().delete()

        parse_file.run(
            "1AA3_questions_archive_to2024_organic.docx",
            sample_docx_file_bytes,
            {
                "code": course.code,
                "year": course.year,
                "semester": course.semester,
            },
            1, 
            True,
        )

        return course