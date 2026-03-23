from core.models import QuestionComment
from rest_framework import serializers


class QuestionCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = QuestionComment
        fields = [
            "public_id",
            "comment_text",
            "user_name",
            "timestamp",
            "replies",
        ]
        read_only_fields = ["public_id", "timestamp"]

    def get_replies(self, obj):
        # This allows the frontend to see nested replies 1-level deep
        replies = QuestionComment.objects.filter(reply_to=obj)
        return QuestionCommentSerializer(replies, many=True).data
