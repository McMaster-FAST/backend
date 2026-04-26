from courses.models import Course, Enrolment
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..serializers import FileUploadSerializer
from ..tasks import parse_file
from core.tasks.upload_result_util import init_upload_result
from logging import getLogger

logger = getLogger(__name__)


class UploadView(APIView):
    """
    Class based view to handle question bank uploads.
    """

    def put(self, request, *args, **kwargs):
        """
        Handles PUT requests for uploading question banks.
        """
        serializer = FileUploadSerializer(data=request.data)

        logger.debug("Received file upload request with data: %s", request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not self._user_has_permission(request.user, serializer):
            return Response(
                {
                    "error": "You do not have permission to upload files for this course."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        uploaded_file = serializer.validated_data.get("file")
        course_data = {
            "code": serializer.validated_data.get("course_code"),
            "year": serializer.validated_data.get("course_year"),
            "semester": serializer.validated_data.get("course_semester"),
        }
        create_required = serializer.validated_data.get("create_required")
        upload_result = init_upload_result(Course.objects.get(**course_data), request.user)
        parse_file.delay(
            file_name=uploaded_file.name,
            file_data=uploaded_file.read(),
            course_data=course_data,
            uploading_user_id=request.user.id,
            create_required=create_required,
            upload_result_id=upload_result.public_id,
        )

        return Response(
            {"upload_result_id": upload_result.public_id}, status=status.HTTP_201_CREATED
        )

    def _user_has_permission(self, user, serializer):
        user_enrolments = Enrolment.objects.filter(
            user=user,
            course__code=serializer.validated_data.get("course_code"),
            course__year=serializer.validated_data.get("course_year"),
            course__semester=serializer.validated_data.get("course_semester"),
        )
        if not user_enrolments.exists():
            return False
        user_enrolment = user_enrolments.first()
        return user_enrolment.is_instructor or user_enrolment.is_ta
