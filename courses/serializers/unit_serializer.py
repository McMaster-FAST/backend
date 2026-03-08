from rest_framework import serializers
from courses.models import Unit


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        exclude = ["id"]
