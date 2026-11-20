import pytest
from core.analysis import analyze_patient
from core.fhir import save_fhir_resource
from core.ingest import build_observation, ingest_message
from core.models import AuditEvent, FHIRResource

pytestmark = pytest.mark.django_db

def create_sensor_fixtures():
    save_fhir_resource('Patient', {'resourceType': 'Patient', 'id': 'sensor-patient', 'name': [{'family': 'Sample'}]})
    save_fhir_resource('Device', {'resourceType': 'Device', 'id': 'sensor-device', 'status': 'active', 'deviceName': [{'name': 'Synthetic monitor'}]})

def test_sensor_message_becomes_a_fhir_observation():
    create_sensor_fixtures()
    obs = ingest_message({'patient_id': 'sensor-patient', 'device_id': 'sensor-device', 'type': 'heart_rate', 'value': 77})
    assert obs.resource_type == 'Observation'
    assert obs.data['code']['coding'][0]['code'] == '8867-4'
    assert obs.data['subject']['reference'] == 'Patient/sensor-patient'
    assert AuditEvent.objects.filter(route_name='mqtt-ingest', action='write', resource_type='observations').exists()

@pytest.mark.parametrize('message', [
    {'patient_id': 'nope', 'device_id': 'd', 'type': 'heart_rate', 'value': 80},
    {'patient_id': 'p', 'device_id': 'd', 'type': 'heart_rate', 'value': 500},
    {'patient_id': 'p', 'device_id': 'd', 'type': 'mood', 'value': 2},
    {'patient_id': 'p', 'device_id': 'd', 'type': 'heart_rate', 'value': True},
])
def test_sensor_message_validation_rejects_invalid_values(message):
    with pytest.raises(ValueError): build_observation(message)

def test_simulator_style_message_needs_existing_patient_and_device():
    with pytest.raises(ValueError, match='unknown_patient'): build_observation({'patient_id': 'missing', 'device_id': 'missing', 'type': 'heart_rate', 'value': 70})

def test_analysis_builds_trend_and_alerts(seeded_demo):
    result = analyze_patient('demo-patient-002')
    assert result['observation_count'] >= 12
    assert any(item['code'] == '59408-5' and item['severity'] == 'moderate' for item in result['alerts'])
    assert any(item['code'] == '8867-4' for item in result['trends'])

def test_analysis_endpoint_requires_auth_and_returns_alerts(seeded_demo, demo_users):
    client = auth_client_for_test(demo_users['clinician']['token'])
    assert client.get('/api/patients/demo-patient-002/analysis/').status_code == 200
    assert client.get('/api/patients/demo-patient-002/analysis/').json()['alerts']

def auth_client_for_test(token):
    from rest_framework.test import APIClient
    client = APIClient(); client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}'); return client
