from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.fhir import save_fhir_resource
from core.models import UserRole

PATIENTS = [
    ('demo-patient-001', 'Mina', 'Solberg', 'female', '1988-03-14'),
    ('demo-patient-002', 'Theo', 'Calder', 'male', '1974-09-02'),
    ('demo-patient-003', 'Iris', 'Novak', 'female', '1996-11-21'),
]
DEVICES = [('demo-device-001', 'Pulse sensor A'), ('demo-device-002', 'Wrist sensor B')]
USERS = [
    ('demo-admin', 'demo-admin@example.test', 'DemoAdmin2026!', 'admin'),
    ('demo-clinician', 'demo-clinician@example.test', 'DemoClinical2026!', 'clinician'),
    ('demo-researcher', 'demo-researcher@example.test', 'DemoResearch2026!', 'researcher'),
]

class Command(BaseCommand):
    help = 'Create synthetic patients, devices, vital signs and demo users.'
    def handle(self, *args, **options):
        for username, email, password, role in USERS:
            user, created = User.objects.get_or_create(username=username, defaults={'email': email, 'is_active': True})
            if created: user.set_password(password); user.save(update_fields=['password'])
            UserRole.objects.update_or_create(user=user, defaults={'role': role})
        for resource_id, first, family, gender, birth_date in PATIENTS:
            save_fhir_resource('Patient', {'resourceType': 'Patient', 'id': resource_id, 'active': True, 'name': [{'use': 'official', 'family': family, 'given': [first]}], 'gender': gender, 'birthDate': birth_date, 'identifier': [{'system': 'https://example.test/demo-patient', 'value': resource_id}]})
        for resource_id, name in DEVICES:
            save_fhir_resource('Device', {'resourceType': 'Device', 'id': resource_id, 'status': 'active', 'deviceName': [{'name': name, 'type': 'user-friendly-name'}], 'type': {'coding': [{'system': 'http://snomed.info/sct', 'code': '706172005', 'display': 'Patient vital signs monitor'}]}})
        now = timezone.now()
        seeds = [
            ('demo-patient-001', 'demo-device-001', 'heart_rate', [71, 73, 75, 72, 78, 82]),
            ('demo-patient-001', 'demo-device-001', 'oxygen_saturation', [98, 97, 98, 96, 96, 95]),
            ('demo-patient-001', 'demo-device-001', 'body_temperature', [36.7, 36.8, 36.9, 37.0, 37.1, 37.2]),
            ('demo-patient-002', 'demo-device-002', 'heart_rate', [92, 96, 99, 104, 106, 108]),
            ('demo-patient-002', 'demo-device-002', 'oxygen_saturation', [96, 95, 94, 93, 91, 90]),
            ('demo-patient-003', 'demo-device-001', 'heart_rate', [66, 67, 65, 68, 67, 66]),
            ('demo-patient-003', 'demo-device-001', 'body_temperature', [36.5, 36.6, 36.5, 36.4, 36.5, 36.6]),
        ]
        from core.ingest import build_observation
        for patient_id, device_id, vital_type, values in seeds:
            for index, value in enumerate(values):
                payload = {'patient_id': patient_id, 'device_id': device_id, 'type': vital_type, 'value': value, 'effectiveDateTime': (now - timedelta(minutes=(len(values) - index) * 5)).isoformat()}
                observation = build_observation(payload)
                observation['id'] = f'demo-{patient_id}-{vital_type}-{index + 1}'
                save_fhir_resource('Observation', observation)
        self.stdout.write(self.style.SUCCESS('Synthetic demo fixtures are ready.'))
