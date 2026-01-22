from rest_framework import serializers
from ..models import TestSession

class TestSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSession
        fields = "__all__"
        # These fields should only be modifiable by the server
        read_only_fields = ["user", "course", "subtopic", "current_question"]
