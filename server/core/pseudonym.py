import hashlib
import hmac
from copy import deepcopy
from django.conf import settings
from .fhir import fhir_json
from .models import FHIRResource

def patient_alias(resource_id: str) -> str:
    digest = hmac.new(settings.PSEUDONYMIZATION_SALT.encode(), resource_id.encode(), hashlib.sha256).hexdigest()[:12]
    return f'p-{digest}'

def original_patient_id(alias: str) -> str | None:
    for resource_id in FHIRResource.objects.filter(resource_type='Patient').values_list('resource_id', flat=True):
        if patient_alias(resource_id) == alias: return resource_id
    return None

def pseudonymized_patient(record: FHIRResource) -> dict:
    resource = fhir_json(record)
    alias = patient_alias(record.resource_id)
    resource['id'] = alias
    resource['name'] = [{'text': alias}]
    for key in ('birthDate', 'address', 'telecom', 'identifier', 'photo', 'contact', 'link'):
        resource.pop(key, None)
    return resource

def pseudonymized_observation(record: FHIRResource) -> dict:
    resource = deepcopy(fhir_json(record))
    reference = resource.get('subject', {}).get('reference', '')
    patient_id = reference.removeprefix('Patient/')
    if reference.startswith('Patient/'):
        resource['subject'] = {'reference': f'Patient/{patient_alias(patient_id)}'}
    return resource
