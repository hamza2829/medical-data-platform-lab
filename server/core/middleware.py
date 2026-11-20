from django.utils.deprecation import MiddlewareMixin
from .models import AuditEvent

class AuditLogMiddleware(MiddlewareMixin):
    """Audit API reads and writes without copying PHI, query strings or addresses."""
    WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
    def __call__(self, request):
        response = None
        try:
            response = self.get_response(request)
            return response
        finally:
            if request.path_info.startswith('/api/') and request.method in self.WRITE_METHODS | {'GET', 'HEAD'}:
                actor = getattr(request, 'user', None)
                if not getattr(actor, 'is_authenticated', False): actor = None
                role = ''
                if actor:
                    try: role = actor.role_profile.role
                    except Exception: role = ''
                parts = request.path_info.strip('/').split('/')
                resource_type = parts[1] if len(parts) > 1 else 'api'
                match = getattr(request, 'resolver_match', None)
                AuditEvent.objects.create(
                    actor=actor,
                    actor_role=role,
                    action='write' if request.method in self.WRITE_METHODS else 'read',
                    resource_type=resource_type[:40],
                    route_name=(getattr(match, 'url_name', '') or '')[:80],
                    status_code=getattr(response, 'status_code', 500),
                )
