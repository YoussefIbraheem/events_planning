from rest_framework import permissions

class IsOrganiser(permissions.BasePermission):
    
    message = "Only organisers can perform this action."
        
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated and request.user.user_type == request.user.UserType.ORGANISER:
            return True
        else:
            raise permissions.PermissionDenied(self.message, code=403)