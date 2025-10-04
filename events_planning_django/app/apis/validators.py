from app.models import CustomUser


class UserLoginValidator:

    @staticmethod
    def validate(data):
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            raise ValueError("Username and password are required")
        if not CustomUser.objects.filter(username=username).exists():
            raise ValueError("User does not exist")
        
        return data


class UserRegisterValidator:

    @staticmethod
    def validate(data):
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        password2 = data.get("password2")
        if not username or not email or not password or not password2:
            raise ValueError("All fields are required")
        if password != password2:
            raise ValueError("Passwords do not match")
        if CustomUser.objects.filter(username=username).exists():
            raise ValueError("Username already exists")
        if CustomUser.objects.filter(email=email).exists():
            raise ValueError("Email already exists")
        return data


class EventValidator:
    
    @staticmethod
    def validate(data):
        title = data.get("title")
        description = data.get("description")
        coordinates = data.get("coordinates")
        location_type = data.get("location_type")
        date_time = data.get("date_time")
        tickets_available = data.get("tickets_available")
        ticket_price = data.get("ticket_price")
        
        if not title or not description or not coordinates or not location_type or not date_time or tickets_available is None or ticket_price is None:
            raise ValueError("All fields are required")
        
        if tickets_available < 0:
            raise ValueError("Tickets available cannot be negative")
        
        if ticket_price < 0:
            raise ValueError("Ticket price cannot be negative") 
        
        return data