from analytics.models import QuestionReport
from analytics.serializers import QuestionReportSerializer

from rest_framework import viewsets

class QuestionReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to report issues with questions.
    Allows RUDing reports (for admins) and creating new reports (for users).
    WARNING: You shouldn't use this unless you are fetching a single question. If you need data from multiple questions 
    it is likely you should be using QuestionReportAggregateViewSet instead, which aggregates reports per question.
    """

    serializer_class = QuestionReportSerializer
    lookup_field = "question__public_id"
    allowed_methods = ["post", "get", "head", "options", "delete"]

    def get_queryset(self):
        return QuestionReport.objects.filter(question__public_id=self.kwargs.get("question_public_id"))
    
    def perform_create(self, serializer):
        if not serializer.validated_data.get("contact_consent", False):
            serializer.save(user=None)
        else:
            serializer.save(user=self.request.user)