from rest_framework import serializers
from app.models import CustomUser, Event, Ticket, Order, OrderItem


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


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["event", "quantity"]


class CreateOrderItemSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_event_id(self, value):
        if not Event.objects.filter(id=value).exists():
            if not Event.objects.filter(id=value).exists():
                raise serializers.ValidationError("Invalid event ID — event not found.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    attendee = serializers.CharField(source="attendee.username", read_only=True)
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "total_price",
            "payment_method",
            "status",
            "attendee",
            "items",
        ]


class CreateOrderSerializer(serializers.Serializer):
    items = CreateOrderItemSerializer(many=True)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.values)
