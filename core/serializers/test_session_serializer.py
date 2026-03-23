from rest_framework import serializers

from core.models import TestSession


class TestSessionSerializer(serializers.ModelSerializer):
    subtopic_id = serializers.CharField(source="subtopic.public_id", read_only=True)
    class Meta:
        model = TestSession
        fields = [
            "public_id",
            "subtopic_id",
            "selection_upper_bound",
            "selection_lower_bound",
        ]
        read_only_fields = ["public_id", "subtopic_id"]

    def validate(self, attrs):
        return super().validate(attrs)
