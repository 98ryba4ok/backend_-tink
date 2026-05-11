from rest_framework import serializers
from .models import UserEvent


class UserEventSerializer(serializers.ModelSerializer):
    movie_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = UserEvent
        fields = ('event_type', 'movie_id', 'value')

    def validate_event_type(self, value):
        valid = {choice[0] for choice in UserEvent.EVENT_TYPES}
        if value not in valid:
            raise serializers.ValidationError(f'Invalid event_type: {value}')
        return value
