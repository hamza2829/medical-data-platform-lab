import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from core.fhir import save_fhir_resource
from core.models import AuditEvent, FHIRResource

pytestmark = pytest.mark.django_db

def auth_client(token):
    client = APIClient(); client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}'); return client

def test_health_reports_fhir_and_schema_version():
    response = APIClient().get('/api/health/')
    assert response.status_code == 200
    assert response.json()['fhir'] == 'R4'
    assert response.json()['schemaVersion'] == '1.0.0'

def test_login_returns_token_and_role(demo_users):
    response = APIClient().post('/api/auth/token/', {'username': 'test-clinician', 'password': 'UnitTestStrongPass!'}, format='json')
    assert response.status_code == 200
    assert response.json()['user']['role'] == 'clinician'
    assert response.json()['token']

def test_patient_list_is_a_fhir_bundle_and_audited(seeded_demo, demo_users):
    response = auth_client(demo_users['clinician']['token']).get('/api/patients/')
    assert response.status_code == 200
    assert response.json()['resourceType'] == 'Bundle'
    assert response.json()['total'] == 3
    assert response['X-Data-Schema-Version'] == '1.0.0'
    assert AuditEvent.objects.filter(action='read', resource_type='patients').exists()
    event = AuditEvent.objects.filter(action='read', resource_type='patients').latest('id')
    assert event.actor_id == demo_users['clinician']['user'].id
    assert event.actor_role == 'clinician'
    assert event.route_name == 'patient-list'

def test_clinician_can_create_a_valid_patient(demo_users):
    response = auth_client(demo_users['clinician']['token']).post('/api/patients/', {'resourceType': 'Patient', 'name': [{'family': 'Synthetic', 'given': ['Casey']}], 'gender': 'other'}, format='json')
    assert response.status_code == 201
    assert response.json()['resourceType'] == 'Patient'
    assert response.json()['meta']['versionId'] == '1'

def test_clinician_can_register_fhir_device_and_create_observation(seeded_demo, demo_users):
    client = auth_client(demo_users['clinician']['token'])
    device = client.post('/api/devices/', {'resourceType': 'Device', 'id': 'api-demo-device', 'status': 'active', 'deviceName': [{'name': 'Synthetic cuff'}]}, format='json')
    assert device.status_code == 201
    observation = client.post('/api/observations/', {'resourceType': 'Observation', 'status': 'final', 'code': {'coding': [{'system': 'http://loinc.org', 'code': '8867-4'}]}, 'subject': {'reference': 'Patient/demo-patient-001'}, 'valueQuantity': {'value': 74, 'unit': 'beats/min'}}, format='json')
    assert observation.status_code == 201
    assert observation.json()['resourceType'] == 'Observation'

def test_observation_api_rejects_boolean_quantity(seeded_demo, demo_users):
    response = auth_client(demo_users['clinician']['token']).post('/api/observations/', {'resourceType': 'Observation', 'status': 'final', 'code': {'coding': [{'system': 'http://loinc.org', 'code': '8867-4'}]}, 'subject': {'reference': 'Patient/demo-patient-001'}, 'valueQuantity': {'value': True, 'unit': 'beats/min'}}, format='json')
    assert response.status_code == 400

def test_invalid_fhir_patient_is_rejected(demo_users):
    response = auth_client(demo_users['clinician']['token']).post('/api/patients/', {'resourceType': 'Patient'}, format='json')
    assert response.status_code == 400

def test_researcher_can_read_but_cannot_create_a_patient(seeded_demo, demo_users):
    client = auth_client(demo_users['researcher']['token'])
    assert client.get('/api/patients/').status_code == 200
    assert client.post('/api/patients/', {'resourceType': 'Patient', 'name': [{'family': 'Nope'}]}, format='json').status_code == 403

def test_researcher_export_pseudonymizes_direct_identifiers(seeded_demo, demo_users):
    response = auth_client(demo_users['researcher']['token']).get('/api/exports/pseudonymized/')
    assert response.status_code == 200
    text = response.content.decode()
    assert 'Mina' not in text and 'Solberg' not in text and 'birthDate' not in text
    assert 'p-' in text

def test_researcher_patient_reads_never_return_real_names(seeded_demo, demo_users):
    client = auth_client(demo_users['researcher']['token'])
    listing = client.get('/api/patients/').json()
    first = listing['entry'][0]['resource']
    assert first['id'].startswith('p-')
    assert first['name'] == [{'text': first['id']}]
    assert 'birthDate' not in first and 'identifier' not in first
    detail = client.get(f"/api/patients/{first['id']}/").json()
    assert detail['name'] == [{'text': first['id']}]
    observations = client.get(f"/api/patients/{first['id']}/observations/").json()
    assert all(item['resource']['subject']['reference'] == f"Patient/{first['id']}" for item in observations['entry'])

def test_gdpr_export_returns_the_requested_synthetic_record(seeded_demo, demo_users):
    response = auth_client(demo_users['clinician']['token']).get('/api/patients/demo-patient-001/gdpr-export/')
    assert response.status_code == 200
    assert response.json()['patient']['id'] == 'demo-patient-001'
    assert response.json()['observations']

def test_admin_gdpr_delete_removes_patient_and_related_observations(seeded_demo, demo_users):
    client = auth_client(demo_users['admin']['token'])
    response = client.delete('/api/patients/demo-patient-001/gdpr-delete/')
    assert response.status_code == 204
    assert not FHIRResource.objects.filter(resource_type='Patient', resource_id='demo-patient-001').exists()
    assert not any(row.data.get('subject', {}).get('reference') == 'Patient/demo-patient-001' for row in FHIRResource.objects.filter(resource_type='Observation'))

def test_user_management_is_admin_only(demo_users):
    assert auth_client(demo_users['admin']['token']).get('/api/users/').status_code == 200
    assert auth_client(demo_users['clinician']['token']).get('/api/users/').status_code == 403

def test_admin_can_create_users_with_scoped_roles(demo_users):
    response = auth_client(demo_users['admin']['token']).post('/api/users/', {'username': 'research-assistant', 'email': 'assistant@example.test', 'password': 'ResearchAssistant2026!', 'role': 'researcher'}, format='json')
    assert response.status_code == 201
    assert response.json()['role'] == 'researcher'
    assert User.objects.get(username='research-assistant').check_password('ResearchAssistant2026!')
