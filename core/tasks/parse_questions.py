from zipfile import ZipFile
from celery import shared_task
from io import BytesIO

from django.db import transaction
from django.core.files.images import ImageFile
from core.models import Question, QuestionComment, QuestionOption, QuestionImage
from courses.models import Course, Unit, UnitSubtopic
from .docx.parser import parse_questions_from_docx
from .docx.formats import docx_table_format_a

import os
import tempfile

from math import log

class DocxParsingError(Exception):
    pass

@shared_task
def parse_file(file_name: str, file_data: bytes, course: dict, create_required: bool) -> None:
    """
    Celery task to parse uploaded question bank files. Determines file type and processes accordingly.

    :param file_name: Name of the uploaded file.
    :param file_data: Byte content of the uploaded file.
    :param course: Dictionary containing course identifiers (code, year, semester).
    :param create_required: Create all required related entities if they do not exist, with the exception of Course.
    """
    try:
        # Unpack dict into kwargs
        course = Course.objects.get(**course)
    except Course.DoesNotExist:
        raise ValueError(f"No course found with identifiers: {course}")
    if file_name.endswith(".docx"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
            temp_file.write(file_data)
            for question_data in parse_questions_from_docx(temp_file.name, docx_table_format_a):
                try:
                    insert_data(question_data, course, create_required, temp_file.name)
                except Exception as e:
                    print(f"Failed inserting {question_data.get('serial_number')} with: {e}")
    else:
        raise ValueError("Unsupported file format. Only .docx files are supported.")

def insert_data(question_data: dict, course: Course, create_required: bool, temp_file_name: str) -> None:
    """
    Inserts parsed question data into the database.
    
    :param question_data: Dictionary containing question details.
    :param course: Course instance that will be referenced in the unit the question belongs to.
    :param create_required: If True, creates Unit and UnitSubtopic if they do not exist. Otherwise, it expects them to exist.
    """
    answer_index = ord(question_data.get("answer").upper()) - ord("A")
    selection_frequency = float(question_data.get("option_selection_frequencies")[answer_index])
    unit_name = question_data.get("unit").strip()
    subtopic_name = question_data.get("subtopic").strip()
    raw_unit_number = question_data.get("unit_number").strip()
    unit_number = int(raw_unit_number) if raw_unit_number not in (None, "") else -1
    with transaction.atomic():
        if create_required:
            unit, _ = Unit.objects.get_or_create(defaults={"number": unit_number}, course=course, name=unit_name)
            subtopic, _ = UnitSubtopic.objects.get_or_create(unit=unit, name=subtopic_name)
        else:
            unit = Unit.objects.get(course=course, name=unit_name)
            subtopic = UnitSubtopic.objects.get(unit=unit, name=subtopic_name)

        question = create_question(question_data, selection_frequency, subtopic)
        created_images = save_images(question_data, question.public_id, temp_file_name)
        question.images.set(created_images)

        create_question_options(question_data, answer_index, question)
        create_question_comments(question_data, question)

def create_question(question_data, selection_frequency, subtopic):
    question = Question.objects.create(
            subtopic=subtopic,
            serial_number=question_data.get("serial_number"),
            content=question_data.get("content", ""),
            answer_explanation=question_data.get("explanation", ""),
            selection_frequency=float(selection_frequency) if selection_frequency else 0.0,
            difficulty=calculate_difficulty_for_test(selection_frequency),
        )
    return question

def create_question_comments(question_data, question):
    comment_text = question_data.get("comments", "")
    if comment_text != "":
        QuestionComment.objects.create(
                question=question,
                comment_text=comment_text
            )

def create_question_options(question_data, answer_index, question):
    for idx, option_content in enumerate(question_data.get("options", [])):
        is_answer = (idx == answer_index)
        option_selection_frequency = float(question_data.get("option_selection_frequencies")[idx])
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
        print(image)
        image_src = image.get("src")
        image_alt = image.get("alt", "")
        image_ref = image.get("ref")
        # Find the image in the docx from src
        with ZipFile(file_name) as docx_zip:
            image_data = docx_zip.read(f"word/{image_src}")

            extension = os.path.splitext(image_src)[1].lower()
            image_filename = f"{question_public_id}_{image_ref}{extension}"
            print(f"Saving image {image_filename}...")
            question_image = QuestionImage.objects.create(
                image_file=ImageFile(BytesIO(image_data), name=image_filename),
                alt_text=image_alt
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