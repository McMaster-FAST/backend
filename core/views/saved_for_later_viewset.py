from rest_framework import viewsets

from ..serializers import SavedForLaterSerializer
from ..models import SavedForLater

class SavedForLaterViewSet(viewsets.ModelViewSet):
    # I think we have authentication required by default
    lookup_field = "public_id"
    serializer_class = SavedForLaterSerializer
    queryset = SavedForLater.objects.all()

    def get_queryset(self):
        # Filter the queryset to only include items for the authenticated user
        return self.queryset.filter(user=self.request.user)
