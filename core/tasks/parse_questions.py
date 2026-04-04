from zipfile import ZipFile
from celery import shared_task
from io import BytesIO

from django.db import IntegrityError, transaction
from django.core.files.images import ImageFile
from core.models import Question, QuestionComment, QuestionOption, QuestionImage
from core.tasks.upload_result_util import finish_upload_result, get_upload_result, update_upload_result
from courses.models import Course, QuestionUploadResult, Enrolment, Unit, UnitSubtopic
from .docx.parser import get_question_table_count, parse_questions_from_docx
from .docx.formats import docx_table_format_a

import tempfile
import traceback

from math import log
import re
from logging import getLogger

logger = getLogger(__name__)
decimal_pattern = re.compile(r"\d?\.\d{0,5}")

PROGRESS_UPDATE_INTERVAL = 0.1


class DocxParsingError(Exception):
    pass


@shared_task
def parse_file(
    file_name: str,
    file_data: bytes,
    course_data: dict,
    uploading_user_id: int,
    create_required: bool,
    upload_result_id: str,
) -> None:
    """
    Celery task to parse uploaded question bank files. Determines file type and processes accordingly.

    :param file_name: Name of the uploaded file.
    :param file_data: Byte content of the uploaded file.
    :param course_data: Dictionary containing course identifiers (code, year, semester).
    :param uploading_user_id: The ID of the user who is uploading the file.
    :param create_required: Create all required related entities if they do not exist, with the exception of Course.
    """
    success_count = 0
    failure_count = 0
    auto_verify = can_auto_verify(uploading_user_id, course_data)
    try:
        course = Course.objects.get(**course_data)
    except Course.DoesNotExist:
        raise ValueError(
            f"Course with code {course_data.get('code')}, year {course_data.get('year')}, semester {course_data.get('semester')} does not exist."
        )
    if file_name.endswith(".docx"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
            temp_file.write(file_data)
            total_question_count = get_question_table_count(temp_file.name)
            upload_result = get_upload_result(upload_result_id)
            interval = int(total_question_count * PROGRESS_UPDATE_INTERVAL)

            for i, question_data in enumerate(
                parse_questions_from_docx(temp_file.name, docx_table_format_a)
            ):
                if interval >= 1 and i % interval == 0:
                    update_upload_result(upload_result, total_question_count, success_count, failure_count)
                try:
                    insert_data(
                        question_data,
                        course,
                        create_required,
                        temp_file.name,
                        auto_verify,
                    )
                    success_count += 1
                except Exception as e:
                    handleParsingException(question_data, e)
                    failure_count += 1
    else:
        raise ValueError("Unsupported file format. Only .docx files are supported.")

    finish_upload_result(upload_result, success_count, failure_count)
    return {"success_count": success_count, "failure_count": failure_count}


def handleParsingException(question_data: dict, e: Exception) -> None:
    summary = None
    if isinstance(e, IntegrityError):
        logger.error(
            f"Insertion failed for question with serial number {question_data.get('serial_number')}. Integrity error: {e}"
        )
    elif isinstance(e, DocxParsingError):
        logger.error(
            f"Explicit parsing error for question with serial number {question_data.get('serial_number')}: {e}"
        )
        summary = traceback.extract_tb(e.__traceback__)
    else:
        logger.error(
            f"Unexpected error for question with serial number {question_data.get('serial_number')}: {e}"
        )
        summary = traceback.extract_tb(e.__traceback__)
    if summary:
        logger.error(f"Error info: {summary[-1]} {e}")


def can_auto_verify(user_id: int, course: dict) -> bool:
    return Enrolment.objects.filter(
        user__id=user_id,
        course__code=course.get("code"),
        course__year=course.get("year"),
        course__semester=course.get("semester"),
        is_instructor=True,
    ).exists()


def parse_select_frequency(value: str) -> float:
    try:
        match = decimal_pattern.search(value)
        if match:
            return float(match.group())
    except (ValueError, TypeError):
        pass
    return 0.0


def insert_data(
    question_data: dict,
    course: Course,
    create_required: bool,
    temp_file_name: str,
    auto_verify: bool,
) -> None:
    """
    Inserts parsed question data into the database.

    :param question_data: Dictionary containing question details.
    :param course: Course instance that will be referenced in the unit the question belongs to.
    :param create_required: If True, creates Unit and UnitSubtopic if they do not exist. Otherwise, it expects them to exist.
    :param auto_verify: Whether the question will be set to verified.
    """
    try:
        answer_index = ord(question_data.get("answer").upper().rstrip("() .")) - ord(
            "A"
        )
    except Exception:
        raise DocxParsingError(f"Invalid answer format: {question_data.get('answer')}")

    raw_selection_frequencies = question_data.get("option_selection_frequencies", [])
    if len(raw_selection_frequencies) <= answer_index:
        raise DocxParsingError(f"Invalid answer index {answer_index}")
    # Match a single digit (0, 1) or a decimal number. Only match at most 5 digits since we round to 4

    selection_frequencies = [
        parse_select_frequency(freq) for freq in raw_selection_frequencies
    ]
    selection_frequency = selection_frequencies[answer_index]

    unit_name = question_data.get("unit").strip()
    subtopic_name = question_data.get("subtopic").strip()
    raw_unit_number = question_data.get("unit_number").strip()
    unit_number = int(raw_unit_number) if raw_unit_number not in (None, "") else -1

    with transaction.atomic():
        if create_required:
            unit, _ = Unit.objects.get_or_create(
                defaults={"number": unit_number}, course=course, name=unit_name
            )
            subtopic, _ = UnitSubtopic.objects.get_or_create(
                unit=unit, name=subtopic_name
            )
        else:
            unit = Unit.objects.get(course=course, name=unit_name)
            subtopic = UnitSubtopic.objects.get(unit=unit, name=subtopic_name)

        question = create_question(
            question_data, selection_frequency, subtopic, auto_verify
        )
        created_images = save_images(question_data, question.public_id, temp_file_name)
        question.images.set(created_images)

        create_question_options(question_data, answer_index, question)
        create_question_comments(question_data, question)


def create_question(
    question_data, selection_frequency: float, subtopic, is_verified: bool
):
    serial_number = question_data.get("serial_number", "N/A").strip()
    content = question_data.get("content")
    if not content or content.strip() == "":
        raise ValueError(
            f"Question content is empty for question with serial number {serial_number}"
        )

    answer_explanation = question_data.get("explanation")
    if not answer_explanation:
        answer_explanation = ""
    question = Question.objects.create(
        subtopic=subtopic,
        serial_number=question_data.get("serial_number"),
        content=content.strip(),
        answer_explanation=answer_explanation.strip(),
        selection_frequency=selection_frequency,
        difficulty=calculate_difficulty_for_test(selection_frequency),
        is_verified=is_verified,
    )
    return question


def create_question_comments(question_data, question):
    comment_text = question_data.get("comments")
    if comment_text is not None and comment_text.strip() != "":
        QuestionComment.objects.create(question=question, comment_text=comment_text)


def create_question_options(question_data, answer_index, question):
    for idx, option_content in enumerate(question_data.get("options", [])):
        is_answer = idx == answer_index
        option_selection_frequency = parse_select_frequency(
            question_data.get("option_selection_frequencies", [])[idx]
        )
        QuestionOption.objects.create(
            question=question,
            content=option_content,
            selection_frequency=option_selection_frequency,
            is_answer=is_answer,
        )


def save_images(question_data, question_public_id, file_name):
    question_images = question_data.get("images", [])
    saved_images = []
    for image in question_images:
        image_src = image.get("src")
        image_alt = image.get("alt", "")
        image_ref = image.get("ref")
        # Find the image in the docx from src
        with ZipFile(file_name) as docx_zip:
            image_data = docx_zip.read(f"word/{image_src}")
            # Ref is expected to include the file extension
            image_filename = f"{question_public_id}_{image_ref}"
            print(f"Saving image {image_filename}...")
            question_image = QuestionImage.objects.create(
                image_file=ImageFile(BytesIO(image_data), name=image_filename),
                alt_text=image_alt,
            )
            saved_images.append(question_image)
    return saved_images


def calculate_difficulty_for_test(selection_frequency: float) -> float:
    if selection_frequency <= 0 or selection_frequency >= 1:
        return 0.0

    difficulty = -log((1 / selection_frequency) - 1)
    return round(difficulty, 4)
