from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from ..serializers import FileUploadSerializer
from ..tasks import parse_file
from logging import getLogger
logger = getLogger(__name__)

class UploadView(APIView):
    """
    Class based view to handle question bank uploads.
    """

    permission_classes = (AllowAny,)

    def put(self, request, *args, **kwargs):
        """
        Handles PUT requests for uploading question banks.
        """
        serializer = FileUploadSerializer(data=request.data)
        logger.debug("Received file upload request with data:", request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data.get("file")
        course = {
            "code": serializer.validated_data.get("course_code"),
            "year": serializer.validated_data.get("course_year"),
            "semester": serializer.validated_data.get("course_semester")
        }
        create_required = serializer.validated_data.get("create_required")

        parse_file.delay(
            uploaded_file.name, 
            uploaded_file.read(), 
            course, 
            request.user,
            create_required,
        )

        return Response(
            {"message": "File uploaded successfully."}, status=status.HTTP_201_CREATED
        )
