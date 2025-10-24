from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes


class PingView(APIView):
    """
    A simple class-based view to check if the API is up and running.
    """

    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and returns a simple 'pong' message.
        """
        return Response({"message": "pong"}, status=status.HTTP_200_OK)
