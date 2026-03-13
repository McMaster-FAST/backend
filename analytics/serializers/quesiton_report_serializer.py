from analytics.models import QuestionReport, QuestionReportReason
from rest_framework import serializers
from sso_auth.serializers.public_user_serializer import PublicUserSerializer


class QuestionReportSerializer(serializers.ModelSerializer):
    contact_consent = serializers.BooleanField(write_only=True, required=False)
    report_reasons = serializers.SerializerMethodField()
    question_public_id = serializers.UUIDField(source="question.public_id", read_only=True)
    user = serializers.SerializerMethodField(read_only=True)

    def get_user(self, obj):
        return PublicUserSerializer(obj.user).data if obj.user else None

    def get_report_reasons(self, obj):
        return QuestionReportReason.objects.filter(question_report=obj).values_list(
            "reason", flat=True
        )

    def set_report_reasons(self, obj, value):
        # Clear existing reasons
        QuestionReportReason.objects.filter(question_report=obj).delete()
        # Create new reasons
        for reason in value:
            QuestionReportReason.objects.create(question_report=obj, reason=reason)

    class Meta:
        model = QuestionReport
        fields = [
            "public_id",
            "question_public_id",
            "user",
            "report_reasons",
            "timestamp",
            "contact_consent",
        ]
        read_only_fields = ["public_id", "timestamp", "user"]
