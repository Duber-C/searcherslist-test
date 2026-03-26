from rest_framework import serializers

from users.models.question import Question


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer to expose question metadata to the frontend.

    Exposes `type` (maps to `question_type`) to match frontend naming.
    """
    type = serializers.CharField(source='question_type')
    options = serializers.SerializerMethodField()
    examples = serializers.SerializerMethodField()
    extra = serializers.JSONField()
    component = serializers.CharField(allow_null=True)
    validation = serializers.JSONField()

    class Meta:
        model = Question
        fields = ['id', 'text', 'type', 'required', 'placeholder', 'subtitle', 'order', 'page', 'options', 'examples', 'extra', 'component', 'validation', 'is_active', 'helper_text']

    def get_options(self, obj):
        return obj.options or []

    def get_examples(self, obj):
        # Prefer explicit examples field, fallback to extra.examples
        if getattr(obj, 'examples', None):
            return obj.examples or []
        return (obj.extra or {}).get('examples', [])
