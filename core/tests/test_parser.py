import pytest
from core.models import Question, QuestionOption, QuestionImage


@pytest.mark.django_db
def test_parser_creates_questions(parsed_docx):
    questions = Question.objects.all()

    assert questions.exists()

    q = questions.first()
    assert q.content is not None
    assert q.content != ""
    assert q.difficulty is not None


@pytest.mark.django_db
def test_parser_creates_question_options(parsed_docx):
    options = QuestionOption.objects.all()

    assert options.exists()
    assert all(option.content is not None and option.content != "" for option in options)


@pytest.mark.django_db
def test_parser_creates_question_images(parsed_docx):
    images = QuestionImage.objects.all()

    assert images.exists()

    img = images.first()
    assert img.image_file is not None


@pytest.mark.django_db
def test_parser_rejects_invalid_file_format(parsed_docx):
    course = parsed_docx

    with pytest.raises(Exception):
        parse_file(
            file_name="invalid.txt",
            file_data=b"not a docx file",
            course={
                "code": course.code,
                "year": course.year,
                "semester": course.semester,
            },
            create_required=True,
        )

