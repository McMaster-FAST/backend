from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from ..serializers import FileUploadSerializer
from ..tasks import parse_file

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

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data["file"]
        group_name = serializer.validated_data.get("group_name")

        parse_file.delay(file_name=uploaded_file.name, file_data=uploaded_file.read(), group_name=group_name)

        return Response(
            {"message": "File uploaded successfully."}, status=status.HTTP_201_CREATED
        )
