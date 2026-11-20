import uuid
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .fhir import save_fhir_resource
from .models import AuditEvent, FHIRResource

VITALS = {
    'heart_rate': {'code': '8867-4', 'display': 'Heart rate', 'unit': 'beats/min', 'ucum': '/min', 'minimum': 30, 'maximum': 220},
    'oxygen_saturation': {'code': '59408-5', 'display': 'Oxygen saturation', 'unit': '%', 'ucum': '%', 'minimum': 70, 'maximum': 100},
    'body_temperature': {'code': '8310-5', 'display': 'Body temperature', 'unit': '°C', 'ucum': 'Cel', 'minimum': 32, 'maximum': 43.2},
}

def build_observation(message: dict) -> dict:
    if not isinstance(message, dict): raise ValueError('message_must_be_object')
    patient_id = str(message.get('patient_id', ''))
    device_id = str(message.get('device_id', ''))
    vital_type = message.get('type')
    spec = VITALS.get(vital_type)
    if not patient_id or not device_id or not spec: raise ValueError('invalid_reference_or_type')
    value = message.get('value')
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not spec['minimum'] <= value <= spec['maximum']: raise ValueError('value_out_of_range')
    if not FHIRResource.objects.filter(resource_type='Patient', resource_id=patient_id).exists(): raise ValueError('unknown_patient')
    if not FHIRResource.objects.filter(resource_type='Device', resource_id=device_id).exists(): raise ValueError('unknown_device')
    timestamp = message.get('effectiveDateTime')
    if timestamp:
        try: timestamp = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
        except ValueError as exc: raise ValueError('invalid_timestamp') from exc
        if timezone.is_naive(timestamp): timestamp = timezone.make_aware(timestamp)
    else: timestamp = timezone.now()
    return {'resourceType': 'Observation', 'id': uuid.uuid4().hex, 'status': 'final', 'category': [{'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/observation-category', 'code': 'vital-signs', 'display': 'Vital Signs'}]}], 'code': {'coding': [{'system': 'http://loinc.org', 'code': spec['code'], 'display': spec['display']}], 'text': spec['display']}, 'subject': {'reference': f'Patient/{patient_id}'}, 'device': {'reference': f'Device/{device_id}'}, 'effectiveDateTime': timestamp.isoformat(), 'valueQuantity': {'value': float(value), 'unit': spec['unit'], 'system': 'http://unitsofmeasure.org', 'code': spec['ucum']}}

@transaction.atomic
def ingest_message(message: dict) -> FHIRResource:
    record = save_fhir_resource('Observation', build_observation(message))
    AuditEvent.objects.create(actor_role='sensor', action='write', resource_type='observations', route_name='mqtt-ingest', status_code=201)
    return record
