from rest_framework.permissions import BasePermission, SAFE_METHODS

def user_role(user):
    try: return user.role_profile.role
    except Exception: return ''

class AdminOnly(BasePermission):
    def has_permission(self, request, view): return bool(request.user and request.user.is_authenticated and user_role(request.user) == 'admin')

class PatientAccess(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated: return False
        return request.method in SAFE_METHODS or user_role(request.user) in {'admin', 'clinician'}

class ClinicalWrite(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated: return False
        if request.method in SAFE_METHODS: return user_role(request.user) in {'admin', 'clinician', 'researcher'}
        return user_role(request.user) in {'admin', 'clinician'}

class ClinicianOrAdmin(BasePermission):
    def has_permission(self, request, view): return bool(request.user and request.user.is_authenticated and user_role(request.user) in {'admin', 'clinician'})
