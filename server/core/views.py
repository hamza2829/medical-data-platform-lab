from copy import deepcopy
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .analysis import analyze_patient
from .fhir import bundle, fhir_json, save_fhir_resource, validate_fhir_resource
from .models import AuditEvent, FHIRResource, ResourceVersion, UserRole
from .permissions import AdminOnly, ClinicalWrite, ClinicianOrAdmin, PatientAccess, user_role
from .pseudonym import original_patient_id, patient_alias, pseudonymized_observation, pseudonymized_patient
from .serializers import LoginSerializer, UserCreateSerializer, UserSerializer, UserUpdateSerializer

class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def get(self, request): return Response({'status': 'ok', 'service': 'medical-data-platform-lab', 'fhir': 'R4', 'schemaVersion': settings.DATA_SCHEMA_VERSION})

class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        user = authenticate(request, username=serializer.validated_data['username'], password=serializer.validated_data['password'])
        if not user or not user.is_active: return Response({'detail': 'Invalid username or password.'}, status=400)
        profile, _ = UserRole.objects.get_or_create(user=user, defaults={'role': 'researcher'})
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': {**UserSerializer(user).data, 'role': profile.role}})

class LogoutView(APIView):
    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PatientCollection(APIView):
    permission_classes = [PatientAccess]
    def get(self, request):
        records = FHIRResource.objects.filter(resource_type='Patient').order_by('resource_id')
        query = request.query_params.get('q', '').strip().casefold()
        if query:
            if user_role(request.user) == 'researcher':
                records = [r for r in records if query in patient_alias(r.resource_id).casefold()]
            else:
                records = [r for r in records if query in str(r.data.get('name', [])).casefold() or query in str(r.data.get('id', '')).casefold()]
        if user_role(request.user) == 'researcher':
            entries = [{'fullUrl': f'Patient/{patient_alias(r.resource_id)}', 'resource': pseudonymized_patient(r), 'search': {'mode': 'match'}} for r in records]
            body = {'resourceType': 'Bundle', 'type': 'searchset', 'total': len(entries), 'entry': entries}
        else: body = bundle(records)
        response = Response(body); response['X-Data-Schema-Version'] = settings.DATA_SCHEMA_VERSION; return response
    def post(self, request):
        record = save_fhir_resource('Patient', request.data, request.user)
        response = Response(fhir_json(record), status=201); response['X-Data-Schema-Version'] = record.schema_version; return response

class PatientDetail(APIView):
    permission_classes = [PatientAccess]
    def get_record(self, patient_id, user):
        if user_role(user) == 'researcher':
            original = original_patient_id(patient_id)
            return FHIRResource.objects.filter(resource_type='Patient', resource_id=original).first() if original else None
        return FHIRResource.objects.filter(resource_type='Patient', resource_id=patient_id).first()
    def get(self, request, patient_id):
        record = self.get_record(patient_id, request.user)
        if not record: return Response({'detail': 'Patient not found.'}, status=404)
        body = pseudonymized_patient(record) if user_role(request.user) == 'researcher' else fhir_json(record)
        response = Response(body); response['X-Data-Schema-Version'] = record.schema_version; return response
    def put(self, request, patient_id): return self.update(request, patient_id)
    def patch(self, request, patient_id): return self.update(request, patient_id, partial=True)
    def update(self, request, patient_id, partial=False):
        record = self.get_record(patient_id, request.user)
        if not record: return Response({'detail': 'Patient not found.'}, status=404)
        payload = deepcopy(record.data)
        if partial: payload.update(request.data)
        else: payload = request.data
        payload['id'] = patient_id
        saved = save_fhir_resource('Patient', payload, request.user)
        response = Response(fhir_json(saved)); response['X-Data-Schema-Version'] = saved.schema_version; return response

class ObservationCollection(APIView):
    permission_classes = [ClinicalWrite]
    def get(self, request):
        records = FHIRResource.objects.filter(resource_type='Observation').order_by('resource_id')
        patient_id = request.query_params.get('patient')
        if patient_id:
            if user_role(request.user) == 'researcher': patient_id = original_patient_id(patient_id) or ''
            records = [r for r in records if r.data.get('subject', {}).get('reference') == f'Patient/{patient_id}']
        if user_role(request.user) == 'researcher':
            entries = [{'fullUrl': f'Observation/{r.resource_id}', 'resource': pseudonymized_observation(r), 'search': {'mode': 'match'}} for r in records]
            body = {'resourceType': 'Bundle', 'type': 'searchset', 'total': len(entries), 'entry': entries}
        else: body = bundle(records)
        response = Response(body); response['X-Data-Schema-Version'] = settings.DATA_SCHEMA_VERSION; return response
    def post(self, request):
        data = validate_fhir_resource('Observation', request.data)
        reference = data.get('subject', {}).get('reference', '')
        patient_id = reference.removeprefix('Patient/')
        if not FHIRResource.objects.filter(resource_type='Patient', resource_id=patient_id).exists(): return Response({'subject': 'Referenced patient does not exist.'}, status=400)
        saved = save_fhir_resource('Observation', data, request.user)
        response = Response(fhir_json(saved), status=201); response['X-Data-Schema-Version'] = saved.schema_version; return response

class PatientObservationCollection(APIView):
    permission_classes = [PatientAccess]
    def get(self, request, patient_id):
        original_id = original_patient_id(patient_id) if user_role(request.user) == 'researcher' else patient_id
        if not original_id or not FHIRResource.objects.filter(resource_type='Patient', resource_id=original_id).exists(): return Response({'detail': 'Patient not found.'}, status=404)
        records = [r for r in FHIRResource.objects.filter(resource_type='Observation') if r.data.get('subject', {}).get('reference') == f'Patient/{original_id}']
        records.sort(key=lambda r: r.data.get('effectiveDateTime', ''))
        body = bundle(records)
        if user_role(request.user) == 'researcher':
            for entry in body['entry']: entry['resource'] = pseudonymized_observation(FHIRResource.objects.get(resource_type='Observation', resource_id=entry['resource']['id']))
        response = Response(body); response['X-Data-Schema-Version'] = settings.DATA_SCHEMA_VERSION; return response

class DeviceCollection(APIView):
    permission_classes = [ClinicalWrite]
    def get(self, request):
        records = FHIRResource.objects.filter(resource_type='Device').order_by('resource_id')
        response = Response(bundle(records)); response['X-Data-Schema-Version'] = settings.DATA_SCHEMA_VERSION; return response
    def post(self, request):
        saved = save_fhir_resource('Device', request.data, request.user)
        response = Response(fhir_json(saved), status=201); response['X-Data-Schema-Version'] = saved.schema_version; return response

class PatientAnalysisView(APIView):
    permission_classes = [PatientAccess]
    def get(self, request, patient_id):
        original_id = original_patient_id(patient_id) if user_role(request.user) == 'researcher' else patient_id
        if not original_id or not FHIRResource.objects.filter(resource_type='Patient', resource_id=original_id).exists(): return Response({'detail': 'Patient not found.'}, status=404)
        result = analyze_patient(original_id)
        if user_role(request.user) == 'researcher': result['patient_id'] = patient_alias(original_id)
        return Response(result)

class PseudonymizedExportView(APIView):
    def get_permissions(self): return [IsAuthenticated()]
    def get(self, request):
        if user_role(request.user) not in {'admin', 'researcher'}: return Response({'detail': 'Only researcher and admin roles can export pseudonymized data.'}, status=403)
        patient_records = list(FHIRResource.objects.filter(resource_type='Patient').order_by('resource_id'))
        mapping = {record.resource_id: patient_alias(record.resource_id) for record in patient_records}
        patients = []
        for record in patient_records:
            patients.append(pseudonymized_patient(record))
        observations = []
        for record in FHIRResource.objects.filter(resource_type='Observation'):
            original = record.data.get('subject', {}).get('reference', '').removeprefix('Patient/')
            if original in mapping: observations.append(pseudonymized_observation(record))
        return Response({'resourceType': 'Bundle', 'type': 'collection', 'schemaVersion': settings.DATA_SCHEMA_VERSION, 'patientCount': len(patients), 'entry': [{'resource': row} for row in patients + observations]})

class GDPRExportView(APIView):
    permission_classes = [ClinicianOrAdmin]
    def get(self, request, patient_id):
        patient = FHIRResource.objects.filter(resource_type='Patient', resource_id=patient_id).first()
        if not patient: return Response({'detail': 'Patient not found.'}, status=404)
        related = [r for r in FHIRResource.objects.filter(resource_type='Observation') if r.data.get('subject', {}).get('reference') == f'Patient/{patient_id}']
        return JsonResponse({'exportedAt': __import__('django.utils.timezone', fromlist=['now']).now().isoformat(), 'schemaVersion': settings.DATA_SCHEMA_VERSION, 'patient': fhir_json(patient), 'observations': [fhir_json(r) for r in related]}, json_dumps_params={'indent': 2})

class GDPRDeleteView(APIView):
    permission_classes = [AdminOnly]
    @transaction.atomic
    def delete(self, request, patient_id):
        patient = FHIRResource.objects.filter(resource_type='Patient', resource_id=patient_id).first()
        if not patient: return Response({'detail': 'Patient not found.'}, status=404)
        observation_ids = [r.pk for r in FHIRResource.objects.filter(resource_type='Observation') if r.data.get('subject', {}).get('reference') == f'Patient/{patient_id}']
        FHIRResource.objects.filter(pk__in=observation_ids).delete()
        patient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserManagementView(APIView):
    permission_classes = [AdminOnly]
    def get(self, request): return Response(UserSerializer(User.objects.select_related('role_profile').order_by('username'), many=True).data)
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data); serializer.is_valid(raise_exception=True); user = serializer.save()
        return Response(UserSerializer(user).data, status=201)

class UserDetailView(APIView):
    permission_classes = [AdminOnly]
    def patch(self, request, user_id):
        user = User.objects.filter(pk=user_id).first()
        if not user: return Response({'detail': 'User not found.'}, status=404)
        serializer = UserUpdateSerializer(data=request.data, partial=True); serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if 'email' in data: user.email = data['email']
        if 'is_active' in data: user.is_active = data['is_active']
        user.save()
        if 'role' in data: UserRole.objects.update_or_create(user=user, defaults={'role': data['role']})
        return Response(UserSerializer(user).data)
    def delete(self, request, user_id):
        user = User.objects.filter(pk=user_id).first()
        if not user: return Response({'detail': 'User not found.'}, status=404)
        if user.pk == request.user.pk: return Response({'detail': 'You cannot delete the active administrator.'}, status=400)
        user.delete(); return Response(status=204)

class AuditLogView(APIView):
    permission_classes = [AdminOnly]
    def get(self, request):
        events = AuditEvent.objects.select_related('actor').all()[:100]
        return Response([{'id': item.id, 'actor': item.actor.username if item.actor else 'system/removed user', 'role': item.actor_role, 'action': item.action, 'resourceType': item.resource_type, 'route': item.route_name, 'status': item.status_code, 'at': item.created_at.isoformat()} for item in events])
