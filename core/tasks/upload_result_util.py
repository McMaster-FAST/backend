from MacFAST import settings
from courses.models import Course, QuestionUploadResult
from sso_auth.models import MacFastUser


def finish_upload_result(
    upload_result: QuestionUploadResult, success_count: int, failure_count: int
) -> None:
    upload_result.result = QuestionUploadResult.QuestionUploadResultChoices.SUCCESS
    upload_result.success_count = success_count
    upload_result.failure_count = failure_count
    upload_result.progress = 1.0
    upload_result.save(
        update_fields=["result", "success_count", "failure_count", "progress"]
    )


def update_upload_result(
    upload_result: QuestionUploadResult,
    total_question_count: int,
    current_successes: int,
    current_failures: int,
) -> None:
    """
    Update the progress of the upload result based on the number of questions processed.
    """

    current_progress = (
        (current_failures + current_successes) / total_question_count
        if total_question_count > 0
        else 0
    )
    upload_result.progress = current_progress
    upload_result.success_count = current_successes
    upload_result.failure_count = current_failures
    upload_result.save(update_fields=["progress", "success_count", "failure_count"])


def init_upload_result(course: Course, user: MacFastUser) -> QuestionUploadResult:
    return QuestionUploadResult.objects.create(
        course=course,
        initiating_user=user,
        result=QuestionUploadResult.QuestionUploadResultChoices.RUNNING,
        success_count=0,
        failure_count=0,
        progress=0.0,
    )


def get_upload_result(upload_result_id: str) -> QuestionUploadResult:
    return QuestionUploadResult.objects.get(public_id=upload_result_id)
