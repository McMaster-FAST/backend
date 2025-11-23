from docx import Document
from celery import shared_task
from io import BytesIO

from django.db import transaction

from core.models import Question, QuestionComment, QuestionOption
from courses.models import Course, Unit, UnitSubTopic
from .docx.parser import parse_questions_from_docx
from .docx.formats import docx_table_format_a

from math import log

class DocxParsingError(Exception):
    pass

@shared_task
def parse_file(file_name: str, file_data: bytes, course: dict) -> None:
    """
    Celery task to parse uploaded question bank files. Determines file type and processes accordingly.
    """
    try:
        course = Course.objects.get(
            code=course.get("code"), 
            year=course.get("year"), 
            semester=course.get("semester")
        )
    except Course.DoesNotExist:
        raise ValueError(f"No course found with code: {course.get('code')}, year: {course.get('year')}, semester: {course.get('semester')}")

    if file_name.endswith(".docx"):
        document = Document(BytesIO(file_data))
        for question_data in parse_questions_from_docx(document, docx_table_format_a):
            try:
                insert_data(question_data, course)
            except Exception as e:
                print(f"Failed inserting {question_data.get('serial_number')} with: {e}")
    else:
        raise ValueError("Unsupported file format. Only .docx files are supported.")

def insert_data(question_data: dict, course: Course, create_required: bool = True) -> None:
    """
    Inserts parsed question data into the database.
    
    :param question_data: Dictionary containing question details.
    :param course: Course instance that will be referenced in the unit the question belongs to.
    :param create_required: If True, creates Unit and UnitSubTopic if they do not exist. Otherwise, it expects them to exist.
    """
    answer_index = ord(question_data.get("answer").upper()) - ord("A")
    selection_frequency = float(question_data.get("option_selection_frequencies")[answer_index])
    unit_name = question_data.get("unit")
    subtopic_name = question_data.get("subtopic")
    unit_number = int(question_data.get("unit_number"))

    with transaction.atomic():
        if create_required:
            unit, _ = Unit.objects.get_or_create(course=course, name=unit_name, number=unit_number)
            subtopic, _ = UnitSubTopic.objects.get_or_create(unit=unit, name=subtopic_name)
        else:
            unit = Unit.objects.get(course=course, name=unit_name, number=unit_number)
            subtopic = UnitSubTopic.objects.get(unit=unit, name=subtopic_name)

        question = Question.objects.create(
            subtopic=subtopic,
            serial_number=question_data.get("serial_number"),
            content=question_data.get("content", ""),
            answer_explanation=question_data.get("explanation", ""),
            selection_frequency=float(selection_frequency) if selection_frequency else 0.0,
            difficulty=calculate_difficulty_for_test(selection_frequency)
        )

        for idx, option_content in enumerate(question_data.get("options", [])):
            is_answer = (idx == answer_index)
            option_selection_frequency = float(question_data.get("option_selection_frequencies")[idx])
            QuestionOption.objects.create(
                question=question,
                content=option_content,
                selection_frequency=option_selection_frequency,
                is_answer=is_answer,   
            )
        
        QuestionComment.objects.create(
            question=question,
            comment_text=question_data.get("comments", "")
        )

def calculate_difficulty_for_test(selection_frequency: float) -> float:
    if selection_frequency <= 0 or selection_frequency >= 1:
        return 0.0
    try:
        difficulty = -log((1 / selection_frequency) - 1)
        return round(difficulty, 4)
    except ValueError:
        return 0.0