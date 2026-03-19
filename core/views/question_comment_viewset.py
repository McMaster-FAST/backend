from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import QuestionComment, Question
from core.serializers.question_comment_serializer import QuestionCommentSerializer


class QuestionCommentViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionCommentSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        queryset = QuestionComment.objects.all().order_by("timestamp")

        # Gets comments for a specific question (Nested route)
        question_uuid = self.kwargs.get("question_public_id")
        if question_uuid:
            return queryset.filter(
                question__public_id=question_uuid, reply_to__isnull=True
            )

        return queryset

    def perform_create(self, serializer):
        """
        Handles standard POST to /api/questions/<uuid>/comments/
        """
        question_uuid = self.kwargs.get("question_public_id")

        if question_uuid:
            try:
                question = Question.objects.get(public_id=question_uuid)
                serializer.save(user=self.request.user, question=question)
            except Question.DoesNotExist:
                raise NotFound(detail="The specified question does not exist.")
        else:
            # POST to /api/comments/ directly, block it
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                detail="You must POST to a question's comment endpoint."
            )

    @action(detail=True, methods=["post"])
    def reply(self, request, *args, **kwargs):
        target_comment = self.get_object()

        root_comment = (
            target_comment.reply_to if target_comment.reply_to else target_comment
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(
            user=request.user,
            question=root_comment.question,
            reply_to=root_comment,
        )
        return Response(serializer.data, status=201)
