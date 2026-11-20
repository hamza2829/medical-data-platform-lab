from copy import deepcopy
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import FHIRResource, ResourceVersion

FHIR_RELEASE = 'R4'
SCHEMA_VERSION = '1.0.0'
FHIR_TYPES = {'Patient', 'Observation', 'Device'}

def validate_fhir_resource(resource_type: str, payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise serializers.ValidationError({'resource': 'FHIR resource must be a JSON object.'})
    if resource_type not in FHIR_TYPES or payload.get('resourceType') != resource_type:
        raise serializers.ValidationError({'resourceType': f'Expected a FHIR {resource_type} resource.'})
    if 'id' in payload and (not isinstance(payload['id'], str) or not payload['id'] or len(payload['id']) > 64):
        raise serializers.ValidationError({'id': 'Use a non-empty FHIR id up to 64 characters.'})
    if resource_type == 'Patient':
        names = payload.get('name')
        if not isinstance(names, list) or not names or not all(isinstance(n, dict) and (n.get('text') or n.get('family') or n.get('given')) for n in names):
            raise serializers.ValidationError({'name': 'Patient requires at least one FHIR HumanName.'})
        gender = payload.get('gender', 'unknown')
        if gender not in {'male', 'female', 'other', 'unknown'}:
            raise serializers.ValidationError({'gender': 'Use a FHIR administrative gender code.'})
        if 'birthDate' in payload:
            from datetime import date
            try: date.fromisoformat(payload['birthDate'])
            except (ValueError, TypeError): raise serializers.ValidationError({'birthDate': 'Use a YYYY-MM-DD date.'})
    elif resource_type == 'Observation':
        if payload.get('status') not in {'registered', 'preliminary', 'final', 'amended', 'corrected', 'cancelled', 'entered-in-error', 'unknown'}:
            raise serializers.ValidationError({'status': 'Use a valid FHIR Observation status.'})
        subject = payload.get('subject', {})
        if not isinstance(subject, dict) or not str(subject.get('reference', '')).startswith('Patient/'):
            raise serializers.ValidationError({'subject.reference': 'Observation must reference Patient/{id}.'})
        code = payload.get('code', {}).get('coding', []) if isinstance(payload.get('code'), dict) else []
        if not isinstance(code, list) or not code or not all(isinstance(c, dict) and c.get('code') and c.get('system') for c in code):
            raise serializers.ValidationError({'code': 'Observation requires a coded concept.'})
        quantity = payload.get('valueQuantity')
        if not isinstance(quantity, dict) or isinstance(quantity.get('value'), bool) or not isinstance(quantity.get('value'), (int, float)) or not quantity.get('unit'):
            raise serializers.ValidationError({'valueQuantity': 'Observation requires a numeric value and unit.'})
    else:
        if payload.get('status') not in {'active', 'inactive', 'entered-in-error', 'unknown'}:
            raise serializers.ValidationError({'status': 'Use a valid FHIR Device status.'})
        names = payload.get('deviceName')
        if not isinstance(names, list) or not names or not isinstance(names[0], dict) or not names[0].get('name'):
            raise serializers.ValidationError({'deviceName': 'Device requires a name.'})
    return deepcopy(payload)

@transaction.atomic
def save_fhir_resource(resource_type: str, payload: dict, actor=None) -> FHIRResource:
    cleaned = validate_fhir_resource(resource_type, payload)
    resource_id = cleaned.setdefault('id', __import__('uuid').uuid4().hex)
    cleaned['resourceType'] = resource_type
    meta = cleaned.setdefault('meta', {})
    record = FHIRResource.objects.select_for_update().filter(resource_type=resource_type, resource_id=resource_id).first()
    version = record.version + 1 if record else 1
    meta['versionId'] = str(version)
    meta['lastUpdated'] = timezone.now().isoformat()
    if record:
        record.version = version
        record.schema_version = SCHEMA_VERSION
        record.data = cleaned
        record.save(update_fields=['version', 'schema_version', 'data', 'updated_at'])
    else:
        record = FHIRResource.objects.create(resource_type=resource_type, resource_id=resource_id, schema_version=SCHEMA_VERSION, data=cleaned)
    ResourceVersion.objects.create(resource=record, version=version, schema_version=SCHEMA_VERSION, data=cleaned, changed_by=actor if getattr(actor, 'is_authenticated', False) else None)
    return record

def fhir_json(record: FHIRResource) -> dict:
    body = deepcopy(record.data)
    body.setdefault('meta', {})['versionId'] = str(record.version)
    body['meta']['lastUpdated'] = record.updated_at.isoformat()
    return body

def bundle(records, bundle_type='searchset') -> dict:
    items = [fhir_json(record) for record in records]
    return {'resourceType': 'Bundle', 'type': bundle_type, 'total': len(items), 'entry': [{'fullUrl': f"{item['resourceType']}/{item['id']}", 'resource': item, 'search': {'mode': 'match'}} for item in items]}
