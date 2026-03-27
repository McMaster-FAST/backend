from core.models import AdaptiveTestQuestionMetric
from core.serializers import AdaptiveTestQuestionMetricSerializer
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class AdaptiveTestQuestionMetricViewSet(viewsets.ModelViewSet):
    queryset = AdaptiveTestQuestionMetric.objects.all()
    serializer_class = AdaptiveTestQuestionMetricSerializer 
    lookup_field = "question__subtopic__public_id"

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="reset")
    def reset_skipped_questions(self, request, question__subtopic__public_id=None):
        """
        Deletes all skipped question records for the user. This is used when a user finishes an adaptive test and we want to reset their skipped question state.
        """
        AdaptiveTestQuestionMetric.objects.filter(
            user=request.user,
            question__subtopic__public_id=question__subtopic__public_id,
        ).update(skipped_at_index=None)
        return Response(status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        # At least for now. I can't think of a reason to show these since they are just used for adaptive testing interally
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
