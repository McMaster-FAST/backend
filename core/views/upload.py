from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from ..serializers import FileUploadSerializer
from ..tasks import parse_file

class UploadView(APIView):
    """
    Class based view to handle question bank uploads.
    """

    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        """
        Handles PUT requests for uploading question banks.
        """
        serializer = FileUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data.get("file")
        course = serializer.validated_data.get("course")

        parse_file.delay(file_name=uploaded_file.name, file_data=uploaded_file.read(), course=course)

        return Response(
            {"message": "File uploaded successfully."}, status=status.HTTP_201_CREATED
        )
