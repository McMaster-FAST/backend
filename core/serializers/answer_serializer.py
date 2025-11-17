from rest_framework import serializers

class AnswerSerializer(serializers.Serializer):
    user_token = serializers.CharField()
    question_serial_number = serializers.CharField()
    selected_answer = serializers.IntegerField()