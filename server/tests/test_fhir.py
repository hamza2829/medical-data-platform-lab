import pytest
from rest_framework.exceptions import ValidationError
from core.fhir import save_fhir_resource, validate_fhir_resource
from core.models import FHIRResource

pytestmark = pytest.mark.django_db

def patient_payload():
    return {'resourceType': 'Patient', 'id': 'synthetic-patient-test', 'active': True, 'name': [{'family': 'Example', 'given': ['Riley']}], 'gender': 'unknown', 'birthDate': '1990-01-15'}

def test_patient_requires_fhir_name():
    with pytest.raises(ValidationError): validate_fhir_resource('Patient', {'resourceType': 'Patient', 'id': 'missing-name'})

def test_rejects_type_mismatch():
    with pytest.raises(ValidationError): validate_fhir_resource('Observation', patient_payload())

def test_fhir_patient_resource_versions_are_immutable(demo_users):
    first = save_fhir_resource('Patient', patient_payload(), demo_users['clinician']['user'])
    updated = dict(patient_payload(), active=False)
    second = save_fhir_resource('Patient', updated, demo_users['clinician']['user'])
    assert first.pk == second.pk
    assert second.version == 2
    assert second.schema_version == '1.0.0'
    assert list(second.history.values_list('version', flat=True)) == [1, 2]

def test_observation_requires_reference_code_and_quantity():
    with pytest.raises(ValidationError): validate_fhir_resource('Observation', {'resourceType': 'Observation', 'status': 'final'})

def test_resource_stores_fhir_json_as_json_field():
    record = save_fhir_resource('Patient', patient_payload())
    assert record.data['resourceType'] == 'Patient'
    assert record.data['name'][0]['given'] == ['Riley']
    assert FHIRResource.objects.get(pk=record.pk).schema_version == '1.0.0'
