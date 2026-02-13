from rest_framework import viewsets
from ..serializers import SavedForLaterSerializer
from ..models import SavedForLater

class SavedForLaterViewSet(viewsets.ModelViewSet):
    # I think we have authentication required by default
    serializer_class = SavedForLaterSerializer
    queryset = SavedForLater.objects.all()

    def get_queryset(self):
        # Filter the queryset to only include items for the authenticated user
        return self.queryset.filter(
            user=self.request.user,
            question__subtopic__unit__course__code=self.kwargs["course_code"],
            question__subtopic__unit__course__is_archived=False,
        )

    def perform_create(self, serializer):
        # Set the user to the authenticated user on creation
        serializer.save(user=self.request.user)
