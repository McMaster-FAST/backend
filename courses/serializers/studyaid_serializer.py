from rest_framework import serializers
from courses.models import StudyAid


class StudyAidSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyAid
        fields = "__all__"
