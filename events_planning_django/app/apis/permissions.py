from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsOrganiser(permissions.BasePermission):
    
    message = "Only organisers can perform this action."
        
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated and request.user.user_type == request.user.UserType.ORGANISER:
            return True
        else:
            raise PermissionDenied(self.message)