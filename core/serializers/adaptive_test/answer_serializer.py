from rest_framework import serializers

class AnswerSerializer(serializers.Serializer):
    question_id = serializers.CharField(write_only=True)
    selected_option_id = serializers.CharField(write_only=True)
    time_spent = serializers.FloatField(write_only=True, required=False, min_value=0)

    correct_option_id = serializers.CharField(read_only=True)
    explanation = serializers.CharField(read_only=True)
