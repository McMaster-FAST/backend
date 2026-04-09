from rest_framework import serializers

from core.models import QuestionOption

from .question_image_serializer import QuestionImageSerializer


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = [
            'public_id',
            'content',
            'is_answer',
            'selection_frequency',
        ]
        read_only_fields = ['public_id', 'selection_frequency']


class QuestionOptionCRUDSerializer(serializers.ModelSerializer):
    images = QuestionImageSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionOption
        fields = [
            'public_id',
            'content',
            'is_answer',
            'selection_frequency',
            'images',
        ]
        read_only_fields = ['public_id', 'selection_frequency']
        extra_kwargs = {
            'content': {
                'required': True,
                'allow_blank': False,
                'error_messages': {
                    'required': 'Option content is required.',
                    'blank': 'Option content is required.',
                },
            }
        }
