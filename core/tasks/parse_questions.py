import tempfile
from docx import Document
from celery import shared_task
from io import BytesIO

from django.utils.text import slugify
from django.db import transaction
from django.core.files.images import ImageFile
from django.conf import settings
from core.models import Question, QuestionComment, QuestionOption, QuestionImage
from courses.models import Course, Unit, UnitSubtopic
from .docx.parser import parse_questions_from_docx
from .docx.formats import docx_table_format_a

import os

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
    with tempfile.TemporaryDirectory(dir=settings.MEDIA_ROOT) as tmpdirname:
        if file_name.endswith(".docx"):
            document = Document(BytesIO(file_data))
            for index, question_data in enumerate(parse_questions_from_docx(document, docx_table_format_a, tmpdirname)):
                try:
                    insert_data(question_data, course, create_required, index, tmpdirname)
                except Exception as e:
                    print(f"Failed inserting {question_data.get('serial_number')} with: {e}")
        else:
            raise ValueError("Unsupported file format. Only .docx files are supported.")

def insert_data(question_data: dict, course: Course, create_required: bool, index: int, tmpdirname: str) -> None:
    """
    Inserts parsed question data into the database.
    
    :param question_data: Dictionary containing question details.
    :param course: Course instance that will be referenced in the unit the question belongs to.
    :param create_required: If True, creates Unit and UnitSubtopic if they do not exist. Otherwise, it expects them to exist.
    """
    # print(f"Inserting question...")
    # print(question_data)
    answer_index = ord(question_data.get("answer").upper()) - ord("A")
    selection_frequency = float(question_data.get("option_selection_frequencies")[answer_index])
    unit_name = question_data.get("unit").strip()
    subtopic_name = question_data.get("subtopic").strip()
    raw_unit_number = question_data.get("unit_number").strip()
    unit_number = int(raw_unit_number) if raw_unit_number not in (None, "") else -1
    with transaction.atomic():
        if create_required:
            unit, _ = Unit.objects.get_or_create(course=course, name=unit_name, number=unit_number)
            subtopic, _ = UnitSubtopic.objects.get_or_create(unit=unit, name=subtopic_name)
        else:
            unit = Unit.objects.get(course=course, name=unit_name, number=unit_number)
            subtopic = UnitSubtopic.objects.get(unit=unit, name=subtopic_name)

        # Collect created QuestionImage instances so we can associate them with the question.
        created_images = []
        images_dir = os.path.join(tmpdirname, str(index))
        if os.path.isdir(images_dir):
            img_files = os.listdir(images_dir)
            for img_name in img_files:
                img_path = os.path.join(images_dir, img_name)
                # Open the file and give it a safe basename when saving to storage.
                with open(img_path, "rb") as fh:
                    # Use the original filename only (basename) to avoid passing absolute paths
                    # to Django storage which triggers path traversal checks.
                    file_name_serial_number = slugify(question_data.get("serial_number"))
                    img_name = f"{file_name_serial_number}_{img_name}"
                    created = QuestionImage.objects.create(
                        image_file=ImageFile(fh, name=os.path.basename(img_name)),
                    )
                    created_images.append(created)

        question = Question.objects.create(
            subtopic=subtopic,
            serial_number=question_data.get("serial_number"),
            content=question_data.get("content", ""),
            answer_explanation=question_data.get("explanation", ""),
            selection_frequency=float(selection_frequency) if selection_frequency else 0.0,
            difficulty=calculate_difficulty_for_test(selection_frequency),
        )
        # Associate the created image instances with the question.
        if created_images:
            question.images.set(created_images)

        for idx, option_content in enumerate(question_data.get("options", [])):
            is_answer = (idx == answer_index)
            option_selection_frequency = float(question_data.get("option_selection_frequencies")[idx])
            QuestionOption.objects.create(
                question=question,
                content=option_content,
                selection_frequency=option_selection_frequency,
                is_answer=is_answer,   
            )
        
        comment_text = question_data.get("comments", "")
        if comment_text != "":
            QuestionComment.objects.create(
                question=question,
                comment_text=comment_text
            )
        

def calculate_difficulty_for_test(selection_frequency: float) -> float:
    if selection_frequency <= 0 or selection_frequency >= 1:
        return 0.0
    try:
        difficulty = -log((1 / selection_frequency) - 1)
        return round(difficulty, 4)
    except ValueError:
        return 0.0