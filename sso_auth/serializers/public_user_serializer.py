from django.contrib.auth import get_user_model
from rest_framework import serializers


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["username", "email"]
        read_only_fields = ["__all__"]