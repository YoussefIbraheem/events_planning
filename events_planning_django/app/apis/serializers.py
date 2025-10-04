from rest_framework import serializers
from app.models import CustomUser , Event


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ["id", "username", "email"]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class EventSerializer(serializers.ModelSerializer):
    organiser = UserSerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "coordinates",
            "location_type",
            "date_time",
            "tickets_available",
            "ticket_price",
            "organiser",
        ]
        
class CreateEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "coordinates",
            "location_type",
            "date_time",
            "tickets_available",
            "ticket_price",
        ]
        