from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from app.models import CustomUser

class IsOrganiser(BasePermission):
    
    message = "Only organisers can perform this action."
        
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated and request.user.user_type == CustomUser.UserType.ORGANISER:
            return True
        else:
            raise PermissionDenied(self.message)
        
        
class IsAttendee(BasePermission):
    
    message = "Only attendees can perform this action."
    
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated and request.user.user_type == CustomUser.UserType.ATTENDEE:
            return True
        else:
            raise PermissionDenied(self.message)