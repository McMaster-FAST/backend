from analytics.models import QuestionReport
from analytics.models import QuestionReportReason
from rest_framework import serializers
from sso_auth.serializers.public_user_serializer import PublicUserSerializer


class QuestionReportSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True, allow_null=True)
    question = serializers.UUIDField(source='question.public_id', read_only=True)
    report_reasons = serializers.ListField(
        child=serializers.ChoiceField(
            choices=QuestionReportReason.ReportReasonChoices.choices
        ),
        required=False,
        write_only=True,
    )
    contact_consent = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = QuestionReport
        fields = [
            'public_id',
            'question',
            'user',
            'additional_details',
            'report_reasons',
            'contact_consent',
            'timestamp',
        ]
        read_only_fields = ['public_id', 'question', 'user', 'timestamp']

    def validate_report_reasons(self, reasons):
        if len(reasons) != len(set(reasons)):
            raise serializers.ValidationError('Duplicate report reasons are not allowed.')
        return reasons

    def validate(self, attrs):
        if self.instance is None and not attrs.get('report_reasons'):
            raise serializers.ValidationError(
                {'report_reasons': 'At least one report reason is required.'}
            )
        return attrs

    def _get_reporting_user(self, contact_consent):
        request = self.context.get('request')
        if contact_consent is False or request is None:
            return None

        return request.user 

    def _set_report_reasons(self, report, reasons):
        if reasons is None:
            return

        report.report_reasons.all().delete()
        QuestionReportReason.objects.bulk_create(
            [
                QuestionReportReason(question_report=report, reason=reason)
                for reason in reasons
            ]
        )

    def create(self, validated_data):
        report_reasons = validated_data.pop('report_reasons', [])
        contact_consent = validated_data.pop('contact_consent', True)
        validated_data['user'] = self._get_reporting_user(contact_consent)

        report = QuestionReport.objects.create(**validated_data)
        self._set_report_reasons(report, report_reasons)
        return report

    def update(self, instance, validated_data):
        report_reasons = validated_data.pop('report_reasons', None)
        contact_consent = validated_data.pop('contact_consent', None)

        if contact_consent is not None:
            instance.user = self._get_reporting_user(contact_consent)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        self._set_report_reasons(instance, report_reasons)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['report_reasons'] = list(
            instance.report_reasons.values_list('reason', flat=True)
        )
        return data
