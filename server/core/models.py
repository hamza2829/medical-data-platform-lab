import uuid
from django.conf import settings
from django.db import models

class UserRole(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CLINICIAN = 'clinician', 'Clinician'
        RESEARCHER = 'researcher', 'Researcher'
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='role_profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.RESEARCHER)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.user.username} ({self.role})'

class FHIRResource(models.Model):
    class ResourceType(models.TextChoices):
        PATIENT = 'Patient', 'Patient'
        OBSERVATION = 'Observation', 'Observation'
        DEVICE = 'Device', 'Device'
    resource_type = models.CharField(max_length=24, choices=ResourceType.choices)
    resource_id = models.CharField(max_length=64, default=uuid.uuid4)
    version = models.PositiveIntegerField(default=1)
    schema_version = models.CharField(max_length=24, default='1.0.0')
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['resource_type', 'resource_id'], name='fhir_resource_identity')]
        indexes = [models.Index(fields=['resource_type', 'resource_id']), models.Index(fields=['updated_at'])]
    def __str__(self): return f'{self.resource_type}/{self.resource_id} v{self.version}'

class ResourceVersion(models.Model):
    resource = models.ForeignKey(FHIRResource, on_delete=models.CASCADE, related_name='history')
    version = models.PositiveIntegerField()
    schema_version = models.CharField(max_length=24)
    data = models.JSONField()
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['resource', 'version'], name='fhir_resource_version')]
        ordering = ['resource_id', 'version']

class AuditEvent(models.Model):
    class Action(models.TextChoices):
        READ = 'read', 'Read'
        WRITE = 'write', 'Write'
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    actor_role = models.CharField(max_length=20, blank=True)
    action = models.CharField(max_length=8, choices=Action.choices)
    resource_type = models.CharField(max_length=40, blank=True)
    route_name = models.CharField(max_length=80, blank=True)
    status_code = models.PositiveSmallIntegerField(default=200)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta:
        ordering = ['-created_at']
