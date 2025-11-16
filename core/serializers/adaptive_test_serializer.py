from rest_framework import serializers

class AdaptiveTestSerializer(serializers.Serializer):
    user_token = serializers.CharField()
    question_group = serializers.CharField()

    def validate_user_token(self, value):
        return value