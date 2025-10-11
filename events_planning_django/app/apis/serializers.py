from rest_framework import serializers
from app.models import CustomUser, Event, Ticket, Order


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
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        if CustomUser.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError("Username already exists.")
        if CustomUser.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError("Email already exists.")
        return data

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class EventSerializer(serializers.ModelSerializer):
    organiser = serializers.CharField(source="organiser.username", read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "coordinates",
            "date_time",
            "tickets_amount",
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


class OrderSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    attendee = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "total", "payment_method", "status", "event", "attendee"]


class EventOrderItemSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    events = EventOrderItemSerializer(many=True)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.values)
