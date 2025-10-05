from rest_framework import serializers
from app.models import CustomUser , Event , Ticket


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ["id", "username", "email"]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already exists.")
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists.")
        return data
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    


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
        
        
class TicketSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    attendee = UserSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "event",
            "attendee",
            "created_at",
            "updated_at",
        ]
        

        