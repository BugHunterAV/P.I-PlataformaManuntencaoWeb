from rest_framework import serializers


class GeminiHistoryItemSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['user', 'model'], default='user')
    text = serializers.CharField()


class GeminiMessageSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, allow_blank=False)
    history = serializers.ListField(
        child=GeminiHistoryItemSerializer(),
        required=False,
        default=list,
    )


class GeminiResponseSerializer(serializers.Serializer):
    response = serializers.CharField()
    model_used = serializers.CharField(required=False, allow_null=True)
