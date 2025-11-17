from docx import Document
from celery import shared_task
from io import BytesIO

from django.db import transaction
from ..models import Question, QuestionComment, QuestionOption, QuestionGroup

CHOSEN_FREQUENCY = "freq"

docx_table_format = [
    ["question_number"],
    ["serial_number"],
    ["unit"],
    ["used"],
    ["content"],
    ["a", "freq"],
    ["b", "freq"],
    ["c", "freq"],
    ["d", "freq"],
    ["answer"],
    ["variants"],
    ["comment"],
]

docx_table_options = (5, 9)


class DocxParsingError(Exception):
    pass

@shared_task
def parse_file(file_name: str, file_data: bytes, group_name: str) -> None:
    question_group = None
    if group_name is None:
        pass # TODO: handle automatically grouping based on coures unit and subtopic
    else:
        with transaction.atomic():
            question_group, created = QuestionGroup.objects.get_or_create(group_name=group_name)

    if file_name.endswith(".docx"):
        parse_questions_from_docx(file_data, question_group)


def parse_questions_from_docx(file_data: bytes, question_group: QuestionGroup) -> None:
    document = Document(BytesIO(file_data))
    question_count = 0
    for table in document.tables:
        table_data = {}
        for i, data_names in enumerate(docx_table_format):
            cells = table.row_cells(i)
            # TODO: When the issue with unexpected cell length is understood,
            # validate the row structure here and handle format errors.
            table_data.setdefault(data_names[0], cells[1].text.strip())
            if len(data_names) == 1:
                continue

            for j, name in enumerate(data_names[1:], 1):
                # The first element is the header in this case (Q #, Serial #, A), etc.) so ignore it
                # Grab the rest of the columns if we name them in docx_table_format
                if j + 1 >= len(cells):
                    break # TODO: More informative error handling
                
                table_data.setdefault(f"{data_names[0]}-{name}", cells[j + 1].text.strip())
        with transaction.atomic():
            insert_data(table_data, question_group)
            question_count += 1
    return question_count

def insert_data(table_data: dict, question_group: QuestionGroup) -> None:
    answer_freq_key = f"{str(table_data.get("answer")).lower()}-{CHOSEN_FREQUENCY}"

    answer_freq = table_data.get(answer_freq_key)
    difficulty = float(answer_freq) if answer_freq != "" else 0.0
    question = Question(
            content=table_data.get("content"),
            difficulty=difficulty,
            serial_number=table_data.get("serial_number", "UNKNOWN"),
            is_flagged=False, 
            is_active=True, 
            is_verified=True,
            # TODO Support images
        )
    question.save()

    for option_row in [row for row in docx_table_format[docx_table_options[0]:docx_table_options[1]]]:
        option_name = option_row[0]
        option_freq_key = f"{option_name}-{CHOSEN_FREQUENCY}"
        option_freq = table_data.get(option_freq_key)
        selection_frequency = float(option_freq) if option_freq != "" else 0.0
        QuestionOption(
                question=Question.objects.get(id=question.id),
                content=table_data.get(option_name),
                is_answer=(option_name == table_data.get("answer")),
                selection_frequency=selection_frequency,
                # TODO Support images
            ).save()

    QuestionComment(
            question=Question.objects.get(id=question.id),
            user=None,  # TODO Support user association
            comment_text=table_data.get("comment"),
            # TODO: Something about not including timestamp if inserted from file upload?
        ).save()
    
    if question_group is not None:
        question_group.questions.add(question)
        question_group.save()