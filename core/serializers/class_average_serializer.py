from rest_framework.serializers import (
    IntegerField,
    CharField,
    FloatField,
    Serializer,
    ListField,
)


class UnitStatsSerializer(Serializer):
    unit_id = IntegerField()
    unit_number = IntegerField()
    unit_name = CharField()

    # Stats
    user_accuracy = FloatField(help_text="User's % correctness (0.0 to 1.0)")
    class_accuracy = FloatField(help_text="Class average % correctness")
    questions_attempted = IntegerField(help_text="Total attempts by user in this unit")


class CourseAnalyticsSerializer(Serializer):
    course_code = CharField()
    course_name = CharField()
    units = UnitStatsSerializer(many=True)
