from rest_framework import serializers

class AnswerSerializer(serializers.Serializer):
    question_id = serializers.CharField(write_only=True)
    selected_option_id = serializers.CharField(write_only=True)

    correct_option_id = serializers.CharField(read_only=True)
    explanation = serializers.CharField(read_only=True)
