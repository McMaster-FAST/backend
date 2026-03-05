from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..serializers import SavedForLaterSerializer
from ..models import SavedForLater, Question


class SavedForLaterViewSet(viewsets.ModelViewSet):
    serializer_class = SavedForLaterSerializer
    queryset = SavedForLater.objects.all()

    def get_queryset(self):
        return self.queryset.filter(
            user=self.request.user,
            question__subtopic__unit__course__code=self.kwargs["course_code"],
            question__subtopic__unit__course__is_archived=False,
        )

    def create(self, request, *args, **kwargs):
        question_public_id = request.data.get("question_public_id")
        if not question_public_id:
            return Response(
                {"error": "question_public_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        question = get_object_or_404(Question, public_id=question_public_id)
        saved, created = SavedForLater.objects.get_or_create(
            user=request.user, question=question
        )
        serializer = self.get_serializer(saved)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        question_public_id = request.data.get("question_public_id")
        if not question_public_id:
            return Response(
                {"error": "question_public_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        deleted, _ = SavedForLater.objects.filter(
            user=request.user, question__public_id=question_public_id
        ).delete()
        if not deleted:
            return Response(
                {"error": "Saved item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
