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
from .csv.parser import parse_questions_from_csv
from .utils import str_to_float
from core.tasks.docx.parser1AA3Q import parse
from core.tasks.docx.parser1AA3exp import parse_explanation_updates
from django.db.models import Q
import os

import tempfile
import hashlib
import re
import traceback

from math import log
from docx import Document

from django.core.files.images import ImageFile
from io import BytesIO

import re
from logging import getLogger

logger = getLogger(__name__)
decimal_pattern = re.compile(r"\d?\.\d{0,5}")

PROGRESS_UPDATE_INTERVAL = 0.1


class DocxParsingError(Exception):
    pass


def is_question_only_docx(docx_path: str) -> bool:
    try:
        doc = Document(docx_path)
    except Exception:
        return False

    for tbl in doc.tables:
        if not tbl.rows:
            continue

        labels = set()

        for row in tbl.rows:
            if not row.cells:
                continue
            label = " ".join((row.cells[0].text or "").strip().split())
            if label:
                labels.add(label)

        if (
            "Q#:" in labels
            and "Serial #:" in labels
            and "Stem" in labels
            and "Ans:" in labels
        ):
            return True

    return False


def is_explanation_update_format(docx_path: str) -> bool:
    try:
        doc = Document(docx_path)
    except Exception:
        return False

    i = 0
    for i, table in enumerate(doc.tables):
        # print(f"Table {i}: rows={len(table.rows)}, cols={len(table.columns)}")

        if len(table.rows) == 5 and len(table.columns) in (2, 3):
            qnum_text = (table.cell(0, 0).text or "").strip()
            # print(f"Checking qnum: '{qnum_text}'")

            if re.match(r"^\D*(\d+)\D*$", qnum_text):
                return True

    return False


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
        raise ValueError(f"No course found with identifiers: {course}")

    if file_name.endswith(".docx"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
            temp_file.write(file_data)
            temp_file.flush()

            try:
                if is_explanation_update_format(temp_file.name):
                    print("USING EXPLANATION UPDATE PARSER")
                    parsed_updates = parse_explanation_updates(
                        temp_file.name, file_name
                    )
                    print("PARSED UPDATES:", len(parsed_updates))

                    for question_data in parsed_updates:
                        try:
                            update_question_explanation(question_data)
                        except Question.DoesNotExist:
                            print(
                                f"Question not found for serial {question_data.get('serial_number')}"
                            )
                        except IntegrityError as e:
                            print(
                                f"Failed updating {question_data.get('serial_number')} with: {e}"
                            )
                elif is_question_only_docx(temp_file.name):
                    parsed_questions = parse(temp_file.name)

                    for question_data in parsed_questions:
                        try:
                            insert_docx_data_v3(question_data, course, create_required)
                        except IntegrityError as e:
                            print(
                                f"Failed inserting exam-bank question "
                                f"{question_data.get('serial_number', question_data.get('number'))} with: {e}"
                            )
                else:
                    parsed_questions = list(
                        parse_questions_from_docx(temp_file.name, docx_table_format_a)
                    )

                    for question_data in parsed_questions:
                        try:
                            insert_data(
                                question_data,
                                course,
                                create_required,
                                temp_file.name,
                                auto_verify,
                            )
                        except Exception as e:
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
            finally:
                try:
                    os.unlink(temp_file.name)
                except OSError as e:
                    logger.warning(
                        f"Failed to delete temporary file '{temp_file.name}': {e}"
                    )

    elif file_name.endswith(".csv"):
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".csv", mode="wb"
        ) as temp_file:
            temp_file.write(file_data)
            temp_file.flush()
            for question_data in parse_questions_from_csv(temp_file.name):
                try:
                    insert_csv_data(question_data, course, create_required)
                    logger.info(
                        f"Successfully inserted question with serial number {question_data.get('serial_number')}"
                    )
                except Exception as e:
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
        raise ValueError(
            f"Course with code {course_data.get('code')}, year {course_data.get('year')}, semester {course_data.get('semester')} does not exist."
        )
    else:
        raise ValueError(
            "Unsupported file format. Only .docx and .csv files are supported."
        )


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


def save_v3_images(image_dicts, question_public_id):
    saved_by_digest = {}
    saved_by_ref = {}

    for image in image_dicts:
        image_name = image.get("name", "image.bin")
        image_bytes = image.get("bytes")
        image_ref = image.get("ref")
        if not image_bytes or not image_ref:
            continue

        digest = hashlib.sha256(image_bytes).hexdigest()

        if digest not in saved_by_digest:
            extension = os.path.splitext(image_name)[1].lower() or ".bin"
            filename = f"{question_public_id}_{digest}{extension}"
            saved_by_digest[digest] = QuestionImage.objects.create(
                image_file=ImageFile(BytesIO(image_bytes), name=filename),
                alt_text="",
            )

        saved_by_ref[image_ref] = saved_by_digest[digest]

    return saved_by_ref


def replace_image_placeholders(html, saved_by_ref):
    def repl(match):
        ref = match.group(0)
        img = saved_by_ref.get(ref)

        if not img:
            print("NO IMAGE FOR PLACEHOLDER:", ref)
            return f"<p>[Missing image: {ref}]</p>"

        return f'<img src="/media/{img.image_file.name}">'

    return re.sub(r"\[\[IMG:[^\]]+\]\]", repl, html)


def resolve_question_by_base_serial(base_serial: str) -> Question:
    matches = Question.objects.filter(
        Q(serial_number=base_serial) | Q(serial_number__startswith=base_serial + "_")
    )

    count = matches.count()
    if count == 0:
        raise Question.DoesNotExist(f"No question found for base serial {base_serial}")
    if count > 1:
        raise Question.MultipleObjectsReturned(
            f"Multiple questions found for base serial {base_serial}"
        )

    return matches.get()


def insert_docx_data_v3(
    question_data: dict, course: Course, create_required: bool
) -> None:
    unit_number = question_data.get("unit_number")
    unit_name = question_data.get("unit_name") or "Imported Unit"
    subtopic_name = question_data.get("subtopic_name") or "Imported Subtopic"

    with transaction.atomic():
        if create_required:
            unit, _ = Unit.objects.get_or_create(
                course=course,
                number=unit_number,
                defaults={"name": unit_name},
            )
            subtopic, _ = UnitSubtopic.objects.get_or_create(
                unit=unit,
                name=subtopic_name,
            )
        else:
            unit = Unit.objects.get(course=course, name=unit_name)
            subtopic = UnitSubtopic.objects.get(unit=unit, name=subtopic_name)

        question = Question.objects.create(
            subtopic=subtopic,
            serial_number=question_data.get("serial_number")
            or f"{course.code}-DOCX-{question_data['number']}",
            content="",
            answer_explanation="",
            selection_frequency=0,
            difficulty=question_data.get("difficulty", 0),
        )

        content_images_by_ref = save_v3_images(
            question_data.get("content_images", []),
            question.public_id,
        )
        explanation_images_by_ref = save_v3_images(
            question_data.get("explanation_images", []),
            question.public_id,
        )

        # M2M needs QuestionImage instances, not dicts
        question_image_objs = list(content_images_by_ref.values()) + list(
            explanation_images_by_ref.values()
        )

        # optional dedupe in case same image instance appears in both
        seen_ids = set()
        unique_question_images = []
        for img in question_image_objs:
            if img.id not in seen_ids:
                seen_ids.add(img.id)
                unique_question_images.append(img)

        question.images.set(unique_question_images)

        content_html = question_data.get("content", "")
        explanation_html = question_data.get("answer_explanation", "")

        content_html = replace_image_placeholders(content_html, content_images_by_ref)
        explanation_html = replace_image_placeholders(
            explanation_html, explanation_images_by_ref
        )

        question.content = content_html
        question.answer_explanation = explanation_html
        question.save(update_fields=["content", "answer_explanation"])

        for opt in question_data.get("options", []):
            option = QuestionOption.objects.create(
                question=question,
                content="",
                is_answer=opt.get("is_answer", False),
                selection_frequency=opt.get("selection_frequency", 0),
            )

            option_images_by_ref = save_v3_images(
                opt.get("images", []),
                question.public_id,
            )

            option.images.set(list(option_images_by_ref.values()))

            option_html = replace_image_placeholders(
                opt.get("content", ""),
                option_images_by_ref,
            )
            option.content = option_html
            option.save(update_fields=["content"])


def update_question_explanation(question_data: dict) -> None:
    question = resolve_question_by_base_serial(question_data["serial_number"])

    explanation_images_by_ref = save_v3_images(
        question_data.get("explanation_images", []),
        question.public_id,
    )

    if explanation_images_by_ref:
        question.images.add(*list(explanation_images_by_ref.values()))

    explanation_html = replace_image_placeholders(
        question_data.get("answer_explanation", ""),
        explanation_images_by_ref,
    )

    question.answer_explanation = explanation_html
    question.save(update_fields=["answer_explanation"])


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
    try:
        difficulty = -log((1 / selection_frequency) - 1)
        return round(difficulty, 4)
    except ValueError:
        return 0.0


def insert_csv_data(question_data: dict, course: Course, create_required: bool) -> None:
    """
    Inserts parsed question data from CSV into the database.

    :param question_data: Dictionary containing question details from CSV.
    :param course: Course instance that will be referenced in the unit the question belongs to.
    :param create_required: If True, creates Unit and UnitSubtopic if they do not exist. For CSV, subtopic is set to None initially and will be updated later.
    """
    answer_index = ord(question_data.get("answer").upper()) - ord("A")
    freq_str = question_data.get("option_selection_frequencies")[answer_index]
    selection_frequency = str_to_float(freq_str)

    # TODO: For CSV, unit and subtopic mapping are in a different file, they will be set later through a different method, So we'll create the question without subtopic initially

    with transaction.atomic():
        # Use the provided IRT parameters from CSV
        difficulty = question_data.get("difficulty", 0.0)
        discrimination = question_data.get("discrimination", 1.0)
        guessing = question_data.get("guessing", 0.0)

        # If difficulty is 0, calculate it from selection frequency
        if difficulty == 0.0 and selection_frequency > 0:
            difficulty = None  # Will be calculated in create_question

        # Use shared create_question function
        question = create_question(
            question_data,
            question_data.get("selection_frequency", selection_frequency),
            subtopic=None,  # Will be set later
            difficulty=difficulty,
        )

        # TODO: images for CSV files

        # Use shared create_question_options function
        create_question_options(question_data, answer_index, question)

        # Use shared create_question_comments function
        create_question_comments(question_data, question)
